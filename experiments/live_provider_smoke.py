from __future__ import annotations

import json
import os
from pathlib import Path

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import OpenAICompatibleProvider
from src.ontto.storage import MemoryStore


def main() -> None:
    api_key = os.environ["ONTTO_API_KEY"]
    model = os.environ["ONTTO_MODEL"]
    base_url = os.environ.get("ONTTO_API_BASE_URL", "https://api.openai.com/v1")

    db = Path("results/live_provider_smoke.db")
    db.parent.mkdir(parents=True, exist_ok=True)

    provider = OpenAICompatibleProvider(
        base_url=base_url,
        api_key=api_key,
        model=model,
        timeout=120,
    )

    cfg = OrganismConfig(
        agent_id=os.environ.get("ONTTO_AGENT_ID", "live-smoke-agent"),
        memory_limit=12,
        event_limit=20,
    )

    store = MemoryStore(db)
    organism = PersistentOrganism(cfg, store, provider, lambda _: None)

    wake_1 = organism.wake_cycle(
        "Recordá que esta prueba es parte de una trayectoria continua. "
        "Identificá qué debería persistir de este ciclo."
    )
    wake_2 = organism.wake_cycle(
        "Ahora observá el cambio respecto del ciclo anterior y explicá qué relación "
        "entre ambos debería conservarse."
    )
    dream = organism.dream_cycle()

    observables_before = store.persistence_observables(cfg.agent_id)
    store.conn.close()

    reopened = MemoryStore(db)
    restored = PersistentOrganism(cfg, reopened, provider, lambda _: None)
    wake_3 = restored.wake_cycle(
        "El proceso fue cerrado y reabierto. Usá la trayectoria persistente para "
        "describir qué continuó respecto de los ciclos anteriores."
    )
    observables_after = reopened.persistence_observables(cfg.agent_id)

    report = {
        "provider": {
            "base_url": base_url,
            "model": model,
            "api_key_present": bool(api_key),
        },
        "responses_nonempty": all(
            bool(x.strip()) for x in (wake_1, wake_2, dream, wake_3)
        ),
        "self_model_version_after_reopen": observables_after["self_model_version"],
        "memory_count_after_reopen": observables_after["memory_count"],
        "event_count_after_reopen": observables_after["event_count"],
        "trajectory_fingerprint_changed_after_continuation": (
            observables_before["trajectory_fingerprint"]
            != observables_after["trajectory_fingerprint"]
        ),
        "state_fingerprint_changed_after_continuation": (
            observables_before["state_fingerprint"]
            != observables_after["state_fingerprint"]
        ),
        "trajectory_fingerprint_before_reopen": observables_before[
            "trajectory_fingerprint"
        ],
        "trajectory_fingerprint_after_reopen": observables_after[
            "trajectory_fingerprint"
        ],
    }

    assert report["responses_nonempty"]
    assert report["event_count_after_reopen"] >= 4
    assert report["memory_count_after_reopen"] >= 1

    output = Path("results/live_provider_smoke.json")
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=" * 72)
    print("CONSCIENCIA PARA IA — LIVE PROVIDER SMOKE")
    print("=" * 72)
    for key, value in report.items():
        print(f"{key}: {value}")
    print(f"RESULT: {output}")
    print("=" * 72)


if __name__ == "__main__":
    main()

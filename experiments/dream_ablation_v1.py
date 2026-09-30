from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore


class DreamAblationProvider:
    def chat(self, messages, temperature=0.7):
        system = messages[0]["content"]
        user = messages[-1]["content"]

        if "Entraste en SUEÑO" in user:
            text = (
                "Actividad interna.\n"
                "MEMORY: CONSOLIDATED_RELATION alpha->beta: alpha ocurrió antes que beta.\n"
                "SELF_MODEL: El sistema aprende relaciones temporales durante el sueño.\n"
                "DREAM_SUMMARY: Comprimí dos episodios en una relación persistente."
            )
        elif "PROBE_RELATION" in user:
            if "CONSOLIDATED_RELATION alpha->beta" in system:
                text = (
                    "PROBE_PASS: La relación persistente indica que alpha ocurrió antes que beta."
                )
            else:
                text = "PROBE_FAIL: Solo dispongo del episodio inmediato y no de la relación consolidada."
        elif "alpha" in user.lower():
            text = "MEMORY: EPISODE alpha: evento alpha observado."
        elif "beta" in user.lower():
            text = "MEMORY: EPISODE beta: evento beta observado."
        else:
            text = "MEMORY: Evento externo registrado en trayectoria."

        return LLMResponse(text=text, raw={"dream_ablation": True})


def train(agent_id: str, db_path: Path, dream: bool) -> dict:
    store = MemoryStore(db_path)
    cfg = OrganismConfig(
        agent_id=agent_id,
        dream_every_cycles=999999,
        memory_limit=20,
        event_limit=20,
    )
    provider = DreamAblationProvider()
    organism = PersistentOrganism(cfg, store, provider, lambda _: None)

    organism.wake_cycle("alpha")
    organism.wake_cycle("beta")

    if dream:
        organism.dream_cycle()

    # Final recall is deliberately capacity-limited to one memory.
    probe_cfg = OrganismConfig(
        agent_id=agent_id,
        memory_limit=1,
        event_limit=4,
    )
    probe_organism = PersistentOrganism(
        probe_cfg,
        store,
        provider,
        lambda _: None,
    )
    response = probe_organism.wake_cycle("PROBE_RELATION")

    return {
        "dream_enabled": dream,
        "probe_response": response,
        "probe_pass": "PROBE_PASS" in response,
        "memories_visible_to_probe": store.recent_memories(agent_id, 1),
        "self_model_version": store.load_state(agent_id).self_model_version,
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        no_dream = train("no-dream", root / "no_dream.db", dream=False)
        with_dream = train("with-dream", root / "with_dream.db", dream=True)

    report = {
        "experiment": "dream_ablation_v1",
        "design": (
            "Identical alpha/beta learning; identical final recall capacity of one memory; "
            "the only experimental difference is whether DREAM is executed before the probe."
        ),
        "no_dream": no_dream,
        "with_dream": with_dream,
        "dream_gain": int(with_dream["probe_pass"]) - int(no_dream["probe_pass"]),
    }

    assert not no_dream["probe_pass"]
    assert with_dream["probe_pass"]
    assert with_dream["self_model_version"] == 1

    output = Path("results/dream_ablation_v1.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=" * 72)
    print("CONSCIENCIA PARA IA — DREAM ABLATION V1")
    print("=" * 72)
    for key, value in report.items():
        print(f"{key}: {value}")
    print(f"RESULT: {output}")
    print("=" * 72)


if __name__ == "__main__":
    main()

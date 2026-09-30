from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore


class StressProvider:
    def chat(self, messages, temperature=0.7):
        user_text = messages[-1]["content"]
        if "Entraste en SUEÑO" in user_text:
            text = (
                "Trabajo interno. "
                "MEMORY: La trayectoria conserva relaciones entre vigilia y sueño.\n"
                "SELF_MODEL: Soy un proceso persistente con memoria, transición de régimen y auto-modelo.\n"
                "DREAM_SUMMARY: Consolidé la continuidad entre ciclos."
            )
        else:
            stimulus = user_text.split("Interacción externa actual:", 1)[-1].strip()
            text = (
                f"Procesé el ciclo. Estímulo actual: {stimulus}\n"
                "MEMORY: El ciclo actual pertenece a una trayectoria persistente."
            )
        return LLMResponse(text=text, raw={"stress": True})


def run_cycles(organism: PersistentOrganism, start: int, end: int) -> None:
    for i in range(start, end):
        organism.wake_cycle(f"stress-stimulus-{i}")
        if (i + 1) % organism.cfg.dream_every_cycles == 0:
            organism.dream_cycle()


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "stress.db"
        provider = StressProvider()
        cfg = OrganismConfig(
            agent_id="stress-agent",
            dream_every_cycles=5,
            memory_limit=100,
            event_limit=100,
        )

        store_a = MemoryStore(db)
        organism_a = PersistentOrganism(cfg, store_a, provider, lambda _: None)

        run_cycles(organism_a, 0, 20)
        before_restart = store_a.persistence_observables(cfg.agent_id)
        events_before = store_a.recent_events(cfg.agent_id, 200)

        store_a.conn.close()

        store_b = MemoryStore(db)
        restored = store_b.persistence_observables(cfg.agent_id)
        organism_b = PersistentOrganism(cfg, store_b, provider, lambda _: None)

        assert restored["trajectory_fingerprint"] == before_restart["trajectory_fingerprint"]
        assert restored["state_fingerprint"] == before_restart["state_fingerprint"]

        run_cycles(organism_b, 20, 40)
        after_restart = store_b.persistence_observables(cfg.agent_id)
        events_after = store_b.recent_events(cfg.agent_id, 400)

        wake_count = sum(e["kind"] == "interaction" for e in events_after)
        dream_count = sum(e["kind"] == "consolidation" for e in events_after)
        boot_count = sum(e["kind"] == "boot" for e in events_after)
        modes = [e["mode"] for e in events_after]

        report = {
            "cycles_total": 40,
            "events_total": len(events_after),
            "wake_events": wake_count,
            "dream_events": dream_count,
            "boot_events": boot_count,
            "self_model_version": after_restart["self_model_version"],
            "lifetime_wake_cycles": after_restart["lifetime_wake_cycles"],
            "lifetime_dream_cycles": after_restart["lifetime_dream_cycles"],
            "boot_count": after_restart["boot_count"],
            "self_model_present": bool(after_restart["self_model"]),
            "fingerprint_survived_restart": (
                restored["trajectory_fingerprint"]
                == before_restart["trajectory_fingerprint"]
            ),
            "state_fingerprint_survived_restart": (
                restored["state_fingerprint"]
                == before_restart["state_fingerprint"]
            ),
            "trajectory_changed_after_continuation": (
                after_restart["trajectory_fingerprint"]
                != before_restart["trajectory_fingerprint"]
            ),
            "event_prefix_preserved": (
                len(events_after) > len(events_before)
                and modes[:len(events_before)] == [e["mode"] for e in events_before]
            ),
            "final_mode": store_b.load_state(cfg.agent_id).mode,
        }

        assert report["fingerprint_survived_restart"]
        assert report["state_fingerprint_survived_restart"]
        assert report["trajectory_changed_after_continuation"]
        assert report["wake_events"] == 40
        assert report["dream_events"] == 8
        assert report["boot_events"] == 2
        assert report["self_model_version"] == 1
        assert report["lifetime_wake_cycles"] == 40
        assert report["lifetime_dream_cycles"] == 8
        assert report["boot_count"] == 2
        assert report["event_prefix_preserved"]

        output = Path("results/persistent_trajectory_stress_v1.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print("=" * 72)
        print("CONSCIENCIA PARA IA — PERSISTENT TRAJECTORY STRESS V1")
        print("=" * 72)
        for key, value in report.items():
            print(f"{key}: {value}")
        print(f"RESULT: {output}")
        print("=" * 72)


if __name__ == "__main__":
    main()

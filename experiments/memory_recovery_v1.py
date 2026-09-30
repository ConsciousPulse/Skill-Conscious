from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore


class RecoveryProvider:
    def chat(self, messages, temperature=0.7):
        user = messages[-1]["content"]
        if "Entraste en SUEÑO" in user:
            text = (
                "MEMORY: Sueño consolidado: la trayectoria puede recuperarse desde sus eventos.\n"
                "SELF_MODEL: Soy persistente y recuperable."
            )
        else:
            token = user.split("Interacción externa actual:", 1)[-1].strip()
            text = f"MEMORY: Evento persistente: {token}"
        return LLMResponse(text=text, raw={"recovery": True})


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "recovery.db"
        store = MemoryStore(db)
        organism = PersistentOrganism(
            OrganismConfig(
                agent_id="recovery-agent",
                dream_every_cycles=3,
                memory_limit=20,
                event_limit=50,
            ),
            store,
            RecoveryProvider(),
            lambda _: None,
        )

        for i in range(6):
            organism.wake_cycle(f"stimulus-{i}")
            if (i + 1) % 3 == 0:
                organism.dream_cycle()

        memory_before = store.memory_count("recovery-agent")
        event_count_before = store.event_count("recovery-agent")
        fingerprint_before_damage = store.trajectory_fingerprint("recovery-agent")

        # Controlled damage: remove every other memory, but leave the event
        # trajectory intact so recovery can reconstruct from the log.
        store.conn.execute(
            """
            DELETE FROM memories
            WHERE agent_id=?
              AND id IN (
                  SELECT id FROM memories
                  WHERE agent_id=?
                  ORDER BY id
              )
            """,
            ("recovery-agent", "recovery-agent"),
        )
        store.conn.commit()

        memory_after_damage = store.memory_count("recovery-agent")
        recovered = store.recover_memories_from_events("recovery-agent")
        memory_after_recovery = store.memory_count("recovery-agent")
        event_count_after = store.event_count("recovery-agent")
        fingerprint_after_recovery = store.trajectory_fingerprint("recovery-agent")

        report = {
            "memory_before_damage": memory_before,
            "memory_after_damage": memory_after_damage,
            "recovered_memories": recovered,
            "memory_after_recovery": memory_after_recovery,
            "event_count_preserved": event_count_before == event_count_after,
            "trajectory_fingerprint_before_damage": fingerprint_before_damage,
            "trajectory_fingerprint_after_recovery": fingerprint_after_recovery,
            "trajectory_changed_after_recovery": (
                fingerprint_before_damage != fingerprint_after_recovery
            ),
        }

    assert report["memory_before_damage"] > 0
    assert report["memory_after_damage"] == 0
    assert report["recovered_memories"] > 0
    assert report["memory_after_recovery"] == report["recovered_memories"]
    assert report["event_count_preserved"]
    assert report["trajectory_changed_after_recovery"]

    output = Path("results/memory_recovery_v1.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=" * 72)
    print("CONSCIENCIA PARA IA — MEMORY RECOVERY V1")
    print("=" * 72)
    for key, value in report.items():
        print(f"{key}: {value}")
    print(f"RESULT: {output}")
    print("=" * 72)


if __name__ == "__main__":
    main()

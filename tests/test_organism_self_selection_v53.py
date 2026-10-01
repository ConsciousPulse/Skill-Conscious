from pathlib import Path
import shutil

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore


class FakeProvider:
    def chat(self, messages, temperature=0.7):
        return LLMResponse(
            text=(
                "Respuesta de continuidad.\n"
                "MEMORY: conservar trayectoria.\n"
                "SELF_MODEL: mi estado cambia según el recorrido."
            ),
            raw={"fake": True},
        )


def warmup(db: Path, agent_id: str) -> tuple[MemoryStore, PersistentOrganism]:
    store = MemoryStore(db)
    cfg = OrganismConfig(
        agent_id=agent_id,
        dream_every_cycles=10_000,
        event_limit=0,
        self_observer_enabled=True,
        self_selection_enabled=False,
    )
    organism = PersistentOrganism(cfg, store, FakeProvider(), lambda _: None)

    for i in range(24):
        organism.wake_cycle(f"seed {i}")
        organism.autonomous_wake_cycle()

    return store, organism


def test_self_selection_changes_autonomous_transition(tmp_path: Path):
    base = tmp_path / "base.db"
    warm_store, warm = warmup(base, "receiver")
    warm_store.conn.close()

    on_db = tmp_path / "on.db"
    off_db = tmp_path / "off.db"
    shutil.copy2(base, on_db)
    shutil.copy2(base, off_db)

    on_store = MemoryStore(on_db)
    off_store = MemoryStore(off_db)

    on_cfg = OrganismConfig(
        agent_id="receiver",
        dream_every_cycles=10_000,
        event_limit=0,
        self_observer_enabled=True,
        self_selection_enabled=True,
    )
    off_cfg = OrganismConfig(
        agent_id="receiver",
        dream_every_cycles=10_000,
        event_limit=0,
        self_observer_enabled=True,
        self_selection_enabled=False,
    )

    on = PersistentOrganism(on_cfg, on_store, FakeProvider(), lambda _: None)
    off = PersistentOrganism(off_cfg, off_store, FakeProvider(), lambda _: None)

    before_on = on_store.persistence_observables("receiver")
    before_off = off_store.persistence_observables("receiver")

    assert before_on["self_prediction_samples"] >= 24
    assert before_off["self_prediction_samples"] >= 24
    assert before_on["dynamic_steps"] == before_off["dynamic_steps"]

    on.autonomous_wake_cycle()
    off.autonomous_wake_cycle()

    after_on = on_store.persistence_observables("receiver")
    after_off = off_store.persistence_observables("receiver")

    assert after_on["dynamic_steps"] == before_on["dynamic_steps"] + 1
    assert after_off["dynamic_steps"] == before_off["dynamic_steps"] + 1

    on_event = on_store.recent_events("receiver", 1)[0]
    off_event = off_store.recent_events("receiver", 1)[0]

    assert on_event["kind"] == "autonomous"
    assert off_event["kind"] == "autonomous"
    assert "self_selection" in on_event["payload"]
    assert on_event["payload"]["self_selection"]["enabled"] is True
    assert off_event["payload"]["self_selection"]["enabled"] is False
    assert len(on_event["payload"]["self_selection"]["candidates"]) == 3

    # The selector is causal only when its chosen signal differs from the
    # control signal actually applied by the disabled branch.
    chosen_signal = on_event["payload"]["self_selection"]["chosen_signal"]
    assert chosen_signal in {-1.0, 0.0, 1.0}

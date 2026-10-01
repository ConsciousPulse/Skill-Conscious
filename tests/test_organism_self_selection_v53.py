from pathlib import Path

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


def test_self_selection_changes_autonomous_transition(tmp_path: Path):
    db_on = tmp_path / "on.db"
    db_off = tmp_path / "off.db"

    on_store = MemoryStore(db_on)
    off_store = MemoryStore(db_off)

    cfg_on = OrganismConfig(
        agent_id="on",
        dream_every_cycles=10_000,
        event_limit=0,
        self_observer_enabled=True,
        self_selection_enabled=True,
    )
    cfg_off = OrganismConfig(
        agent_id="off",
        dream_every_cycles=10_000,
        event_limit=0,
        self_observer_enabled=True,
        self_selection_enabled=False,
    )

    on = PersistentOrganism(cfg_on, on_store, FakeProvider(), lambda _: None)
    off = PersistentOrganism(cfg_off, off_store, FakeProvider(), lambda _: None)

    for i in range(40):
        on.wake_cycle(f"seed {i}")
        off.wake_cycle(f"seed {i}")

    before_on = on_store.persistence_observables("on")
    before_off = off_store.persistence_observables("off")

    on.autonomous_wake_cycle()
    off.autonomous_wake_cycle()

    after_on = on_store.persistence_observables("on")
    after_off = off_store.persistence_observables("off")

    assert after_on["dynamic_steps"] == before_on["dynamic_steps"] + 1
    assert after_off["dynamic_steps"] == before_off["dynamic_steps"] + 1

    on_event = on_store.recent_events("on", 1)[0]
    assert on_event["kind"] == "autonomous"
    assert "self_selection" in on_event["payload"]

    assert isinstance(on_event["payload"]["self_selection"]["chosen_signal"], float)

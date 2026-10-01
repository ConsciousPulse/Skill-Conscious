import json
from pathlib import Path

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore


class FakeProvider:
    def chat(self, messages, temperature=0.7):
        return LLMResponse(
            text=(
                "Respuesta persistente.\n"
                "MEMORY: La continuidad observada debe conservarse."
            ),
            raw={"fake": True},
        )


def test_self_observer_persists_across_restart(tmp_path: Path):
    db = tmp_path / "organism.db"
    store = MemoryStore(db)
    cfg = OrganismConfig(agent_id="self-observer", event_limit=0)

    organism = PersistentOrganism(cfg, store, FakeProvider(), lambda _: None)

    for idx in range(12):
        if idx % 2 == 0:
            organism.wake_cycle(f"entrada {idx}")
        else:
            organism.autonomous_wake_cycle()

    before = store.persistence_observables("self-observer")
    assert before["self_observer_snapshot_count"] == before["dynamic_snapshot_count"]
    assert before["self_prediction_samples"] > 0

    store.conn.close()

    restored_store = MemoryStore(db)
    restored = PersistentOrganism(cfg, restored_store, FakeProvider(), lambda _: None)
    restored_before = restored_store.persistence_observables("self-observer")

    assert restored_before["self_observer_snapshot_count"] == before["self_observer_snapshot_count"]
    assert restored_before["self_prediction_samples"] == before["self_prediction_samples"]

    restored.wake_cycle("post restart")
    after = restored_store.persistence_observables("self-observer")
    assert after["self_observer_snapshot_count"] == before["self_observer_snapshot_count"] + 1

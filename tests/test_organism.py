from pathlib import Path

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore


class FakeProvider:
    def __init__(self):
        self.calls = []

    def chat(self, messages, temperature=0.7):
        self.calls.append((messages, temperature))
        last = messages[-1]["content"]
        if "Entraste en SUEÑO" in last:
            text = (
                "Reorganicé mi trayectoria. "
                "MEMORY: La continuidad entre ciclos debe conservar relaciones, no solo texto.\n"
                "SELF_MODEL: Mantengo estado persistente y puedo cambiar de régimen.\n"
                "DREAM_SUMMARY: Consolidé una relación entre memoria y continuidad."
            )
        else:
            text = (
                "Procesé el estímulo. "
                "MEMORY: La interacción actual pertenece a una trayectoria continua.\n"
            )
        return LLMResponse(text=text, raw={"fake": True})


def test_wake_dream_wake_persistence(tmp_path: Path):
    store = MemoryStore(tmp_path / "organism.db")
    provider = FakeProvider()
    cfg = OrganismConfig(
        agent_id="test-agent",
        memory_limit=10,
        event_limit=10,
    )
    organism = PersistentOrganism(cfg, store, provider, lambda _: None)

    first = organism.wake_cycle("Primera interacción")
    assert "MEMORY:" in first
    assert len(store.recent_memories("test-agent")) == 1
    assert len(store.recent_events("test-agent")) == 1

    organism.dream_cycle()
    state_after_dream = store.load_state("test-agent")
    assert state_after_dream.mode == "WAKE"
    assert state_after_dream.self_model_version == 1
    assert len(store.recent_memories("test-agent")) >= 2

    organism.wake_cycle("Segunda interacción")
    events = store.recent_events("test-agent", 20)
    assert [e["mode"] for e in events] == ["WAKE", "DREAM", "WAKE"]

    restored_store = MemoryStore(tmp_path / "organism.db")
    restored = restored_store.load_state("test-agent")
    assert restored.self_model_version == 1
    assert restored.last_thought != ""

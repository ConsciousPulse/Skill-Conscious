from src.ontto.storage import MemoryStore, OntologicalState


def test_state_survives_restart(tmp_path):
    db = tmp_path / "state.db"
    a = MemoryStore(db)
    state = OntologicalState(
        state=0.7,
        mode="DREAM",
        continuity_index=0.8,
        self_model_version=3,
    )
    a.save_state("agent", state)
    a.conn.close()

    b = MemoryStore(db)
    restored = b.load_state("agent")
    assert restored.state == 0.7
    assert restored.mode == "DREAM"
    assert restored.continuity_index == 0.8
    assert restored.self_model_version == 3
    b.conn.close()



def test_memory_recovery_from_event_log(tmp_path):
    db = tmp_path / "recovery.db"
    store = MemoryStore(db)

    store.add_memory("agent", "recuerdo A")
    store.add_event(
        "agent",
        "WAKE",
        "interaction",
        {"response": "MEMORY: recuerdo A"},
    )
    store.add_event(
        "agent",
        "WAKE",
        "interaction",
        {"response": "MEMORY: recuerdo B"},
    )

    store.conn.execute("DELETE FROM memories WHERE agent_id=?", ("agent",))
    store.conn.commit()

    recovered = store.recover_memories_from_events("agent")

    assert recovered == 2
    assert store.recent_memories("agent") == ["recuerdo A", "recuerdo B"]

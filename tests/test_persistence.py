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

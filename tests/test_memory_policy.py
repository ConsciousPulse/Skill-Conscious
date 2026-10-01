from src.ontto.memory_policy import ContinuityMemoryPolicy


def test_continuity_memory_policy_rejects_redundant_memory():
    policy = ContinuityMemoryPolicy()
    admission = policy.admit(
        "La relación estable mantiene continuidad",
        ["La relación estable mantiene continuidad"],
        importance=0.2,
    )
    assert admission.coupling == 1.0
    assert admission.decision.exists is False


def test_continuity_memory_policy_accepts_novel_low_persistence_memory():
    policy = ContinuityMemoryPolicy()
    admission = policy.admit(
        "La transición futura abre una ruta nueva",
        ["El ciclo anterior conservó estado basal"],
        importance=0.2,
    )
    assert admission.novelty > 0.5
    assert admission.decision.exists is True


def test_continuity_memory_policy_is_deterministic():
    policy = ContinuityMemoryPolicy()
    a = policy.admit("alpha beta", ["alpha gamma"], importance=0.2)
    b = policy.admit("alpha beta", ["alpha gamma"], importance=0.2)
    assert a == b

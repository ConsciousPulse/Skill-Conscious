from src.ontto.continuity import AevumContinuityGate


def test_aevum_gate_frozen_coefficients():
    gate = AevumContinuityGate()
    result = gate.evaluate(0.7, 0.3, 0.3)
    assert result.exists is True
    assert abs(result.omega - 0.3) < 1e-12


def test_aevum_gate_rejects_future_closing_transition():
    gate = AevumContinuityGate()
    result = gate.evaluate(0.2, 0.7, 0.8)
    assert result.exists is False
    assert result.omega < 0.0


def test_aevum_gate_is_deterministic():
    gate = AevumContinuityGate()
    a = gate.evaluate(0.4, 0.2, 0.1)
    b = gate.evaluate(0.4, 0.2, 0.1)
    assert a == b

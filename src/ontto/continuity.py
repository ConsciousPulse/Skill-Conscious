from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContinuityDecision:
    novelty: float
    coupling: float
    persistence: float
    omega: float
    exists: bool


class AevumContinuityGate:
    """AEVUM-inspired future-compatibility gate.

    The coefficients are frozen to the uploaded AEVUM specification. This class
    is an adapter for organism experiments, not a redefinition of canonical AEVUM.
    """

    A = 1.2
    B = 1.0
    C = 0.8

    def evaluate(self, novelty: float, coupling: float, persistence: float) -> ContinuityDecision:
        values = (float(novelty), float(coupling), float(persistence))
        if any(value < 0.0 or value > 1.0 for value in values):
            raise ValueError("novelty, coupling and persistence must be in [0, 1]")
        omega = self.A * novelty - self.B * coupling - self.C * persistence
        return ContinuityDecision(
            novelty=novelty,
            coupling=coupling,
            persistence=persistence,
            omega=float(omega),
            exists=bool(omega > 0.0),
        )
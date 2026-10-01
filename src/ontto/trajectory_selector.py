from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .self_observer import SelfObserver, SelfPrediction


@dataclass(frozen=True)
class TrajectoryCandidate:
    signal: float
    prediction: SelfPrediction
    attractor_distance: float
    displacement: float
    score: float


class TrajectorySelector:
    """Counterfactual selector driven by the organism's self-model.

    The selector does not inspect the hidden simulator outcome. It evaluates
    counterfactual next states predicted by SelfObserver and chooses the signal
    with the highest declared coherence score.
    """

    def __init__(self, attractor_weight: float = 0.70, coherence_weight: float = 0.30):
        if attractor_weight < 0 or coherence_weight < 0:
            raise ValueError("selector weights must be non-negative")
        total = attractor_weight + coherence_weight
        if total <= 0:
            raise ValueError("selector weights cannot both be zero")
        self.attractor_weight = float(attractor_weight / total)
        self.coherence_weight = float(coherence_weight / total)

    def evaluate(
        self,
        observer: SelfObserver,
        *,
        current_state: float,
        current_memory: float,
        current_pressure: float,
        current_input: float,
        current_attractor: float,
        steps_delta: int,
        signals: Iterable[float] = (-1.0, 0.0, 1.0),
    ) -> tuple[TrajectoryCandidate, ...]:
        candidates = []
        for signal in signals:
            prediction = observer.predict(
                previous_state=current_state,
                state=current_state,
                memory=current_memory,
                pressure=current_pressure,
                last_input=float(signal),
                attractor_distance=abs(current_state - current_attractor),
                steps_delta=steps_delta,
            )
            distance = abs(prediction.predicted_state - current_attractor)
            displacement = abs(prediction.predicted_state - current_state)
            # Higher score = closer to the attractor while preserving continuity.
            attractor_term = 1.0 / (1.0 + distance)
            coherence_term = 1.0 / (1.0 + displacement)
            score = (
                self.attractor_weight * attractor_term
                + self.coherence_weight * coherence_term
            )
            candidates.append(
                TrajectoryCandidate(
                    signal=float(signal),
                    prediction=prediction,
                    attractor_distance=float(distance),
                    displacement=float(displacement),
                    score=float(score),
                )
            )
        return tuple(candidates)

    @staticmethod
    def choose(candidates: tuple[TrajectoryCandidate, ...]) -> TrajectoryCandidate:
        if not candidates:
            raise ValueError("at least one trajectory candidate is required")
        return max(candidates, key=lambda c: (c.score, -abs(c.signal)))
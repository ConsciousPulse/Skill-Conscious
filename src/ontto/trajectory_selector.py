from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .self_observer import SelfObserver, SelfPrediction
from .meta_observer import MetaSelfObserver


@dataclass(frozen=True)
class TrajectoryCandidate:
    signal: float
    prediction: SelfPrediction
    attractor_distance: float
    displacement: float
    predicted_error: float | None
    score: float


class TrajectorySelector:
    """Counterfactual selector driven by the organism's self-model.

    The selector can optionally include a meta-self-model term that estimates
    how much prediction error the primary self-model is likely to make for
    each candidate trajectory.
    """

    def __init__(
        self,
        attractor_weight: float = 0.70,
        coherence_weight: float = 0.30,
        meta_error_weight: float = 0.0,
    ):
        if attractor_weight < 0 or coherence_weight < 0 or meta_error_weight < 0:
            raise ValueError("selector weights must be non-negative")
        total = attractor_weight + coherence_weight + meta_error_weight
        if total <= 0:
            raise ValueError("selector weights cannot all be zero")
        self.attractor_weight = float(attractor_weight / total)
        self.coherence_weight = float(coherence_weight / total)
        self.meta_error_weight = float(meta_error_weight / total)

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
        meta_observer: MetaSelfObserver | None = None,
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
            predicted_error = (
                meta_observer.predict_error(
                    previous_state=current_state,
                    state=current_state,
                    memory=current_memory,
                    pressure=current_pressure,
                    last_input=float(signal),
                    attractor_distance=abs(current_state - current_attractor),
                    steps_delta=steps_delta,
                )
                if meta_observer is not None
                else None
            )

            attractor_term = 1.0 / (1.0 + distance)
            coherence_term = 1.0 / (1.0 + displacement)
            meta_term = (
                1.0 / (1.0 + max(0.0, predicted_error))
                if predicted_error is not None
                else 0.0
            )
            score = (
                self.attractor_weight * attractor_term
                + self.coherence_weight * coherence_term
                + self.meta_error_weight * meta_term
            )
            candidates.append(
                TrajectoryCandidate(
                    signal=float(signal),
                    prediction=prediction,
                    attractor_distance=float(distance),
                    displacement=float(displacement),
                    predicted_error=(
                        float(predicted_error)
                        if predicted_error is not None
                        else None
                    ),
                    score=float(score),
                )
            )
        return tuple(candidates)

    @staticmethod
    def choose(candidates: tuple[TrajectoryCandidate, ...]) -> TrajectoryCandidate:
        if not candidates:
            raise ValueError("at least one trajectory candidate is required")
        return max(candidates, key=lambda c: (c.score, -abs(c.signal)))

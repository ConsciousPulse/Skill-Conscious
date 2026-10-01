from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MetaPrediction:
    predicted_error: float
    baseline_error: float
    confidence: float
    samples: int


class MetaSelfObserver:
    """Online model of the primary self-model's own prediction error.

    The target is the absolute prediction error produced by SelfObserver on
    previously observed transitions. The meta-model therefore estimates where
    the organism's first-order self-model is likely to be reliable or uncertain.
    """

    FEATURE_COUNT = 8

    def __init__(self, ridge: float = 1e-3, max_samples: int = 2048):
        self.ridge = float(ridge)
        self.max_samples = int(max_samples)
        self.features: list[np.ndarray] = []
        self.targets: list[float] = []

    @staticmethod
    def _fit(
        features: list[np.ndarray],
        targets: list[float],
        ridge: float,
    ) -> np.ndarray:
        if not features:
            return np.zeros(MetaSelfObserver.FEATURE_COUNT, dtype=float)
        x = np.vstack(features)
        y = np.asarray(targets, dtype=float)
        reg = ridge * np.eye(x.shape[1], dtype=float)
        reg[0, 0] = ridge * 0.1
        try:
            return np.linalg.solve(x.T @ x + reg, x.T @ y)
        except np.linalg.LinAlgError:
            return np.linalg.pinv(x.T @ x + reg) @ x.T @ y

    @staticmethod
    def features_for(
        *,
        previous_state: float,
        state: float,
        memory: float,
        pressure: float,
        last_input: float,
        attractor_distance: float,
        steps_delta: int,
    ) -> np.ndarray:
        return np.asarray(
            [
                1.0,
                float(previous_state),
                float(state),
                float(memory),
                float(pressure),
                float(last_input),
                float(attractor_distance),
                float(steps_delta),
            ],
            dtype=float,
        )

    def predict_error(
        self,
        *,
        previous_state: float,
        state: float,
        memory: float,
        pressure: float,
        last_input: float,
        attractor_distance: float,
        steps_delta: int,
    ) -> float:
        x = self.features_for(
            previous_state=previous_state,
            state=state,
            memory=memory,
            pressure=pressure,
            last_input=last_input,
            attractor_distance=attractor_distance,
            steps_delta=steps_delta,
        )
        if not self.features:
            return 0.0
        weights = self._fit(self.features, self.targets, self.ridge)
        prediction = float(x @ weights)
        return float(max(0.0, prediction))

    def predict(
        self,
        *,
        previous_state: float,
        state: float,
        memory: float,
        pressure: float,
        last_input: float,
        attractor_distance: float,
        steps_delta: int,
    ) -> MetaPrediction:
        predicted = self.predict_error(
            previous_state=previous_state,
            state=state,
            memory=memory,
            pressure=pressure,
            last_input=last_input,
            attractor_distance=attractor_distance,
            steps_delta=steps_delta,
        )
        samples = len(self.targets)
        confidence = min(1.0, samples / 32.0)
        baseline = float(np.mean(self.targets)) if self.targets else 0.0
        return MetaPrediction(
            predicted_error=predicted,
            baseline_error=baseline,
            confidence=confidence,
            samples=samples,
        )

    def observe(self, *, features: np.ndarray, prediction_error: float) -> None:
        self.features.append(np.asarray(features, dtype=float))
        self.targets.append(max(0.0, float(prediction_error)))
        if len(self.features) > self.max_samples:
            self.features.pop(0)
            self.targets.pop(0)

    def absolute_error(
        self,
        *,
        predicted_error: float,
        actual_prediction_error: float,
    ) -> float:
        return abs(float(actual_prediction_error) - float(predicted_error))

    def reset(self) -> None:
        self.features.clear()
        self.targets.clear()

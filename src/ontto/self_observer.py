from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class SelfPrediction:
    predicted_state: float
    baseline_state: float
    confidence: float
    samples: int


class SelfObserver:
    """Online, persisted-compatible model of the organism's own dynamics.

    The observer learns from the organism's previous transition records. It does
    not inspect the hidden dynamics implementation. It predicts the next state
    from the currently observed internal state and transition variables.
    """

    FEATURE_COUNT = 7

    def __init__(self, ridge: float = 1e-3, max_samples: int = 2048):
        self.ridge = float(ridge)
        self.max_samples = int(max_samples)
        self.features: list[np.ndarray] = []
        self.targets: list[float] = []

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

    @staticmethod
    def _fit(features: list[np.ndarray], targets: list[float], ridge: float) -> np.ndarray:
        if not features:
            return np.zeros(SelfObserver.FEATURE_COUNT, dtype=float)
        x = np.vstack(features)
        y = np.asarray(targets, dtype=float)
        reg = ridge * np.eye(x.shape[1], dtype=float)
        reg[0, 0] = ridge * 0.1
        try:
            return np.linalg.solve(x.T @ x + reg, x.T @ y)
        except np.linalg.LinAlgError:
            return np.linalg.pinv(x.T @ x + reg) @ x.T @ y

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
    ) -> SelfPrediction:
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
            predicted = float(state)
        else:
            weights = self._fit(self.features, self.targets, self.ridge)
            predicted = float(np.clip(x @ weights, -1.0, 1.0))

        samples = len(self.targets)
        confidence = min(1.0, samples / 32.0)
        return SelfPrediction(
            predicted_state=predicted,
            baseline_state=float(state),
            confidence=confidence,
            samples=samples,
        )

    def observe(
        self,
        *,
        features: np.ndarray,
        actual_state: float,
    ) -> None:
        self.features.append(np.asarray(features, dtype=float))
        self.targets.append(float(actual_state))
        if len(self.features) > self.max_samples:
            self.features.pop(0)
            self.targets.pop(0)

    def reset(self) -> None:
        self.features.clear()
        self.targets.clear()
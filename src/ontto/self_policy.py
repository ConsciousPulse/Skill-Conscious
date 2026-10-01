from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class PolicyPrediction:
    utility: float


class SelfPolicy:
    """Persistible numeric policy learned from self-model features.

    Training labels come from an explicit experimental continuity objective.
    The objective is external to the model and remains part of the protocol.
    """

    FEATURE_COUNT = 7

    def __init__(self, ridge: float = 1e-3):
        self.ridge = float(ridge)
        self.features: list[np.ndarray] = []
        self.targets: list[float] = []

    @staticmethod
    def features_for(
        *,
        current_state: float,
        attractor_distance: float,
        predicted_state: float,
        predicted_displacement: float,
        signal: float,
    ) -> np.ndarray:
        return np.asarray(
            [
                1.0,
                float(current_state),
                float(attractor_distance),
                float(predicted_state),
                float(predicted_displacement),
                float(signal),
                float(signal) * float(current_state),
            ],
            dtype=float,
        )

    def observe(self, features: np.ndarray, utility: float) -> None:
        self.features.append(np.asarray(features, dtype=float))
        self.targets.append(float(utility))

    def _fit(self) -> np.ndarray:
        if not self.features:
            return np.zeros(self.FEATURE_COUNT, dtype=float)
        x = np.vstack(self.features)
        y = np.asarray(self.targets, dtype=float)
        reg = self.ridge * np.eye(x.shape[1], dtype=float)
        reg[0, 0] = self.ridge * 0.1
        try:
            return np.linalg.solve(x.T @ x + reg, x.T @ y)
        except np.linalg.LinAlgError:
            return np.linalg.pinv(x.T @ x + reg) @ x.T @ y

    def predict(
        self,
        *,
        current_state: float,
        attractor_distance: float,
        predicted_state: float,
        predicted_displacement: float,
        signal: float,
    ) -> PolicyPrediction:
        features = self.features_for(
            current_state=current_state,
            attractor_distance=attractor_distance,
            predicted_state=predicted_state,
            predicted_displacement=predicted_displacement,
            signal=signal,
        )
        weights = self._fit()
        return PolicyPrediction(utility=float(features @ weights))

    def choose(self, candidates: list[dict[str, float]]) -> dict[str, float]:
        if not candidates:
            raise ValueError("at least one candidate is required")
        scored = [
            (
                self.predict(
                    current_state=row["current_state"],
                    attractor_distance=row["attractor_distance"],
                    predicted_state=row["predicted_state"],
                    predicted_displacement=row["predicted_displacement"],
                    signal=row["signal"],
                ).utility,
                row,
            )
            for row in candidates
        ]
        return max(
            scored,
            key=lambda pair: (pair[0], -abs(pair[1]["signal"])),
        )[1]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ridge": self.ridge,
            "features": [row.tolist() for row in self.features],
            "targets": list(self.targets),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SelfPolicy":
        policy = cls(ridge=float(payload.get("ridge", 1e-3)))
        for row, target in zip(
            payload.get("features", []),
            payload.get("targets", []),
        ):
            policy.observe(np.asarray(row, dtype=float), float(target))
        return policy

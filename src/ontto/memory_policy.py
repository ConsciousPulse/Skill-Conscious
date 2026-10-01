from __future__ import annotations

import re
from dataclasses import dataclass

from .continuity import AevumContinuityGate, ContinuityDecision


@dataclass(frozen=True)
class MemoryAdmission:
    content: str
    novelty: float
    coupling: float
    persistence: float
    decision: ContinuityDecision


class ContinuityMemoryPolicy:
    """Optional AEVUM-inspired admission policy for persistent memory."""

    def __init__(self, gate: AevumContinuityGate | None = None):
        self.gate = gate or AevumContinuityGate()

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return set(re.findall(r"\w+", text.lower(), flags=re.UNICODE))

    def score(
        self,
        content: str,
        recent_memories: list[str],
        importance: float = 0.65,
    ) -> MemoryAdmission:
        candidate = self._tokens(content)
        if not candidate:
            raise ValueError("memory content must contain at least one token")

        if not recent_memories:
            overlap = 0.0
        else:
            overlaps = []
            for memory in recent_memories:
                tokens = self._tokens(memory)
                union = candidate | tokens
                overlaps.append(
                    len(candidate & tokens) / len(union)
                    if union else 0.0
                )
            overlap = max(overlaps)

        novelty = 1.0 - overlap
        persistence = max(0.0, min(1.0, float(importance)))
        coupling = max(0.0, min(1.0, float(overlap)))

        decision = self.gate.evaluate(
            novelty=novelty,
            coupling=coupling,
            persistence=persistence,
        )
        return MemoryAdmission(
            content=content,
            novelty=novelty,
            coupling=coupling,
            persistence=persistence,
            decision=decision,
        )

    def admit(
        self,
        content: str,
        recent_memories: list[str],
        importance: float = 0.65,
    ) -> MemoryAdmission:
        return self.score(content, recent_memories, importance)

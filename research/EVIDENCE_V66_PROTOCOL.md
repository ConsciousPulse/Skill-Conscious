# Evidence V66 — Dream consolidation after episodic-memory ablation

## Hypothesis

A DREAM-generated lesson can remain functionally active after the raw episodic
memories that produced it are removed.

## Design

24 matched replicates.

DREAM first processes repeated experience memories and writes a consolidated lesson.
Then the post-dream state is cloned into two arms:

- retained_lesson: delete raw EXPERIENCE records only;
- ablated_lesson: delete raw EXPERIENCE records and the CONSOLIDATED lesson.

Both arms run the same retrieval probe and semantic dynamic bridge before future
trajectory selection.

## Primary analysis

Compare paired regret and oracle-hit rate between retained_lesson and ablated_lesson.

## Limitation

The deterministic provider is synthetic. This protocol demonstrates operational
retention and causal use of a consolidated computational trace, not subjective
memory or consciousness.

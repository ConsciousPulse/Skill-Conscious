# V66 — Dream consolidation after episodic-memory ablation

## Question

After DREAM transforms recent experiences into a consolidated lesson, does the
organism retain a functional trace of that lesson when the original episodic
experience memories are removed?

## Protocol

Each replicate executes a deterministic DREAM consolidation phase.

After DREAM, the two matched arms are cloned from the same post-dream state:

1. retained_lesson — raw experience memories are removed, but the consolidated
   lesson remains;
2. ablated_lesson — raw experience memories and the consolidated lesson are
   removed.

Both arms then receive the same post-dream retrieval probe. The resulting MEMORY
output is routed through the ordinary semantic-to-dynamic bridge before future
trajectory selection.

The raw episodic records therefore cannot directly explain the retained arm's later
behavior. The only intended preserved semantic difference is the consolidated lesson.

## Causal chain

```
experiences
   ↓
DREAM
   ↓
consolidated lesson
   ↓
raw-memory ablation
   ↓
lesson retrieval
   ↓
semantic bridge
   ↓
internal state
   ↓
future selection
```

## Result

The CI audit completed successfully on 24 matched replicates.

- retained-lesson mean regret: **-0.1086777912**;
- ablated-lesson mean regret: **-0.1086777912**;
- retained-lesson oracle-hit rate: **85.0694%**;
- ablated-lesson oracle-hit rate: **85.0694%**;
- ablation-minus-retained regret advantage: **0.0**;
- paired sign-flip p for regret difference: **1.0**;
- retained-minus-ablated oracle-hit advantage: **0.0**;
- paired sign-flip p for hit-rate difference: **1.0**;
- all retained runs produced a retrieval bridge signal: **true**.

## Interpretation

V66 is a **null result**.

The retained consolidated lesson was present and generated a semantic retrieval signal,
but preserving it did not produce a measurable difference in regret or oracle-hit rate
relative to deleting it in this protocol.

This means the experiment did **not** demonstrate that DREAM-created episodic
consolidation becomes functionally necessary for later trajectory selection after raw
episodic-memory ablation.

The null does not show that dream consolidation is useless in general. It shows that
the present retrieval-and-selection pathway did not make the retained lesson
discriminatively important under the tested deterministic conditions.

## Methodological consequence

The next protocol should avoid asking the retained lesson to influence behavior only
through a new semantic retrieval response. Instead, it should test whether the
**numeric internal state produced by DREAM itself** carries a recoverable and
causally transferable trace after semantic memory and self-model text are removed.

## Evidence boundary

The provider is deterministic and synthetic. V66 tests persistence of a consolidated
computational trace after source-memory removal. It does not establish human-like
memory consolidation, subjective dreaming, or phenomenological consciousness.

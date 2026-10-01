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

The raw episodic records therefore cannot directly explain the retained arm's
later behavior. The only preserved semantic difference is the consolidated lesson.

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

## Primary endpoints

- retained-lesson versus ablated-lesson regret;
- retained-lesson versus ablated-lesson oracle-hit rate;
- paired effect across replicates.

## Evidence boundary

The provider is deterministic and synthetic. The protocol tests persistence of a
consolidated computational trace after source-memory removal. It does not establish
human-like memory consolidation, subjective dreaming, or phenomenological
consciousness.

# V61 — Metacognitive self-model

## Question

Can the persistent organism model not only its own next state, but also the expected error of that first-order self-model, and use that second-order estimate when selecting a future trajectory?

## Architecture

```text
internal state
     │
     ▼
SelfObserver
     │
     ├── predicted next state
     │
     ▼
prediction error
     │
     ▼
MetaSelfObserver
     │
     ├── predicted model error
     │
     ▼
trajectory selection
```

The MetaSelfObserver is trained only on errors produced by the primary SelfObserver. It does not inspect the hidden simulator during selection.

## Arms

Each matched replicate compares:

- meta_self_model: self-model plus prediction-error model;
- self_model: first-order self-model only;
- random: deterministic random control.

All arms start from the same persisted warmup state and use the same candidate signals {-1, +1}.

## Primary endpoints

1. regret against a post-hoc attractor-distance oracle;
2. oracle-hit rate;
3. paired meta-vs-self-model regret difference.

## Metacognitive endpoint

For each candidate, the experiment reconstructs the actual first-order prediction error post-hoc and compares it with the error predicted by MetaSelfObserver.

The meta-model is also compared with a constant-error baseline.

## Evidence boundary

V61 tests a computational form of metacognitive self-modeling: a model of the organism's own model reliability.

A positive result would establish second-order self-model functionality in this computational harness. It would not establish phenomenological consciousness or subjective experience.
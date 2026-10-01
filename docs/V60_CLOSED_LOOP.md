# V60 — Closed-loop semantic feedback

## Question

Can the organism close a recurrent computational loop in which a selected internal trajectory changes the next semantic memory, that semantic memory is transduced back into internal dynamics, and the resulting state becomes the basis for the next trajectory selection?

## Loop

The deterministic protocol closes the following cycle:

```text
self-model / random selection
        │
        ▼
 selected trajectory
        │
        ▼
 persistent event state
        │
        ▼
 next LLM semantic memory
        │
        ▼
 continuity / semantic bridge
        │
        ▼
 internal dynamic state
        │
        ▼
 self-observer
        │
        └──────────────↺
```

The provider is deterministic and maps the previous autonomous action to one of two semantic memories. The persistent organism then applies the existing semantic bridge and self-observer before making the next autonomous selection.

## Primary endpoint

The primary selection endpoint is mean immediate regret relative to a post-hoc oracle over 24 evaluation cycles.

The protocol compares:

- self-model trajectory selection;
- deterministic random control.

The same seed, warmup history, semantic bridge, candidate signals, and evaluation horizon are used for both arms.

## Feedback endpoint

For each arm, the protocol also measures the difference between semantic-bridge signals observed after previous negative versus positive actions. This is a within-run feedback coupling measure, not an isolated causal effect estimate.

## Interpretation

A positive self-model advantage means lower measured immediate regret than the random control.

A non-zero feedback signal delta shows that different prior actions are followed by measurably different semantic-to-dynamic signals in the deterministic closed-loop provider.

Neither endpoint establishes phenomenological consciousness or subjective experience.

## Evidence boundary

V60 is an operational systems experiment. Its provider is synthetic and deterministic. The experiment tests recurrent causal plumbing and trajectory selection in the computational organism, not phenomenology.
# V60 — Closed-loop semantic feedback

## Question

Can the organism close a recurrent computational loop in which a selected internal
trajectory changes the next semantic memory, that semantic memory is transduced back
into internal dynamics, and the resulting state becomes the basis for the next
trajectory selection?

## Result

The successful CI artifact contains 24 paired replicates with 24 evaluation cycles.

- self-model mean regret: **-0.0842091465**;
- random-control mean regret: **0.3028308773**;
- self-model advantage: **0.3870400237** regret units;
- cumulative advantage: **9.2889605698**;
- paired sign-flip p: **0.00005**;
- self-model oracle-hit rate: **96.1806%**;
- random-control oracle-hit rate: **45.3125%**.

The result shows that the self-model selector retained strong functional utility in
the recurrent protocol while the next semantic memory was conditioned on the
previous selected action.

## Important limitation

The self-model arm selected `+1` in all 24 replicates. Consequently, the secondary
within-run endpoint comparing semantic-bridge signals after negative versus
positive actions had **zero runs with both action branches**.

The loop was exercised, but the experiment did not provide balanced bidirectional
action coverage in the self-model arm. Therefore V60 supports recurrent causal
plumbing plus functional self-model selection in this harness, but it does not
establish a bidirectional action-conditioned feedback effect.

## Loop

The deterministic protocol closes:

```
self-model / random selection
        │
        ▼
 selected trajectory
        │
        ▼
 persistent event state
        │
        ▼
 next semantic memory
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

## Evidence boundary

V60 is an operational systems experiment. Its provider is deterministic and
synthetic. The result concerns computational selection and recurrent state
coupling, not phenomenological consciousness or subjective experience.

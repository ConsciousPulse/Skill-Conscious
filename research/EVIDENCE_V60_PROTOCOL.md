# Evidence V60 — Closed-loop semantic feedback

## Hypothesis

The organism should be able to maintain a recurrent loop in which its selected trajectory is persisted as state, influences the next semantic memory, and that semantic memory is converted back into the organism's internal dynamics before the next trajectory selection.

## Design

Each replicate:

1. constructs a matched warmup history with semantic bridge enabled and self-selection disabled;
2. clones the same persistent state into a self-model arm and a random-control arm;
3. runs repeated wake → semantic bridge → autonomous selection cycles;
4. uses the same seed and candidate set {-1, +1} in both arms;
5. evaluates each selected trajectory against a post-hoc oracle that never participates in selection.

The synthetic provider reads the latest persisted autonomous action and emits a deterministic semantic memory associated with that action. The memory then enters the ContinuityMemoryPolicy and semantic dynamic bridge.

## Primary measure

Mean immediate regret:

`actual_distance - oracle_distance`

and paired self-model advantage:

`regret_random - regret_self_model`.

## Secondary measure

Within-run feedback signal difference between cycles following negative and positive actions.

This is not a formal isolated causal effect because action history and internal state co-evolve over the closed loop.

## Limitations

The provider is deterministic and synthetic. The protocol does not test phenomenology, subjective reports, or real external LLM behavior.
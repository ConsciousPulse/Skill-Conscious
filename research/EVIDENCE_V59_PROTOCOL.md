# Evidence V59 — Semantic bridge × self-model factorial

## Hypothesis

The semantic memory bridge should alter the internal state presented to the self-model, while the self-model should retain a measurable trajectory-selection advantage over a matched random policy. V59 tests whether those effects interact.

## Design

For each seed, two bridge conditions are constructed from matched warmup histories:

- bridge OFF: wake dynamics use the fixed dynamic_wake_signal;
- bridge ON: wake dynamics use the semantic-memory continuity signal.

From each condition, the exact same post-wake state is cloned into two policy arms:

- self_model;
- random.

Selection candidates are {-1, +1}. Oracle distances are computed after selection from frozen pre-selection state variables using the same deterministic dynamics implementation and seed. The oracle is never provided to the selector.

## Pre-registered interpretation

The primary quantity is the paired interaction:

(regret_random - regret_self)_ON - (regret_random - regret_self)_OFF.

Positive values indicate greater measured self-model advantage in the bridge-ON condition; negative values indicate the opposite. Near-zero values indicate no detectable interaction at the tested resolution.

All outcomes, including null or adverse interactions, are retained.

## Limitations

The provider is deterministic and synthetic. The protocol does not test phenomenology, subjective report, or real-world deployment. The bridge coefficients are operational adapters from the repository's continuity gate, not physical measurements.

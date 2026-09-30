# Context Transplant V10b

V10b uses matched noise seeds and transplants one context component at a time between two histories. Future input is zero for 500 steps.

Affinity is positive when the hybrid trajectory is closer to the A reference and negative when closer to B.

## Key result

| Regime | A state-only affinity | B state-only affinity | A memory-only affinity | B memory-only affinity |
|---|---:|---:|---:|---:|
| Critical | +0.754 | -0.561 | -0.020 | -0.345 |
| Persistence | +0.223 | -0.392 | -0.281 | +0.259 |
| Baseline | +0.029 | +0.014 | +0.801 | -0.793 |

The critical ridge shows a stronger state-mediated causal identity signal than the persistence ridge in this particular history pair.

Baseline behavior is qualitatively different: the explicit memory variable strongly determines the short continuation, while the high-persistence critical regime shifts identity control toward the recurrent state.

The persistence ridge is less cleanly separable and shows some component asymmetry, which motivates multi-history replication before treating it as a general mechanism.

This is a causal intervention result about the implemented dynamical model, not evidence of consciousness.
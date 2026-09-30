# Context Factorial — V9

V9 decomposes the historical persistence after a 300-step history followed by 500 zero-input steps. Both branches use identical noise seeds.

Interventions synchronize selected context variables at the history/future boundary while preserving the others.

## End-gap retention relative to the full historical context

| Regime | State+Memory reset | State+Pressure reset | Memory+Pressure reset |
|---|---:|---:|---:|
| baseline | ~0 | ~0 | effectively baseline numerical residual |
| critical | **0.250** | **0.551** | **0.832** |
| persistence | **0.274** | **1.004** | **0.962** |

Interpretation of columns:
- State+Memory reset: pressure is the only branch-specific variable retained.
- State+Pressure reset: memory is the only branch-specific variable retained.
- Memory+Pressure reset: state is the only branch-specific variable retained.

## Main finding

The critical ridge retains approximately 83% of the full end-gap when only the recurrent state difference is preserved, and approximately 55% when only the explicit memory difference is preserved.

The persistence ridge is even more state-dominated: preserving only the state retains approximately 96% of the full effect, while preserving only memory retains approximately 100% in this protocol.

Pressure alone does not account for the persistence: resetting pressure while retaining state and memory leaves the high-persistence effect essentially unchanged.

The strongest operational description is therefore **distributed context persistence**: the system stores history across interacting dynamical variables rather than in one explicit memory scalar.

This is a property of the implemented computational model. It does not establish consciousness, subjective experience, or a physical interpretation of the model's symbolic states.
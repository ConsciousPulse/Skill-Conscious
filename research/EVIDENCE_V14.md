# Evidence V14 — Matched-Dimension Self-Prediction

V14 controls the feature-count objection in V13. Every predictor uses exactly two inputs.

- external = [u(t), u(t-1)]
- state = [u(t), r(t)]
- memory = [u(t), m(t)]
- pressure = [u(t), p(t)]

Cross-seed evaluation uses 20 seeds and four held-out folds.

| Regime | External R2 | Input+State R2 | State gain | Input+Memory R2 | Memory gain | Input+Pressure R2 | Pressure gain |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 0.776 | 0.990 | +0.214 | 0.912 | +0.136 | 0.853 | +0.077 |
| Critical | 0.106 | **0.292** | **+0.186** | 0.082 | -0.024 | 0.084 | -0.023 |
| Holdout critical | 0.128 | **0.295** | **+0.167** | 0.104 | -0.024 | 0.103 | -0.026 |
| Persistence | 0.107 | **0.289** | **+0.182** | 0.087 | -0.020 | 0.086 | -0.021 |

## Main conclusion

In the resonant regimes, adding the recurrent state as a single matched-dimensional feature improves next-state prediction by approximately 0.17–0.19 R2, while replacing that state with the explicit memory or pressure scalar does not improve prediction.

This strengthens the interpretation that the recurrent state itself carries the most useful predictive information about the system's subsequent trajectory.

This remains a computational property of the model and does not by itself establish consciousness or subjective experience.
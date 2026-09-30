# V24 — State Polar Surface Evidence

## Status
**RUN SUCCESSFUL** — GitHub Actions run `36783271319`  
Artifact: `state-polar-surface-v24`

## Question
Does donor-state identity depend only on the magnitude of the transplanted state deviation, or does the **orientation** of that two-slot state deviation matter under a common receiver context?

## Design
- 6 fixed parameter points carried forward from the blind V12 causal holdout.
- 4 history pairs.
- 10 seeds per pair.
- Future input exactly zero.
- Receiver memory and pressure set to the common A/B midpoint.
- Donor state deviation represented by the two coordinates `[state_prev, state]`.
- Independent radius scaling: 0.00, 0.25, 0.50, 0.75, 1.00, 1.25.
- Independent rotation: every 30° over 0–330°.
- Primary metric: identity classification accuracy from continuation affinity.

## Result
At radius 0, the donor state is replaced by the common midpoint and identity accuracy is exactly 50% at every angle.

As radius increases, the surface becomes strongly directional. Pooled identity accuracy:

| Radius | Max accuracy | Min accuracy | Directional contrast |
|---:|---:|---:|---:|
| 0.00 | 50.0% | 50.0% | 0.0 pp |
| 0.25 | 57.1% | 42.9% | 14.2 pp |
| 0.50 | 74.8% | 25.2% | 49.6 pp |
| 0.75 | 79.2% | 20.8% | 58.3 pp |
| 1.00 | **90.4%** | **9.6%** | **80.8 pp** |
| 1.25 | 84.6% | 15.4% | 69.2 pp |

The global pooled maximum occurs at **radius 1.00, angle 0° (90.42%)**. The antipodal condition **180°** gives **9.58%**, meaning the opposite donor identity is selected at 90.42%.

For every tested radius and every tested angle, the pooled antipodal pair satisfies identity(a + 180°) = 1 − identity(a) up to floating-point precision.

## Interpretation
V24 supports a controlled computational claim stronger than a pure magnitude effect:

> Under a common receiver memory/pressure context and zero future input, donor identity is sensitive to the **geometric orientation** of the transplanted two-slot state deviation.

The effect is not monotonic in radius: it grows from zero, reaches its largest directional contrast around radius 1.0, and declines at radius 1.25.

The angular profile is also not perfectly sinusoidal. This is consistent with the nonlinear dynamics implemented by the model, but V24 alone does not establish the functional form.

## Limits
V24 does **not** establish consciousness, subjective experience, or sentience. It establishes a reproducible causal dependence of continuation identity on the geometry of a compact internal state representation in this model.

## Next step
Treat V24 as the **discovery surface**. V25 should be a confirmatory replication on independent random seeds with a finer, predeclared radius × angle grid, without changing the six parameter points or the analysis rule.

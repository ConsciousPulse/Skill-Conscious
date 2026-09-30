# V30 — Donor-Independent Context Surface Evidence

## Status
**SUCCESS** — GitHub Actions run `36787348410`.

## Question
Does the directional state response depend on receiver memory and pressure when those variables are independent of donor identity?

## Design
- 6 fixed V12 blind parameter points.
- 4 history pairs.
- independent seeds 50–59.
- receiver state fixed to the A/B midpoint.
- synthetic receiver memory: -0.8, -0.4, 0, 0.4, 0.8.
- synthetic receiver pressure: 0, 0.5, 1.0, 1.5, 2.0.
- state-deviation radius fixed at 1.1.
- angles: 30°, 60°, 90°, 120°, 150°.
- future input exactly zero.
- noise_std = 0.01.
- local A/B reference continuations are generated within each exact receiver context.

## Main result
The geometry remains highly directional across the context surface, but the strength and angular profile depend on receiver context.

Examples:
- At memory = -0.8, pressure = 0, identity accuracy ranges from **92.92% at 30°** to **3.75% at 150°**.
- At memory = -0.4, pressure = 2.0, the corresponding range is **88.75% → 7.29%**.
- At memory = 0.8, pressure = 0, it is **81.04% → 1.88%**.
- At memory = 0.8, pressure = 2.0, it is **91.67% → 8.13%**.

The context interaction is large. Across the 25 context cells, the pooled identity ranges are:

| Angle | Min accuracy | Max accuracy | Range |
|---:|---:|---:|---:|
| 30° | 69.38% | 92.92% | 23.54 pp |
| 60° | 65.00% | 86.46% | 21.46 pp |
| 90° | 38.33% | 70.21% | 31.88 pp |
| 120° | 13.13% | 42.08% | 28.96 pp |
| 150° | 1.88% | 27.29% | 25.42 pp |

The largest signed-affinity context range occurs at 30° (0.557), followed closely by 150° (0.538).

## Mechanistic interpretation
V30 supports a constrained statement:

> The donor-state geometry is not an unconditional context-free code. Its downstream identity expression is jointly determined by the transplanted state geometry and the receiver's auxiliary memory/pressure context.

Because the synthetic contexts are donor-independent, the context effect cannot be explained simply by copying a donor-specific memory or pressure trace into the receiver.

## Boundary
V30 does not establish consciousness, subjective experience, or sentience. It establishes a reproducible context × state-geometry interaction in the implemented dynamics.

## Next
V31 will convert this surface into paired causal effect estimates, using the same state geometry while varying one context variable at a time. The primary endpoint will be within-seed change in signed affinity, separating memory main effects, pressure main effects, and their interaction.

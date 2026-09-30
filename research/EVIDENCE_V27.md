# V27 — Noise Robustness Evidence

## Status
**SUCCESS** — GitHub Actions run `36786151676`.

## Design
Six blind V12 parameter points, four history pairs, and independent seeds 20–29 were used. Future input was exactly zero. Receiver memory and pressure were the common A/B midpoint. Two established radii (0.5 and 1.1) and three established orientations (0°, 90°, 180°) were evaluated under six noise levels.

## Pooled identity accuracy

| Noise | r=0.5 @ 0° | r=0.5 @ 90° | r=0.5 @ 180° | r=1.1 @ 0° | r=1.1 @ 90° | r=1.1 @ 180° |
|---:|---:|---:|---:|---:|---:|---:|
| 0.000 | 64.79% | 59.17% | 35.21% | **89.79%** | 36.46% | **10.21%** |
| 0.005 | 67.29% | 53.75% | 32.71% | 88.96% | 38.96% | 11.04% |
| 0.010 | 68.33% | 51.67% | 31.67% | **89.58%** | 37.71% | **10.42%** |
| 0.025 | 69.58% | 49.17% | 30.42% | 84.58% | 40.21% | 15.42% |
| 0.050 | 63.75% | 48.13% | 36.25% | 80.00% | 40.00% | 20.00% |
| 0.100 | 61.25% | 56.25% | 38.75% | 73.33% | 41.25% | 26.67% |

At the largest tested noise level, r=1.1 retains a 0°–180° identity contrast of **46.67 percentage points**. At the reference noise 0.01, the contrast is **79.17 points**.

The effect therefore weakens as noise increases, but remains strongly directional at `noise_std=0.10`.

## Important nuance
The response is not monotonic in noise at every condition. For r=0.5, some low-to-moderate noise levels slightly increase pooled identity accuracy relative to the zero-noise case. Therefore V27 supports robustness, not a simple monotonic noise law.

## Interpretation
V27 shows that the V24–V26 state-geometry effect is not confined to a single exact noise setting. The dominant 1.1-radius directional separation survives substantial injected dynamical noise.

## Boundary
This is a reproducible computational property of the implemented model. It does not establish consciousness, subjective experience, or sentience.

## Next
V28 tests context transport: whether the same state geometry remains informative when transplanted into receiver contexts with different memory/pressure histories.

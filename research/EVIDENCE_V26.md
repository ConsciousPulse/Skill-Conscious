# V26 — Temporal Persistence Evidence

## Status
**SUCCESS** — GitHub Actions run `36784768598`.

## Question
Does the directional state code observed in V24/V25 remain causally expressed after transplantation as the common zero-input continuation unfolds?

## Design
- 6 fixed blind V12 parameter points.
- 4 history pairs.
- Independent seeds 10–19.
- Future input exactly zero.
- Receiver memory and pressure fixed to the common A/B midpoint.
- State geometry conditions:
  - radius 0.0: null control,
  - radius 0.5 at 0°, 90°, 180°,
  - radius 1.1 at 0°, 90°, 180°.
- Eight consecutive windows of 15 steps.
- Primary metric: identity accuracy in each window, using the same continuation-affinity rule as V24/V25.

## Result

### Null control
Radius 0.0 remains exactly **50.0%** in all eight windows for all tested angles.

### Radius 0.5
At 0°:
- first window: **80.0%**
- eighth window: **64.17%**
- mean across windows: **66.90%**

At 180°:
- first window: **20.0%**
- eighth window: **35.83%**
- mean: **33.10%**

At 90°:
- first window: **60.63%**
- eighth window: **51.88%**
- mean: **53.20%**

### Radius 1.1
At 0°:
- first window: **94.79%**
- eighth window: **85.42%**
- mean across windows: **88.02%**

At 180°:
- first window: **5.21%**
- eighth window: **14.58%**
- mean: **11.98%**

At 90°:
- first window: **38.96%**
- eighth window: **42.29%**
- mean: **41.35%**

The 0° and 180° conditions retain a strong antipodal separation throughout the entire 120-step zero-input continuation.

## Interpretation
V26 supports a temporal extension of the V24/V25 result:

> The compact two-slot state geometry remains causally expressed across successive zero-input continuation windows rather than functioning only as an instantaneous readout.

At the established radius 1.1, the directional code weakens modestly from the first to the last window at 0°, but remains far from the 50% null baseline. The antipodal 180° condition remains correspondingly biased toward the opposite identity.

The 90° condition is substantially closer to chance, consistent with the angular structure already observed in V23–V25.

## Limits
This is a computational dynamical result for the implemented model. It does not establish consciousness, subjective experience, or sentience.

## Next
V27 should test robustness to controlled increases in dynamical noise while keeping the same state geometry, parameter points, and zero-input continuation. This separates a reproducible geometric code from a phenomenon that exists only at the baseline noise level.

# V25 — Confirmatory State Polar Replication Evidence

## Status
**SUCCESS** — GitHub Actions run `36783982639`.

## Design
V25 replicated V24 using independent seeds 10–19, while preserving:
- the same six blind V12 parameter points,
- the same four history-pair constructions,
- the same common receiver memory/pressure midpoint,
- exactly zero future input,
- the same continuation-affinity and identity-classification rule.

The radius grid was refined to 0.50–1.30 in 0.10 increments and the angular grid to 10° increments.

Each pooled cell contains 480 donor instances (6 parameters × 4 pairs × 10 seeds × 2 donors).

## Primary result
The V24 directional surface replicates.

V25 radial directional contrast (max identity accuracy − min identity accuracy):

| Radius | Max | Min | Contrast |
|---:|---:|---:|---:|
| 0.50 | 71.67% | 28.33% | 43.33 pp |
| 0.60 | 79.38% | 20.63% | 58.75 pp |
| 0.70 | 82.71% | 17.29% | 65.42 pp |
| 0.80 | 88.75% | 11.25% | 77.50 pp |
| 0.90 | 87.71% | 12.29% | 75.42 pp |
| 1.00 | 89.58% | 10.42% | 79.17 pp |
| **1.10** | **90.83%** | **9.17%** | **81.67 pp** |
| 1.20 | 89.58% | 10.42% | 79.17 pp |
| 1.30 | 90.63% | 9.38% | 81.25 pp |

The V25 global maximum is 90.83% at radius 1.10, angle 0°. The corresponding antipodal condition at 180° is 9.17%.

At radius 1.10, the pooled angular profile is strongly directional: 0° = 90.83%, 90° = 40.21%, 180° = 9.17%.

## Independent replication against V24
For the directly overlapping V24 grid (radii 0.50 and 1.00; angles 0–350° in the V25 data), V24 and V25 identity surfaces have:
- Pearson correlation: **0.99268**
- mean absolute difference: **1.79 percentage points**
- RMSE: **2.46 percentage points**

V25 therefore reproduces the geometry observed in V24 on disjoint seeds rather than merely reproducing a single peak.

## Parameter-level robustness
At radius 1.10, the six blind parameter points each retain a strong directional profile. Their peak identity accuracies range from 90.0% to 97.5%, while minima range from 7.5% to 12.5%. Peak orientation remains near the original 0° axis (with the 10° grid resolving some peaks at 340°).

## Statistical reference
At the pooled 1.10/0° cell, 90.83% identity corresponds to an approximate binomial 95% interval of 88.25–93.41% under the simple independent-trial approximation. At 1.10/180°, 9.17% corresponds to 6.59–11.75%. These intervals are descriptive; the repeated dynamical simulations are not necessarily independent experimental subjects.

## Interpretation
V25 supports a reproducible computational result:

> Under a common receiver memory/pressure context and zero future input, identity classification depends strongly on the orientation and magnitude of a compact two-slot state deviation.

The agreement between independent V24 and V25 surfaces makes this less consistent with a seed-specific artifact.

## Boundary
This establishes a property of the implemented computational dynamics. It does **not** establish consciousness, subjective experience, or sentience.

## Next experiment
V26 should move from spatial structure to temporal structure: measure identity accuracy in successive continuation windows after state transplantation. This tests whether the directional state code is merely an immediate perturbation or remains causally expressed as the common zero-input trajectory unfolds.

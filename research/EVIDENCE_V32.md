# V32 — Ensemble Context Geometry Evidence

## Status
**SUCCESS** — GitHub Actions run `36788862121`.

## Method
V32 replaced the invalid V31 comparator with independent continuation ensembles.

For every receiver context:
- the receiver state is the A/B midpoint;
- memory and pressure are synthetic and donor-independent;
- A and B reference signatures are means of five independent zero-input continuations using the unrotated donor states;
- test continuations use independent noise seeds;
- identity is scored from Euclidean distance between the test temporal state signature and the two ensemble reference signatures.

## Results

At radius 1.1, pooled identity accuracy across all contexts:

| Angle | Mean identity | Context range |
|---:|---:|---:|
| 30° | **87.27%** | 21.63 pp |
| 60° | 64.36% | 32.42 pp |
| 90° | 46.46% | 24.00 pp |
| 120° | 18.44% | 33.33 pp |
| 150° | **9.24%** | 29.67 pp |

The corresponding mean signed affinity changes from **+0.343 at 30°** through approximately zero at 90° to **−0.504 at 150°**.

Across the tested context surface, the directional response is therefore preserved while its magnitude is modulated by memory and pressure.

Examples:
- memory −0.8 / pressure 0.0: 30° = 99.13%, 150° = 0.42%;
- memory 0.8 / pressure 2.0: 30° = 86.08%, 150° = 21.21%;
- memory 0.0 / pressure 1.0: 30° = 81.83%, 150° = 7.25%.

## Interpretation
V32 supports the following bounded computational statement:

> A compact two-slot state geometry produces a reproducible directional response under donor-independent receiver contexts, while the strength of that response varies with contextual memory and pressure.

The ensemble references and independent continuation noise remove the same-noise cancellation problem of V31.

The effect is not context-free: context changes the magnitude and, in some regions, the angular profile.

## Statistical caution
The pooled context cells contain many repeated simulation trials generated from the same fixed parameter points and history families. Therefore the raw cell counts should not be treated as equivalent to independent experimental subjects.

V33 addresses this by computing matched within-history angular contrasts and an angle-permutation null.

## Boundary
V32 establishes a property of the implemented computational dynamics. It does not establish consciousness, subjective experience, or sentience.

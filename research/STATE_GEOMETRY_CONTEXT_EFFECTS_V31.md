# V31 — Paired Context Effect Decomposition

## Status
The first V31 run (`36787649896`) is **discarded as methodological invalidity**, not as a scientific result. Its implementation generated the A/B reference continuations using the same rotation angle as the test condition, which makes the identity score tautological.

The corrected implementation uses:
- unrotated donor A/B state geometry (0°) as the local reference pair;
- rotated donor geometry (30°, 90°, 150°) as the test conditions;
- identical receiver state, memory, and pressure context in reference and test.

## Corrected design
- six fixed V12 blind parameter points;
- four history pairs;
- independent seeds 60–69;
- receiver state fixed to A/B midpoint;
- donor-independent synthetic memory and pressure;
- radius 1.1;
- test angles 30°, 90°, 150°;
- future input exactly zero;
- primary continuous endpoint: signed affinity relative to the **unrotated** local A/B reference.

The corrected push automatically launches a new V31 run.

This experiment is mechanistic and does not establish consciousness or subjective experience.

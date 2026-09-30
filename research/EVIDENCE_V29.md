# V29 — Exploratory Auxiliary Context Isolation

## Status
**SUCCESS** — GitHub Actions run `36787019017`.

## Methodological disposition
V29 is retained as an exploratory run, **not as confirmatory evidence**.

Two limitations were identified:

1. With the receiver state fixed at the A/B midpoint, a 180° rotation of donor A maps exactly onto donor B (and vice versa). Therefore the 180° condition is a geometric identity swap by construction, not an independent test.
2. In MEM_A/MEM_B and PRESS_A/PRESS_B, the nuisance context is taken from one of the donor histories. That creates donor-linked context and can bias identity classification independently of the transplanted state geometry.

## Observed exploratory result
At 90°, pooled identity accuracy ranged from 52.08% to 58.75% across the tested contexts, with positive signed affinity in every context. The 180° condition was 0% identity across contexts by construction.

These numbers are therefore useful for diagnosing the design but should not be treated as evidence that memory or pressure independently controls the state code.

## Decision
V29 is explicitly marked **exploratory / confounded**.

## Next
V30 replaces donor-linked nuisance contexts with predeclared synthetic contexts independent of A/B history and removes the tautological 180° comparison as a primary endpoint.
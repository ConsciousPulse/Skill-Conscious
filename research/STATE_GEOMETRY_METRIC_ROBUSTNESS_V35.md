# V35 — Metric Robustness / Angular Cluster Null

V35 is an independent replication of the V34 design using history seeds 100–109 and disjoint reference/test continuation seeds.

The simulation design is held fixed at the six V34 parameter points, four history-pair strata, nine synthetic memory/pressure contexts, radius 1.1, angles 30° and 150°, and exactly zero future input.

The purpose is to test whether the observed 30°→150° directional contrast depends specifically on the signed-affinity formula used in V33/V34.

Three readouts are computed from the same trajectories:

1. **signed_affinity**: normalized Euclidean distance score used in V34.
2. **distance_margin**: raw Euclidean distance difference, db − da, after donor-consistent sign correction.
3. **cosine_delta**: difference in cosine similarity to the two independent reference continuation signatures, after donor-consistent sign correction.

Inference is performed at the same history-seed block level as V34: repeated parameter/context cells are averaged inside each of the 40 history-seed blocks. The primary contrast is 30° minus 150°.

The null is a stratified sign-flip permutation within each of the four history-pair strata (20,000 permutations). A stratified bootstrap across history-seed blocks (10,000 resamples) provides a 95% interval.

Interpretation is restricted to computational geometry/dynamics. A positive result does not establish consciousness, subjective experience, sentience, or any physical realization outside the implemented simulator.

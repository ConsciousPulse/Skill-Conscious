# V36 — Leave-One-History-Pair-Out Cluster Validation

V36 is a fresh replication using history seeds 110–119.

The full design matches V34/V35: six blind parameter points, four history-pair strata, nine memory/pressure contexts, radius 1.1, angles 30° and 150°, exactly zero future input, and disjoint reference/test continuation seeds.

The primary analysis is performed at the history-seed block level. Repeated parameter/context cells are first averaged inside each history-seed block.

In addition to the full 40-block analysis, V36 performs four leave-one-history-pair-out analyses. Each asks whether the aggregate 30°−150° contrast remains positive after removing one of the four historical strata.

For each metric, inference uses a stratified sign-flip null over the remaining history-pair strata and a bootstrap over history-seed blocks.

Readouts:
- signed_affinity
- distance_margin
- cosine_delta

The experiment tests robustness to historical-stratum dominance. It does not establish consciousness, subjective experience, sentience, or any property outside the implemented computational system.

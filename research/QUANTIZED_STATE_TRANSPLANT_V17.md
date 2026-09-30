# V17 — Quantized State-Only Causal Transplant

## Question

V16 showed that a few bits can preserve identity when the donor retains its full contextual state. V17 tests the stronger condition: can a compressed recurrent state transfer identity to a receiver whose explicit memory and pressure contain no donor-specific information?

## Design

Six parameter points from the V12 blind holdout are reused. Each point uses four history-pair protocols and ten matched-noise seeds.

At the boundary:
- donor A or B supplies `state_prev` and `state`;
- receiver memory and pressure are replaced by the common A/B midpoint;
- future external input is exactly zero;
- the donor state is either kept full precision or uniformly quantized to 1, 2, 3, 4, 6, or 8 bits over [-1, 1].

Identity is classified by affinity to the intact A/B continuation references over the first 60 future steps.

## Interpretation rule

High identity accuracy under the state-only receiver demonstrates that the recurrent state can causally transfer historical identity without donor-specific explicit memory or pressure. Retention at 3–4 bits would additionally show that the transferable carrier is compact.

Because these parameter points were used as V12 blind holdout points, this is a replication/extension of the causal transplant result rather than a re-test of the exact V10/V11 candidates.

This remains a computational dynamical finding, not a demonstration of subjective consciousness.
# V40 — Cross-History Reference Test

V40 tests whether the strong angular effect from V34–V36 survives when the A/B reference continuations are generated from a **different history seed** than the test trajectories.

For each of four history-pair templates, test seeds 150–159 are paired with disjoint reference seeds 180–189. References are therefore never generated from the same historical trajectory as the test.

The test retains the reference-based signed-affinity readout, six blind parameter points, nine synthetic memory/pressure contexts, radius 1.1, angles 30°/150°, exactly zero future input, and disjoint continuation noise seeds.

Primary statistic: 30°−150° signed-affinity contrast at the history-seed block level.

Inference: 20,000 stratified sign flips and 10,000 stratified bootstrap resamples across history-seed blocks.

Interpretation:
- persistence would support a reference-based effect that is not specific to same-history reference construction;
- collapse toward zero would identify same-history reference coupling as a key dependency.

This experiment tests the computational readout and does not establish consciousness, subjective experience, or sentience.

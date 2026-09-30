# V39 — Reference-Free Continuous Decoder Margin

V39 revisits the negative V37 result with a continuous readout instead of thresholded accuracy.

A standardized logistic decoder is trained on nine history-seeds and evaluated on the tenth. No within-history reference continuation is constructed.

For each held-out trajectory, the decoder produces a probability/logit for donor identity. The score is signed by the true donor label, so larger positive values mean stronger donor-consistent decoding.

The primary statistic is the difference between mean signed decoding at 30° and 150°, averaged at held-out history-seed block level.

Design: six fixed parameter points, four history-pair strata, nine synthetic memory/pressure contexts, angles 0°, 30°, 150°, radius 1.1, zero future input, and disjoint continuation seeds.

Inference: paired sign-flip across the ten held-out history blocks.

Purpose: determine whether V37's negative result was mainly a threshold/accuracy artifact. The test does not establish consciousness or subjective experience.

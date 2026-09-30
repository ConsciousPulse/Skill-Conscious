# V38 — Amplitude-Blind Cross-History Decoder

V38 repeats the reference-free decoder logic with fresh history seeds 130–139.

Before feature extraction, each future state trajectory is L2-normalized. The decoder therefore receives only scale-invariant trajectory-shape statistics rather than absolute trajectory amplitude.

The model is trained on nine history seeds and evaluated on the held-out tenth seed. No same-history continuation reference is constructed.

Design: six fixed parameter points, four history-pair strata, nine memory/pressure contexts, angles 0°, 30°, and 150°, exactly zero future input, and disjoint continuation seeds.

Primary statistic: held-out accuracy difference 30° minus 150° across the ten held-out history-seed blocks.

Inference: paired sign-flip across the ten held-out history blocks.

The experiment tests whether the reference-free angular signal survives removal of global trajectory scale. It does not establish consciousness or subjective experience.

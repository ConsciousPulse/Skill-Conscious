# V43 — Reference-Free Temporal-History Decoding

V43 removes the V34–V42 reference-based readout entirely.

The system receives one of four paired history templates, then the future input is set exactly to zero for 60 steps. A classifier is asked to identify the historical template from the internal continuation alone.

The primary evaluation is leave-one-parameter-out (LOPO): each of the six blind parameter points is held out in turn. Within each held-out parameter, training uses the other five parameter points, while the held-out parameter contributes ten disjoint history seeds per class and five independent continuation-noise seeds.

Feature sets are evaluated separately:
- state trajectory only;
- L2-normalized state trajectory;
- memory trajectory only;
- pressure trajectory only;
- concatenated state + memory + pressure, L2-normalized.

A permutation null is applied to the primary joint-normalized LOPO readout.

This is a reference-free retention test. It does not establish consciousness, subjective experience, sentience, or any phenomenological claim.

# V45 — Official Evidence

Run: 36796065094
Artifact: 11133732320
Commit: 3c45bdede896597f6efcfa3fba8a961a1ab4109a

V45 used a single deterministic novel external probe shared by all four history classes. The decoder saw only the future state trajectory and was evaluated leave-one-parameter-out. No reference trajectory or angular comparison was used.

Clean history decoding:
- LOPO mean accuracy: **77.9167%**
- Chance: 25%

Primary causal result:
- Memory-swap Δ donor-minus-receiver pull: **+0.5041785**
- 1,440 matched blocks
- Positive in **70.9028%**
- Sign-flip null 95th percentile: **0.0388239**
- permutation p = **0.00009999**
- bootstrap 95% CI: **[0.4660757, 0.5421739]**

Controls:
- Pressure-swap Δpull: +0.2677794
- State-swap Δpull: +0.4461006

Interpretation: after identical external input, replacing only the retained memory changed the future state trajectory toward the donor-history class. This supports causal, context-dependent use of internal history under a common subsequent stimulus.

V45 still does not establish consciousness, subjective experience, sentience, or phenomenological awareness.

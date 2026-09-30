# V31 — Paired Context Effect Decomposition

V31 turns the V30 context surface into paired effect estimates.

The receiver state is fixed to the common A/B midpoint. Receiver memory and pressure are synthetic and donor-independent. The state geometry is fixed at radius 1.1 and angles 30°, 90°, and 150°.

The reference context is memory 0.0 and pressure 1.0.

For each identical history pair and seed, V31 computes:
- memory main effects by changing memory while pressure stays at 1.0;
- pressure main effects by changing pressure while memory stays at 0.0;
- a two-way interaction term:
  f(memory, pressure) − f(memory, baseline pressure) − f(baseline memory, pressure) + f(baseline context).

The primary outcome is continuous signed affinity rather than binary identity accuracy.

Seeds 60–69 are independent of V30.

The purpose is mechanistic decomposition, not parameter optimization. It does not establish consciousness or subjective experience.

# V44 — Reference-Free Causal Memory Transport

V44 asks whether encoded history in the internal memory variable is merely readable, or whether it is causally used by downstream dynamics.

A state-only decoder is trained on clean future trajectories and evaluated leave-one-parameter-out. The decoder never receives memory or pressure as features.

For each held-out receiver context, future input is exactly zero. Only one component of the internal starting context is changed:
- intact receiver context;
- memory swapped with a donor history from another history class;
- pressure swapped;
- state swapped as a positive causal control.

The primary statistic is the paired change in donor-minus-receiver class probability caused by memory replacement, relative to the intact trajectory. Because the decoder sees only the resulting future state trajectory, a positive memory effect indicates that changing memory altered downstream state dynamics in the direction of the donor history class.

The experiment uses disjoint receiver and donor history seed ranges and six blind parameter points.

This experiment does not establish consciousness, subjective experience, sentience, or phenomenological awareness.

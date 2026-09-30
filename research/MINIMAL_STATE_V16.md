# V16 — Minimal-State Bottleneck

## Question

V15 showed that selectively erasing the recurrent state causes a strong loss of historical identity in the critical regimes. V16 asks how much of that state is actually necessary.

## Structural bottleneck

At the history boundary, the full donor context contains two recurrent state slots: `state_prev` and `state`.

We compare:
- `full`: both state slots retained.
- `current_only`: current state retained, previous state replaced by the A/B common value.
- `previous_only`: previous state retained, current state replaced by the common value.
- `state_zero`: both state slots replaced by the common value.

The other context variables remain donor-specific.

## Precision bottleneck

Both state slots are retained, but their values are uniformly quantized over the natural tanh range [-1, 1] at 1, 2, 3, 4, 6, and 8 bits.

The continuation input is exactly zero and the noise seed is matched across interventions.

## Readout

Identity is classified from trajectory affinity to the intact A/B continuation references over the first 60 future steps. Prediction MAE is measured against the intact donor trajectory.

## Interpretation

If `current_only` retains most of the identity signal while `previous_only` does not, the current recurrent state is the dominant temporal carrier at the boundary. If low-bit quantization retains identity, the mechanism has a compact effective state representation.

This experiment characterizes the implemented computational dynamics. It does not establish subjective experience or consciousness.
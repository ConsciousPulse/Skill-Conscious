# V19 — State Counterfactual Inversion

## Question

V18 showed that classification follows the source of the transferred state rather than the nominal receiver label. V19 tests a stronger counterfactual: reflect the donor state around the common A/B state while keeping memory and pressure common and future input zero.

## Protocol

Six V12 blind parameter points, four history pairs, and ten matched-noise seeds per pair are used.

For each donor:
- `intact`: retain the donor state;
- `erase`: replace the state with the A/B common midpoint;
- `invert`: reflect both temporal state slots around the common midpoint;
- `invert_quantized`: perform the same reflection and then quantize both state slots to 3 bits.

The receiver memory and pressure are always common, so donor-specific identity enters only through state.

## Prediction

If state encodes historical identity directionally, the inverted state should preferentially move the continuation toward the opposite donor reference. The readout therefore reports both original-donor accuracy and flipped-donor accuracy.

## Interpretation limits

This is a counterfactual causal test of state encoding in the implemented dynamical model. Even a successful inversion would establish state-dependent information transport, not subjective consciousness.
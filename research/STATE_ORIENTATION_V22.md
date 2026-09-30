# V22 — State Orientation / Equal-Norm Rotation

## Question

V21 showed that temporal organization matters. V22 asks whether the recurrent state encodes identity in the **orientation of its temporal state vector**, independently of its total magnitude.

## Protocol

Six blind parameter points from V12, four history pairs, ten matched-noise seeds per pair, exact-zero future input, and common receiver memory/pressure.

At the boundary, define the two-dimensional donor deviation:

`d = (state_prev - common_prev, state - common_state)`.

The experiment rotates this vector by 0, 45, 90, 135, 180, 225, 270, and 315 degrees around the common context. Rotation preserves the Euclidean norm exactly; only orientation changes.

Identity is classified by affinity to intact A/B continuation references over the first 60 future steps.

## Interpretation rule

If identity changes systematically with rotation angle despite fixed state-deviation magnitude, the result supports a geometric/orientational representation of historical information in the recurrent state.

An approximately 180-degree inversion that favors the opposite donor would be especially informative because it is the equal-norm analogue of V19.

This remains a computational dynamical test and does not establish subjective consciousness.
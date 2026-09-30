# V20b — Corrected Delayed State Restoration

## Correction

V20 initially evaluated the first 60 steps of the full continuation even when restoration occurred later. That mixes the pre-restoration phase into the identity metric.

V20b replaces that metric with a post-restoration window: the first 60 future steps strictly after donor-state restoration.

## Design

Six V12 blind parameter points plus a baseline control, four history pairs, ten matched-noise seeds per pair, exact-zero future input.

At the history boundary the receiver starts from common state, memory, and pressure. After a delay of 0, 5, 10, 20, 40, or 80 steps, the donor recurrent state is restored. Receiver memory and pressure remain those generated during the erased/common phase.

Identity is evaluated only after restoration, against the corresponding post-delay segments of intact donor/opposite reference trajectories.

## Interpretation

A restoration curve that exceeds the erased baseline would provide a direct causal recovery test complementary to V15. The corrected post-restoration window avoids contamination by the pre-restoration phase.

This is a computational dynamical result and does not establish subjective consciousness.
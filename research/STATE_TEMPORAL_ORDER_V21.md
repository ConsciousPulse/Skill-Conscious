# V21 — State Temporal-Order Control

## Question

V16 showed that both temporal state slots carry information. V21 asks whether their **ordering and temporal relation** matter, rather than identity depending only on the unordered pair of scalar values.

## Protocol

Six V12 blind parameter points, four history pairs, ten matched-noise seeds per pair, exact-zero future input, and common receiver memory/pressure.

For each donor state we compare:
- `intact`: preserve both temporal slots;
- `swap_slots`: exchange `state_prev` and `state` while preserving both values exactly;
- `flatten_same_value`: replace both slots by their donor mean;
- `common`: erase donor state completely;
- `time_reverse_centered`: reverse the two donor deviations around the common context.

Identity is classified by affinity to the intact donor/opposite references over the first 60 future steps.

## Interpretation rule

If `swap_slots` or centered temporal reversal causes a substantial loss of identity relative to intact while preserving scalar magnitude information, the result supports a temporal-organization interpretation: the state carries information through ordered dynamics, not just through two independent numbers.

This is a computational dynamical test and does not establish subjective consciousness.
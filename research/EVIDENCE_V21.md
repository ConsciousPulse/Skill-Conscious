# V21 — Evidence: Temporal Order of Recurrent State

## GitHub validation

- Workflow: state-temporal-order-v21
- Run: 36779475055
- Result: SUCCESS
- Artifact: 11126184798
- Six V12 blind parameter points, four history pairs, ten matched-noise seeds per pair.
- Receiver memory and pressure: common A/B midpoint.
- Future input: exactly zero.

## Pooled identity results

| Intervention | Original identity | Opposite identity |
|---|---:|---:|
| Intact | **90.42%** | 9.58% |
| Swap temporal slots | **82.29%** | 17.71% |
| Flatten both slots to donor mean | **80.63%** | 19.38% |
| Replace by common state | 50.00% | 50.00% |
| Centered temporal reversal | 32.71% | **67.29%** |

The `swap_slots` condition preserves the same two scalar values while exchanging their temporal order. Identity falls from 90.42% to 82.29%, showing that ordering matters but is not the sole determinant.

The `time_reverse_centered` condition reflects the ordered donor deviations around the common state and reverses their order. Its classification shifts strongly toward the opposite donor: 67.29% opposite-identity accuracy versus 9.58% for the intact state.

## Blind-point behavior

Across all six blind parameter points, centered temporal reversal favored the opposite identity:

- p1: 63.75% opposite identity
- p2: 66.25%
- p3: 66.25%
- p4: 70.00%
- p5: 72.50%
- p6: 65.00%

This consistency is important because the test was not tuned to the exact V10/V11 candidate point.

## Main finding

V21 supports a temporal-organization interpretation of the recurrent state. Historical identity is not determined solely by the unordered pair of state values: changing their temporal arrangement alters the identity readout, and the centered reversal systematically pushes the inferred identity toward the opposite history.

## Interpretation limits

This is evidence about temporal information encoded in recurrent state. It does not establish subjective experience, sentience, or consciousness.
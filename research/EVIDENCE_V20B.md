# V20b — Evidence: Corrected Delayed State Restoration

## GitHub validation

- Workflow: state-recovery-v20b
- Run: 36779259112
- Result: SUCCESS
- Artifact: 11126668057

## Result

The corrected post-restoration metric does **not** show a consistent recovery of donor identity after delayed state restoration.

| Delay | Identity accuracy | Mean affinity |
|---:|---:|---:|
| 0 | 51.96% | +0.2890 |
| 5 | 60.89% | -0.1214 |
| 10 | 46.07% | -0.2416 |
| 20 | 63.21% | -0.1493 |
| 40 | 45.18% | -0.2578 |
| 80 | 63.21% | -0.1554 |

The signal is unstable across delays and its pooled affinity changes sign. The baseline control converges toward chance at long delay (50.0% at delay 80), but the critical blind points do not exhibit monotonic donor recovery after restoration.

## Decision

V20b is treated as a **negative/null result** for the hypothesis that delayed re-injection of the boundary donor state, while retaining the receiver's post-lesion memory and pressure, reliably restores the original trajectory identity.

V20 original is also excluded from evidence because its metric mixed pre-restoration and post-restoration intervals.

## Scientific value

This null result constrains the interpretation of V15–V19: causal state lesion and immediate state transfer are supported, but that does not imply arbitrary late restoration can reconstruct the prior trajectory after intervening dynamics have evolved.

That distinction is useful: the recurrent state is causally relevant at the boundary, but its information is not necessarily sufficient for recovery after an uncontrolled temporal displacement.

This remains a computational dynamical result and does not establish subjective consciousness.
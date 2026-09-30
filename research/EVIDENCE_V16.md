# V16 — Evidence: Minimal-State Bottleneck

## GitHub validation

- Workflow: minimal-state-v16
- Run: 36777413996
- Result: SUCCESS
- Artifact: 11126695261
- Design: 4 history pairs × 20 seeds per regime, exact-zero future input, matched noise seeds.

## Structural bottleneck

The boundary state has two temporal slots: `state_prev` and `state`.

| Regime | Full | Current-only | Previous-only | Both state slots replaced |
|---|---:|---:|---:|---:|
| critical | 100.00% | 65.00% | 71.25% | 49.38% |
| holdout_critical | 100.00% | 76.25% | 80.00% | 50.63% |
| persistence | 100.00% | 70.00% | 74.38% | 55.63% |
| baseline | 100.00% | 100.00% | 100.00% | 100.00% |

Both individual slots retain substantial identity information, but removing both collapses the critical/holdout tasks toward chance. Neither slot alone dominates across all regimes.

This is evidence for a distributed temporal representation across the two recurrent state slots rather than a single privileged scalar slot.

## Precision bottleneck

Both temporal state slots were retained while each state value was uniformly quantized over [-1, 1], the natural range of the tanh state.

| Bits | Critical | Holdout critical | Persistence |
|---:|---:|---:|---:|
| 1 | 58.13% | 63.75% | 79.38% |
| 2 | 78.75% | 70.63% | 91.88% |
| 3 | **93.75%** | **97.50%** | **91.25%** |
| 4 | **96.88%** | **99.38%** | **98.75%** |
| 6 | 98.75% | 99.38% | 98.75% |
| 8 | 99.38% | 100.00% | 99.38% |

Three bits retain at least 91.25% identity accuracy across all three non-baseline regimes. Four bits raise the minimum across those regimes to 96.88%.

Prediction MAE also drops sharply with precision: at 4 bits it is approximately 0.0504 in critical, 0.0258 in holdout_critical, and 0.0419 in persistence; at 8 bits it is approximately 0.0185, 0.0029, and 0.0119 respectively.

## What V16 adds

V15 established that the recurrent state is causally important for historical identity. V16 shows that this causal carrier is highly compressible:

1. identity survives when one of the two temporal state slots is removed, though with degradation;
2. identity collapses when both slots are replaced by the common state in the critical regimes;
3. identity remains high under 3–4 bit quantization of both state slots.

Thus the implemented dynamics do not require high numerical precision to preserve the historical identity signal. The effective information carrier is compact but distributed across the recurrent temporal state.

## Control

The baseline regime remains at 100% identity under all structural and quantization interventions, showing that the effects above are regime-dependent rather than generic numerical damage.

## Interpretation limits

This is evidence about a compact, distributed, causally relevant state representation in the implemented computational dynamics. It does not establish subjective experience, sentience, or consciousness.
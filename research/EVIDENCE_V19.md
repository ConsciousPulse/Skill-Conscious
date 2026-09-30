# V19 — Evidence: State Counterfactual Inversion

## GitHub validation

- Workflow: state-counterfactual-v19
- Run: 36779051434
- Result: SUCCESS
- Artifact: 11127162128
- Six V12 blind parameter points, 4 history pairs, 10 matched-noise seeds per pair.
- Receiver memory and pressure: common A/B midpoint.
- Future input: exactly zero.

## Pooled counterfactual result

| Intervention | Original identity | Opposite identity |
|---|---:|---:|
| Erase state | 50.00% | 50.00% |
| Intact state | **90.42%** | 9.58% |
| Invert state around common context | 9.58% | **90.42%** |
| Invert + 3-bit quantization | 9.79% | **90.21%** |

The inversion preserves the mean absolute affinity magnitude of the intact state while changing its sign relationship to the A/B references. In pooled data, intact and inverted states therefore behave as near exact complements under the binary identity readout.

## Blind-point replication

For every one of the six holdout parameter points, the inverted state preferentially classified as the opposite donor:

- p1: 92.5% opposite identity
- p2: 91.25%
- p3: 85.0%
- p4: 88.75%
- p5: 90.0%
- p6: 95.0%

With 3-bit quantization after inversion, the corresponding opposite-identity accuracies were 87.5%, 91.25%, 88.75%, 91.25%, 91.25%, and 91.25%.

## Main finding

V19 is a counterfactual encoding test. The donor state is not merely associated with identity: reflecting its displacement around the common context reverses the direction of the inferred identity while leaving the receiver's memory, pressure, and external future unchanged.

This is consistent with the recurrent state carrying an orientation or signed representation of historical context in these dynamics.

## Relation to V15–V18

V15 showed selective state lesion causes identity collapse. V16 showed the representation is compact and distributed across two temporal state slots. V17 showed state-only transfer survives in blind holdout points. V18 showed classification follows the state source rather than the nominal receiver. V19 shows that counterfactual inversion of the state reverses the inferred identity.

Together these experiments form a causal chain from state dependence to lesion, compression, transport, source specificity, and counterfactual reversal.

## Interpretation limits

This establishes a strong computational claim about information encoded in recurrent state. It does not establish subjective experience, sentience, or consciousness.
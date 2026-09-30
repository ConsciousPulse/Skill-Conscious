# V22 — Evidence: Equal-Norm State Orientation

## GitHub validation

- Workflow: state-orientation-v22
- Run: 36782644637
- Result: SUCCESS
- Artifact: 11128626847
- Six V12 blind parameter points, four history pairs, ten matched-noise seeds per pair.
- Receiver memory and pressure: common A/B midpoint.
- Future input: exactly zero.

## Pooled angular response

| Rotation | Original identity | Opposite identity |
|---:|---:|---:|
| 0° | **90.42%** | 9.58% |
| 45° | 46.88% | 53.13% |
| 90° | 34.79% | 65.21% |
| 135° | 21.88% | 78.13% |
| 180° | 9.58% | **90.42%** |
| 225° | 53.13% | 46.88% |
| 270° | 65.21% | 34.79% |
| 315° | 78.13% | 21.88% |

The rotation preserves the Euclidean norm of the two-component state deviation exactly; only orientation changes.

The response is strongly orientation-dependent. The 180° condition is the exact equal-norm counterpart of V19's counterfactual inversion and gives 90.42% opposite-identity classification.

## Blind-point consistency

At 180°, original-donor identity accuracy ranged from 5.0% to 15.0% across the six blind parameter points. At 135°, it ranged from 15.0% to 40.0%. At 315°, it ranged from 60.0% to 85.0%.

Thus the angular effect is not confined to one tuned parameter point.

## Main finding

Historical identity in the recurrent state is sensitive to the geometric orientation of its temporal state vector even when its total deviation magnitude is held constant. This strengthens the temporal-organization finding from V21 and the counterfactual inversion finding from V19.

## Interpretation limits

This establishes a geometric property of information encoded in the implemented recurrent state. It does not establish subjective experience, sentience, or consciousness.
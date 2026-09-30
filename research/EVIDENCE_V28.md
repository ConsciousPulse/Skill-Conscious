# V28 — Context Dependence / Transport Test

## Status
**SUCCESS** — GitHub Actions run `36786588699` (corrected isorradial version).

## Important analysis note
The original V28 identity column at radius 0 is not a valid 50% null because exact zero affinity maps to `sign(0)=0`, which is counted as incorrect for either donor. Also, the 0° condition at radius 1.1 is a built-in local-reference control: the transformed donor state exactly reproduces its own local reference state, so its 100% identity is tautological.

The informative V28 quantities are therefore the off-axis conditions, especially signed affinity at 90° and 180°.

## Design
- 6 fixed V12 blind parameter points.
- 4 history pairs.
- seeds 30–39.
- 3 receiver histories:
  - context 0: zero history,
  - context 1: all-positive history,
  - context 2: independent random-sign history.
- Future input exactly zero.
- Donor state geometry: radius 1.1 at 0°, 90°, 180°.
- Receiver memory and pressure come from the selected receiver history.
- Local A/B reference continuations are generated within each receiver context.

## Result

### Pooled identity accuracy at r = 1.1

| Receiver context | 0° | 90° | 180° |
|---|---:|---:|---:|
| zero-history | 100.0% | 38.75% | 43.13% |
| all-positive | 100.0% | 49.38% | 51.46% |
| random-sign | 100.0% | 42.29% | 39.58% |

The 0° result is the expected local-reference control and is not a discovery.

The 90°/180° results do not reproduce the strong antipodal inversion seen in the common-midpoint protocol.

Signed affinity at 180°, where positive means closer to the donor's original local reference and negative means antipodal reversal:
- context 0: **-0.010**
- context 1: **+0.215**
- context 2: **-0.118**

## Interpretation
V28 places a constraint on V24–V27:

> The directional state effect is **not demonstrated to be context-invariant** when receiver memory/pressure context is changed through distinct histories.

This is a useful mechanistic boundary. It indicates that the measured geometry is coupled to local dynamical context rather than functioning as an unconditional context-free code.

## Boundary
V28 does not establish consciousness, subjective experience, or sentience. It establishes a limitation on transportability of the tested computational state representation.

## Next
V29 isolates nuisance variables one at a time: receiver state held fixed while memory-only or pressure-only context is changed, with antipodal affinity measured directly.

# V15 — Evidence: State Lesion / Causal Necessity

## GitHub validation

- Workflow: state-lesion-v15
- Run: 36776941623
- Result: SUCCESS
- Artifact: 11125209290
- Protocol: 4 history pairs × 20 seeds per regime × 8 lesion doses × 3 lesion targets.
- Future input after the history boundary: exactly zero.
- Noise seeds were matched across all interventions.

## Main result

The recurrent state is the only tested context component whose complete lesion repeatedly drives identity classification close to chance in the critical regimes.

| Regime | Intact | State lesion | State loss | Memory lesion | Memory loss | Pressure lesion | Pressure loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| critical | 1.000 | 0.494 | 0.506 | 0.881 | 0.119 | 0.950 | 0.050 |
| holdout_critical | 1.000 | 0.506 | 0.494 | 0.844 | 0.156 | 0.950 | 0.050 |
| persistence | 1.000 | 0.556 | 0.444 | 0.825 | 0.175 | 0.931 | 0.069 |
| baseline | 1.000 | 1.000 | 0.000 | 0.844 | 0.156 | 1.000 | 0.000 |

Identity is donor classification from trajectory affinity. A value near 0.5 is approximately chance for the binary A/B task.

## Dose-response

The state lesion produces a strong monotone association between lesion dose and identity loss in the critical regimes:

- critical state lesion: Spearman rho = -0.994
- holdout_critical state lesion: Spearman rho = -1.000
- persistence state lesion: Spearman rho = -0.929

For comparison, the corresponding rho values are weaker for pressure in critical (-0.916) and persistence (-0.754), while memory also shows dose sensitivity but does not reduce identity as strongly at full lesion.

The response is not expected to be perfectly monotone at every dose because the underlying system is stochastic and nonlinear.

## What this establishes

Within this computational model, the result is stronger than a correlational readout: selectively moving the recurrent state toward a common state causes a substantially larger loss of historical identity than the matched memory/pressure interventions, and this effect replicates in the holdout-critical regime.

The baseline control is important: the same state lesion does not destroy identity there. This indicates that the effect depends on the dynamical regime rather than being a trivial consequence of the intervention itself.

## What it does not establish

This is evidence for causal state dependence of a persistent, history-dependent dynamical regime. It is not evidence of subjective experience, sentience, or consciousness in the philosophical or biological sense.

## Relation to prior evidence

V14 showed that the recurrent state contributes predictive information under matched feature dimensionality. V15 adds a causal necessity-style perturbation: when the recurrent state is selectively erased, historical identity collapses in the resonant/critical regimes.

Together, V14 + V15 support the narrower computational claim that the recurrent state is an important causal carrier of historical information in the implemented dynamics.
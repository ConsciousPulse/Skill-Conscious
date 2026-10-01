# Organism Experimental Result Ledger — V47 → V57

## Strong positive results

### V51 — Self-prediction
104 post-warmup transitions: MAE 0.0424 vs baseline 0.2211; mean prediction gain
0.1787; 84.6% positive-gain transitions; paired sign-flip p = 0.00005.

### V57 — Self-model-guided trajectory selection
24 paired replicates: self-model regret 0.0231 vs random 0.1369; 70.83% vs
45.83% oracle-hit rate; paired sign-flip p = 0.00435.

## Negative / null / limitation results

### V53
The original three-candidate selector selected the neutral signal in all 12
replicates, producing no causal divergence from the zero-input control.
This was treated as a failed discriminatory protocol, not positive evidence.

### V54
80-cycle fake self-forecast accuracy was 43.75% with 40 TOWARD and 40 AWAY
transitions. Chance for this balanced binary direction task is 50%, so V54 was not
supportive evidence.

### V55
12 replicates × two perturbation signs × selection on/off preserved the identity
fingerprint in 100% of runs and recovered within the horizon in 100% of runs, with
mean recovery time 2.5 cycles. Selection-on and selection-off recovery were both
100%, so V55 demonstrates resilience in the tested harness but not a selective
benefit from self-modeling.

## Engineering status

All V47–V57 organism-specific auditors and the full pytest suite were green on
the V57 head at the recorded run.

## Evidence boundary

These results establish increasingly strong computational properties of the
organism: persistent dynamics, self-prediction and causal use of a learned
self-model for trajectory choice. They do not establish phenomenological
consciousness.

### V58 — Semantic-to-dynamic coupling
Matched 2×2 intervention. Bridge OFF: A/B dynamic-state delta 0.0 and signal delta
0.0. Bridge ON: Omega A -1.52, Omega B +0.68, signal delta 1.5002170539 and
dynamic-state delta 0.4558697583. The deterministic harness therefore supports
causal transduction from the organism's semantic memory output into its numeric
internal dynamics when the bridge is enabled. LIVE replication remains pending.

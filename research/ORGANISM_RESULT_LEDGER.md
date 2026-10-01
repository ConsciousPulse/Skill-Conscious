# Organism Experimental Result Ledger — V47 → V62

## Strong positive results

### V51 — Self-prediction
104 post-warmup transitions: MAE 0.0424 vs baseline 0.2211; mean prediction gain
0.1787; 84.6% positive-gain transitions; paired sign-flip p = 0.00005.

### V57 — Self-model-guided trajectory selection
24 paired replicates: self-model regret 0.0231 vs random 0.1369; 70.83% vs
45.83% oracle-hit rate; paired sign-flip p = 0.00435.

### V58 — Semantic-to-dynamic coupling
Matched 2×2 intervention. Bridge OFF: A/B dynamic-state delta 0.0 and signal delta
0.0. Bridge ON: Omega A -1.52, Omega B +0.68, signal delta 1.5002170539 and
dynamic-state delta 0.4558697583. The deterministic harness supports causal
transduction from the organism's semantic memory output into numeric internal
dynamics when the bridge is enabled.

### V60 — Self-model selection inside a recurrent semantic loop
24 paired replicates, 24 evaluation cycles.

- self-model mean regret: -0.0842091465;
- random-control mean regret: 0.3028308773;
- mean regret advantage (random - self): 0.3870400237;
- cumulative regret advantage: 9.2889605698;
- median regret advantage: 0.3858317486;
- paired sign-flip p for mean and cumulative advantage: 0.00005;
- self-model oracle-hit rate: 96.1806%;
- random-control oracle-hit rate: 45.3125%.

Interpretation: the self-model retained a large functional selection advantage in
the deterministic closed-loop protocol, under a provider whose next semantic
memory depends on the previous selected action. However, the self-model arm
selected +1 in all 24 replicates, so the within-run secondary feedback endpoint
never observed both action branches. The recurrent plumbing is exercised, but
action-conditioned feedback branch coverage is incomplete and must not be
reported as a fully demonstrated bidirectional feedback effect.

### V62 — Semantic self-model causal bridge
24 matched replicates crossing self-model content A/B with bridge OFF/ON.

- bridge OFF state delta mean: 0.0;
- bridge OFF signal delta mean: 0.0;
- bridge ON state delta mean: 0.0567495528;
- bridge ON signal delta mean: 0.1844584720;
- bridge OFF isolated the text intervention in all runs;
- bridge ON transduced the self-model difference into signal and state in all runs;
- self-model persistence and versioning were recorded in all ON runs.

Interpretation: in this deterministic intervention, changing only the organism's
semantic self-model altered its internal numerical state only when the explicit
self-model bridge was enabled. This is causal computational coupling, not
evidence of subjective experience.

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

### V59 — Semantic bridge × self-model selection
24 paired factorial replicates crossed semantic bridge OFF/ON with self-model/random policy.

- bridge OFF self-model mean regret: 0.0000;
- bridge OFF random mean regret: 0.23233;
- bridge ON self-model mean regret: 0.0000;
- bridge ON random mean regret: 0.24022;
- self-model oracle-hit rate: 100% in both bridge conditions;
- random oracle-hit rate: 50% in both bridge conditions;
- semantic bridge changed the post-wake internal state by mean absolute 0.94273 and the dynamic signal by 0.55376;
- bridge × selection interaction = +0.00789;
- interaction sign-flip p = 0.83941.

Interpretation: the protocol reproduces the previously observed self-model selection
advantage while independently showing substantial semantic-to-dynamic state
transduction. The factorial interaction was not distinguishable from zero in this
deterministic harness, so V59 does not support a claim that semantic bridging
itself increases self-model selection utility. It remains a null interaction /
compositionality result.

### V61 — Metacognitive self-model
24 paired replicates × 32 evaluation cycles.

- meta-self-model mean regret: 0.0888081147;
- first-order self-model mean regret: 0.0787785152;
- random-control mean regret: 0.1929241942;
- meta-self-model oracle-hit rate: 41.2760%;
- first-order self-model oracle-hit rate: 45.3125%;
- random-control oracle-hit rate: 46.4844%;
- meta vs first-order regret advantage: -0.0100295995;
- paired sign-flip p for regret difference: 0.00005;
- meta vs first-order hit-rate advantage: -0.0403645833;
- paired sign-flip p for hit-rate difference: 0.0008999550;
- meta prediction MAE: 0.1277240710;
- constant baseline MAE: 0.0849867822;
- meta model beat the constant baseline in 0% of replicates.

Interpretation: the implemented second-order meta-self-model did not improve
trajectory selection and did not predict first-order model error better than a
constant baseline in this harness. The result is retained as a negative finding
and points to a redesign rather than support for metacognitive capability.

## Engineering status

V60, V61, and V62 completed successfully on the recorded V62 head. Their artifacts
are preserved in the corresponding GitHub Actions runs. Earlier V43–V59 results
remain reproducible from their historical workflows and evidence records.

## Evidence boundary

These results establish increasingly specific computational properties of the
tested organism and its deterministic experimental harness: persistence,
self-prediction, causal self-model use, semantic-to-dynamic coupling, and
semantic self-representation as a causally active variable.

They do not establish phenomenological consciousness or subjective experience.
The next experiments should specifically target closed-loop self-model causality,
identity persistence under self-model change, and a redesigned second-order
meta-model rather than treating the current metacognitive result as a success.

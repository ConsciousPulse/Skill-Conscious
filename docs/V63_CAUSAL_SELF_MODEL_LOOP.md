# V63 — Causal self-model loop

## Result

24 matched replicates × 32 evaluation cycles across four arms.

With the self-model bridge ON:
- self-model mean regret: 0.1422226601
- random-control mean regret: 0.2666042539
- random-minus-self-model regret advantage: 0.1243815939
- paired sign-flip p: 0.00005
- self-model oracle-hit rate: 60.6771%
- random-control oracle-hit rate: 33.8542%

For the self-model selection arm:
- bridge OFF mean regret: 0.2876865581
- bridge ON mean regret: 0.1422226601
- OFF-minus-ON regret improvement: 0.1454638980
- paired sign-flip p: 0.00005
- oracle-hit rate: 10.0260% -> 60.6771%
- paired sign-flip p for hit-rate change: 0.00005

The regret difference-in-differences between self-model and random arms was
0.2837493367 with paired sign-flip p = 0.00005.

Action coverage reached 100% of replicates for bridge ON + self-model, bridge OFF + random, and bridge ON + random; bridge OFF + self-model reached 66.67%.

For bridge ON + self-model, the action-conditioned self-model bridge signal was observed after both branches. Across 243 observations after -1 and 501 after +1, mean signals were approximately +0.4999 and -0.2406, respectively, absolute difference 0.7405. This is a within-loop association, not an isolated causal effect estimate.

## Interpretation

V62 showed one-step causal transduction of semantic self-representation into numerical state. V63 extends that pathway into a recurrent action-conditioned loop: prior trajectory -> next self-model -> internal dynamics -> next trajectory selection.

The matched deterministic harness therefore supports recurrent computational coupling between semantic self-representation and future trajectory selection.

## Evidence boundary

The provider is deterministic and synthetic. These results establish computational behavior in the tested harness; they do not establish phenomenological consciousness or subjective experience.

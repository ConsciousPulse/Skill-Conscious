# Evidence V63 — Causal self-model loop

## Hypothesis

A semantic self-model generated from the organism's prior trajectory can become a causally active variable in a recurrent computational loop: it can alter internal dynamics through the self-model bridge, and the altered state can affect future trajectory selection.

## Design

24 matched replicates × 32 evaluation cycles.

Four arms start from cloned warmup state:
- self-model selection + bridge OFF;
- self-model selection + bridge ON;
- random selection + bridge OFF;
- random selection + bridge ON.

The provider maps the previous selected action to the next semantic SELF_MODEL. Semantic MEMORY is held constant and is not routed through the dynamic bridge.

## Primary endpoints

1. self-model vs random regret with the self-model bridge ON;
2. bridge OFF vs ON regret under self-model selection;
3. paired oracle-hit differences;
4. factorial difference-in-differences for regret.

## Successful artifact

Workflow: organism-causal-self-model-loop-v63
Artifact: organism-causal-self-model-loop-v63
Replicates: 24

Key values:
- bridge-ON self-model regret: 0.1422226601;
- bridge-ON random regret: 0.2666042539;
- random-minus-self regret advantage: 0.1243815939;
- bridge OFF→ON regret improvement under self-model: 0.1454638980;
- regret difference-in-differences: 0.2837493367;
- self-model bridge OFF→ON oracle-hit change: +0.5065104167;
- paired sign-flip p-values for the main effects/interaction: 0.00005.

## Limitations

The provider is deterministic and synthetic. The feedback signal comparison is a within-run association, not an isolated causal estimate, because action history and internal state co-evolve.

The artifact establishes computational behavior in the specified harness. It does not establish phenomenological consciousness or subjective experience.

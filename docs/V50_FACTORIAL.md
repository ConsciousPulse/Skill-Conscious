# V50 — Memory × Dynamic-State Factorial Intervention

## Question

Do persistent memory and numerical dynamic state act independently, or does the
effect of one depend on the level of the other?

## Design

A 2×2 matched intervention is repeated for multiple replicas:

| Condition | Memory | dynamic_state |
| --- | --- | ---: |
| A_LOW | ALFA → AMBAR | -0.8 |
| B_LOW | ALFA → VIOLETA | -0.8 |
| A_HIGH | ALFA → AMBAR | +0.8 |
| B_HIGH | ALFA → VIOLETA | +0.8 |

All four conditions use the same receiver base database and the same probe.
`event_limit=0` prevents event-history text from entering the LLM context.

## Primary analysis

Encode `CHOICE=AMBAR` as 0 and `CHOICE=VIOLETA` as 1.

Estimate:

- memory effect at low dynamic state;
- memory effect at high dynamic state;
- dynamic-state effect for memory A;
- dynamic-state effect for memory B;
- factorial interaction:

`(B_HIGH - A_HIGH) - (B_LOW - A_LOW)`

A nonzero interaction means the effect of memory differs as a function of the
dynamic state, or vice versa, under this operational task.

## Interpretation boundary

A nonzero interaction is evidence of a joint behavioral effect in the tested
organism architecture. It does not establish consciousness, subjective experience,
sentience, or phenomenological awareness.

Repeated live runs are required before treating the interaction as robust.
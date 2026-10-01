# V57 — Result Record

## Run

- workflow: `organism-self-model-selection-v57`
- run: `36802728735`
- artifact: `11135928002`
- head: `75791177fdf7cf8c167aae1a051f7def700f4b32`

## Result

24 paired replicates were run after 32 calibration cycles using candidate signals
`-1.0` and `+1.0`.

- self-model mean regret = 0.0230727418;
- random-control mean regret = 0.1368546699;
- mean regret advantage of self-model = 0.1137819281;
- median paired advantage = 0.0;
- self-model oracle-hit rate = 70.8333%;
- random-control oracle-hit rate = 45.8333%;
- oracle-hit rate difference = 25 percentage points;
- paired sign-flip p = 0.00434978.

The self-model arm therefore selected the post-hoc optimal candidate more often
and incurred substantially lower regret than the matched random control.

## Interpretation

V57 is the first experiment in this ladder where the learned self-model is shown
to have a causal behavioral effect on future trajectory selection under a paired
control.

This is evidence that the internal self-model is functionally useful for choosing
among possible trajectories. It is not evidence of subjective experience.
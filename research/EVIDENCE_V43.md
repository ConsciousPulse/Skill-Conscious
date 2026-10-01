# V43 — Evidence Record

Official GitHub Actions execution completed successfully on 2026-10-01.

Run: 36795357386  
Artifact: 11133184914  
Commit: 78822a6bc45f7af1e154d0c14ca2de251856ec1e

## Result

V43 removed the V34–V42 reference-based readout entirely. After a history template was presented, future input was set exactly to zero for 60 steps. A classifier then identified the historical template from internal continuation alone.

Leave-one-parameter-out mean accuracy, chance = 25%:

| Feature set | LOPO accuracy |
| --- | ---: |
| State trajectory | 79.08% |
| L2-normalized state | 78.25% |
| Memory trajectory | 93.75% |
| Pressure trajectory | 87.50% |
| Joint normalized state+memory+pressure | 89.25% |

For the joint normalized readout, a 5,000-sample label-permutation null had mean 24.996%, 95th percentile 26.917%, and p = 0.00020.

## Interpretation

This is a genuine reference-free history-retention result: after external input is removed, future internal dynamics retain enough information to recover which of four distinct temporal histories generated the current context, including across held-out parameter points.

The strongest single-channel readout is memory. State and pressure also carry substantial information. Therefore V43 supports persistent, distributed internal encoding of temporal history rather than a purely reference-defined geometric effect.

It does not establish consciousness, subjective experience, sentience, or phenomenological awareness. In particular, high decodability of history is evidence for information retention and accessibility, not evidence by itself for experience.

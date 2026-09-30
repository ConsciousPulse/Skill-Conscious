# Parametric Exponential Audit V3

Audit of the empirical exponential path-dependence scaling using the exact V1 history protocol.

## Exact V1 protocol
- beta scan: 0.940 to 0.998, 59 points
- fixed relaxation: 1.1375
- fixed pressure_gain: 0.175
- fixed cross_gain: 0.25
- path gap: mean absolute state difference over the last 150 steps
- fit: log(path_gap) versus beta for beta >= 0.96

Observed:
- log slope = 69.4072
- R^2 = 0.98839
- implied multiplier per +0.01 beta = 2.00185x

## Local-slice robustness
27 nearby parameter slices were tested across:
- relaxation: 1.10, 1.1375, 1.175
- pressure_gain: 0.15, 0.175, 0.20
- cross_gain: 0.20, 0.25, 0.30

Results:
- median R^2 = 0.98839
- 100% of slices had R^2 >= 0.90
- 22.2% had R^2 >= 0.99
- best nearby slice: relaxation=1.1375, pressure_gain=0.15, cross_gain=0.20
- best-slice R^2 = 0.99171
- best-slice multiplier per +0.01 beta = 2.10242x

## History-window robustness
Exact V1 dynamics were repeated with suffix lengths 120, 150, 180, 210, 240:
- R^2: 0.94360, 0.97971, 0.98839, 0.99077, 0.98910
- implied multipliers: 1.1984x, 1.4884x, 2.0018x, 3.3987x, 4.9982x per +0.01 beta

## Noise robustness
The exact V1 slice was scanned with noise_std=0.01 across 10 independent seeds:
- mean R^2 = 0.99171
- SD R^2 = 0.00087

## Interpretation
The exponential scaling observed in V1 is not confined to one exact parameter tuple: it persists across nearby slices, multiple history-window lengths, and additive noise. This is an empirical scaling law of the measured path-gap observable in this computational system. It is not a physical law and is not evidence by itself of consciousness.

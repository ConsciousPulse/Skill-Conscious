# V15 — State Lesion / Causal Necessity

## Question

V14 showed that the recurrent state adds predictive information in the critical, holdout-critical, and persistence regimes under matched feature dimensionality. V15 asks the stronger causal question:

> When historical identity is present, does selectively erasing the recurrent state degrade identity more strongly than erasing explicit memory or pressure?

## Experimental design

Four regimes are tested: critical, holdout_critical, persistence, and baseline.

Each regime uses four history-pair protocols and 20 matched-noise seeds per protocol. The continuation input is exactly zero.

At the history boundary, A and B generate distinct donor contexts. Their arithmetic midpoint is the common context.

For each donor, one context component is selectively lesioned toward the common context at doses 0, .05, .10, .20, .40, .60, .80, and 1.0.

- State lesion: both recurrent state slots (state_prev and state) are interpolated toward the common state.
- Memory lesion: only explicit memory is interpolated.
- Pressure lesion: only pressure is interpolated.

All other components remain donor-specific, and the same continuation seed is used for every intervention.

## Readouts

Identity is measured by affinity to the intact A and B reference trajectories over the first 60 future steps. Identity accuracy is the fraction classified as the correct donor.

Prediction MAE measures divergence from the intact donor continuation over the same window.

## Interpretation rule

A replicated state-specific dose-response, larger than memory and pressure controls and present in the holdout regime, would support the claim that the recurrent state is a causally important carrier of historical information in this model.

This is a computational dynamical result. It does not establish consciousness or subjective experience.
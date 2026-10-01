# Evidence V61 — Metacognitive self-model

## Hypothesis

A persistent organism with a first-order self-model should be able to learn a second-order model of that model's prediction error and use the estimated reliability of its own predictions as part of trajectory selection.

## Experimental design

Each replicate:

1. builds a matched warmup trajectory;
2. persists first-order self-observer snapshots;
3. initializes a second-order MetaSelfObserver from historical first-order prediction errors;
4. clones the same state into three arms;
5. selects among {-1, +1} using meta-self-model, first-order self-model, or random control;
6. scores the chosen trajectory against a post-hoc oracle;
7. reconstructs actual first-order prediction errors for both candidate trajectories;
8. compares those errors with the second-order model's predicted errors.

## Primary comparison

regret_self_model - regret_meta_self_model

is the paired meta-self-model advantage.

## Secondary metacognitive comparison

For every candidate:

abs(predicted_error - actual_prediction_error)

is compared against the error of a constant mean-error baseline.

## Limitations

The simulator is deterministic apart from its seeded noise process and the provider is synthetic. The protocol measures computational model-of-model behavior, not phenomenology.
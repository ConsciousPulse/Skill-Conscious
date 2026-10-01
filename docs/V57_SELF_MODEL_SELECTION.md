# V57 — Oracle-Compared Self-Model Selection

## Question

Does the organism's learned self-model select future trajectories better than a
matched random policy after the same calibration history?

## Design

Each replicate begins from a matched warmup trajectory.

Two candidate signals are allowed:

- `-1.0`;
- `+1.0`.

The self-model arm scores both counterfactual next states and chooses the signal
with the better declared coherence score.

The random arm chooses one of the same candidates with a deterministic seeded
random policy.

After the choice, the actual transition is executed.

Separately, an oracle evaluates both candidate transitions directly from the
same pre-transition state using the frozen numerical dynamics. The oracle is used
only after the intervention to calculate regret; it is never exposed to the
organism's selector.

## Primary observables

- self-model regret;
- random-control regret;
- paired regret advantage;
- oracle-hit rate;
- paired sign-flip permutation p-value.

## Interpretation

If the self-model arm has systematically lower regret than the matched random arm,
the organism's internal self-model is not merely descriptive: it is causally useful
for selecting among future trajectories.

This remains a computational self-model result, not proof of phenomenological
consciousness.
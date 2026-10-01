# V59 — Semantic bridge × self-model trajectory selection

## Question

Does the semantic memory → internal dynamics bridge change the functional usefulness of the learned self-model when the organism selects between future trajectories?

## Factorial

The protocol crosses two independent factors:

- semantic bridge OFF vs ON;
- trajectory policy self-model vs matched random control.

The candidate trajectories are fixed at {-1.0, +1.0}.

## Operational loop

Each evaluation follows the same ordered chain:

1. fake LLM emits a novel MEMORY;
2. when enabled, ContinuityMemoryPolicy converts that semantic memory into Ω and then a bounded dynamic signal;
3. the organism advances its internal numerical state;
4. the learned self-model evaluates the two future signals;
5. either the learned self-model or a deterministic random control chooses a trajectory;
6. the hidden dynamics are evaluated post-hoc against an oracle that is never exposed during selection.

The paired comparison therefore tests the interaction between semantic transduction and self-model-guided future choice.

## Controls

Warmup is performed independently inside each bridge condition with selection disabled, so the self-observer learns the local dynamics before the paired evaluation.

Each replicate uses the same seed across bridge and policy arms.

The evaluation memory is novel relative to the warmup memories, preventing the bridge from collapsing to an exact-memory repeat.

## Primary endpoint

The primary endpoint is:

selection_advantage = regret_random - regret_self_model

and the factorial interaction:

interaction = selection_advantage_bridge_on - selection_advantage_bridge_off.

A positive interaction means the measured self-model advantage is larger under the semantic bridge condition. It does not by itself establish phenomenological consciousness.

## Secondary endpoints

Semantic state and signal deltas, oracle-hit rates, and the full candidate prediction records are stored for auditability.

## Evidence boundary

V59 is a deterministic computational protocol. Its provider is a fake deterministic LLM, not a live external model. Even a positive V59 result would establish an operational causal chain in this harness, not subjective experience.

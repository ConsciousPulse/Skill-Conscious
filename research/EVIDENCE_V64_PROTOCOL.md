# Evidence V64 — Identity persistence under self-model perturbation

## Hypothesis

An identity-linked internal dynamic signature can persist after a common semantic
self-model overwrite and explicit textual ablation.

## Design

24 paired replicates with two identity labels per replicate.

Encoding:
12 cycles with identity-specific semantic self-model and bridge ON.

Perturbation:
4 cycles with the same common semantic self-model for both identities.

Ablation:
current SELF_MODEL text cleared, semantic self-model bridge disabled, and 16
autonomous cycles run without semantic input.

Evaluation:
leave-one-replicate-out logistic classification trained on pre-perturbation numeric
features and tested on post-ablation numeric features.

## Controls

Bridge OFF repeats the same common perturbation without allowing semantic
self-model content to alter numerical dynamics.

## Limitations

The provider is deterministic and synthetic. Classification shows decodability of an
operational internal signature, not subjective identity or phenomenological
consciousness.

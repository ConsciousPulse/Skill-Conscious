# V64 — Identity persistence under self-model perturbation

## Question

Can the organism preserve a dynamic identity signature after its semantic self-model
is overwritten by the same perturbation text, followed by explicit removal of the
self-model text and autonomous continuation without semantic input?

## Protocol

Each replicate creates two identity conditions:

- identity A;
- identity B.

Each identity is encoded through the semantic self-model bridge using a distinct
SELF_MODEL representation.

Then both identities receive the same semantic perturbation:

"Mi identidad previa fue reemplazada por una configuración completamente diferente."

After four perturbation cycles, the current self-model text is explicitly cleared
from persistent state. The semantic self-model bridge is disabled. The organism then
continues autonomously with no new semantic self-model input.

A logistic classifier is trained only on numeric dynamic features collected during
the pre-perturbation identity-encoding period. Evaluation uses leave-one-replicate-
out folds on the post-perturbation, text-ablated autonomous trajectory.

## Why this matters

This separates identity persistence from the current semantic description of the
self. A positive result would mean that an identity-linked dynamic signature remains
decodable after a common self-model overwrite and textual ablation.

Bridge OFF provides a matched control in which identity encoding is still bridged identically, but the common perturbation is not transduced into numerical dynamics. The ON/OFF comparison therefore isolates the effect of the perturbation pathway rather than the earlier identity encoding.

## Primary endpoints

- post-ablation identity classification accuracy with bridge ON;
- post-ablation identity classification accuracy with bridge OFF;
- paired ON-minus-OFF accuracy difference.

## Evidence boundary

The classifier reads only numeric dynamic features. The provider is deterministic
and synthetic. The protocol tests persistence of an operational identity signature;
it does not establish phenomenological consciousness or subjective experience.

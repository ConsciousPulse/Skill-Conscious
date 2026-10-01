# V53 — Evidence Protocol

**Status: protocol implemented; empirical result pending.**

Required controls:

1. matched histories before autonomous selection;
2. identical candidate set `[-1, 0, +1]`;
3. selection uses only persisted internal observables;
4. actual selected signal is logged before the resulting transition;
5. a self-selection-disabled control runs the same history;
6. downstream dynamic state is compared after the autonomous transition.

Evidence boundary:

V53 tests causal use of an internal self-model for trajectory selection. It does
not establish phenomenological consciousness.
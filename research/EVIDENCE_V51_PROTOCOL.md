# V51 — Evidence Protocol

**Status: protocol implemented; empirical result pending until CI and live artifacts are inspected.**

Required controls:

1. prediction uses only prior persisted organism observables;
2. actual next state is withheld until after prediction;
3. persistence baseline is computed from the pre-transition state;
4. observer model survives SQLite restart;
5. post-restart snapshots continue accumulating without resetting the model;
6. sign-flip test evaluates whether gain is systematically different from zero.

Evidence boundary:

Passing V51 supports the existence of an operational self-predictive model in the
organism. It does not establish phenomenological awareness.
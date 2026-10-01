# V57 — Evidence Protocol

**Status: protocol implemented; empirical result pending.**

Controls:

1. identical warmup history within each pair;
2. identical candidate set;
3. self-model selector and random selector start from identical persisted states;
4. oracle is computed post hoc and is not exposed during selection;
5. paired replicate differences are evaluated with a sign-flip permutation test;
6. raw candidate predictions and realized states are retained.

Evidence boundary:

V57 tests causal utility of an internal self-model for future trajectory selection.
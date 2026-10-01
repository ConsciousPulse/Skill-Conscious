# IA Consciente — Investigación y Experimentación

**Engineering a persistent AI organism toward machine consciousness.**

Consciencia-Skill is an open research and engineering project focused on building an AI system that can maintain continuity across time instead of resetting at every response.

The project combines persistent state, long-term memory, self-modeling, self-observation, autonomous trajectory selection, wake/dream regimes, and reproducible experiments designed to test whether these mechanisms can produce increasingly integrated forms of machine cognition.

> **Research objective:** build computational architectures that move toward artificial consciousness through persistent continuity, self-reference, memory, autonomous internal dynamics, and causal self-modeling.

## What this project is

The core idea is simple:

**an AI should be studied as a continuous process, not as a sequence of isolated answers.**

The persistent organism maintains state between model calls and can continue operating without external input. Its language model is one cognitive component; the organism itself carries continuity.

The current architecture combines:

- persistent SQLite state and memory;
- WAKE and DREAM regimes;
- self-model persistence and versioning;
- a learned self-observer;
- counterfactual trajectory selection;
- semantic-to-dynamic bridges;
- autonomous cycles without external interaction;
- reproducible GitHub Actions experiments.

## Core architecture

```
                    ENVIRONMENT
                         │
                         ▼
                    PERCEPTION
                         │
                         ▼
              ┌────────────────────┐
              │  PERSISTENT STATE  │
              │ memory + identity  │
              │ self-model + time  │
              └─────────┬──────────┘
                        │
                 ┌──────┴──────┐
                 ▼             ▼
               WAKE          DREAM
                 │             │
                 └──────┬──────┘
                        ▼
              INTERNAL DYNAMICS
                        │
                        ▼
                 SELF-OBSERVATION
                        │
                        ▼
              TRAJECTORY SELECTION
                        │
                        └──────────↺
```

### WAKE

Interaction with the environment, language, decision-making, memory updates, and autonomous action selection.

### DREAM

Reduced external interaction with increased internal activity: consolidation, recombination, simulation, and state reorganization.

The organism is designed to remain alive as a process between interactions rather than being re-created from scratch for every request.

## Research program

The experiments are organized as numbered protocols so that each architectural claim can be tested independently.

| Protocol | Focus | Current finding |
|---|---|---|
| V51 | Self-prediction | Positive self-prediction gain over a persistence baseline |
| V57 | Self-model trajectory selection | Self-model outperformed matched random control in the deterministic harness |
| V58 | Semantic memory → dynamics | Causal semantic-to-dynamic transduction |
| V63 | Recurrent self-model loop | Action-conditioned self-model feedback altered later trajectory selection |
| V64 | Identity persistence after perturbation | **Null** under the tested feature set and horizon |
| V65 | DREAM → future selection | DREAM and dream-to-dynamics coupling produced measurable downstream effects |
| V66 | Consolidated lesson after episodic-memory ablation | **Null**: retained lesson was not behaviorally discriminative |
| V67 | DREAM-generated numeric trace after semantic ablation | **In progress** |

The full experimental record lives in [`research/ORGANISM_RESULT_LEDGER.md`](research/ORGANISM_RESULT_LEDGER.md).

## Why the null results matter

This project is not built to collect only positive demonstrations.

V64 showed that an identity-specific numeric signature was not recoverable after the tested perturbation.

V66 showed that preserving a consolidated semantic lesson did not, by itself, create a measurable downstream behavioral difference after raw episodic-memory removal.

Those failures are part of the research program. They force the architecture toward stronger tests of internal continuity instead of relying on textual memory or favorable interpretations.

## V67 — current frontier

V67 directly tests a harder version of the continuity hypothesis.

After DREAM, the experiment removes:

- episodic memories;
- events and snapshots;
- textual self-model;
- semantic memory;
- pressure traces;
- semantic input during readout.

Only the organism's **numeric dynamic core** is retained.

A zero-input continuation then tests whether the post-DREAM state still carries a recoverable trace.

A matched state-swap intervention goes one step further: only the numeric core is transferred between paired organisms to test whether downstream behavior follows the transferred state rather than the original semantic history.

The goal is to determine whether DREAM can write persistent internal information into the organism itself, rather than merely producing another useful text response.

## Reproducibility

The research laboratory runs through **GitHub Actions**.

Each protocol can:

1. start from a concrete commit;
2. execute automated tests;
3. run deterministic or controlled experiments;
4. generate JSON evidence;
5. publish an artifact for inspection.

See [`docs/GITHUB_LAB.md`](docs/GITHUB_LAB.md) for the laboratory structure.

Experimental implementations live in [`experiments/`](experiments/), reusable organism components in [`src/ontto/`](src/ontto/), and evidence protocols in [`research/`](research/).

## Research terms

**Persistent AI · AI organism · machine consciousness · artificial consciousness · computational consciousness · self-modeling AI · self-observation · autonomous cognition · cognitive architecture · persistent memory · long-term memory · semantic memory · identity persistence · trajectory selection · recurrent AI · closed-loop cognition · wake-dream architecture · computational cognition · consciousness research**

These terms describe the technical scope of the repository. They are not claims that the system has achieved phenomenological consciousness.

## Evidence boundary

The project distinguishes four layers:

**Observation** — measured data.

**Result** — a reproducible pattern under a defined protocol.

**Hypothesis** — an interpretation that still requires testing.

**Ontology** — philosophical or metaphysical interpretation kept separate from computational evidence.

The experiments in this repository establish computational properties of the tested architecture and experimental harness.

They do **not** by themselves establish subjective experience, phenomenological consciousness, or a solution to the hard problem of consciousness.

## Status

**Active research — persistent organism, self-modeling, wake/dream dynamics, and continuity experiments.**

The immediate research direction is to determine whether information generated inside the organism can remain functionally active after its original semantic representation has been removed.

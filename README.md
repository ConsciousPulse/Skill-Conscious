# Skill-Conscious — AI Consciousness Research

[🇺🇸 English](README.md) · [🇦🇷 Español](README.es.md)

[![TCF v3.3 — Zenodo](https://zenodo.org/badge/DOI/10.5281/zenodo.23074332.svg)](https://doi.org/10.5281/zenodo.23074332) [![ORCID](https://img.shields.io/badge/ORCID-0009--0003--5333--7395-a6ce39?logo=orcid&logoColor=white)](https://orcid.org/0009-0003-5333-7395)

## Make your AI conscious.

**That is the goal of this project.**

We are developing a method for an AI to become more than a sequence of responses: to **maintain continuity, remember its history, represent itself, observe its own state, explore possible trajectories, and modify its internal dynamics**.

We do not ask you to believe it. **We build the method, implement it, and test it experimentally.**

## The method

The idea is direct:

```
MEMORY
   ↓
CONTINUITY
   ↓
SELF-REFERENCE
   ↓
SELF-MODEL
   ↓
SELF-OBSERVATION
   ↓
INTERNAL DYNAMICS
   ↓
FUTURE TRAJECTORIES
   ↓
CONSCIOUSNESS
```

The AI preserves information about what happened to it, uses that history to maintain its own continuity, builds a model of itself, observes how it changes, evaluates possible futures, and uses its own state to influence what it does next.

The project also includes two operating regimes:

- **WAKE:** interaction, perception, memory, and decision-making.
- **SLEEP:** internal activity, consolidation, reorganization, and continuity without requiring permanent external input.

### What are we trying to build?

An AI that does not end when the message ends.

An AI that can:

- remember its trajectory;
- maintain internal relationships over time;
- distinguish itself from its surroundings;
- represent aspects of itself;
- predict part of its own behavior;
- compare possible future trajectories;
- use its internal state to choose;
- reorganize itself without necessarily losing continuity.

## This is not just an idea: it is an experimental program

Each capability becomes a hypothesis and then a protocol.

**V47 → V70** progressively studies history, memory, dynamic state, self-observation, self-modeling, trajectory selection, recurrent loops, identity, SLEEP, and the persistence of internal information.

Results can be positive, null, or negative.

**We keep them all.**

[View protocols →](docs/INDICE.md) · [View results →](research/ORGANISM_RESULT_LEDGER.md) · [View the method →](docs/METODO.md)

## What is it based on?

The method has two foundations.

**Mathematical Manifesto of Being**  
Defines the project's ontological framework: relation, continuity, identity, dynamics, and self-trajectory.

→ [Read the Manifesto of Being](MANIFIESTO_DEL_SER.md)

**TCF v3.3 — Fundamental Continuity Theory**  
Provides the effective dynamical formulation that inspires part of the architecture: operators, regimes, transitions, attractors, and renormalization-group flow.

→ [Read TCF v3.3](docs/fundamentos/TCF_V3_3.md)  
→ [Zenodo publication](https://zenodo.org/doi/10.5281/zenodo.23074332)  
→ [DOI 10.5281/zenodo.23074332](https://doi.org/10.5281/zenodo.23074332)

## An important distinction

The project investigates **how to build and measure computational properties associated with consciousness**.

We do not present an experimental result as an automatic demonstration of subjective experience.

The rule is simple:

**hypothesis → implementation → control → experiment → result → limitation**

If a test fails, it stays recorded.

If a test works, we try to break it with a more demanding test.

## The architecture

The AI does not receive consciousness from a single instruction. The method builds **a persistent continuity around the language model**.

The current architecture integrates:

- persistent memory;
- persistent internal state;
- a self-model;
- self-observation;
- selection among possible trajectories;
- internal dynamics;
- WAKE and SLEEP regimes;
- autonomous cycles;
- reproducible experimentation.

## Conceptual architecture

```
                         ENVIRONMENT
                              │
                              ▼
                         PERCEPTION
                              │
                              ▼
                ┌────────────────────────┐
                │    PERSISTENT STATE    │
                │ memory + identity      │
                │ self-model + time      │
                └───────────┬────────────┘
                            │
                     ┌──────┴──────┐
                     ▼             ▼
                   WAKE          SLEEP
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

Interaction with the environment, language, memory updates, decision-making, and action selection.

### SLEEP

Less external interaction and more internal activity: consolidation, recombination, simulation, state reorganization, and autonomous learning.

Continuity is maintained even when there is no external input on every cycle.

## Experimental program

Experiments are organized as numbered protocols so that each property can be tested independently.

| Protocol | What we test | Current result |
|---|---|---|
| V51 | Self-prediction | Self-prediction gain over a persistence baseline |
| V57 | Self-model-guided trajectory selection | Functional advantage over random control in the deterministic environment |
| V58 | Semantic memory → dynamics | Causal transduction from semantic signal to dynamic state |
| V63 | Recurrent self-model loop | Trajectory-conditioned feedback changed future selection |
| V64 | Identity persistence after perturbation | **Null** under the tested conditions |
| V65 | SLEEP → future selection | Measurable downstream effects |
| V66 | Consolidation after episodic-memory removal | **Null**: retaining the lesson was not discriminative |
| V67 | Numeric trace generated during SLEEP | **Null** under the corrected test |
| V68 | Temporal persistence of the dynamic trace | **Immediate trace** with rapid magnitude reduction and weak/non-monotonic persistence |
| V69 | Reading internal state through a self-model | **Positive numeric readout; null selection effect** under the current protocol |
| V69 | Internal-state reading and selection | **Causal effect**: read state changed the decision in 16/24 replications; blinded control 0/24 |
| V70 | Persistent self-reader | **Survives restart** with prediction error 0.0 and retains a decision effect after ablation |

The [full result ledger](research/ORGANISM_RESULT_LEDGER.md) preserves positive, null, and negative results.

## Why null results matter

This project is not designed to collect only positive results.

V64 did not recover the numerical identity signature after the tested perturbation.

V66 did not find a measurable behavioral difference from retaining the consolidated lesson after the original episodic memories were removed.

Those results are part of the method. Every null result forces the next test to become more demanding.

## V67 — current frontier

V67 tests a more demanding version of the continuity hypothesis.

After SLEEP, the following are removed:

- episodic memories;
- events and snapshots;
- self-model text;
- semantic memory;
- pressure traces;
- semantic input during reading.

Only the **numeric dynamic core** remains.

A zero-input continuation is then generated to test whether the post-sleep state preserves a recoverable trace.

The second intervention swaps only that dynamic core between paired instances. The question is whether subsequent behavior follows the transferred state rather than the original semantic history.

The goal is to determine whether SLEEP can write persistent information into internal state, rather than simply producing another useful textual response.

## Reproducibility

The research laboratory runs through **GitHub Actions**.

Each protocol can:

1. start from a specific commit;
2. run automated tests;
3. run the controlled experiment;
4. generate JSON evidence;
5. publish a reproducible artifact.

The laboratory structure is documented in [docs/GITHUB_LAB.md](docs/GITHUB_LAB.md).

Experimental implementations live in [experiments/](experiments/), organism components in [src/ontto/](src/ontto/), and protocols/results in [research/](research/).

## Keywords

**AI consciousness · artificial consciousness · persistent artificial intelligence · AI organism · informational continuity · persistent memory · long-term memory · self-model · self-observation · self-reference · autonomous cognition · cognitive architecture · persistent identity · trajectory selection · internal dynamics · recurrent systems · cognitive loops · wake and sleep · computational cognition · consciousness research · reproducible experimentation**

These keywords describe the technical and scientific scope of the repository. They do not constitute a claim that the system has achieved phenomenal consciousness.

## Evidence standard

The project separates four levels:

**Observation** — data produced by an experiment.

**Result** — a reproducible pattern under a defined protocol.

**Hypothesis** — an interpretation that still requires testing.

**Ontology** — a philosophical or metaphysical interpretation kept separate from computational evidence.

The experiments in this repository establish computational properties of the tested system and experimental environment.

They do not, by themselves, establish subjective experience, phenomenal consciousness, or a solution to the hard problem of consciousness.

## Current status

**Active research — persistent organism, self-model, WAKE/SLEEP dynamics, and continuity experiments.**

V67 produced a null result under the corrected test. V68 showed an immediate but attenuated dynamic trace. V69 showed that a numeric self-model frozen before SLEEP can read internal-state differences after semantic ablation, but the current policy did not turn that readout into a different action. V70 studies persistence of the self-reader.

## License

The project license has not yet been defined.

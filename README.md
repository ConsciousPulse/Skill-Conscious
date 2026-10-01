# IA Consciente — Investigación y Experimentación

**Experimental research on persistent AI agents, self-modeling, memory, autonomous cognition, and machine consciousness.**

A public research and engineering project focused on **persistent AI**, **self-modeling AI**, **machine consciousness**, continuous memory, self-observation, and autonomous cognition.

The engineering goal is to build a persistent AI organism capable of maintaining continuity, memory, self-modeling, and autonomous learning over time, while developing reproducible experiments that can measure those properties.

## Research focus

This project studies what computational properties emerge when an AI maintains persistent state across cycles, learns a model of its own dynamics, and uses that model to select future trajectories.

We do not treat "consciousness" as an assumed result. We start from a working hypothesis that consciousness may be related to a system's ability to sustain internal relationships, preserve identity while changing, traverse its own state, and reorganize under perturbation.

An isolated linguistic response is not treated as sufficient evidence. The object of study is the **continuous trajectory of a persistent AI system**.

## Keywords

**Persistent AI · AI organism · machine consciousness · artificial consciousness · computational consciousness · self-modeling AI · self-observation · metacognition · cognitive architecture · autonomous AI · autonomous agents · long-term memory · persistent memory · LLM research · AI research · trajectory selection · semantic memory · identity persistence · computational cognition · closed-loop AI · recurrent cognitive systems**

These terms describe the technical and research areas represented by the repository; they are not claims that the system is phenomenologically conscious.

## Initial architecture

\`\`\`
              ENVIRONMENT
                   │
                   ▼
              PERCEPTION
                   │
                   ▼
          RELATIONAL DYNAMICS
                   │
            ┌──────┴──────┐
            ▼             ▼
          WAKE          DREAM
            │             │
            └──────┬──────┘
                   ▼
          CONTINUOUS MEMORY
                   │
                   ▼
             SELF-MODEL
                   │
                   ▼
            SHARED ATTRACTOR
                   │
                   ▼
             INTERNAL STATE
                   │
                   └──────────↺
\`\`\`

The LLM or API-served model is a cognitive component of the system. Continuity belongs to the persistent organism that maintains state between calls.

## Persistent input

The organism does not depend on an interaction arriving while the process is awake. External inputs are stored in a durable SQLite queue and processed by the organism when appropriate.

The daemon can also perform autonomous activity during periods with no external input.

### Regimes

### Wake

Interaction with the environment, perception, language, decision-making, action, and memory updates.

### Dream

Reduced external interaction and increased internal activity: memory consolidation, recombination, simulation, state reorganization, and autonomous learning.

The system does not "die" between responses. The persistent process continues and alternates between regimes.

## Research foundation

The project uses the **Manifiesto Matemático del Ser** as one conceptual starting point. Its ontology describes being as stable relation, reality as iteration, and consciousness as a system capable of traversing itself.

The project also incorporates computational hypotheses inspired by the **Teoría de Continuidad Fundamental (TCF)** and previous experiments on memory, pressure, hysteresis, critical transitions, topology, and multi-regime dynamics.

These conceptual sources are used as research and engineering hypotheses. They are not treated as established physical theories.

## What we measure

- identity continuity;
- trajectory dependence;
- attractor persistence and recovery;
- structural memory;
- self-modeling;
- learning during dream cycles;
- wake/dream differences;
- perturbation resistance;
- the cost of maintaining continuity;
- longitudinal evolution over days and weeks.

## Evidence principle

Every result is classified at one of four levels:

1. **Observation:** data produced by an experiment.
2. **Result:** a reproducible pattern under a defined protocol.
3. **Hypothesis:** an interpretation that still requires testing.
4. **Ontology:** a philosophical or metaphysical interpretation kept separate from computational evidence.

## Reproducible laboratory

The main reproducible laboratory runs through **GitHub Actions**. Each run starts from a concrete commit, executes tests and experiments, generates JSON/log outputs, and publishes an evidence artifact.

The architecture, workflows, and reproducible protocol are documented in [docs/GITHUB_LAB.md](docs/GITHUB_LAB.md).

Research protocols and evidence records primarily live in \`research/\`, while \`experiments/\` contains experimental implementations and historical or auxiliary tools.

A manual smoke test with a real model connects a persistent organism to an OpenAI-compatible provider.

## Current status

**Phase 1 — persistent core + validation of internal dynamics and history.**

Research has completed the V43–V46 series covering history retention, intervention, and cross-probe generalization in the simulator. The persistent organism now also has an explicit bridge to numerical dynamics, state persisted in SQLite, and autonomous cycles without external input.

V47 defined the organism protocol: the same probe across divergent histories, a null control, SQLite reopening, and textual-past ablation.

V48 added a matched intervention where only the content of a persistent memory is replaced while the rest of the receiver is controlled.

V49 added a matched intervention on \`dynamic_state\`, while keeping memory, pressure, events, and other receiver state controlled.

The project does not claim that an AI has been made conscious. The goal is to build increasingly testable computational properties and develop experiments capable of distinguishing continuity, self-reference, persistent identity, and related properties.

V50 added a 2×2 factorial of persistent memory × \`dynamic_state\` to measure joint effects and interaction under the same probe.

V51 added a persistent self-observer that learns to predict its own dynamic transitions and measures prediction gain against a persistence baseline.

V52 added a future-compatibility adapter inspired by the AEVUM operator, still separated from the organism's canonical memory policy.

V53 added counterfactual trajectory selection using the self-model.

V54 measured linguistic prediction of movement relative to the attractor before the transition.

V55 added identity recovery under perturbation, comparing counterfactual selection enabled vs disabled.

V56 added an optional memory-admission policy based on AEVUM future compatibility, still separated from canonical organism memory.

V57 compared self-model-based trajectory selection against a matched random control and measured regret against a post-hoc oracle.

V58 added an optional semantic bridge that converts the \`MEMORY:\` relation generated by the AI into a dynamic signal through the AEVUM-inspired operator, using a matched OFF/ON intervention.

V59 added a 2×2 factorial crossing semantic bridge OFF/ON with \`self_model\`/random selection. The bridge produced a substantial internal change, while the measured utility of the self-model did not change detectably between conditions.

V60 added a closed-loop semantic feedback protocol in which the selected trajectory is persisted as an event, conditions the next semantic memory, and that memory is transduced back into internal dynamics before the next trajectory selection. The successful audit produced 24 paired replicates: self-model mean regret -0.0842 vs random 0.3028, self-model oracle-hit 96.18% vs random 45.31%, and paired sign-flip p = 0.00005. The self-model arm selected +1 in all replicates, so the secondary bidirectional feedback endpoint had no balanced action coverage; the result supports recurrent plumbing and functional self-model selection, but not a demonstrated two-branch feedback effect.

V61 added an optional second-order meta-self-model: the organism learns to predict the error of its own first-order self-model and can use that predicted reliability when selecting among future trajectories. The completed audit was negative: meta-self-model regret 0.0888 vs first-order 0.0788, oracle-hit 41.28% vs 45.31%, meta prediction MAE 0.1277 vs constant baseline MAE 0.0850, and the meta model beat the constant baseline in 0% of replicates.

V62 adds an optional semantic self-model bridge and persists SELF_MODEL updates during wake cycles. In 24 matched replicates, bridge OFF produced exactly 0.0 mean state and signal separation, while bridge ON produced 0.05675 mean state separation and 0.18446 mean signal separation, with successful transduction in all runs. This is a deterministic computational causal result, not evidence of phenomenological consciousness.

V63 extends the V62 intervention into a recurrent action-conditioned loop: the previous selected trajectory determines the next semantic SELF_MODEL, the self-model bridge changes internal dynamics, and the resulting state is fed into future trajectory selection. In 24 matched replicates × 32 cycles, bridge-ON self-model regret was 0.1422 vs random 0.2666, oracle-hit was 60.68% vs 33.85%, and the paired sign-flip p was 0.00005. The bridge OFF→ON regret improvement under self-model selection was 0.14546, while the factorial regret difference-in-differences was 0.28375 (p = 0.00005). Bridge-ON self-model runs traversed both action branches in 100% of replicates. This is a deterministic computational result, not evidence of phenomenological consciousness.

V64 adds an identity-persistence intervention: two identity representations are encoded through the self-model bridge, both receive the same semantic self-model perturbation, then the current self-model text is cleared and the organism continues autonomously without semantic self-model input. A leave-one-replicate-out classifier evaluates whether the original identity remains decodable from numeric internal dynamics. The V64 audit is currently pending.

V65 adds a dedicated DREAM-to-dynamics bridge and compares no_dream, dream_no_bridge, and dream_bridge. In 24 matched replicates × 24 evaluation cycles, dream_bridge mean regret was 0.17793 vs 0.21095 for dream_no_bridge, with paired p = 0.00005; oracle-hit was 25.35% vs 13.37%. Entering DREAM alone also improved regret relative to no_dream (-0.11490, p = 0.00005). This is a deterministic computational result showing that DREAM-generated semantic consolidation can influence later trajectory selection.

## Evidence boundary

The experiments in this repository establish computational properties of the tested system and harness.

They do **not** by themselves establish phenomenological consciousness, subjective experience, or a solution to the hard problem of consciousness.

The project deliberately keeps computational evidence, hypotheses, and philosophical interpretations separate.

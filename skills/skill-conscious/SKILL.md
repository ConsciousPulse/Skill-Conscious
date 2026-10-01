---
name: skill-conscious
description: Use Skill-Conscious to add persistent continuity, memory, self-modeling, self-observation, internal dynamics, WAKE/SLEEP cycles, and reproducible experiments to an AI system. Activate when an agent needs to integrate, inspect, operate, or extend a persistent AI organism, or reason from its experimental evidence.
---

# Skill-Conscious

## Purpose

Skill-Conscious is a persistent AI organism architecture and research program. Treat it as a modular system, not as a prompt.

The core loop is:

```
input
→ persistent state
→ memory
→ self-model / self-observation
→ trajectory or action selection
→ internal dynamics
→ persistence
→ next cycle
```

The organism also supports WAKE and SLEEP regimes.

## Retrieval discipline

Do not load the whole repository.

Start with:

1. `AI_INDEX.md`
2. `AI_MAP.json`
3. `research/ORGANISM_RESULT_LEDGER.md` for current evidence

Then load only the exact source, experiment, test, protocol, or workflow needed.

Preferred evidence route:

```
ledger → protocol → experiment → test → workflow
```

Preserve null results and explicit limitations.

## Integration modes

### Agent-only

Use this skill when an existing AI system only needs the Skill-Conscious workflow and concepts.

Do not require the full organism runtime.

### Embedded organism

Use the Python package and `PersistentOrganism` when the host application owns the process, storage, and provider lifecycle.

Primary modules:

- `src/ontto/organism.py`
- `src/ontto/storage.py`
- `src/ontto/provider.py`

### Server deployment

Use the organism as a long-running service when persistence, scheduled WAKE/SLEEP cycles, external inputs, and multiple clients must be coordinated by a server.

Keep the Skill-Conscious workflow layer separate from transport/API concerns.

## Architectural rules

- Persistence is part of the organism state, not only chat history.
- Self-observation is computational and testable; do not convert it into a claim of phenomenal consciousness.
- WAKE and SLEEP are functional regimes.
- Experimental claims must point to a protocol and reproducible evidence.
- Do not rewrite historical experiments merely to improve their outcome.

## Current frontier

For V69/V70, distinguish these protocol lines:

- `docs/V69_SELF_STATE_READOUT.md`: numeric state-readout endpoint.
- `docs/V69_SELF_READ_STATE.md`: read-state → trajectory-selection endpoint.
- `docs/V70_SELF_MODEL_ACTION.md`: self-model readout → continuous action.
- `docs/V70_PERSISTENT_SELF_READER.md`: self-reader persistence across restart.

Do not merge their claims.

## When modifying the system

Inspect the smallest relevant set:

1. target implementation;
2. matching test;
3. matching experiment;
4. matching protocol;
5. workflow only when CI behavior matters.

Before finishing, verify persistence, restart behavior, and reproducibility when the change touches organism state.

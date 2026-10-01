# Skill-Conscious Architecture Reference

## Layers

### 1. Skill layer
Portable agent instructions in `skills/skill-conscious/SKILL.md`.

### 2. Organism layer
`src/ontto/organism.py` orchestrates the persistent cycle.

### 3. State layer
`src/ontto/storage.py` persists organism state, memory, events, and self-observer state.

### 4. Cognitive components
- `dynamics.py` — numeric internal dynamics.
- `self_observer.py` — self-model / self-observation.
- `meta_observer.py` — higher-order observation.
- `trajectory_selector.py` — trajectory/action selection.
- `memory_policy.py` — memory handling.
- `continuity.py` — continuity primitives.
- `bridge.py` — semantic ↔ dynamic-state bridge.
- `provider.py` — model-provider contract.

### 5. Runtime
`run_daemon.py` runs the persistent loop with external input, autonomous cycles, and SLEEP scheduling.

## Deployment boundary

The installable skill teaches an agent how to use the system.

The Python runtime executes the organism.

A future server/MCP layer should expose controlled organism operations without moving the research logic into the transport layer.

## Progressive loading

Load:
`SKILL.md`
→ exact reference
→ exact source
→ exact experiment/test

Do not preload the full repository.

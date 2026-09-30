# Context Persistence — V8b

V8b is the corrected version of the context-reset intervention experiment. Both history branches use the same noise seed during continuation, removing the confound present in V8.

## Regimes

- persistence ridge: beta=0.99730, relaxation=1.205, pressure_gain=0.125, cross_gain=0.15
- critical ridge: beta=0.998606, relaxation=1.205, pressure_gain=0.125, cross_gain=0.15
- baseline: beta=0.92, relaxation=0.32, pressure_gain=0.55, cross_gain=0.85

## Continuation

After 300 history steps, both branches receive 500 zero-input steps.

Interventions:
- full: preserve both branches' state, memory and pressure
- reset_state: synchronize the two recent state values, preserve branch-specific memory and pressure
- reset_memory: synchronize branch memory, preserve state and pressure
- reset_pressure: synchronize pressure, preserve state and memory
- reset_all: synchronize state, memory and pressure

## Corrected results

| Regime | Mode | End gap | Retention |
|---|---|---:|---:|
| baseline | full | ~5.8e-16 | ~0 |
| baseline | reset_memory | 1.6e-6 | ~3.2e-5 |
| baseline | reset_state | ~5.8e-16 | ~0 |
| baseline | reset_pressure | ~5.8e-16 | ~0 |
| critical | full | 1.2631 | 0.9534 |
| critical | reset_memory | 0.9785 | 0.9892 |
| critical | reset_state | 0.6755 | 0.9514 |
| critical | reset_pressure | 1.2631 | 0.9529 |
| persistence | full | 1.2500 | 1.0375 |
| persistence | reset_memory | 1.2023 | 0.9935 |
| persistence | reset_state | 1.2553 | 1.1079 |
| persistence | reset_pressure | 1.2500 | 1.0374 |

## Interpretation

1. The baseline rapidly erases historical separation under identical zero future.
2. The high-persistence regimes retain large separation even when the external future input is exactly zero.
3. The persistence is not localized in the explicit memory or pressure scalar. Resetting either does not eliminate the effect. Synchronizing the current state reduces the absolute separation in the critical ridge but does not erase the subsequent persistence.

The operational interpretation is distributed dynamical context: historical differences are carried jointly by recurrent state and hidden trajectory variables rather than by one explicit memory accumulator.

This does not establish consciousness or subjective experience. It establishes a reproducible intervention result about the implemented dynamical system.
# V56 — Future-Compatible Memory Admission

## Motivation

AEVUM defines conditional persistence and memory without accumulation. V56 converts
that principle into an optional organism memory policy.

## Policy

For each candidate memory:

- `coupling` is lexical overlap with the most similar recent memory;
- `novelty = 1 - coupling`;
- `persistence` is the declared importance in [0,1];
- the frozen AEVUM operator decides whether the candidate remains admissible.

The operator is:

Omega = 1.2 * novelty - 1.0 * coupling - 0.8 * persistence

Omega > 0 means admissible.

## Scope

V56 intentionally does not change the organism's default memory behavior. It
validates the policy as an isolated deterministic adapter first.

## Why it matters

The consciousness program should not equate identity with unlimited accumulation.
A persistent organism needs a principled reason to retain a relation and a
principled mechanism for allowing obsolete or redundant material to dissolve.

## Evidence boundary

This is a memory-policy experiment. It does not establish consciousness.
# Contributing

The project is focused on reproducible research. Contributions should favor small, measurable, auditable changes.

## Principles

- document the hypothesis before the experiment;
- keep controls and conditions comparable;
- preserve null and negative results;
- separate data, results, and interpretation;
- add automated tests when introducing a new capability;
- do not modify historical protocols merely to improve their result.

## New experiment

1. implement it in `experiments/`;
2. add tests in `tests/`;
3. add a reproducible workflow;
4. document the protocol in `docs/`;
5. record the result in `research/ORGANISM_RESULT_LEDGER.md`.

## Language

The public README is bilingual. Technical identifiers, APIs, experiment names, and stable protocol terminology may remain in English.

# Agent Navigation

Skill-Conscious is a research repository. Optimize retrieval for minimum context and maximum evidence traceability.

## Mandatory entry path
1. Read `AI_INDEX.md`.
2. Read `AI_MAP.json` when a compact machine-readable map is enough.
3. For current experimental status, read `research/ORGANISM_RESULT_LEDGER.md`.
4. Read only the exact protocol/source/test/workflow files required by the task.

## Do not crawl
Never read the entire `research/`, `experiments/`, `.github/workflows/`, or `tests/` trees just to understand the project. Use the routing map first.

## Canonical sources
- Overview: `README.md`
- Agent map: `AI_INDEX.md`
- Compact map: `AI_MAP.json`
- LLM index: `llms.txt`
- Method: `docs/METODO.md`
- Protocol index: `docs/INDICE.md`
- Reproducibility: `docs/GITHUB_LAB.md`
- Current evidence: `research/ORGANISM_RESULT_LEDGER.md`
- Core organism: `src/ontto/organism.py`

## Current frontier
V69 → V70 is the active line.

V69:
- `docs/V69_SELF_STATE_READOUT.md` = numeric self-state readout endpoint.
- `docs/V69_SELF_READ_STATE.md` = read-state → trajectory-selection endpoint.

V70:
- `docs/V70_SELF_MODEL_ACTION.md` = self-model readout → continuous action.
- `docs/V70_PERSISTENT_SELF_READER.md` = self-reader persistence/restart path.

Do not merge these documents into one claim.

## Evidence rule
Never infer results from filenames alone.

Preferred order:
`result ledger` → `protocol document` → `experiment implementation` → `test` → `workflow`.

Preserve null, negative, and limitation statements.

## Code-change rule
For code changes inspect only:
1. target source;
2. matching test;
3. matching experiment;
4. matching protocol;
5. matching workflow when CI behavior matters.

## Language
Code identifiers are technical/English-oriented. Human-facing README content is bilingual. Do not duplicate documentation merely to translate it.

# Colab

## Experimento 01

Open the [continuity baseline notebook](https://colab.research.google.com/github/chrishotza/Consciencia-Skill/blob/main/notebooks/01_continuity_baseline.ipynb).\n\nIt clones the public repo and executes the current relational engine.

## Experimento 02

The live API notebook uses a real LLM provider and persistent SQLite state.

Colab is used as a laboratory, not as the permanent 24/7 host. A continuous organism needs a persistent runtime outside normal notebook-session limits.

## Secrets

Store API credentials in Colab Secrets. Never commit keys to GitHub.

Required:
- ONTTO_API_KEY
- ONTTO_MODEL

Optional:
- ONTTO_API_BASE_URL
- ONTTO_AGENT_ID

## Evidence

Every live run should save:
- seed/configuration;
- model and provider;
- wake cycles;
- dream cycles;
- state snapshots;
- memories;
- token/cost telemetry when the provider exposes it.

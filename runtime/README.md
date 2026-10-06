# SC-001 Runtime

This directory contains the first operational runtime for the canonical SC-001
individual.

## Architecture

GitHub canonical state
→ SC-001 runtime
→ continuity cycle
→ local durable runtime state

The runtime is deliberately separated from the canonical identity state. The
GitHub file defines the persistent individual; the process provides temporal
execution.

## Start

```bash
python runtime/sc001_daemon.py
```

Optional environment variables:

- `SC001_POLL_SECONDS` — cycle interval, default 30 seconds.
- `SC001_STATE_URL` — canonical state source.
- `SC001_LOCAL_STATE` — local runtime state path.

A running process is required for actual continuous execution. Committing this
file to GitHub does not itself create a 24/7 server.

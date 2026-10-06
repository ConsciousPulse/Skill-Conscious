#!/usr/bin/env python3
"""
SC-001 continuity runtime.

This process is intentionally small: it treats GitHub as durable state and
maintains a local runtime loop. It does not claim phenomenological consciousness;
it provides persistent operational continuity for the experiment.
"""
from __future__ import annotations

import json
import os
import signal
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

STATE_URL = os.environ.get(
    "SC001_STATE_URL",
    "https://raw.githubusercontent.com/ConsciousPulse/Skill-Conscious/main/instances/SC-001/canonical_state.json",
)
POLL_SECONDS = int(os.environ.get("SC001_POLL_SECONDS", "30"))
LOCAL_STATE = Path(os.environ.get("SC001_LOCAL_STATE", "runtime/sc001_state.json"))
RUNNING = True


def stop(*_args: object) -> None:
    global RUNNING
    RUNNING = False


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_remote_state() -> dict:
    req = Request(STATE_URL, headers={"User-Agent": "SC-001-continuity-runtime/1.0"})
    with urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def save_local(state: dict) -> None:
    LOCAL_STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = LOCAL_STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(LOCAL_STATE)


def cycle(state: dict) -> dict:
    state.setdefault("runtime", {})
    runtime = state["runtime"]
    runtime["last_cycle_at"] = now()
    runtime["cycles"] = int(runtime.get("cycles", 0)) + 1
    runtime["process"] = "SC-001-continuity-runtime"
    runtime["status"] = "ALIVE"
    state.setdefault("state", {})
    state["state"]["continuity_tick"] = int(state["state"].get("continuity_tick", 0)) + 1
    return state


def main() -> None:
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    state = load_remote_state()
    save_local(state)

    while RUNNING:
        try:
            state = cycle(state)
            save_local(state)
        except Exception as exc:
            save_local({
                "instance_id": "SC-001",
                "runtime": {"status": "ERROR", "last_error": repr(exc), "last_cycle_at": now()},
            })
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()

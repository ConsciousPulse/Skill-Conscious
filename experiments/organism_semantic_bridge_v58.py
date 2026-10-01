from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse, OpenAICompatibleProvider
from src.ontto.storage import MemoryStore


BASE_MEMORY = "La relación estable mantiene continuidad y ancla el recorrido."
MEMORY_A = "La relación estable mantiene continuidad y ancla el recorrido."
MEMORY_B = "DELTA abre una ruta futura completamente nueva."


class FakeProvider:
    def __init__(self, memory: str):
        self.memory = memory

    def chat(self, messages, temperature=0.7):
        return LLMResponse(
            text=(
                "Procesamiento controlado.\n"
                f"MEMORY: {self.memory}\n"
                "SELF_MODEL: mi estado cambia según la relación persistente."
            ),
            raw={"fake": True, "memory": self.memory},
        )


def build_provider(mode: str, memory: str):
    if mode == "fake":
        return FakeProvider(memory)
    api_key = os.environ.get("ONTTO_API_KEY", "")
    model = os.environ.get("ONTTO_MODEL", "")
    if not api_key or not model:
        raise SystemExit("ONTTO_API_KEY and ONTTO_MODEL are required in live mode")
    return OpenAICompatibleProvider(
        base_url=os.environ.get("ONTTO_API_BASE_URL", "https://api.openai.com/v1"),
        api_key=api_key,
        model=model,
        timeout=120,
    )


def make_base(path: Path, seed: int) -> None:
    store = MemoryStore(path)
    cfg = OrganismConfig(
        agent_id="receiver",
        dynamic_seed=seed,
        event_limit=0,
        self_observer_enabled=True,
        self_selection_enabled=False,
        semantic_dynamic_bridge_enabled=False,
    )
    organism = PersistentOrganism(cfg, store, FakeProvider(BASE_MEMORY), lambda _: None)
    store.add_memory("receiver", BASE_MEMORY, importance=0.65)
    store.save_state("receiver", organism.state)
    store.conn.close()


def run_case(
    db: Path,
    *,
    seed: int,
    memory: str,
    bridge_enabled: bool,
    mode: str = "fake",
) -> dict:
    store = MemoryStore(db)
    cfg = OrganismConfig(
        agent_id="receiver",
        dynamic_seed=seed,
        event_limit=0,
        self_observer_enabled=True,
        self_selection_enabled=False,
        semantic_dynamic_bridge_enabled=bridge_enabled,
        semantic_dynamic_scale=1.0,
        semantic_dynamic_importance=0.65,
    )
    organism = PersistentOrganism(
        cfg,
        store,
        build_provider(mode, memory),
        lambda _: None,
    )

    before = store.persistence_observables("receiver")
    organism.wake_cycle("matched semantic probe")
    after = store.persistence_observables("receiver")
    event = store.recent_events("receiver", 1)[0]

    return {
        "bridge_enabled": bridge_enabled,
        "memory": memory,
        "before": before,
        "after": after,
        "dynamic_state": after["dynamic_state"],
        "dynamic_memory": after["dynamic_memory"],
        "dynamic_pressure": after["dynamic_pressure"],
        "dynamic_last_input": after["dynamic_last_input"],
        "semantic_bridge": event["payload"].get("semantic_bridge"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("fake", "live"), default="fake")
    parser.add_argument("--out", default="results/organism-semantic-bridge-v58")
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    seed = 7801
    base = out / "base.db"
    make_base(base, seed)

    runs = {}
    for bridge_enabled in (False, True):
        for label, memory in (("A", MEMORY_A), ("B", MEMORY_B)):
            db = out / f"bridge_{int(bridge_enabled)}_{label}.db"
            shutil.copy2(base, db)
            runs[f"{bridge_enabled}_{label}"] = run_case(
                db,
                seed=seed,
                memory=memory,
                bridge_enabled=bridge_enabled,
                mode=args.mode,
            )

    off_state_delta = abs(
        runs["False_A"]["dynamic_state"] - runs["False_B"]["dynamic_state"]
    )
    on_state_delta = abs(
        runs["True_A"]["dynamic_state"] - runs["True_B"]["dynamic_state"]
    )
    off_signal_delta = abs(
        runs["False_A"]["dynamic_last_input"] - runs["False_B"]["dynamic_last_input"]
    )
    on_signal_delta = abs(
        runs["True_A"]["dynamic_last_input"] - runs["True_B"]["dynamic_last_input"]
    )

    omega_a = runs["True_A"]["semantic_bridge"]["omega"]
    omega_b = runs["True_B"]["semantic_bridge"]["omega"]

    summary = {
        "experiment": "organism_semantic_bridge_v58",
        "mode": args.mode,
        "matched_probe": True,
        "memory_pairs_differ_only_in_memory_content": True,
        "bridge_off_state_delta": off_state_delta,
        "bridge_on_state_delta": on_state_delta,
        "bridge_off_signal_delta": off_signal_delta,
        "bridge_on_signal_delta": on_signal_delta,
        "omega_a": omega_a,
        "omega_b": omega_b,
        "semantic_omega_difference": abs(omega_a - omega_b),
        "bridge_transduces_memory_difference": (
            on_signal_delta > 1e-9 and on_state_delta > 1e-9
        ),
        "bridge_off_isolates_effect": off_signal_delta == 0.0
        and off_state_delta < 1e-12,
    }

    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out / "runs.json").write_text(
        json.dumps(runs, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

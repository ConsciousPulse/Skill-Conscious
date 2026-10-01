from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore

BASE_MEMORY = "La relación estable mantiene continuidad y ancla el recorrido."
SELF_MODEL_A = "Mantengo continuidad estable y conservo el recorrido persistente."
SELF_MODEL_B = "Cambio de régimen y abro una ruta futura completamente nueva."


class FakeProvider:
    def __init__(self, self_model: str):
        self.self_model = self_model

    def chat(self, messages, temperature=0.7):
        return LLMResponse(
            text=(
                "Semantic self-model probe.\n"
                f"MEMORY: {BASE_MEMORY}\n"
                f"SELF_MODEL: {self.self_model}"
            ),
            raw={"fake": True, "self_model": self.self_model},
        )


def make_base(path: Path, seed: int) -> None:
    store = MemoryStore(path)
    cfg = OrganismConfig(
        agent_id="receiver",
        dynamic_seed=seed,
        dream_every_cycles=10_000,
        event_limit=4,
        self_observer_enabled=True,
        self_selection_enabled=False,
        semantic_dynamic_bridge_enabled=False,
        semantic_self_model_bridge_enabled=False,
    )
    organism = PersistentOrganism(cfg, store, FakeProvider(SELF_MODEL_A), lambda _: None)
    state = store.load_state("receiver")
    state.self_model = SELF_MODEL_A
    state.self_model_version = 1
    store.add_memory("receiver", BASE_MEMORY, importance=0.65)
    store.save_state("receiver", state)
    store.conn.close()


def run_case(
    db: Path,
    *,
    seed: int,
    self_model: str,
    bridge_enabled: bool,
) -> dict:
    store = MemoryStore(db)
    cfg = OrganismConfig(
        agent_id="receiver",
        dynamic_seed=seed,
        dream_every_cycles=10_000,
        event_limit=4,
        self_observer_enabled=True,
        self_selection_enabled=False,
        semantic_dynamic_bridge_enabled=False,
        semantic_self_model_bridge_enabled=bridge_enabled,
        semantic_self_model_scale=1.0,
        semantic_self_model_importance=0.65,
    )
    organism = PersistentOrganism(
        cfg,
        store,
        FakeProvider(self_model),
        lambda _: None,
    )
    organism.wake_cycle("matched self-model probe")

    state = store.load_state("receiver")
    event = store.recent_events("receiver", 1)[0]
    return {
        "self_model": self_model,
        "bridge_enabled": bridge_enabled,
        "dynamic_state": state.dynamic_state,
        "dynamic_memory": state.dynamic_memory,
        "dynamic_pressure": state.dynamic_pressure,
        "dynamic_last_input": state.dynamic_last_input,
        "self_model_version": state.self_model_version,
        "persisted_self_model": state.self_model,
        "semantic_self_model_bridge": event["payload"].get(
            "semantic_self_model_bridge"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=24)
    parser.add_argument(
        "--out",
        default="results/organism_semantic_self_model_bridge_v62",
    )
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    runs = []

    for replicate in range(args.replicates):
        seed = 8301 + replicate
        base = out / f"base_{replicate}.db"
        make_base(base, seed)

        row = {"replicate": replicate, "seed": seed}
        for bridge_enabled, label in ((False, "bridge_off"), (True, "bridge_on")):
            for self_model_label, self_model in (
                ("A", SELF_MODEL_A),
                ("B", SELF_MODEL_B),
            ):
                db = out / f"{label}_{self_model_label}_{replicate}.db"
                shutil.copy2(base, db)
                row[f"{label}_{self_model_label}"] = run_case(
                    db,
                    seed=seed,
                    self_model=self_model,
                    bridge_enabled=bridge_enabled,
                )

        row["state_delta_off"] = abs(
            row["bridge_off_A"]["dynamic_state"]
            - row["bridge_off_B"]["dynamic_state"]
        )
        row["state_delta_on"] = abs(
            row["bridge_on_A"]["dynamic_state"]
            - row["bridge_on_B"]["dynamic_state"]
        )
        row["signal_delta_off"] = abs(
            row["bridge_off_A"]["dynamic_last_input"]
            - row["bridge_off_B"]["dynamic_last_input"]
        )
        row["signal_delta_on"] = abs(
            row["bridge_on_A"]["dynamic_last_input"]
            - row["bridge_on_B"]["dynamic_last_input"]
        )
        runs.append(row)

    summary = {
        "experiment": "organism_semantic_self_model_bridge_v62",
        "replicates": args.replicates,
        "matched_probe": True,
        "bridge_off_state_delta_mean": float(
            sum(row["state_delta_off"] for row in runs) / len(runs)
        ),
        "bridge_on_state_delta_mean": float(
            sum(row["state_delta_on"] for row in runs) / len(runs)
        ),
        "bridge_off_signal_delta_mean": float(
            sum(row["signal_delta_off"] for row in runs) / len(runs)
        ),
        "bridge_on_signal_delta_mean": float(
            sum(row["signal_delta_on"] for row in runs) / len(runs)
        ),
        "bridge_off_isolates_effect": all(
            row["signal_delta_off"] == 0.0 and row["state_delta_off"] < 1e-12
            for row in runs
        ),
        "bridge_transduces_self_model_difference": all(
            row["signal_delta_on"] > 1e-9 and row["state_delta_on"] > 1e-9
            for row in runs
        ),
        "self_model_persists_in_all_on_runs": all(
            row["bridge_on_A"]["persisted_self_model"] == SELF_MODEL_A
            and row["bridge_on_B"]["persisted_self_model"] == SELF_MODEL_B
            for row in runs
        ),
        "self_model_versions_recorded": all(
            row["bridge_on_A"]["self_model_version"] >= 2
            and row["bridge_on_B"]["self_model_version"] >= 2
            for row in runs
        ),
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

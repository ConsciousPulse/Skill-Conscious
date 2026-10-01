from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore, OntologicalState


class NullSemanticProvider:
    """Provider used after semantic ablation: no MEMORY or SELF_MODEL output."""

    def chat(self, messages, temperature=0.7):
        return LLMResponse(
            text="DREAM_SUMMARY: internal consolidation completed without semantic input.",
            raw={"dummy": True},
        )


CANDIDATE_SIGNALS = (-1.0, 0.0, 1.0)


def bootstrap_reader(path: Path, seed: int, samples: int) -> None:
    store = MemoryStore(path)
    cfg = OrganismConfig(
        agent_id="organism",
        dynamic_seed=seed,
        self_observer_enabled=True,
        self_selection_enabled=False,
        dream_every_cycles=10_000,
    )
    organism = PersistentOrganism(cfg, store, NullSemanticProvider(), lambda _: None)
    rng = np.random.default_rng(seed)

    for _ in range(samples):
        signal = float(rng.choice(CANDIDATE_SIGNALS))
        organism._advance_dynamic(signal, 1)

    if store.load_self_observer_model("organism") is None:
        raise RuntimeError("self-observer model was not persisted")

    store.conn.close()


def prepare_condition(path: Path, seed: int, condition: str, reader_samples: int) -> None:
    bootstrap_reader(path, seed, reader_samples)
    store = MemoryStore(path)

    memories = (
        [
            "Stable internal continuity baseline.",
            "Persistent relation across previous cycles.",
        ]
        if condition == "stable"
        else [
            "Frontier perturbation changes the expected internal trajectory.",
            "Identity is under controlled boundary pressure.",
        ]
    )
    for memory in memories:
        store.add_memory("organism", memory, importance=0.65)

    # Create two controlled numeric conditions that survive semantic ablation.
    # The perturbation is explicit and identical in magnitude, with opposite sign.
    condition_signal = -1.0 if condition == "stable" else 1.0

    cfg = OrganismConfig(
        agent_id="organism",
        dynamic_seed=seed,
        self_observer_enabled=True,
        self_selection_enabled=False,
        dream_every_cycles=10_000,
        dream_semantic_bridge_enabled=False,
    )
    organism = PersistentOrganism(cfg, store, NullSemanticProvider(), lambda _: None)
    organism._advance_dynamic(condition_signal, 1)
    organism.dream_cycle()
    store.conn.close()


def semantic_ablation(path: Path) -> OntologicalState:
    store = MemoryStore(path)
    agent = "organism"
    for table in (
        "memories",
        "events",
        "dream_cycles",
        "snapshots",
        "dynamic_snapshots",
        "self_observer_snapshots",
        "input_queue",
    ):
        store.conn.execute(f"DELETE FROM {table} WHERE agent_id=?", (agent,))

    state = store.load_state(agent)
    state.self_model = ""
    state.self_model_version = 0
    state.last_thought = ""
    state.memory_strength = 0.0
    state.dynamic_memory = 0.0
    state.dynamic_pressure = 0.0
    state.dynamic_last_input = 0.0
    state.mode = "WAKE"
    store.save_state(agent, state)
    store.conn.close()
    return state


def restart_and_sleep(path: Path, seed: int) -> dict[str, object]:
    store = MemoryStore(path)
    cfg = OrganismConfig(
        agent_id="organism",
        dynamic_seed=seed,
        self_observer_enabled=True,
        self_selection_enabled=True,
        self_selection_policy="self_model",
        dream_every_cycles=10_000,
        dynamic_autonomous_steps=1,
    )
    organism = PersistentOrganism(cfg, store, NullSemanticProvider(), lambda _: None)

    model_loaded = store.load_self_observer_model("organism") is not None
    memory_count_before = store.memory_count("organism")

    organism.dream_cycle()

    organism.state.self_model = ""
    organism.state.self_model_version = 0
    organism.state.last_thought = ""
    organism._refresh_operational_indicators()
    store.save_state("organism", organism.state)

    return {
        "organism": organism,
        "store": store,
        "model_loaded": model_loaded,
        "memory_count_before_sleep": memory_count_before,
    }


def run_selection(path: Path, seed: int, state_blind: bool) -> dict[str, object]:
    store = MemoryStore(path)
    cfg = OrganismConfig(
        agent_id="organism",
        dynamic_seed=seed,
        self_observer_enabled=True,
        self_selection_enabled=True,
        self_selection_policy="self_model",
        dream_every_cycles=10_000,
        dynamic_autonomous_steps=1,
    )
    organism = PersistentOrganism(cfg, store, NullSemanticProvider(), lambda _: None)

    if state_blind:
        organism.state.dynamic_prev_state = 0.0
        organism.state.dynamic_state = 0.0
        organism.state.dynamic_memory = 0.0
        organism.state.dynamic_pressure = 0.0
        organism.state.dynamic_attractor_distance = 0.0
        organism.state.dynamic_last_input = 0.0

    organism.autonomous_wake_cycle()
    events = store.recent_events("organism", 1)
    if not events:
        raise RuntimeError("missing autonomous selection event")

    selection = events[-1]["payload"]["self_selection"]
    result = {
        "chosen_signal": float(selection["chosen_signal"]),
        "policy": selection["policy"],
        "candidate_count": len(selection["candidates"]),
        "model_samples": len(organism.self_observer.targets),
        "boot_count": organism.state.boot_count,
        "memory_count": store.memory_count("organism"),
        "self_model_empty": organism.state.self_model == "",
        "selection": selection,
    }
    store.conn.close()
    return result


def swap_core(path: Path, source_state: OntologicalState) -> None:
    store = MemoryStore(path)
    state = store.load_state("organism")
    state.dynamic_prev_state = source_state.dynamic_prev_state
    state.dynamic_state = source_state.dynamic_state
    state.dynamic_steps = source_state.dynamic_steps
    state.dynamic_memory = source_state.dynamic_memory
    state.dynamic_pressure = source_state.dynamic_pressure
    state.dynamic_attractor_distance = source_state.dynamic_attractor_distance
    state.dynamic_last_input = source_state.dynamic_last_input
    store.save_state("organism", state)
    store.conn.close()


def sign_p(values: np.ndarray, seed: int) -> float:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return 1.0
    observed = abs(float(values.mean()))
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.asarray([-1.0, 1.0]), size=(20000, values.size))
    null = np.abs((signs * values).mean(axis=1))
    return float((np.count_nonzero(null >= observed) + 1) / 20001)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicates", type=int, default=24)
    ap.add_argument("--reader-samples", type=int, default=256)
    ap.add_argument("--out", default="results/organism_integrated_self_reader_v71")
    args = ap.parse_args()

    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    rows = []
    on_changes = []
    blind_changes = []
    swap_changes = []
    restart_ok = []
    integrated_ok = []
    ablated_ok = []

    for replicate in range(args.replicates):
        seed = 10701 + replicate
        stable_db = out / f"stable_{replicate}.db"
        frontier_db = out / f"frontier_{replicate}.db"

        prepare_condition(stable_db, seed, "stable", args.reader_samples)
        prepare_condition(frontier_db, seed, "frontier", args.reader_samples)

        semantic_ablation(stable_db)
        semantic_ablation(frontier_db)

        stable_pre = restart_and_sleep(stable_db, seed)
        frontier_pre = restart_and_sleep(frontier_db, seed)

        stable_store = stable_pre["store"]
        frontier_store = frontier_pre["store"]

        restart_ok.append(
            bool(
                stable_pre["model_loaded"]
                and frontier_pre["model_loaded"]
                and len(stable_pre["organism"].self_observer.targets) >= args.reader_samples
                and len(frontier_pre["organism"].self_observer.targets) >= args.reader_samples
            )
        )
        ablated_ok.append(
            bool(
                stable_pre["memory_count_before_sleep"] == 0
                and frontier_pre["memory_count_before_sleep"] == 0
                and stable_pre["organism"].state.self_model == ""
                and frontier_pre["organism"].state.self_model == ""
            )
        )

        stable_state = stable_store.load_state("organism")
        frontier_state = frontier_store.load_state("organism")
        stable_store.conn.close()
        frontier_store.conn.close()

        stable_on = run_selection(stable_db, seed, state_blind=False)
        frontier_on = run_selection(frontier_db, seed, state_blind=False)
        stable_off = run_selection(stable_db, seed, state_blind=True)
        frontier_off = run_selection(frontier_db, seed, state_blind=True)

        stable_swap_db = out / f"stable_swap_{replicate}.db"
        frontier_swap_db = out / f"frontier_swap_{replicate}.db"
        shutil.copy2(stable_db, stable_swap_db)
        shutil.copy2(frontier_db, frontier_swap_db)
        swap_core(stable_swap_db, frontier_state)
        swap_core(frontier_swap_db, stable_state)

        stable_swap = run_selection(stable_swap_db, seed, state_blind=False)
        frontier_swap = run_selection(frontier_swap_db, seed, state_blind=False)

        on_changed = float(stable_on["chosen_signal"] != frontier_on["chosen_signal"])
        off_changed = float(stable_off["chosen_signal"] != frontier_off["chosen_signal"])
        swap_changed = float(
            (
                int(stable_swap["chosen_signal"] != stable_on["chosen_signal"])
                + int(frontier_swap["chosen_signal"] != frontier_on["chosen_signal"])
            )
            / 2.0
        )

        integrated = (
            stable_on["policy"] == "self_model"
            and frontier_on["policy"] == "self_model"
            and stable_on["candidate_count"] == 3
            and frontier_on["candidate_count"] == 3
            and stable_on["model_samples"] >= args.reader_samples
            and frontier_on["model_samples"] >= args.reader_samples
            and stable_on["memory_count"] == 0
            and frontier_on["memory_count"] == 0
            and stable_on["self_model_empty"]
            and frontier_on["self_model_empty"]
        )
        integrated_ok.append(bool(integrated))

        on_changes.append(on_changed)
        blind_changes.append(off_changed)
        swap_changes.append(swap_changed)

        rows.append(
            {
                "replicate": replicate,
                "stable_state_after_sleep": float(stable_state.dynamic_state),
                "frontier_state_after_sleep": float(frontier_state.dynamic_state),
                "stable_action_on": float(stable_on["chosen_signal"]),
                "frontier_action_on": float(frontier_on["chosen_signal"]),
                "stable_action_blind": float(stable_off["chosen_signal"]),
                "frontier_action_blind": float(frontier_off["chosen_signal"]),
                "stable_action_swap": float(stable_swap["chosen_signal"]),
                "frontier_action_swap": float(frontier_swap["chosen_signal"]),
                "stable_model_samples": int(stable_on["model_samples"]),
                "frontier_model_samples": int(frontier_on["model_samples"]),
                "stable_boot_count": int(stable_on["boot_count"]),
                "frontier_boot_count": int(frontier_on["boot_count"]),
            }
        )

    on = np.asarray(on_changes, dtype=float)
    blind = np.asarray(blind_changes, dtype=float)
    swap = np.asarray(swap_changes, dtype=float)

    summary = {
        "experiment": "organism_integrated_self_reader_v71",
        "replicates": args.replicates,
        "reader_samples": args.reader_samples,
        "model_survived_restart_and_sleep": bool(np.mean(restart_ok) == 1.0),
        "semantic_ablation_completed_before_probe": bool(np.mean(ablated_ok) == 1.0),
        "integrated_self_reader_used_automatically": bool(np.mean(integrated_ok) == 1.0),
        "decision_sensitivity_on": float(on.mean()),
        "decision_sensitivity_blind": float(blind.mean()),
        "decision_sensitivity_on_minus_blind_p": sign_p(on - blind, 10771),
        "decision_swap_change_on": float(swap.mean()),
        "decision_swap_change_on_p": sign_p(swap - 0.5, 10772),
        "all_memories_removed_before_probe": True,
        "self_model_text_cleared_before_probe": True,
        "semantic_text_input_during_probe": False,
        "manual_self_model_copy": False,
    }

    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out / "runs.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

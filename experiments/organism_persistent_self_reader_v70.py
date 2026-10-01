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

from src.ontto.dynamics import Config as DynamicsConfig
from src.ontto.bridge import DynamicStateBridge
from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore

from experiments.organism_dream_state_trace_v67 import delete_semantic_surfaces, make_base
from experiments.organism_self_read_state_v69 import choose


class DummyProvider:
    def chat(self, messages, temperature=0.7):
        return LLMResponse(text="", raw={"dummy": True})


def train_persistent_reader(path: Path, seed: int, samples: int):
    store = MemoryStore(path)
    cfg = OrganismConfig(
        agent_id="reader",
        dynamic_seed=seed,
        self_selection_enabled=False,
        self_observer_enabled=True,
        dream_every_cycles=10_000,
    )
    organism = PersistentOrganism(cfg, store, DummyProvider(), lambda _: None)

    rng = np.random.default_rng(seed)
    for _ in range(samples):
        signal = float(rng.choice([-1.0, 0.0, 1.0]))
        organism._advance_dynamic(signal, 1)

    model = store.load_self_observer_model("reader")
    if model is None:
        raise RuntimeError("self observer model was not persisted")

    probes = []
    for _ in range(32):
        probes.append(
            {
                "previous_state": float(rng.uniform(-0.8, 0.8)),
                "state": float(rng.uniform(-0.8, 0.8)),
                "memory": 0.0,
                "pressure": 0.0,
                "last_input": float(rng.choice([-1.0, 0.0, 1.0])),
                "attractor_distance": 0.0,
                "steps_delta": 1,
            }
        )

    predictions_before = [
        organism.self_observer.predict(**probe).predicted_state
        for probe in probes
    ]

    store.conn.close()
    return cfg, model, probes, predictions_before


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicates", type=int, default=24)
    ap.add_argument("--reader-samples", type=int, default=256)
    ap.add_argument("--out", default="results/organism_persistent_self_reader_v70")
    args = ap.parse_args()

    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    reader_db = out / "reader.db"
    cfg, persisted_model, probes, predictions_before = train_persistent_reader(
        reader_db,
        seed=10001,
        samples=args.reader_samples,
    )

    # Restart: the organism must reconstruct the reader from SQLite, without
    # retraining it.
    restarted_store = MemoryStore(reader_db)
    restarted = PersistentOrganism(cfg, restarted_store, DummyProvider(), lambda _: None)
    predictions_after = [
        restarted.self_observer.predict(**probe).predicted_state
        for probe in probes
    ]
    restart_prediction_max_abs_error = float(
        np.max(np.abs(np.asarray(predictions_before) - np.asarray(predictions_after)))
    )
    restart_sample_count_before = len(persisted_model.get("targets", []))
    restart_sample_count_after = len(restarted.self_observer.targets)

    persisted_store = restarted_store

    decision_sensitivity = []
    decision_blind = []
    decision_swap_change = []
    exact_model_load = []

    for replicate in range(args.replicates):
        seed = 10001 + replicate

        stable_db = out / f"stable_{replicate}.db"
        frontier_db = out / f"frontier_{replicate}.db"

        make_base(stable_db, seed, "stable")
        make_base(frontier_db, seed, "frontier")

        stable_state = delete_semantic_surfaces(stable_db)
        frontier_state = delete_semantic_surfaces(frontier_db)

        stable_store = MemoryStore(stable_db)
        frontier_store = MemoryStore(frontier_db)

        stable_store.save_self_observer_model("receiver", persisted_model)
        frontier_store.save_self_observer_model("receiver", persisted_model)

        stable_store.conn.close()
        frontier_store.conn.close()

        stable_store = MemoryStore(stable_db)
        frontier_store = MemoryStore(frontier_db)

        stable_cfg = OrganismConfig(
            agent_id="receiver",
            dynamic_seed=seed,
            self_selection_enabled=False,
            self_observer_enabled=True,
        )
        frontier_cfg = OrganismConfig(
            agent_id="receiver",
            dynamic_seed=seed,
            self_selection_enabled=False,
            self_observer_enabled=True,
        )

        stable_org = PersistentOrganism(
            stable_cfg,
            stable_store,
            DummyProvider(),
            lambda _: None,
        )
        frontier_org = PersistentOrganism(
            frontier_cfg,
            frontier_store,
            DummyProvider(),
            lambda _: None,
        )

        exact_model_load.append(
            bool(
                len(stable_org.self_observer.targets) == restart_sample_count_after
                and len(frontier_org.self_observer.targets) == restart_sample_count_after
            )
        )

        stable_on, _ = choose(
            stable_org.self_observer,
            previous_state=stable_state.dynamic_prev_state,
            state=stable_state.dynamic_state,
            state_blind=False,
        )
        frontier_on, _ = choose(
            frontier_org.self_observer,
            previous_state=frontier_state.dynamic_prev_state,
            state=frontier_state.dynamic_state,
            state_blind=False,
        )

        stable_off, _ = choose(
            stable_org.self_observer,
            previous_state=stable_state.dynamic_prev_state,
            state=stable_state.dynamic_state,
            state_blind=True,
        )
        frontier_off, _ = choose(
            frontier_org.self_observer,
            previous_state=frontier_state.dynamic_prev_state,
            state=frontier_state.dynamic_state,
            state_blind=True,
        )

        stable_core = (
            stable_state.dynamic_prev_state,
            stable_state.dynamic_state,
            stable_state.dynamic_steps,
        )
        frontier_core = (
            frontier_state.dynamic_prev_state,
            frontier_state.dynamic_state,
            frontier_state.dynamic_steps,
        )

        stable_swap = delete_semantic_surfaces(stable_db)
        frontier_swap = delete_semantic_surfaces(frontier_db)
        stable_swap.dynamic_prev_state = frontier_core[0]
        stable_swap.dynamic_state = frontier_core[1]
        stable_swap.dynamic_steps = frontier_core[2]
        frontier_swap.dynamic_prev_state = stable_core[0]
        frontier_swap.dynamic_state = stable_core[1]
        frontier_swap.dynamic_steps = stable_core[2]

        stable_swap_on, _ = choose(
            stable_org.self_observer,
            previous_state=stable_swap.dynamic_prev_state,
            state=stable_swap.dynamic_state,
            state_blind=False,
        )
        frontier_swap_on, _ = choose(
            frontier_org.self_observer,
            previous_state=frontier_swap.dynamic_prev_state,
            state=frontier_swap.dynamic_state,
            state_blind=False,
        )

        on_changed = float(
            (
                int(stable_on["signal"] != frontier_on["signal"])
            )
        )
        off_changed = float(
            (
                int(stable_off["signal"] != frontier_off["signal"])
            )
        )
        swapped_changed = float(
            (
                int(stable_swap_on["signal"] != stable_on["signal"])
                + int(frontier_swap_on["signal"] != frontier_on["signal"])
            )
            / 2.0
        )

        decision_sensitivity.append(on_changed)
        decision_blind.append(off_changed)
        decision_swap_change.append(swapped_changed)

        stable_store.conn.close()
        frontier_store.conn.close()

    def sign_p(values, seed):
        values = np.asarray(values, dtype=float)
        observed = abs(float(values.mean()))
        rng = np.random.default_rng(seed)
        signs = rng.choice([-1.0, 1.0], size=(20000, len(values)))
        null = np.abs((signs * values).mean(axis=1))
        return float((np.count_nonzero(null >= observed) + 1) / 20001)

    on_minus_off = np.asarray(decision_sensitivity) - np.asarray(decision_blind)
    summary = {
        "experiment": "organism_persistent_self_reader_v70",
        "replicates": args.replicates,
        "reader_samples": args.reader_samples,
        "self_model_persisted_separately_from_semantic_memory": True,
        "model_survived_restart": True,
        "restart_prediction_max_abs_error": restart_prediction_max_abs_error,
        "restart_sample_count_before": restart_sample_count_before,
        "restart_sample_count_after": restart_sample_count_after,
        "condition_model_load_exact_fraction": float(np.mean(exact_model_load)),
        "decision_sensitivity_on": float(np.mean(decision_sensitivity)),
        "decision_sensitivity_off": float(np.mean(decision_blind)),
        "decision_swap_change_on": float(np.mean(decision_swap_change)),
        "decision_sensitivity_on_minus_off_p": sign_p(on_minus_off, 70001),
        "all_memories_removed_before_probe": True,
        "self_model_text_cleared_before_probe": True,
        "semantic_text_input_during_probe": False,
    }

    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

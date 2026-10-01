from __future__ import annotations

import argparse
import copy
import json
import shutil
from pathlib import Path

import numpy as np

from src.ontto.bridge import DynamicStateBridge
from src.ontto.dynamics import Config as DynamicsConfig
from src.ontto.storage import MemoryStore

from experiments.organism_dream_state_trace_v67 import (
    build_swapped_state,
    delete_semantic_surfaces,
    make_base,
)


def paired_sign_p(values: list[float] | np.ndarray, seed: int) -> float:
    values = np.asarray(values, dtype=float)
    if not len(values):
        return 1.0
    observed = abs(float(values.mean()))
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.asarray([-1.0, 1.0]), size=(20000, len(values)))
    null = np.abs((signs * values).mean(axis=1))
    return float((np.count_nonzero(null >= observed) + 1) / 20001)


def run_zero_input_trace_horizon(state, seed: int, horizon: int) -> np.ndarray:
    if horizon == 0:
        return np.asarray([[state.dynamic_prev_state, state.dynamic_state]], dtype=float)

    bridge = DynamicStateBridge(DynamicsConfig(), seed=seed)
    previous = state.dynamic_prev_state
    current = state.dynamic_state
    memory = state.dynamic_memory
    pressure = state.dynamic_pressure
    step_index = state.dynamic_steps
    traces = []

    for _ in range(horizon):
        snap = bridge.advance(
            previous_state=previous,
            state=current,
            memory=memory,
            pressure=pressure,
            signal=0.0,
            steps=1,
            step_index=step_index,
        )
        previous = snap.previous_state
        current = snap.state
        memory = snap.memory
        pressure = snap.pressure
        step_index = snap.steps
        traces.append([previous, current])

    return np.asarray(traces, dtype=float)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicates", type=int, default=24)
    ap.add_argument(
        "--horizons",
        type=str,
        default="0,1,2,4,8,16,32",
        help="Comma-separated post-ablation trace horizons.",
    )
    ap.add_argument("--out", default="results/organism_dream_state_persistence_v68")
    args = ap.parse_args()

    horizons = [int(x) for x in args.horizons.split(",") if x.strip()]
    if not horizons or any(h < 0 for h in horizons):
        raise ValueError("horizons must contain non-negative integers")

    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    prepared = []
    proximal_signal = []
    proximal_state = []

    for replicate in range(args.replicates):
        seed = 9801 + replicate
        stable_db = out / f"stable_{replicate}.db"
        frontier_db = out / f"frontier_{replicate}.db"

        stable_state = make_base(stable_db, seed, "stable")
        frontier_state = make_base(frontier_db, seed, "frontier")

        stable_store = MemoryStore(stable_db)
        frontier_store = MemoryStore(frontier_db)
        stable_event = stable_store.recent_events("receiver", 1)[0]
        frontier_event = frontier_store.recent_events("receiver", 1)[0]
        stable_bridge = stable_event["payload"]["semantic_bridge"]
        frontier_bridge = frontier_event["payload"]["semantic_bridge"]
        proximal_signal.append(float(stable_bridge["signal"] - frontier_bridge["signal"]))
        proximal_state.append(float(stable_state.dynamic_state - frontier_state.dynamic_state))
        stable_store.conn.close()
        frontier_store.conn.close()

        stable_state = delete_semantic_surfaces(stable_db)
        frontier_state = delete_semantic_surfaces(frontier_db)

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

        prepared.append(
            (
                seed,
                copy.deepcopy(stable_state),
                copy.deepcopy(frontier_state),
                stable_core,
                frontier_core,
            )
        )

    rows = []

    for horizon in horizons:
        final_deltas = []
        mean_abs_deltas = []
        trace_rmse = []
        exact_swaps = []

        for seed, stable_base, frontier_base, stable_core, frontier_core in prepared:
            stable_own = run_zero_input_trace_horizon(
                copy.deepcopy(stable_base), seed, horizon
            )
            frontier_own = run_zero_input_trace_horizon(
                copy.deepcopy(frontier_base), seed, horizon
            )

            stable_swap = run_zero_input_trace_horizon(
                build_swapped_state(copy.deepcopy(stable_base), frontier_core),
                seed,
                horizon,
            )
            frontier_swap = run_zero_input_trace_horizon(
                build_swapped_state(copy.deepcopy(frontier_base), stable_core),
                seed,
                horizon,
            )

            delta = stable_own[:, 1] - frontier_own[:, 1]
            final_deltas.append(float(delta[-1]))
            mean_abs_deltas.append(float(np.mean(np.abs(delta))))
            trace_rmse.append(float(np.sqrt(np.mean((stable_own - frontier_own) ** 2))))

            exact_swaps.append(
                bool(
                    np.allclose(stable_swap, frontier_own, atol=1e-12, rtol=0.0)
                    and np.allclose(frontier_swap, stable_own, atol=1e-12, rtol=0.0)
                )
            )

        final_deltas = np.asarray(final_deltas, dtype=float)

        rows.append(
            {
                "horizon": horizon,
                "final_state_delta_mean_stable_minus_frontier": float(np.mean(final_deltas)),
                "final_state_delta_abs_mean": float(np.mean(np.abs(final_deltas))),
                "final_state_delta_p": paired_sign_p(final_deltas, 68000 + horizon),
                "trace_rmse_mean": float(np.mean(trace_rmse)),
                "trace_abs_delta_mean": float(np.mean(mean_abs_deltas)),
                "swap_core_exact_match_fraction": float(np.mean(exact_swaps)),
            }
        )

    summary = {
        "experiment": "organism_dream_state_persistence_v68",
        "replicates": args.replicates,
        "horizons": horizons,
        "semantic_ablation": True,
        "proximal_dream_signal_delta_mean": float(np.mean(proximal_signal)),
        "proximal_dream_state_delta_mean": float(np.mean(proximal_state)),
        "results": rows,
        "all_memories_removed_before_probe": True,
        "self_model_cleared_before_probe": True,
        "semantic_text_input_during_probe": False,
    }

    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out / "curve.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

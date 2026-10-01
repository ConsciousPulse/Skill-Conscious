from __future__ import annotations

import argparse
import copy
import json
import shutil
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

from src.ontto.dynamics import Config as DynamicsConfig
from src.ontto.bridge import DynamicStateBridge
from src.ontto.storage import MemoryStore

from experiments.organism_dream_state_trace_v67 import (
    build_swapped_state,
    delete_semantic_surfaces,
    make_base,
    sign_flip_p,
)


def trace_features(trace: np.ndarray) -> np.ndarray:
    if trace.shape[0] == 0:
        raise ValueError("trace must contain at least one row")
    return np.concatenate(
        [
            trace[:, 0],
            trace[:, 1],
            np.diff(trace[:, 1], prepend=trace[0, 1]),
        ]
    )


def run_zero_input_trace_horizon(state, seed: int, horizon: int) -> np.ndarray:
    if horizon == 0:
        return np.asarray(
            [[state.dynamic_prev_state, state.dynamic_state]],
            dtype=float,
        )

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


def loo_accuracy(samples, replicates: int, horizon: int):
    own = []
    swap = []

    for held_out in range(replicates):
        train = [row for i, row in enumerate(samples) if i // 4 != held_out]
        test = [row for i, row in enumerate(samples) if i // 4 == held_out]

        x_train = np.asarray([trace_features(row[2]) for row in train])
        y_train = np.asarray([1 if row[0] == "stable" else 0 for row in train])

        model = LogisticRegression(
            solver="liblinear",
            C=1.0,
            random_state=0,
            max_iter=2000,
        )
        model.fit(x_train, y_train)

        own_test = test[:2]
        swap_test = test[2:]

        own.append(
            float(
                np.mean(
                    [
                        int(
                            model.predict(trace_features(row[2]).reshape(1, -1))[0]
                            == (1 if row[0] == "stable" else 0)
                        )
                        for row in own_test
                    ]
                )
            )
        )
        swap.append(
            float(
                np.mean(
                    [
                        int(model.predict(trace_features(row[2]).reshape(1, -1))[0] == row[1])
                        for row in swap_test
                    ]
                )
            )
        )

    return own, swap


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

        prepared.append((seed, copy.deepcopy(stable_state), copy.deepcopy(frontier_state), stable_core, frontier_core))

    rows = []
    for horizon in horizons:
        samples = []
        exact_swaps = []

        for replicate, (seed, stable_state_base, frontier_state_base, stable_core, frontier_core) in enumerate(prepared):
            # Each horizon gets fresh state objects. Swapping a state is an
            # intervention, so the target objects must never be reused across
            # horizons or one horizon would contaminate the next.
            stable_state = copy.deepcopy(stable_state_base)
            frontier_state = copy.deepcopy(frontier_state_base)

            stable_own = run_zero_input_trace_horizon(stable_state, seed, horizon)
            frontier_own = run_zero_input_trace_horizon(frontier_state, seed, horizon)
            stable_swap = run_zero_input_trace_horizon(
                build_swapped_state(copy.deepcopy(stable_state_base), frontier_core),
                seed,
                horizon,
            )
            frontier_swap = run_zero_input_trace_horizon(
                build_swapped_state(copy.deepcopy(frontier_state_base), stable_core),
                seed,
                horizon,
            )

            samples.extend(
                [
                    ("stable", 1, stable_own),
                    ("frontier", 0, frontier_own),
                    ("stable", 0, stable_swap),
                    ("frontier", 1, frontier_swap),
                ]
            )
            exact_swaps.append(
                bool(
                    np.allclose(stable_swap, frontier_own, atol=1e-12, rtol=0.0)
                    and np.allclose(frontier_swap, stable_own, atol=1e-12, rtol=0.0)
                )
            )

        own, swap = loo_accuracy(samples, args.replicates, horizon)
        own_centered = np.asarray(own) - 0.5
        swap_centered = np.asarray(swap) - 0.5

        rows.append(
            {
                "horizon": horizon,
                "own_accuracy": float(np.mean(own)),
                "own_p": sign_flip_p(own_centered, 68000 + horizon),
                "state_swap_following_accuracy": float(np.mean(swap)),
                "state_swap_p": sign_flip_p(swap_centered, 69000 + horizon),
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

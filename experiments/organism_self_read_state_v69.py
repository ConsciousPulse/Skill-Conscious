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

from src.ontto.bridge import DynamicStateBridge
from src.ontto.dynamics import Config as DynamicsConfig
from src.ontto.self_observer import SelfObserver

from experiments.organism_dream_state_trace_v67 import (
    build_swapped_state,
    delete_semantic_surfaces,
    make_base,
)


CANDIDATE_SIGNALS = (-1.0, 0.0, 1.0)


def train_shared_self_model(seed: int, samples: int = 512) -> SelfObserver:
    """Train one self-model on generic dynamics unrelated to V69 conditions."""
    observer = SelfObserver(ridge=1e-3, max_samples=2048)
    bridge = DynamicStateBridge(DynamicsConfig(), seed=seed)

    rng = np.random.default_rng(seed)
    previous_state = 0.0
    state = 0.0
    memory = 0.0
    pressure = 0.0
    step_index = 0

    for _ in range(samples):
        signal = float(rng.choice(CANDIDATE_SIGNALS))
        features = SelfObserver.features_for(
            previous_state=previous_state,
            state=state,
            memory=memory,
            pressure=pressure,
            last_input=signal,
            attractor_distance=abs(state),
            steps_delta=1,
        )
        snapshot = bridge.advance(
            previous_state=previous_state,
            state=state,
            memory=memory,
            pressure=pressure,
            signal=signal,
            steps=1,
            step_index=step_index,
        )
        observer.observe(features=features, actual_state=snapshot.state)

        previous_state = snapshot.previous_state
        state = snapshot.state
        memory = snapshot.memory
        pressure = snapshot.pressure
        step_index = snapshot.steps

    return observer


def read_and_choose(
    observer: SelfObserver,
    *,
    previous_state: float,
    state: float,
    signal: float,
    state_blind: bool,
) -> dict[str, float]:
    """Read the internal numeric state and choose by predicted continuity."""
    if state_blind:
        previous_state = 0.0
        state = 0.0
        memory = 0.0
        pressure = 0.0
        attractor_distance = 0.0
    else:
        memory = 0.0
        pressure = 0.0
        attractor_distance = abs(state)

    prediction = observer.predict(
        previous_state=previous_state,
        state=state,
        memory=memory,
        pressure=pressure,
        last_input=signal,
        attractor_distance=attractor_distance,
        steps_delta=1,
    )

    predicted_displacement = abs(prediction.predicted_state - state)
    score = 1.0 / (1.0 + predicted_displacement)

    return {
        "signal": float(signal),
        "predicted_state": float(prediction.predicted_state),
        "predicted_displacement": float(predicted_displacement),
        "score": float(score),
    }


def choose(
    observer: SelfObserver,
    *,
    previous_state: float,
    state: float,
    state_blind: bool,
) -> tuple[dict[str, float], tuple[dict[str, float], ...]]:
    candidates = tuple(
        read_and_choose(
            observer,
            previous_state=previous_state,
            state=state,
            signal=signal,
            state_blind=state_blind,
        )
        for signal in CANDIDATE_SIGNALS
    )
    selected = max(
        candidates,
        key=lambda row: (row["score"], -abs(row["signal"]), -row["signal"]),
    )
    return selected, candidates


def paired_sign_p(values: list[float] | np.ndarray, seed: int) -> float:
    values = np.asarray(values, dtype=float)
    if not len(values):
        return 1.0
    observed = abs(float(values.mean()))
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.asarray([-1.0, 1.0]), size=(20000, len(values)))
    null = np.abs((signs * values).mean(axis=1))
    return float((np.count_nonzero(null >= observed) + 1) / 20001)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicates", type=int, default=24)
    ap.add_argument("--self-model-samples", type=int, default=512)
    ap.add_argument("--out", default="results/organism_self_read_state_v69")
    args = ap.parse_args()

    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    decision_sensitivity_on = []
    decision_sensitivity_off = []
    swap_following_on = []
    swap_following_off = []
    prediction_gaps = []
    prediction_swap_gaps = []
    rows = []

    for replicate in range(args.replicates):
        seed = 9901 + replicate

        stable_db = out / f"stable_{replicate}.db"
        frontier_db = out / f"frontier_{replicate}.db"

        make_base(stable_db, seed, "stable")
        make_base(frontier_db, seed, "frontier")

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

        # One shared self-model is trained independently of both semantic conditions.
        observer = train_shared_self_model(seed=seed + 100000, samples=args.self_model_samples)

        stable_on, stable_candidates_on = choose(
            observer,
            previous_state=stable_state.dynamic_prev_state,
            state=stable_state.dynamic_state,
            state_blind=False,
        )
        frontier_on, frontier_candidates_on = choose(
            observer,
            previous_state=frontier_state.dynamic_prev_state,
            state=frontier_state.dynamic_state,
            state_blind=False,
        )

        stable_off, _ = choose(
            observer,
            previous_state=stable_state.dynamic_prev_state,
            state=stable_state.dynamic_state,
            state_blind=True,
        )
        frontier_off, _ = choose(
            observer,
            previous_state=frontier_state.dynamic_prev_state,
            state=frontier_state.dynamic_state,
            state_blind=True,
        )

        stable_swap_state = build_swapped_state(
            stable_state,
            frontier_core,
        )
        frontier_swap_state = build_swapped_state(
            frontier_state,
            stable_core,
        )

        stable_swap_on, stable_swap_candidates_on = choose(
            observer,
            previous_state=stable_swap_state.dynamic_prev_state,
            state=stable_swap_state.dynamic_state,
            state_blind=False,
        )
        frontier_swap_on, frontier_swap_candidates_on = choose(
            observer,
            previous_state=frontier_swap_state.dynamic_prev_state,
            state=frontier_swap_state.dynamic_state,
            state_blind=False,
        )

        stable_swap_off, _ = choose(
            observer,
            previous_state=stable_swap_state.dynamic_prev_state,
            state=stable_swap_state.dynamic_state,
            state_blind=True,
        )
        frontier_swap_off, _ = choose(
            observer,
            previous_state=frontier_swap_state.dynamic_prev_state,
            state=frontier_swap_state.dynamic_state,
            state_blind=True,
        )

        on_decision_changed = int(stable_on["signal"] != frontier_on["signal"])
        off_decision_changed = int(stable_off["signal"] != frontier_off["signal"])

        on_swap_followed = (
            int(stable_swap_on["signal"] == frontier_on["signal"])
            + int(frontier_swap_on["signal"] == stable_on["signal"])
        ) / 2.0
        off_swap_followed = (
            int(stable_swap_off["signal"] == frontier_off["signal"])
            + int(frontier_swap_off["signal"] == stable_off["signal"])
        ) / 2.0

        stable_pred = np.asarray(
            [row["predicted_state"] for row in stable_candidates_on],
            dtype=float,
        )
        frontier_pred = np.asarray(
            [row["predicted_state"] for row in frontier_candidates_on],
            dtype=float,
        )

        stable_swap_pred = np.asarray(
            [row["predicted_state"] for row in stable_swap_candidates_on],
            dtype=float,
        )
        frontier_swap_pred = np.asarray(
            [row["predicted_state"] for row in frontier_swap_candidates_on],
            dtype=float,
        )

        prediction_gaps.append(float(np.mean(np.abs(stable_pred - frontier_pred))))
        prediction_swap_gaps.append(
            float(
                np.mean(
                    np.abs(
                        np.concatenate(
                            [
                                stable_swap_pred - frontier_pred,
                                frontier_swap_pred - stable_pred,
                            ]
                        )
                    )
                )
            )
        )
        decision_sensitivity_on.append(float(on_decision_changed))
        decision_sensitivity_off.append(float(off_decision_changed))
        swap_following_on.append(float(on_swap_followed))
        swap_following_off.append(float(off_swap_followed))

        rows.append(
            {
                "replicate": replicate,
                "stable_state": float(stable_state.dynamic_state),
                "frontier_state": float(frontier_state.dynamic_state),
                "stable_action_on": float(stable_on["signal"]),
                "frontier_action_on": float(frontier_on["signal"]),
                "stable_action_off": float(stable_off["signal"]),
                "frontier_action_off": float(frontier_off["signal"]),
                "stable_swap_action_on": float(stable_swap_on["signal"]),
                "frontier_swap_action_on": float(frontier_swap_on["signal"]),
                "prediction_gap": prediction_gaps[-1],
                "prediction_swap_gap": prediction_swap_gaps[-1],
                "decision_sensitivity_on": decision_sensitivity_on[-1],
                "decision_sensitivity_off": decision_sensitivity_off[-1],
                "swap_following_on": swap_following_on[-1],
                "swap_following_off": swap_following_off[-1],
            }
        )

    on_vs_off_decision = np.asarray(decision_sensitivity_on) - np.asarray(decision_sensitivity_off)
    on_vs_off_swap = np.asarray(swap_following_on) - np.asarray(swap_following_off)

    summary = {
        "experiment": "organism_self_read_state_v69",
        "replicates": args.replicates,
        "self_model_samples": args.self_model_samples,
        "candidate_signals": list(CANDIDATE_SIGNALS),
        "semantic_ablation": True,
        "self_model_trained_independently_of_conditions": True,
        "mean_prediction_gap_stable_vs_frontier": float(np.mean(prediction_gaps)),
        "mean_prediction_swap_gap": float(np.mean(prediction_swap_gaps)),
        "decision_sensitivity_on": float(np.mean(decision_sensitivity_on)),
        "decision_sensitivity_off": float(np.mean(decision_sensitivity_off)),
        "swap_following_on": float(np.mean(swap_following_on)),
        "swap_following_off": float(np.mean(swap_following_off)),
        "decision_sensitivity_on_minus_off_p": paired_sign_p(
            on_vs_off_decision, 69001
        ),
        "swap_following_on_minus_off_p": paired_sign_p(on_vs_off_swap, 69002),
        "all_memories_removed_before_probe": True,
        "self_model_text_cleared_before_probe": True,
        "semantic_text_input_during_probe": False,
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

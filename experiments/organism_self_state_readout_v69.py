from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.organism_dream_state_trace_v67 import (  # noqa: E402
    FRONTIER_MEMORIES,
    STABLE_MEMORIES,
    DreamTraceProvider,
    delete_semantic_surfaces,
)
from src.ontto.bridge import DynamicStateBridge  # noqa: E402
from src.ontto.dynamics import Config as DynamicsConfig  # noqa: E402
from src.ontto.organism import OrganismConfig, PersistentOrganism  # noqa: E402
from src.ontto.self_observer import SelfObserver  # noqa: E402
from src.ontto.storage import MemoryStore  # noqa: E402
from src.ontto.trajectory_selector import TrajectorySelector  # noqa: E402


CALIBRATION_SIGNALS = (-1.0, 1.0, 0.0, 1.0, -1.0, 0.0)
PROBE_SIGNALS = (-1.0, 1.0)


def paired_sign_p(values: list[float] | np.ndarray, seed: int) -> float:
    values = np.asarray(values, dtype=float)
    if not len(values):
        return 1.0
    observed = abs(float(values.mean()))
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.asarray([-1.0, 1.0]), size=(20000, len(values)))
    null = np.abs((signs * values).mean(axis=1))
    return float((np.count_nonzero(null >= observed) + 1) / 20001)


def make_condition_db(path: Path, seed: int, condition: str, calibration_cycles: int):
    store = MemoryStore(path)
    cfg = OrganismConfig(
        agent_id="receiver",
        dynamic_seed=seed,
        dream_every_cycles=10_000,
        event_limit=16,
        self_observer_enabled=True,
        self_selection_enabled=False,
        semantic_dynamic_bridge_enabled=False,
        semantic_self_model_bridge_enabled=False,
        dream_semantic_bridge_enabled=True,
    )
    organism = PersistentOrganism(
        cfg,
        store,
        DreamTraceProvider(condition),
        lambda _: None,
    )

    for _ in range(calibration_cycles):
        signal = CALIBRATION_SIGNALS[organism.cycles % len(CALIBRATION_SIGNALS)]
        organism._advance_dynamic(signal, 1)
        organism.cycles += 1
        store.save_state("receiver", organism.state)

    frozen_observer = SelfObserver.from_dict(organism.self_observer.to_dict())

    memories = STABLE_MEMORIES if condition == "stable" else FRONTIER_MEMORIES
    for memory in memories:
        store.add_memory("receiver", memory, importance=0.65)

    organism.dream_cycle()
    dream_state = store.load_state("receiver")

    state_delta = float(dream_state.dynamic_state)
    store.conn.close()

    ablated_state = delete_semantic_surfaces(path)
    return frozen_observer, ablated_state, state_delta


def evaluate_policy(
    observer: SelfObserver,
    state,
    *,
    signals: tuple[float, ...] = PROBE_SIGNALS,
    clamped: bool = False,
    clamp_state: float = 0.0,
):
    selector = TrajectorySelector(
        attractor_weight=0.70,
        coherence_weight=0.30,
        meta_error_weight=0.0,
    )

    probe_state = float(clamp_state if clamped else state.dynamic_state)
    candidates = selector.evaluate(
        observer,
        current_state=probe_state,
        current_memory=0.0,
        current_pressure=0.0,
        current_input=0.0,
        current_attractor=0.0,
        steps_delta=1,
        signals=signals,
    )
    chosen = selector.choose(candidates)

    prediction_vector = np.asarray(
        [candidate.prediction.predicted_state for candidate in candidates],
        dtype=float,
    )
    score_vector = np.asarray([candidate.score for candidate in candidates], dtype=float)
    return {
        "chosen_signal": float(chosen.signal),
        "prediction_vector": prediction_vector,
        "score_vector": score_vector,
        "candidates": candidates,
    }


def apply_signal(state, signal: float, seed: int):
    bridge = DynamicStateBridge(DynamicsConfig(), seed=seed)
    snap = bridge.advance(
        previous_state=state.dynamic_prev_state,
        state=state.dynamic_state,
        memory=0.0,
        pressure=0.0,
        signal=signal,
        steps=1,
        step_index=state.dynamic_steps,
    )
    return float(snap.state)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicates", type=int, default=24)
    ap.add_argument("--calibration-cycles", type=int, default=48)
    ap.add_argument("--out", default="results/organism_self_state_readout_v69")
    args = ap.parse_args()

    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    rows = []
    read_score_deltas = []
    prediction_deltas = []
    read_vs_clamped_changes = []
    read_actions = []
    swap_policy_following = []
    post_action_state_deltas = []
    dream_state_deltas = []

    for replicate in range(args.replicates):
        seed = 9901 + replicate
        stable_db = out / f"stable_{replicate}.db"
        frontier_db = out / f"frontier_{replicate}.db"

        stable_observer, stable_state, stable_dream_delta = make_condition_db(
            stable_db,
            seed,
            "stable",
            args.calibration_cycles,
        )
        frontier_observer, frontier_state, frontier_dream_delta = make_condition_db(
            frontier_db,
            seed,
            "frontier",
            args.calibration_cycles,
        )

        # The frozen numeric self-models must be identical across conditions.
        observer_a = stable_observer
        observer_b = frontier_observer
        observer_consistent = json.dumps(observer_a.to_dict(), sort_keys=True) == json.dumps(
            observer_b.to_dict(), sort_keys=True
        )

        # Common probe state for the state-clamped control.
        clamp_state = float(
            (stable_state.dynamic_state + frontier_state.dynamic_state) / 2.0
        )

        stable_read = evaluate_policy(observer_a, stable_state, clamped=False)
        frontier_read = evaluate_policy(observer_b, frontier_state, clamped=False)
        stable_clamped = evaluate_policy(
            observer_a, stable_state, clamped=True, clamp_state=clamp_state
        )
        frontier_clamped = evaluate_policy(
            observer_b, frontier_state, clamped=True, clamp_state=clamp_state
        )

        stable_frontier_swap = copy.deepcopy(stable_state)
        stable_frontier_swap.dynamic_prev_state = frontier_state.dynamic_prev_state
        stable_frontier_swap.dynamic_state = frontier_state.dynamic_state
        stable_frontier_swap.dynamic_steps = frontier_state.dynamic_steps

        frontier_stable_swap = copy.deepcopy(frontier_state)
        frontier_stable_swap.dynamic_prev_state = stable_state.dynamic_prev_state
        frontier_stable_swap.dynamic_state = stable_state.dynamic_state
        frontier_stable_swap.dynamic_steps = stable_state.dynamic_steps

        stable_swap_read = evaluate_policy(observer_a, stable_frontier_swap, clamped=False)
        frontier_swap_read = evaluate_policy(observer_b, frontier_stable_swap, clamped=False)

        stable_read_scores = stable_read["score_vector"]
        frontier_read_scores = frontier_read["score_vector"]
        score_delta = float(np.mean(np.abs(stable_read_scores - frontier_read_scores)))
        prediction_delta = float(
            np.mean(
                np.abs(
                    stable_read["prediction_vector"]
                    - frontier_read["prediction_vector"]
                )
            )
        )

        stable_changed = float(
            stable_read["chosen_signal"] != stable_clamped["chosen_signal"]
        )
        frontier_changed = float(
            frontier_read["chosen_signal"] != frontier_clamped["chosen_signal"]
        )

        stable_swap_follow = float(
            stable_swap_read["chosen_signal"] == frontier_read["chosen_signal"]
        )
        frontier_swap_follow = float(
            frontier_swap_read["chosen_signal"] == stable_read["chosen_signal"]
        )

        stable_post = apply_signal(stable_state, stable_read["chosen_signal"], seed)
        frontier_post = apply_signal(frontier_state, frontier_read["chosen_signal"], seed)
        post_delta = abs(stable_post - frontier_post)

        read_score_deltas.append(score_delta)
        prediction_deltas.append(prediction_delta)
        read_vs_clamped_changes.extend([stable_changed, frontier_changed])
        read_actions.extend([stable_read["chosen_signal"], frontier_read["chosen_signal"]])
        swap_policy_following.extend([stable_swap_follow, frontier_swap_follow])
        post_action_state_deltas.append(post_delta)
        dream_state_deltas.append(float(stable_dream_delta - frontier_dream_delta))

        rows.append(
            {
                "replicate": replicate,
                "seed": seed,
                "observer_models_identical": observer_consistent,
                "stable_dream_state": float(stable_dream_delta),
                "frontier_dream_state": float(frontier_dream_delta),
                "stable_read_action": stable_read["chosen_signal"],
                "frontier_read_action": frontier_read["chosen_signal"],
                "stable_clamped_action": stable_clamped["chosen_signal"],
                "frontier_clamped_action": frontier_clamped["chosen_signal"],
                "stable_swap_action": stable_swap_read["chosen_signal"],
                "frontier_swap_action": frontier_swap_read["chosen_signal"],
                "state_read_score_delta": score_delta,
                "prediction_delta": prediction_delta,
                "stable_action_changed_by_read": bool(stable_changed),
                "frontier_action_changed_by_read": bool(frontier_changed),
                "post_action_state_delta_abs": post_delta,
            }
        )

    read_score_arr = np.asarray(read_score_deltas, dtype=float)
    prediction_arr = np.asarray(prediction_deltas, dtype=float)
    change_arr = np.asarray(read_vs_clamped_changes, dtype=float)
    swap_arr = np.asarray(swap_policy_following, dtype=float) - 0.5

    summary = {
        "experiment": "organism_self_state_readout_v69",
        "replicates": args.replicates,
        "calibration_cycles": args.calibration_cycles,
        "semantic_ablation": True,
        "probe_signals": list(PROBE_SIGNALS),
        "dream_state_delta_mean_stable_minus_frontier": float(np.mean(dream_state_deltas)),
        "read_score_delta_mean": float(np.mean(read_score_arr)),
        "prediction_delta_mean": float(np.mean(prediction_arr)),
        "read_vs_clamped_action_change_fraction": float(np.mean(change_arr + 0.5)),
        "read_score_delta_p": paired_sign_p(read_score_arr, 69001),
        "prediction_delta_p": paired_sign_p(prediction_arr, 69002),
        "read_vs_clamped_action_change_fraction": float(np.mean(change_arr)),
        "read_action_unique_fraction": float(len(set(read_actions)) / len(read_actions)),
        "state_swap_policy_following_fraction": float(np.mean(swap_arr + 0.5)),
        "state_swap_policy_following_informative": bool(len(set(read_actions)) > 1),
        "post_action_state_delta_abs_mean": float(np.mean(post_action_state_deltas)),
        "observer_models_identical_fraction": float(
            np.mean([row["observer_models_identical"] for row in rows])
        ),
        "all_memories_removed_before_probe": True,
        "self_model_text_cleared_before_probe": True,
        "numeric_self_model_frozen_before_dream": True,
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

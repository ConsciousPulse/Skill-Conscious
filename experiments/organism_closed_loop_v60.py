from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

import numpy as np

from src.ontto.bridge import DynamicStateBridge
from src.ontto.dynamics import Config as DynamicsConfig
from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore

CANDIDATE_SIGNALS = (-1.0, 1.0)
SEED_MEMORY = "SEED relation anchor continuity."
POSITIVE_MEMORY = "CONTINUE relation anchor stability."
NEGATIVE_MEMORY = "DELTA QUASAR NEBULA frontier explore divergence."


class ClosedLoopProvider:
    """Deterministic provider whose next semantic memory depends on prior action."""

    ACTION_RE = re.compile(r"['\"]chosen_signal['\"]:\s*(-?1\.0|0\.0)")

    def chat(self, messages, temperature=0.7):
        context = "\n".join(
            message.get("content", "")
            for message in messages
            if isinstance(message, dict)
        )
        matches = self.ACTION_RE.findall(context)
        previous_action = float(matches[-1]) if matches else 0.0

        if previous_action > 0.5:
            memory = POSITIVE_MEMORY
            route = "CONTINUE"
        elif previous_action < -0.5:
            memory = NEGATIVE_MEMORY
            route = "EXPLORE"
        else:
            memory = SEED_MEMORY
            route = "SEED"

        return LLMResponse(
            text=(
                f"Closed-loop response route={route}.\n"
                f"MEMORY: {memory}\n"
                "SELF_MODEL: my internal trajectory depends on persistent state."
            ),
            raw={
                "fake": True,
                "route": route,
                "previous_action": previous_action,
                "memory": memory,
            },
        )


def make_base(path: Path, seed: int, warmup: int) -> None:
    store = MemoryStore(path)
    cfg = OrganismConfig(
        agent_id="receiver",
        dynamic_seed=seed,
        dream_every_cycles=10_000,
        event_limit=0,
        self_observer_enabled=True,
        self_selection_enabled=False,
        semantic_dynamic_bridge_enabled=True,
        semantic_dynamic_scale=1.0,
        semantic_dynamic_importance=0.65,
        self_selection_signals=CANDIDATE_SIGNALS,
    )
    organism = PersistentOrganism(
        cfg,
        store,
        ClosedLoopProvider(),
        lambda _: None,
    )
    store.add_memory("receiver", SEED_MEMORY, importance=0.65)
    store.save_state("receiver", organism.state)

    for index in range(warmup):
        organism.wake_cycle(f"closed-loop warmup {index}")
        organism.autonomous_wake_cycle()

    store.save_state("receiver", organism.state)
    store.conn.close()


def paired_oracle(*, state, seed: int, step_index: int) -> dict:
    bridge = DynamicStateBridge(DynamicsConfig(), seed=seed)
    outcomes = {}

    for signal in CANDIDATE_SIGNALS:
        snap = bridge.advance(
            previous_state=state.dynamic_prev_state,
            state=state.dynamic_state,
            memory=state.dynamic_memory,
            pressure=state.dynamic_pressure,
            signal=signal,
            steps=1,
            step_index=step_index,
        )
        outcomes[signal] = {
            "state": snap.state,
            "distance": abs(snap.state),
        }

    oracle_signal = min(
        CANDIDATE_SIGNALS,
        key=lambda signal: (outcomes[signal]["distance"], abs(signal)),
    )
    return {
        "oracle_signal": oracle_signal,
        "oracle_distance": outcomes[oracle_signal]["distance"],
        "outcomes": outcomes,
    }


def run_arm(
    db_path: Path,
    *,
    seed: int,
    policy: str,
    cycles: int,
) -> dict:
    store = MemoryStore(db_path)
    cfg = OrganismConfig(
        agent_id="receiver",
        dynamic_seed=seed,
        dream_every_cycles=10_000,
        event_limit=8,
        self_observer_enabled=True,
        self_selection_enabled=True,
        self_selection_policy=policy,
        self_selection_signals=CANDIDATE_SIGNALS,
        semantic_dynamic_bridge_enabled=True,
        semantic_dynamic_scale=1.0,
        semantic_dynamic_importance=0.65,
    )
    organism = PersistentOrganism(
        cfg,
        store,
        ClosedLoopProvider(),
        lambda _: None,
    )

    rows = []

    for cycle in range(cycles):
        before = store.load_state("receiver")
        oracle = paired_oracle(
            state=before,
            seed=seed,
            step_index=before.dynamic_steps,
        )

        organism.wake_cycle(f"closed-loop evaluation {cycle}")
        after_semantic = store.load_state("receiver")
        interaction = store.recent_events("receiver", 1)[0]
        semantic_bridge = interaction["payload"].get("semantic_bridge") or {}

        organism.autonomous_wake_cycle()

        after_selection = store.load_state("receiver")
        autonomous_event = store.recent_events("receiver", 1)[0]
        selection = autonomous_event["payload"]["self_selection"]
        chosen_signal = float(selection["chosen_signal"])

        actual_distance = abs(
            after_selection.dynamic_state - after_selection.dynamic_attractor
        )
        regret = actual_distance - oracle["oracle_distance"]

        rows.append(
            {
                "cycle": cycle,
                "policy": policy,
                "chosen_signal": chosen_signal,
                "oracle_signal": oracle["oracle_signal"],
                "oracle_hit": chosen_signal == oracle["oracle_signal"],
                "regret": regret,
                "pre_state": before.dynamic_state,
                "post_semantic_state": after_semantic.dynamic_state,
                "post_selection_state": after_selection.dynamic_state,
                "semantic_signal": float(after_semantic.dynamic_last_input),
                "semantic_memory": semantic_bridge.get("memory"),
                "semantic_route": (
                    "CONTINUE"
                    if semantic_bridge.get("memory") == POSITIVE_MEMORY
                    else "EXPLORE"
                    if semantic_bridge.get("memory") == NEGATIVE_MEMORY
                    else "SEED"
                ),
                "selection_candidates": selection["candidates"],
            }
        )

    previous_actions = [None] + [row["chosen_signal"] for row in rows[:-1]]
    semantic_by_previous = {
        -1.0: [
            row["semantic_signal"]
            for previous, row in zip(previous_actions, rows)
            if previous == -1.0
        ],
        1.0: [
            row["semantic_signal"]
            for previous, row in zip(previous_actions, rows)
            if previous == 1.0
        ],
    }

    feedback_delta = None
    if semantic_by_previous[-1.0] and semantic_by_previous[1.0]:
        feedback_delta = float(
            abs(
                np.mean(semantic_by_previous[1.0])
                - np.mean(semantic_by_previous[-1.0])
            )
        )

    regrets = np.asarray([row["regret"] for row in rows], dtype=float)
    return {
        "policy": policy,
        "cycles": cycles,
        "mean_regret": float(regrets.mean()),
        "median_regret": float(np.median(regrets)),
        "oracle_hit_rate": float(np.mean([row["oracle_hit"] for row in rows])),
        "cumulative_regret": float(regrets.sum()),
        "mean_abs_state": float(
            np.mean([abs(row["post_selection_state"]) for row in rows])
        ),
        "feedback_signal_delta_by_previous_action": feedback_delta,
        "previous_action_signal_counts": {
            "negative": len(semantic_by_previous[-1.0]),
            "positive": len(semantic_by_previous[1.0]),
        },
        "rows": rows,
    }


def sign_permutation_p(
    values: np.ndarray,
    permutations: int = 20000,
    seed: int = 60001,
) -> float:
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return 1.0
    observed = abs(float(values.mean()))
    rng = np.random.default_rng(seed)
    signs = rng.choice(
        np.array([-1.0, 1.0]),
        size=(permutations, len(values)),
    )
    null = np.abs((signs * values).mean(axis=1))
    return float((np.count_nonzero(null >= observed) + 1) / (permutations + 1))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=24)
    parser.add_argument("--warmup", type=int, default=16)
    parser.add_argument("--cycles", type=int, default=24)
    parser.add_argument("--out", default="results/organism_closed_loop_v60")
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    rows = []

    for replicate in range(args.replicates):
        seed = 8101 + replicate
        base = out / f"base_{replicate}.db"
        self_db = out / f"self_{replicate}.db"
        random_db = out / f"random_{replicate}.db"

        make_base(base, seed, args.warmup)
        shutil.copy2(base, self_db)
        shutil.copy2(base, random_db)

        self_arm = run_arm(
            self_db,
            seed=seed,
            policy="self_model",
            cycles=args.cycles,
        )
        random_arm = run_arm(
            random_db,
            seed=seed,
            policy="random",
            cycles=args.cycles,
        )

        rows.append(
            {
                "replicate": replicate,
                "seed": seed,
                "self_model": self_arm,
                "random_control": random_arm,
                "regret_advantage_random_minus_self": (
                    random_arm["mean_regret"] - self_arm["mean_regret"]
                ),
                "cumulative_regret_advantage_random_minus_self": (
                    random_arm["cumulative_regret"]
                    - self_arm["cumulative_regret"]
                ),
                "oracle_hit_difference": (
                    self_arm["oracle_hit_rate"] - random_arm["oracle_hit_rate"]
                ),
            }
        )

    regret_advantages = np.asarray(
        [row["regret_advantage_random_minus_self"] for row in rows],
        dtype=float,
    )
    cumulative_advantages = np.asarray(
        [row["cumulative_regret_advantage_random_minus_self"] for row in rows],
        dtype=float,
    )
    feedback_deltas = [
        row["self_model"]["feedback_signal_delta_by_previous_action"]
        for row in rows
        if row["self_model"]["feedback_signal_delta_by_previous_action"] is not None
    ]

    summary = {
        "experiment": "organism_closed_loop_v60",
        "replicates": args.replicates,
        "warmup_cycles": args.warmup,
        "evaluation_cycles": args.cycles,
        "candidate_signals": list(CANDIDATE_SIGNALS),
        "feedback_memory_map": {
            "positive_action": POSITIVE_MEMORY,
            "negative_action": NEGATIVE_MEMORY,
        },
        "self_model_mean_regret": float(
            np.mean([row["self_model"]["mean_regret"] for row in rows])
        ),
        "random_control_mean_regret": float(
            np.mean([row["random_control"]["mean_regret"] for row in rows])
        ),
        "self_model_cumulative_regret": float(
            np.mean([row["self_model"]["cumulative_regret"] for row in rows])
        ),
        "random_control_cumulative_regret": float(
            np.mean([row["random_control"]["cumulative_regret"] for row in rows])
        ),
        "mean_regret_advantage_self_model": float(regret_advantages.mean()),
        "cumulative_regret_advantage_self_model": float(cumulative_advantages.mean()),
        "median_regret_advantage_self_model": float(np.median(regret_advantages)),
        "paired_sign_flip_p_mean_regret": sign_permutation_p(regret_advantages),
        "paired_sign_flip_p_cumulative_regret": sign_permutation_p(
            cumulative_advantages,
            seed=60002,
        ),
        "self_model_oracle_hit_rate": float(
            np.mean([row["self_model"]["oracle_hit_rate"] for row in rows])
        ),
        "random_oracle_hit_rate": float(
            np.mean([row["random_control"]["oracle_hit_rate"] for row in rows])
        ),
        "mean_feedback_signal_delta_self_model": (
            float(np.mean(feedback_deltas))
            if feedback_deltas
            else None
        ),
        "feedback_cycles_with_both_actions": len(feedback_deltas),
        "all_runs_have_two_candidates": all(
            len(row["self_model"]["rows"][0]["selection_candidates"]) == 2
            and len(row["random_control"]["rows"][0]["selection_candidates"]) == 2
            for row in rows
        ),
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

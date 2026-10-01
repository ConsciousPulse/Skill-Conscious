from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np

from src.ontto.bridge import DynamicStateBridge
from src.ontto.dynamics import Config as DynamicsConfig
from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore

CANDIDATE_SIGNALS = (-1.0, 1.0)


class FakeProvider:
    def chat(self, messages, temperature=0.7):
        return LLMResponse(
            text=(
                "Metacognitive calibration response.\n"
                "MEMORY: preserve the continuity of internal trajectory.\n"
                "SELF_MODEL: I can model my own state transition."
            ),
            raw={"fake": True},
        )


def warmup(db_path: Path, seed: int, cycles: int) -> None:
    store = MemoryStore(db_path)
    cfg = OrganismConfig(
        agent_id="receiver",
        dynamic_seed=seed,
        dream_every_cycles=10_000,
        event_limit=8,
        self_observer_enabled=True,
        meta_self_observer_enabled=True,
        self_selection_enabled=False,
        self_selection_signals=CANDIDATE_SIGNALS,
    )
    organism = PersistentOrganism(cfg, store, FakeProvider(), lambda _: None)

    for index in range(cycles):
        organism.wake_cycle(f"metacognitive warmup {index}")
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
        "outcomes": outcomes,
        "oracle_signal": oracle_signal,
        "oracle_distance": outcomes[oracle_signal]["distance"],
    }


def run_arm(
    db_path: Path,
    *,
    seed: int,
    policy: str,
    cycles: int,
) -> dict:
    store = MemoryStore(db_path)
    meta_enabled = policy == "meta_self_model"
    cfg = OrganismConfig(
        agent_id="receiver",
        dynamic_seed=seed,
        dream_every_cycles=10_000,
        event_limit=8,
        self_observer_enabled=True,
        meta_self_observer_enabled=meta_enabled,
        meta_self_observer_ridge=1e-3,
        meta_self_observer_max_samples=2048,
        self_selection_enabled=True,
        self_selection_policy=("random" if policy == "random" else "self_model"),
        self_selection_attractor_weight=0.55,
        self_selection_coherence_weight=0.20,
        self_selection_meta_error_weight=(0.25 if meta_enabled else 0.0),
        self_selection_signals=CANDIDATE_SIGNALS,
    )
    organism = PersistentOrganism(cfg, store, FakeProvider(), lambda _: None)

    rows = []
    for cycle in range(cycles):
        before = store.load_state("receiver")
        oracle = paired_oracle(
            state=before,
            seed=seed,
            step_index=before.dynamic_steps,
        )

        organism.autonomous_wake_cycle()
        after = store.load_state("receiver")
        event = store.recent_events("receiver", 1)[0]
        selection = event["payload"]["self_selection"]

        actual_distance = abs(after.dynamic_state - 0.0)
        regret = actual_distance - oracle["oracle_distance"]

        candidate_rows = []
        for candidate in selection["candidates"]:
            signal = float(candidate["signal"])
            actual_next_state = oracle["outcomes"][signal]["state"]
            predicted_state = float(candidate["predicted_state"])
            actual_prediction_error = abs(actual_next_state - predicted_state)
            predicted_error = candidate.get("predicted_error")
            candidate_rows.append(
                {
                    "signal": signal,
                    "predicted_state": predicted_state,
                    "actual_state": actual_next_state,
                    "actual_prediction_error": actual_prediction_error,
                    "predicted_error": (
                        float(predicted_error)
                        if predicted_error is not None
                        else None
                    ),
                }
            )

        rows.append(
            {
                "cycle": cycle,
                "chosen_signal": float(selection["chosen_signal"]),
                "oracle_signal": oracle["oracle_signal"],
                "oracle_hit": float(selection["chosen_signal"]) == oracle["oracle_signal"],
                "regret": regret,
                "candidates": candidate_rows,
                "meta_enabled": meta_enabled,
            }
        )

    all_candidates = [
        candidate
        for row in rows
        for candidate in row["candidates"]
        if candidate["predicted_error"] is not None
    ]
    meta_mae = (
        float(
            np.mean([
                abs(candidate["predicted_error"] - candidate["actual_prediction_error"])
                for candidate in all_candidates
            ])
        )
        if all_candidates
        else None
    )
    baseline_targets = np.asarray(
        [candidate["actual_prediction_error"] for candidate in all_candidates],
        dtype=float,
    )
    baseline_mae = (
        float(
            np.mean(
                np.abs(
                    baseline_targets - float(np.mean(baseline_targets))
                )
            )
        )
        if len(baseline_targets)
        else None
    )

    regrets = np.asarray([row["regret"] for row in rows], dtype=float)
    return {
        "policy": policy,
        "cycles": cycles,
        "mean_regret": float(regrets.mean()),
        "median_regret": float(np.median(regrets)),
        "cumulative_regret": float(regrets.sum()),
        "oracle_hit_rate": float(np.mean([row["oracle_hit"] for row in rows])),
        "meta_prediction_mae": meta_mae,
        "constant_baseline_mae": baseline_mae,
        "meta_beats_constant_baseline": (
            bool(meta_mae < baseline_mae)
            if meta_mae is not None and baseline_mae is not None
            else False
        ),
        "rows": rows,
    }


def sign_flip_p(values: np.ndarray, permutations: int = 20000, seed: int = 61001) -> float:
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return 1.0
    observed = abs(float(values.mean()))
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.array([-1.0, 1.0]), size=(permutations, len(values)))
    null = np.abs((signs * values).mean(axis=1))
    return float((np.count_nonzero(null >= observed) + 1) / (permutations + 1))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=24)
    parser.add_argument("--warmup", type=int, default=32)
    parser.add_argument("--cycles", type=int, default=32)
    parser.add_argument("--out", default="results/organism_meta_self_model_v61")
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for replicate in range(args.replicates):
        seed = 8201 + replicate
        base = out / f"base_{replicate}.db"
        warmup(base, seed, args.warmup)

        arms = {}
        for policy in ("meta_self_model", "self_model", "random"):
            db = out / f"{policy}_{replicate}.db"
            shutil.copy2(base, db)
            arms[policy] = run_arm(
                db,
                seed=seed,
                policy=policy,
                cycles=args.cycles,
            )

        rows.append(
            {
                "replicate": replicate,
                "seed": seed,
                "arms": arms,
                "meta_vs_self_regret_advantage": (
                    arms["self_model"]["mean_regret"]
                    - arms["meta_self_model"]["mean_regret"]
                ),
                "meta_vs_self_hit_advantage": (
                    arms["meta_self_model"]["oracle_hit_rate"]
                    - arms["self_model"]["oracle_hit_rate"]
                ),
            }
        )

    regret_advantages = np.asarray(
        [row["meta_vs_self_regret_advantage"] for row in rows],
        dtype=float,
    )
    hit_advantages = np.asarray(
        [row["meta_vs_self_hit_advantage"] for row in rows],
        dtype=float,
    )

    summary = {
        "experiment": "organism_meta_self_model_v61",
        "replicates": args.replicates,
        "warmup_cycles": args.warmup,
        "evaluation_cycles": args.cycles,
        "candidate_signals": list(CANDIDATE_SIGNALS),
        "meta_self_model_mean_regret": float(
            np.mean([row["arms"]["meta_self_model"]["mean_regret"] for row in rows])
        ),
        "base_self_model_mean_regret": float(
            np.mean([row["arms"]["self_model"]["mean_regret"] for row in rows])
        ),
        "random_control_mean_regret": float(
            np.mean([row["arms"]["random"]["mean_regret"] for row in rows])
        ),
        "meta_self_model_oracle_hit_rate": float(
            np.mean([row["arms"]["meta_self_model"]["oracle_hit_rate"] for row in rows])
        ),
        "base_self_model_oracle_hit_rate": float(
            np.mean([row["arms"]["self_model"]["oracle_hit_rate"] for row in rows])
        ),
        "random_control_oracle_hit_rate": float(
            np.mean([row["arms"]["random"]["oracle_hit_rate"] for row in rows])
        ),
        "mean_regret_advantage_meta_vs_self": float(regret_advantages.mean()),
        "median_regret_advantage_meta_vs_self": float(np.median(regret_advantages)),
        "paired_sign_flip_p_regret": sign_flip_p(regret_advantages),
        "mean_hit_advantage_meta_vs_self": float(hit_advantages.mean()),
        "paired_sign_flip_p_hit": sign_flip_p(hit_advantages, seed=61002),
        "meta_prediction_mae": float(
            np.mean([
                row["arms"]["meta_self_model"]["meta_prediction_mae"]
                for row in rows
                if row["arms"]["meta_self_model"]["meta_prediction_mae"] is not None
            ])
        ),
        "meta_constant_baseline_mae": float(
            np.mean([
                row["arms"]["meta_self_model"]["constant_baseline_mae"]
                for row in rows
                if row["arms"]["meta_self_model"]["constant_baseline_mae"] is not None
            ])
        ),
        "meta_beats_constant_baseline_fraction": float(
            np.mean([
                row["arms"]["meta_self_model"]["meta_beats_constant_baseline"]
                for row in rows
            ])
        ),
        "all_arms_have_two_candidates": all(
            all(
                len(row["arms"][policy]["rows"][0]["candidates"]) == 2
                for policy in ("meta_self_model", "self_model", "random")
            )
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

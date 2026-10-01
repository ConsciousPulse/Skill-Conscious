from __future__ import annotations

import argparse
import json
import math
import random
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
                "Calibration response.\n"
                "MEMORY: retain dynamic continuity.\n"
                "SELF_MODEL: internal state follows trajectory."
            ),
            raw={"fake": True},
        )


def warmup(db_path: Path, agent_id: str, seed: int, cycles: int) -> None:
    store = MemoryStore(db_path)
    cfg = OrganismConfig(
        agent_id=agent_id,
        dynamic_seed=seed,
        dream_every_cycles=10_000,
        event_limit=0,
        self_observer_enabled=True,
        self_selection_enabled=False,
    )
    organism = PersistentOrganism(cfg, store, FakeProvider(), lambda _: None)

    for i in range(cycles):
        organism.wake_cycle(f"calibration {i}")
        organism.autonomous_wake_cycle()

    store.conn.close()


def paired_oracle(
    *,
    state,
    seed: int,
    step_index: int,
) -> dict:
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
            "distance": abs(snap.state - 0.0),
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
    agent_id: str,
    policy: str,
    cycles: int,
) -> dict:
    store = MemoryStore(db_path)
    cfg = OrganismConfig(
        agent_id=agent_id,
        dynamic_seed=seed,
        dream_every_cycles=10_000,
        event_limit=0,
        self_observer_enabled=True,
        self_selection_enabled=True,
        self_selection_policy=policy,
        self_selection_signals=CANDIDATE_SIGNALS,
    )
    organism = PersistentOrganism(cfg, store, FakeProvider(), lambda _: None)

    state_before = store.load_state(agent_id)
    oracle = paired_oracle(
        state=state_before,
        seed=seed,
        step_index=state_before.dynamic_steps,
    )

    organism.autonomous_wake_cycle()
    state_after = store.load_state(agent_id)
    event = store.recent_events(agent_id, 1)[0]
    chosen_signal = float(event["payload"]["self_selection"]["chosen_signal"])
    actual_distance = abs(state_after.dynamic_state - state_after.attractor)

    return {
        "policy": policy,
        "chosen_signal": chosen_signal,
        "oracle_signal": oracle["oracle_signal"],
        "oracle_distance": oracle["oracle_distance"],
        "actual_distance": actual_distance,
        "regret": actual_distance - oracle["oracle_distance"],
        "oracle_hit": chosen_signal == oracle["oracle_signal"],
        "predictions": event["payload"]["self_selection"]["candidates"],
        "before_state": state_before.dynamic_state,
        "after_state": state_after.dynamic_state,
        "before_steps": state_before.dynamic_steps,
    }


def sign_permutation_p(values: np.ndarray, permutations: int = 20000, seed: int = 57101) -> float:
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
    parser.add_argument("--out", default="results/organism_self_model_selection_v57")
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    rows = []

    for replicate in range(args.replicates):
        seed = 7001 + replicate
        base = out / f"base_{replicate}.db"
        self_db = out / f"self_{replicate}.db"
        random_db = out / f"random_{replicate}.db"

        warmup(base, "receiver", seed, args.warmup)
        shutil.copy2(base, self_db)
        shutil.copy2(base, random_db)

        self_row = run_arm(
            self_db,
            seed=seed,
            agent_id="receiver",
            policy="self_model",
            cycles=args.warmup,
        )
        random_row = run_arm(
            random_db,
            seed=seed,
            agent_id="receiver",
            policy="random",
            cycles=args.warmup,
        )

        rows.append(
            {
                "replicate": replicate,
                "seed": seed,
                "self_model": self_row,
                "random_control": random_row,
                "regret_difference_random_minus_self": (
                    random_row["regret"] - self_row["regret"]
                ),
                        "oracle_hit_difference": (
                    int(self_row["oracle_hit"]) - int(random_row["oracle_hit"])
                ),
                "self_model_correct_direction": (
                    self_row["chosen_signal"] == self_row["oracle_signal"]
                ),
                "random_correct_direction": (
                    random_row["chosen_signal"] == random_row["oracle_signal"]
                ),
            }
        )

    regret_differences = np.asarray(
        [row["regret_difference_random_minus_self"] for row in rows],
        dtype=float,
    )
    self_regrets = np.asarray(
        [row["self_model"]["regret"] for row in rows],
        dtype=float,
    )
    random_regrets = np.asarray(
        [row["random_control"]["regret"] for row in rows],
        dtype=float,
    )

    summary = {
        "experiment": "organism_self_model_selection_v57",
        "replicates": args.replicates,
        "warmup_cycles": args.warmup,
        "candidate_signals": list(CANDIDATE_SIGNALS),
        "self_model_mean_regret": float(self_regrets.mean()),
        "random_control_mean_regret": float(random_regrets.mean()),
        "mean_regret_advantage_self_model": float(regret_differences.mean()),
        "median_regret_advantage_self_model": float(np.median(regret_differences)),
        "self_model_oracle_hit_rate": float(
            np.mean([row["self_model"]["oracle_hit"] for row in rows])
        ),
        "random_oracle_hit_rate": float(
            np.mean([row["random_control"]["oracle_hit"] for row in rows])
        ),
        "self_minus_random_oracle_hit_rate": float(
            np.mean([
                int(row["self_model"]["oracle_hit"]) - int(row["random_control"]["oracle_hit"])
                for row in rows
            ])
        ),
        "paired_sign_flip_p": sign_permutation_p(regret_differences),
        "effect_positive_for_self_model": bool(regret_differences.mean() > 0),
        "all_predictions_have_two_candidates": all(
            len(row["self_model"]["predictions"]) == 2 for row in rows
        ),
    }

    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out / "runs.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False,
                   default=lambda x: float(x) if isinstance(x, np.floating) else x),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

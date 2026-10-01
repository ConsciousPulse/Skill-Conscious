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

BASE_MEMORY = "La relación estable mantiene continuidad y ancla el recorrido."
BASE_SELF_MODEL = "Mantengo una identidad persistente entre ciclos."
SELF_MODEL_A = "Mantengo continuidad estable y conservo el recorrido persistente."
SELF_MODEL_B = "Cambio de régimen y abro una ruta futura completamente nueva."


class ActionConditionedSelfModelProvider:
    """Deterministic provider whose next SELF_MODEL depends on the previous action."""

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
            self_model = SELF_MODEL_A
            route = "CONTINUE"
        elif previous_action < -0.5:
            self_model = SELF_MODEL_B
            route = "EXPLORE"
        else:
            self_model = BASE_SELF_MODEL
            route = "SEED"

        return LLMResponse(
            text=(
                "Closed-loop semantic self-model update.\n"
                f"MEMORY: {BASE_MEMORY}\n"
                f"SELF_MODEL: {self_model}"
            ),
            raw={
                "fake": True,
                "previous_action": previous_action,
                "route": route,
                "self_model": self_model,
            },
        )


def warmup(path: Path, seed: int, cycles: int) -> None:
    store = MemoryStore(path)
    cfg = OrganismConfig(
        agent_id="receiver",
        dynamic_seed=seed,
        dream_every_cycles=10_000,
        event_limit=12,
        self_observer_enabled=True,
        self_selection_enabled=False,
        semantic_dynamic_bridge_enabled=False,
        semantic_self_model_bridge_enabled=False,
    )
    organism = PersistentOrganism(
        cfg,
        store,
        ActionConditionedSelfModelProvider(),
        lambda _: None,
    )

    for index in range(cycles):
        organism.wake_cycle(f"V63 warmup {index}")
        organism.autonomous_wake_cycle()

    state = store.load_state("receiver")
    state.self_model = BASE_SELF_MODEL
    state.self_model_version = 1
    store.add_memory("receiver", BASE_MEMORY, importance=0.65)
    store.save_state("receiver", state)
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
    bridge_enabled: bool,
    cycles: int,
) -> dict:
    store = MemoryStore(db_path)
    cfg = OrganismConfig(
        agent_id="receiver",
        dynamic_seed=seed,
        dream_every_cycles=10_000,
        event_limit=12,
        self_observer_enabled=True,
        self_selection_enabled=True,
        self_selection_policy=policy,
        self_selection_attractor_weight=0.55,
        self_selection_coherence_weight=0.45,
        self_selection_signals=CANDIDATE_SIGNALS,
        semantic_dynamic_bridge_enabled=False,
        semantic_self_model_bridge_enabled=bridge_enabled,
        semantic_self_model_scale=1.0,
        semantic_self_model_importance=0.65,
    )
    organism = PersistentOrganism(
        cfg,
        store,
        ActionConditionedSelfModelProvider(),
        lambda _: None,
    )

    rows = []
    previous_action = None

    for cycle in range(cycles):
        organism.wake_cycle("V63 closed-loop self-model update")
        after_wake = store.load_state("receiver")
        interaction_event = store.recent_events("receiver", 1)[0]
        semantic_bridge = interaction_event["payload"].get(
            "semantic_self_model_bridge"
        )

        oracle = paired_oracle(
            state=after_wake,
            seed=seed,
            step_index=after_wake.dynamic_steps,
        )

        organism.autonomous_wake_cycle()
        after_selection = store.load_state("receiver")
        selection_event = store.recent_events("receiver", 1)[0]
        selection = selection_event["payload"]["self_selection"]
        chosen_signal = float(selection["chosen_signal"])

        actual_distance = abs(after_selection.dynamic_state)
        regret = actual_distance - oracle["oracle_distance"]

        rows.append(
            {
                "cycle": cycle,
                "policy": policy,
                "bridge_enabled": bridge_enabled,
                "previous_action": previous_action,
                "chosen_signal": chosen_signal,
                "oracle_signal": float(oracle["oracle_signal"]),
                "oracle_hit": chosen_signal == oracle["oracle_signal"],
                "regret": regret,
                "post_wake_state": after_wake.dynamic_state,
                "post_selection_state": after_selection.dynamic_state,
                "self_model_version": after_wake.self_model_version,
                "self_model": after_wake.self_model,
                "semantic_self_model_bridge": semantic_bridge,
                "candidate_count": len(selection["candidates"]),
            }
        )
        previous_action = chosen_signal

    feedback_by_previous = {
        -1.0: [
            float(row["semantic_self_model_bridge"]["signal"])
            for row in rows
            if row["semantic_self_model_bridge"] is not None
            and row["previous_action"] == -1.0
        ],
        1.0: [
            float(row["semantic_self_model_bridge"]["signal"])
            for row in rows
            if row["semantic_self_model_bridge"] is not None
            and row["previous_action"] == 1.0
        ],
    }
    feedback_delta = None
    if feedback_by_previous[-1.0] and feedback_by_previous[1.0]:
        feedback_delta = float(
            abs(
                np.mean(feedback_by_previous[1.0])
                - np.mean(feedback_by_previous[-1.0])
            )
        )

    regrets = np.asarray([row["regret"] for row in rows], dtype=float)
    chosen = np.asarray([row["chosen_signal"] for row in rows], dtype=float)
    return {
        "policy": policy,
        "bridge_enabled": bridge_enabled,
        "cycles": cycles,
        "mean_regret": float(regrets.mean()),
        "median_regret": float(np.median(regrets)),
        "oracle_hit_rate": float(
            np.mean([row["oracle_hit"] for row in rows])
        ),
        "cumulative_regret": float(regrets.sum()),
        "action_counts": {
            "negative": int(np.count_nonzero(chosen < 0)),
            "positive": int(np.count_nonzero(chosen > 0)),
        },
        "both_actions_selected": bool(
            np.any(chosen < 0) and np.any(chosen > 0)
        ),
        "feedback_signal_delta_by_previous_action": feedback_delta,
        "feedback_previous_action_counts": {
            "negative": len(feedback_by_previous[-1.0]),
            "positive": len(feedback_by_previous[1.0]),
        },
        "first_cycle_self_model_bridge_signal": (
            float(rows[0]["semantic_self_model_bridge"]["signal"])
            if rows[0]["semantic_self_model_bridge"] is not None
            else None
        ),
        "first_cycle_post_wake_state": float(rows[0]["post_wake_state"]),
        "rows": rows,
    }


def sign_flip_p(values: np.ndarray, permutations: int = 20000, seed: int = 63001) -> float:
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
    parser.add_argument("--warmup", type=int, default=24)
    parser.add_argument("--cycles", type=int, default=32)
    parser.add_argument(
        "--out",
        default="results/organism_causal_self_model_loop_v63",
    )
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    rows = []

    for replicate in range(args.replicates):
        seed = 8301 + replicate
        base = out / f"base_{replicate}.db"
        warmup(base, seed, args.warmup)

        arms = {}
        for bridge_enabled, bridge_label in (
            (False, "bridge_off"),
            (True, "bridge_on"),
        ):
            for policy in ("self_model", "random"):
                label = f"{bridge_label}_{policy}"
                db = out / f"{label}_{replicate}.db"
                shutil.copy2(base, db)
                arms[label] = run_arm(
                    db,
                    seed=seed,
                    policy=policy,
                    bridge_enabled=bridge_enabled,
                    cycles=args.cycles,
                )

        row = {
            "replicate": replicate,
            "seed": seed,
            "arms": arms,
            "self_model_bridge_regret_advantage": (
                arms["bridge_off_self_model"]["mean_regret"]
                - arms["bridge_on_self_model"]["mean_regret"]
            ),
            "self_model_bridge_hit_advantage": (
                arms["bridge_on_self_model"]["oracle_hit_rate"]
                - arms["bridge_off_self_model"]["oracle_hit_rate"]
            ),
            "closed_loop_selection_advantage": (
                arms["bridge_on_random"]["mean_regret"]
                - arms["bridge_on_self_model"]["mean_regret"]
            ),
        }
        rows.append(row)

    bridge_regret = np.asarray(
        [row["self_model_bridge_regret_advantage"] for row in rows],
        dtype=float,
    )
    bridge_hit = np.asarray(
        [row["self_model_bridge_hit_advantage"] for row in rows],
        dtype=float,
    )
    selection_advantage = np.asarray(
        [row["closed_loop_selection_advantage"] for row in rows],
        dtype=float,
    )

    def mean_arm(key: str, field: str) -> float:
        return float(np.mean([row["arms"][key][field] for row in rows]))

    summary = {
        "experiment": "organism_causal_self_model_loop_v63",
        "replicates": args.replicates,
        "warmup_cycles": args.warmup,
        "evaluation_cycles": args.cycles,
        "candidate_signals": list(CANDIDATE_SIGNALS),
        "mean_regret": {
            key: mean_arm(key, "mean_regret")
            for key in (
                "bridge_off_self_model",
                "bridge_on_self_model",
                "bridge_off_random",
                "bridge_on_random",
            )
        },
        "oracle_hit_rate": {
            key: mean_arm(key, "oracle_hit_rate")
            for key in (
                "bridge_off_self_model",
                "bridge_on_self_model",
                "bridge_off_random",
                "bridge_on_random",
            )
        },
        "closed_loop_selection_advantage_random_minus_self_on_bridge": float(
            selection_advantage.mean()
        ),
        "paired_sign_flip_p_selection_advantage": sign_flip_p(
            selection_advantage,
            seed=63002,
        ),
        "self_model_bridge_regret_advantage_off_minus_on": float(
            bridge_regret.mean()
        ),
        "paired_sign_flip_p_bridge_regret": sign_flip_p(
            bridge_regret,
            seed=63003,
        ),
        "self_model_bridge_hit_advantage_on_minus_off": float(
            bridge_hit.mean()
        ),
        "paired_sign_flip_p_bridge_hit": sign_flip_p(
            bridge_hit,
            seed=63004,
        ),
        "action_coverage_fraction": {
            key: float(
                np.mean([
                    bool(row["arms"][key]["both_actions_selected"])
                    for row in rows
                ])
            )
            for key in (
                "bridge_off_self_model",
                "bridge_on_self_model",
                "bridge_off_random",
                "bridge_on_random",
            )
        },
        "feedback_signal_delta_mean_when_both_actions": {
            key: (
                float(
                    np.mean([
                        row["arms"][key]["feedback_signal_delta_by_previous_action"]
                        for row in rows
                        if row["arms"][key]["feedback_signal_delta_by_previous_action"]
                        is not None
                    ])
                )
                if any(
                    row["arms"][key]["feedback_signal_delta_by_previous_action"]
                    is not None
                    for row in rows
                )
                else None
            )
            for key in ("bridge_on_self_model", "bridge_on_random")
        },
        "all_arms_have_two_candidates": all(
            all(
                row["arms"][key]["rows"][0]["candidate_count"] == 2
                for key in (
                    "bridge_off_self_model",
                    "bridge_on_self_model",
                    "bridge_off_random",
                    "bridge_on_random",
                )
            )
            for row in rows
        ),
        "all_bridge_on_runs_persist_self_model": all(
            all(
                row["arms"][key]["rows"][-1]["self_model_version"] > 1
                for key in ("bridge_on_self_model", "bridge_on_random")
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

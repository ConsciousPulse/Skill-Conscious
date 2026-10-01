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

BASE_MEMORY = "La relación estable mantiene continuidad y ancla el recorrido."
WARMUP_MEMORIES = (
    "CALIBRA mantiene una secuencia estable.",
    "BETA registra una transición intermedia.",
)
EVAL_MEMORY = "EPSILON abre una ruta futura completamente nueva."


class FakeProvider:
    """Deterministic provider used to isolate the protocol from API variance."""

    def __init__(self, memories: tuple[str, ...]):
        self.memories = tuple(memories)
        self.index = 0

    def chat(self, messages, temperature=0.7):
        memory = self.memories[self.index % len(self.memories)]
        self.index += 1
        return LLMResponse(
            text=(
                "Closed-loop calibration response.\n"
                f"MEMORY: {memory}\n"
                "SELF_MODEL: mi estado cambia según la relación persistente."
            ),
            raw={"fake": True, "memory": memory, "index": self.index},
        )


def make_base(path: Path, seed: int, bridge_enabled: bool, warmup: int) -> None:
    store = MemoryStore(path)
    cfg = OrganismConfig(
        agent_id="receiver",
        dynamic_seed=seed,
        dream_every_cycles=10_000,
        event_limit=0,
        self_observer_enabled=True,
        self_selection_enabled=False,
        semantic_dynamic_bridge_enabled=bridge_enabled,
        semantic_dynamic_scale=1.0,
        semantic_dynamic_importance=0.65,
        self_selection_signals=CANDIDATE_SIGNALS,
    )
    organism = PersistentOrganism(
        cfg,
        store,
        FakeProvider(WARMUP_MEMORIES),
        lambda _: None,
    )
    store.add_memory("receiver", BASE_MEMORY, importance=0.65)
    store.save_state("receiver", organism.state)

    for i in range(warmup):
        organism.wake_cycle(f"semantic warmup {i}")

    store.save_state("receiver", organism.state)
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
    bridge_enabled: bool,
    policy: str,
) -> dict:
    store = MemoryStore(db_path)
    cfg = OrganismConfig(
        agent_id="receiver",
        dynamic_seed=seed,
        dream_every_cycles=10_000,
        event_limit=0,
        self_observer_enabled=True,
        self_selection_enabled=True,
        self_selection_policy=policy,
        self_selection_signals=CANDIDATE_SIGNALS,
        semantic_dynamic_bridge_enabled=bridge_enabled,
        semantic_dynamic_scale=1.0,
        semantic_dynamic_importance=0.65,
    )
    organism = PersistentOrganism(
        cfg,
        store,
        FakeProvider((EVAL_MEMORY,)),
        lambda _: None,
    )

    organism.wake_cycle("matched semantic evaluation probe")

    state_before = store.load_state("receiver")
    oracle = paired_oracle(
        state=state_before,
        seed=seed,
        step_index=state_before.dynamic_steps,
    )

    organism.autonomous_wake_cycle()
    state_after = store.load_state("receiver")
    event = store.recent_events("receiver", 1)[0]
    selection = event["payload"]["self_selection"]

    chosen_signal = float(selection["chosen_signal"])
    actual_distance = abs(state_after.dynamic_state - state_after.attractor)

    semantic_events = store.recent_events("receiver", 2)
    wake_event = semantic_events[1]

    return {
        "policy": policy,
        "bridge_enabled": bridge_enabled,
        "chosen_signal": chosen_signal,
        "oracle_signal": oracle["oracle_signal"],
        "oracle_distance": oracle["oracle_distance"],
        "actual_distance": actual_distance,
        "regret": actual_distance - oracle["oracle_distance"],
        "oracle_hit": chosen_signal == oracle["oracle_signal"],
        "predictions": selection["candidates"],
        "semantic_bridge": wake_event["payload"].get("semantic_bridge"),
        "before_state": state_before.dynamic_state,
        "after_state": state_after.dynamic_state,
        "before_steps": state_before.dynamic_steps,
        "post_semantic_signal": state_before.dynamic_last_input,
    }


def sign_permutation_p(values: np.ndarray, permutations: int = 20000, seed: int = 59001) -> float:
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return 1.0
    observed = abs(float(values.mean()))
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.array([-1.0, 1.0]), size=(permutations, len(values)))
    null = np.abs((signs * values).mean(axis=1))
    return float((np.count_nonzero(null >= observed) + 1) / (permutations + 1))


def summarize(rows: list[dict]) -> dict:
    def arr(path):
        values = []
        for row in rows:
            value = row
            for key in path:
                value = value[key]
            values.append(float(value))
        return np.asarray(values, dtype=float)

    self_off = arr(("bridge_off", "self_model", "regret"))
    random_off = arr(("bridge_off", "random_control", "regret"))
    self_on = arr(("bridge_on", "self_model", "regret"))
    random_on = arr(("bridge_on", "random_control", "regret"))

    advantage_off = random_off - self_off
    advantage_on = random_on - self_on
    interaction = advantage_on - advantage_off

    return {
        "experiment": "organism_semantic_self_model_v59",
        "replicates": len(rows),
        "candidate_signals": list(CANDIDATE_SIGNALS),
        "evaluation_memory": EVAL_MEMORY,
        "self_model_mean_regret_bridge_off": float(self_off.mean()),
        "random_mean_regret_bridge_off": float(random_off.mean()),
        "self_model_mean_regret_bridge_on": float(self_on.mean()),
        "random_mean_regret_bridge_on": float(random_on.mean()),
        "selection_advantage_bridge_off": float(advantage_off.mean()),
        "selection_advantage_bridge_on": float(advantage_on.mean()),
        "interaction_self_model_advantage_on_minus_off": float(interaction.mean()),
        "interaction_median": float(np.median(interaction)),
        "interaction_sign_flip_p": sign_permutation_p(interaction),
        "self_model_oracle_hit_rate_bridge_off": float(
            np.mean([row["bridge_off"]["self_model"]["oracle_hit"] for row in rows])
        ),
        "random_oracle_hit_rate_bridge_off": float(
            np.mean([row["bridge_off"]["random_control"]["oracle_hit"] for row in rows])
        ),
        "self_model_oracle_hit_rate_bridge_on": float(
            np.mean([row["bridge_on"]["self_model"]["oracle_hit"] for row in rows])
        ),
        "random_oracle_hit_rate_bridge_on": float(
            np.mean([row["bridge_on"]["random_control"]["oracle_hit"] for row in rows])
        ),
        "semantic_state_delta_mean": float(
            np.mean([
                abs(
                    row["bridge_on"]["self_model"]["before_state"]
                    - row["bridge_off"]["self_model"]["before_state"]
                )
                for row in rows
            ])
        ),
        "semantic_signal_delta_mean": float(
            np.mean([
                abs(
                    row["bridge_on"]["self_model"]["post_semantic_signal"]
                    - row["bridge_off"]["self_model"]["post_semantic_signal"]
                )
                for row in rows
            ])
        ),
        "effect_positive_for_interaction": bool(interaction.mean() > 0),
        "all_predictions_have_two_candidates": all(
            len(row["bridge_off"]["self_model"]["predictions"]) == 2
            and len(row["bridge_on"]["self_model"]["predictions"]) == 2
            and len(row["bridge_off"]["random_control"]["predictions"]) == 2
            and len(row["bridge_on"]["random_control"]["predictions"]) == 2
            for row in rows
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=24)
    parser.add_argument("--warmup", type=int, default=32)
    parser.add_argument(
        "--out",
        default="results/organism_semantic_self_model_v59",
    )
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    rows = []

    for replicate in range(args.replicates):
        seed = 7901 + replicate
        bases = {}
        for bridge_enabled, label in ((False, "bridge_off"), (True, "bridge_on")):
            base = out / f"base_{label}_{replicate}.db"
            make_base(base, seed, bridge_enabled, args.warmup)
            bases[label] = base

        row = {"replicate": replicate, "seed": seed}
        for label, bridge_enabled in (
            ("bridge_off", False),
            ("bridge_on", True),
        ):
            self_db = out / f"{label}_self_{replicate}.db"
            random_db = out / f"{label}_random_{replicate}.db"
            shutil.copy2(bases[label], self_db)
            shutil.copy2(bases[label], random_db)

            row[label] = {
                "self_model": run_arm(
                    self_db,
                    seed=seed,
                    bridge_enabled=bridge_enabled,
                    policy="self_model",
                ),
                "random_control": run_arm(
                    random_db,
                    seed=seed,
                    bridge_enabled=bridge_enabled,
                    policy="random",
                ),
            }

        row["selection_advantage_bridge_off"] = (
            row["bridge_off"]["random_control"]["regret"]
            - row["bridge_off"]["self_model"]["regret"]
        )
        row["selection_advantage_bridge_on"] = (
            row["bridge_on"]["random_control"]["regret"]
            - row["bridge_on"]["self_model"]["regret"]
        )
        row["interaction"] = (
            row["selection_advantage_bridge_on"]
            - row["selection_advantage_bridge_off"]
        )
        rows.append(row)

    summary = summarize(rows)

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

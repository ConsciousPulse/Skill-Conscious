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
from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.self_observer import SelfObserver
from src.ontto.self_policy import SelfPolicy
from src.ontto.storage import MemoryStore

SIGNALS = (-1.0, 0.0, 1.0)


class NullProvider:
    def chat(self, messages, temperature=0.7):
        return LLMResponse(
            text="DREAM_SUMMARY: controlled internal cycle.",
            raw={"dummy": True},
        )


def train_observer_and_policy(seed, observer_samples, train_episodes):
    observer = SelfObserver(ridge=1e-3, max_samples=2048)
    bridge = DynamicStateBridge(DynamicsConfig(), seed=seed)
    rng = np.random.default_rng(seed)
    previous = state = memory = pressure = 0.0
    step = 0

    for _ in range(observer_samples):
        signal = float(rng.choice(SIGNALS))
        features = SelfObserver.features_for(
            previous_state=previous,
            state=state,
            memory=memory,
            pressure=pressure,
            last_input=signal,
            attractor_distance=abs(state),
            steps_delta=1,
        )
        snap = bridge.advance(
            previous_state=previous,
            state=state,
            memory=memory,
            pressure=pressure,
            signal=signal,
            steps=1,
            step_index=step,
        )
        observer.observe(features=features, actual_state=snap.state)
        previous = snap.previous_state
        state = snap.state
        memory = snap.memory
        pressure = snap.pressure
        step = snap.steps

    policy = SelfPolicy(ridge=1e-3)
    for episode in range(train_episodes):
        train_bridge = DynamicStateBridge(
            DynamicsConfig(), seed=seed + 100 + episode
        )
        episode_state = float(rng.uniform(-0.8, 0.8))
        for step in range(16):
            for signal in SIGNALS:
                prediction = observer.predict(
                    previous_state=episode_state,
                    state=episode_state,
                    memory=0.0,
                    pressure=0.0,
                    last_input=signal,
                    attractor_distance=abs(
                        episode_state - train_bridge.cfg.attractor
                    ),
                    steps_delta=1,
                )
                snap = train_bridge.advance(
                    previous_state=episode_state,
                    state=episode_state,
                    memory=0.0,
                    pressure=0.0,
                    signal=signal,
                    steps=1,
                    step_index=step,
                )
                utility = -(
                    0.70
                    * abs(snap.state - train_bridge.cfg.attractor)
                    + 0.30 * abs(snap.state - episode_state)
                )
                policy.observe(
                    SelfPolicy.features_for(
                        current_state=episode_state,
                        attractor_distance=abs(
                            episode_state - train_bridge.cfg.attractor
                        ),
                        predicted_state=prediction.predicted_state,
                        predicted_displacement=abs(
                            prediction.predicted_state - episode_state
                        ),
                        signal=signal,
                    ),
                    utility,
                )
            chosen_signal = float(rng.choice(SIGNALS))
            chosen = train_bridge.advance(
                previous_state=episode_state,
                state=episode_state,
                memory=0.0,
                pressure=0.0,
                signal=chosen_signal,
                steps=1,
                step_index=step,
            )
            episode_state = chosen.state

    return observer, policy


def seed_condition(path, seed, policy, condition_signal, observer):
    store = MemoryStore(path)
    cfg = OrganismConfig(
        agent_id="organism",
        dynamic_seed=seed,
        self_observer_enabled=True,
        self_selection_enabled=True,
        self_policy_enabled=False,
        dream_every_cycles=10_000,
    )
    organism = PersistentOrganism(cfg, store, NullProvider(), lambda _: None)
    organism.self_observer = observer
    organism._advance_dynamic(condition_signal, 1)
    store.save_self_observer_model("organism", observer.to_dict())
    store.save_self_policy_model("organism", policy.to_dict())
    store.save_state("organism", organism.state)
    store.conn.close()


def ablate_semantic_surfaces(path):
    store = MemoryStore(path)
    for table in (
        "memories",
        "events",
        "dream_cycles",
        "snapshots",
        "dynamic_snapshots",
        "self_observer_snapshots",
        "input_queue",
    ):
        store.conn.execute(
            f"DELETE FROM {table} WHERE agent_id='organism'"
        )
    state = store.load_state("organism")
    state.self_model = ""
    state.self_model_version = 0
    state.last_thought = ""
    state.memory_strength = 0.0
    state.dynamic_memory = 0.0
    state.dynamic_pressure = 0.0
    state.dynamic_last_input = 0.0
    state.mode = "WAKE"
    store.save_state("organism", state)
    store.conn.close()


def run_persistent_cycle(path, seed, learned, blind):
    store = MemoryStore(path)
    cfg = OrganismConfig(
        agent_id="organism",
        dynamic_seed=seed,
        self_observer_enabled=True,
        self_selection_enabled=True,
        self_selection_policy="self_model",
        self_policy_enabled=learned,
        dream_every_cycles=10_000,
        dynamic_autonomous_steps=1,
    )
    organism = PersistentOrganism(cfg, store, NullProvider(), lambda _: None)
    model_loaded = store.load_self_observer_model("organism") is not None
    policy_loaded = store.load_self_policy_model("organism") is not None

    organism.dream_cycle()
    if blind:
        organism.state.dynamic_prev_state = 0.0
        organism.state.dynamic_state = 0.0
        organism.state.dynamic_memory = 0.0
        organism.state.dynamic_pressure = 0.0
        organism.state.dynamic_attractor_distance = 0.0
        organism.state.dynamic_last_input = 0.0
        store.save_state("organism", organism.state)

    organism.autonomous_wake_cycle()
    event = store.recent_events("organism", 1)[0]
    selection = event["payload"]["self_selection"]
    result = {
        "policy_enabled": learned,
        "policy_loaded": policy_loaded,
        "self_model_loaded": model_loaded,
        "chosen_signal": float(selection["chosen_signal"]),
        "policy": selection["policy"],
        "candidate_count": len(selection["candidates"]),
        "policy_samples": int(selection.get("self_policy_samples", 0)),
        "memory_count": store.memory_count("organism"),
        "self_model_empty": organism.state.self_model == "",
        "boot_count": organism.state.boot_count,
    }
    store.conn.close()
    return result


def swap_dynamic_core(path, source_path):
    target = MemoryStore(path)
    source = MemoryStore(source_path)
    target_state = target.load_state("organism")
    source_state = source.load_state("organism")
    for field in (
        "dynamic_prev_state",
        "dynamic_state",
        "dynamic_steps",
        "dynamic_memory",
        "dynamic_pressure",
        "dynamic_attractor_distance",
        "dynamic_last_input",
    ):
        setattr(target_state, field, getattr(source_state, field))
    target.save_state("organism", target_state)
    target.conn.close()
    source.conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicates", type=int, default=24)
    ap.add_argument("--observer-samples", type=int, default=256)
    ap.add_argument("--train-episodes", type=int, default=64)
    ap.add_argument("--out", default="results/organism_integrated_self_policy_v73")
    args = ap.parse_args()

    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    rows = []
    loaded_ok = []
    integrated_ok = []
    blind_changes = []
    state_swaps = []

    for replicate in range(args.replicates):
        seed = 73001 + replicate
        observer, policy = train_observer_and_policy(
            seed, args.observer_samples, args.train_episodes
        )

        stable_db = out / f"stable_{replicate}.db"
        frontier_db = out / f"frontier_{replicate}.db"
        seed_condition(stable_db, seed, policy, -1.0, observer)
        seed_condition(frontier_db, seed, policy, 1.0, observer)
        ablate_semantic_surfaces(stable_db)
        ablate_semantic_surfaces(frontier_db)

        stable = run_persistent_cycle(
            stable_db, seed, learned=True, blind=False
        )
        frontier = run_persistent_cycle(
            frontier_db, seed, learned=True, blind=False
        )
        stable_blind = run_persistent_cycle(
            stable_db, seed, learned=True, blind=True
        )
        frontier_blind = run_persistent_cycle(
            frontier_db, seed, learned=True, blind=True
        )

        loaded_ok.append(
            stable["policy_loaded"]
            and frontier["policy_loaded"]
            and stable["self_model_loaded"]
            and frontier["self_model_loaded"]
        )
        integrated_ok.append(
            stable["policy"] == "learned_self_policy"
            and frontier["policy"] == "learned_self_policy"
            and stable["candidate_count"] == 3
            and frontier["candidate_count"] == 3
            and stable["policy_samples"] > 0
            and frontier["policy_samples"] > 0
            and stable["memory_count"] == 0
            and frontier["memory_count"] == 0
            and stable["self_model_empty"]
            and frontier["self_model_empty"]
        )
        blind_changes.append(
            (
                int(stable["chosen_signal"] != stable_blind["chosen_signal"])
                + int(frontier["chosen_signal"] != frontier_blind["chosen_signal"])
            )
            / 2.0
        )

        stable_swap_db = out / f"stable_swap_{replicate}.db"
        frontier_swap_db = out / f"frontier_swap_{replicate}.db"
        shutil.copy2(stable_db, stable_swap_db)
        shutil.copy2(frontier_db, frontier_swap_db)
        swap_dynamic_core(stable_swap_db, frontier_db)
        swap_dynamic_core(frontier_swap_db, stable_db)

        stable_swap = run_persistent_cycle(
            stable_swap_db, seed, learned=True, blind=False
        )
        frontier_swap = run_persistent_cycle(
            frontier_swap_db, seed, learned=True, blind=False
        )
        state_swaps.append(
            (
                int(stable_swap["chosen_signal"] != stable["chosen_signal"])
                + int(frontier_swap["chosen_signal"] != frontier["chosen_signal"])
            )
            / 2.0
        )

        rows.append(
            {
                "replicate": replicate,
                "stable_action": stable["chosen_signal"],
                "frontier_action": frontier["chosen_signal"],
                "stable_blind_action": stable_blind["chosen_signal"],
                "frontier_blind_action": frontier_blind["chosen_signal"],
                "stable_swap_action": stable_swap["chosen_signal"],
                "frontier_swap_action": frontier_swap["chosen_signal"],
            }
        )

    summary = {
        "experiment": "organism_integrated_self_policy_v73",
        "replicates": args.replicates,
        "observer_samples": args.observer_samples,
        "train_episodes": args.train_episodes,
        "policy_persisted_inside_organism_store": True,
        "model_and_policy_recovered_after_restart": bool(
            np.mean(loaded_ok) == 1.0
        ),
        "learned_policy_used_automatically_after_sleep": bool(
            np.mean(integrated_ok) == 1.0
        ),
        "mean_blind_action_change": float(np.mean(blind_changes)),
        "mean_causal_state_swap_change": float(np.mean(state_swaps)),
        "semantic_input_during_probe": False,
        "manual_policy_copy_after_restart": False,
        "objective_remains_externally_defined": True,
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

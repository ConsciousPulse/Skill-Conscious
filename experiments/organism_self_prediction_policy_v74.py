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
from src.ontto.self_policy import SelfPolicy
from src.ontto.trajectory_selector import TrajectorySelector


SIGNALS = (-1.0, 0.0, 1.0)


def train_self_observer(seed: int, samples: int) -> SelfObserver:
    observer = SelfObserver(ridge=1e-3, max_samples=2048)
    bridge = DynamicStateBridge(DynamicsConfig(), seed=seed)
    rng = np.random.default_rng(seed)

    previous = 0.0
    state = 0.0
    memory = 0.0
    pressure = 0.0
    step_index = 0

    for _ in range(samples):
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
        snapshot = bridge.advance(
            previous_state=previous,
            state=state,
            memory=memory,
            pressure=pressure,
            signal=signal,
            steps=1,
            step_index=step_index,
        )
        observer.observe(features=features, actual_state=snapshot.state)

        previous = snapshot.previous_state
        state = snapshot.state
        memory = snapshot.memory
        pressure = snapshot.pressure
        step_index = snapshot.steps

    return observer


def candidate_features(
    observer: SelfObserver,
    *,
    state: float,
    signal: float,
) -> dict[str, float]:
    prediction = observer.predict(
        previous_state=state,
        state=state,
        memory=0.0,
        pressure=0.0,
        last_input=signal,
        attractor_distance=abs(state),
        steps_delta=1,
    )
    return {
        "current_state": float(state),
        "attractor_distance": 0.0,
        "predicted_state": float(prediction.predicted_state),
        "predicted_displacement": float(
            abs(prediction.predicted_state - state)
        ),
        "signal": float(signal),
    }


def self_prediction_utility(
    observer: SelfObserver,
    bridge: DynamicStateBridge,
    *,
    state: float,
    signal: float,
    step_index: int,
) -> tuple[dict[str, float], float]:
    features = candidate_features(observer, state=state, signal=signal)
    prediction = features["predicted_state"]

    snapshot = bridge.advance(
        previous_state=state,
        state=state,
        memory=0.0,
        pressure=0.0,
        signal=signal,
        steps=1,
        step_index=step_index,
    )
    actual = float(snapshot.state)

    model_error = abs(actual - prediction)
    persistence_baseline_error = abs(actual - state)

    # Self-referential objective:
    # how much better did the organism predict its own next state than
    # simply assuming that its current state would persist?
    utility = persistence_baseline_error - model_error

    return {
        **features,
        "actual_next_state": actual,
        "model_prediction_error": float(model_error),
        "persistence_baseline_error": float(persistence_baseline_error),
    }, float(utility)


def train_self_policy(
    observer: SelfObserver,
    *,
    seed: int,
    episodes: int,
    steps_per_episode: int,
) -> SelfPolicy:
    policy = SelfPolicy(ridge=1e-3)
    rng = np.random.default_rng(seed)

    for episode in range(episodes):
        bridge = DynamicStateBridge(
            DynamicsConfig(),
            seed=seed + episode,
        )
        state = float(rng.uniform(-0.8, 0.8))

        for step_index in range(steps_per_episode):
            for signal in SIGNALS:
                features, utility = self_prediction_utility(
                    observer,
                    bridge,
                    state=state,
                    signal=signal,
                    step_index=step_index,
                )
                policy.observe(
                    SelfPolicy.features_for(
                        current_state=features["current_state"],
                        attractor_distance=features["attractor_distance"],
                        predicted_state=features["predicted_state"],
                        predicted_displacement=features["predicted_displacement"],
                        signal=features["signal"],
                    ),
                    utility,
                )

            exploration_signal = float(rng.choice(SIGNALS))
            snapshot = bridge.advance(
                previous_state=state,
                state=state,
                memory=0.0,
                pressure=0.0,
                signal=exploration_signal,
                steps=1,
                step_index=step_index,
            )
            state = snapshot.state

    return policy


def choose_learned_policy(
    policy: SelfPolicy,
    observer: SelfObserver,
    *,
    state: float,
    state_blind: bool,
) -> float:
    effective_state = 0.0 if state_blind else state
    candidates = [
        candidate_features(
            observer,
            state=effective_state,
            signal=signal,
        )
        for signal in SIGNALS
    ]
    return float(policy.choose(candidates)["signal"])


def choose_fixed_policy(
    observer: SelfObserver,
    *,
    state: float,
) -> float:
    selector = TrajectorySelector(
        attractor_weight=0.70,
        coherence_weight=0.30,
    )
    candidates = selector.evaluate(
        observer,
        current_state=state,
        current_memory=0.0,
        current_pressure=0.0,
        current_input=0.0,
        current_attractor=0.0,
        steps_delta=1,
        signals=SIGNALS,
    )
    return float(selector.choose(candidates).signal)


def run_policy(
    *,
    policy: SelfPolicy,
    observer: SelfObserver,
    seed: int,
    episodes: int,
    state_blind: bool,
) -> tuple[float, list[float]]:
    episode_scores = []

    for episode in range(episodes):
        bridge = DynamicStateBridge(
            DynamicsConfig(),
            seed=seed + episode,
        )
        rng = np.random.default_rng(seed + 5000 + episode)
        state = float(rng.uniform(-0.8, 0.8))
        total = 0.0

        for step_index in range(16):
            signal = choose_learned_policy(
                policy,
                observer,
                state=state,
                state_blind=state_blind,
            )
            snapshot = bridge.advance(
                previous_state=state,
                state=state,
                memory=0.0,
                pressure=0.0,
                signal=signal,
                steps=1,
                step_index=step_index,
            )

            total += (
                abs(snapshot.state - state)
                - abs(snapshot.state - state)
                + 0.0
            )
            state = snapshot.state

        # Re-run the same trajectory conceptually as a measured self-prediction
        # score: score the final system state against its own persistence baseline.
        final_prediction = observer.predict(
            previous_state=state,
            state=state,
            memory=0.0,
            pressure=0.0,
            last_input=0.0,
            attractor_distance=abs(state),
            steps_delta=1,
        )
        total = -abs(final_prediction.predicted_state - state)
        episode_scores.append(total)

    return float(np.mean(episode_scores)), episode_scores


def run_direct_self_gain(
    *,
    observer: SelfObserver,
    seed: int,
    episodes: int,
    learned_policy: SelfPolicy | None,
    state_blind: bool,
) -> tuple[float, list[float]]:
    scores = []

    for episode in range(episodes):
        bridge = DynamicStateBridge(
            DynamicsConfig(),
            seed=seed + episode,
        )
        rng = np.random.default_rng(seed + 9000 + episode)
        state = float(rng.uniform(-0.8, 0.8))
        episode_gain = []

        for step_index in range(16):
            if learned_policy is not None:
                signal = choose_learned_policy(
                    learned_policy,
                    observer,
                    state=state,
                    state_blind=state_blind,
                )
            else:
                signal = float(rng.choice(SIGNALS))

            features = candidate_features(
                observer,
                state=0.0 if state_blind else state,
                signal=signal,
            )
            snapshot = bridge.advance(
                previous_state=state,
                state=state,
                memory=0.0,
                pressure=0.0,
                signal=signal,
                steps=1,
                step_index=step_index,
            )

            actual = float(snapshot.state)
            model_error = abs(actual - features["predicted_state"])
            baseline_error = abs(actual - (0.0 if state_blind else state))
            episode_gain.append(baseline_error - model_error)
            state = actual

        scores.append(float(np.mean(episode_gain)))

    return float(np.mean(scores)), scores


def sign_p(values: np.ndarray, seed: int) -> float:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return 1.0
    observed = abs(float(values.mean()))
    rng = np.random.default_rng(seed)
    signs = rng.choice(
        np.asarray([-1.0, 1.0]),
        size=(20000, values.size),
    )
    null = np.abs((signs * values).mean(axis=1))
    return float((np.count_nonzero(null >= observed) + 1) / 20001)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=64)
    ap.add_argument("--train-episodes", type=int, default=64)
    ap.add_argument("--observer-samples", type=int, default=512)
    ap.add_argument(
        "--out",
        default="results/organism_self_prediction_policy_v74",
    )
    args = ap.parse_args()

    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    observer = train_self_observer(
        seed=74001,
        samples=args.observer_samples,
    )
    policy = train_self_policy(
        observer,
        seed=74002,
        episodes=args.train_episodes,
        steps_per_episode=16,
    )

    policy_path = out / "self_prediction_policy.json"
    policy_path.write_text(
        json.dumps(policy.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    restored_policy = SelfPolicy.from_dict(
        json.loads(policy_path.read_text(encoding="utf-8"))
    )

    learned_gain, learned_rows = run_direct_self_gain(
        observer=observer,
        seed=74003,
        episodes=args.episodes,
        learned_policy=restored_policy,
        state_blind=False,
    )
    blind_gain, blind_rows = run_direct_self_gain(
        observer=observer,
        seed=74003,
        episodes=args.episodes,
        learned_policy=restored_policy,
        state_blind=True,
    )
    random_gain, random_rows = run_direct_self_gain(
        observer=observer,
        seed=74003,
        episodes=args.episodes,
        learned_policy=None,
        state_blind=False,
    )

    learned = np.asarray(learned_rows)
    blind = np.asarray(blind_rows)
    random = np.asarray(random_rows)

    fixed_signal_rows = []
    for episode in range(args.episodes):
        bridge = DynamicStateBridge(
            DynamicsConfig(),
            seed=74003 + episode,
        )
        rng = np.random.default_rng(78000 + episode)
        state = float(rng.uniform(-0.8, 0.8))
        gains = []
        for step_index in range(16):
            signal = choose_fixed_policy(observer, state=state)
            features = candidate_features(
                observer,
                state=state,
                signal=signal,
            )
            snapshot = bridge.advance(
                previous_state=state,
                state=state,
                memory=0.0,
                pressure=0.0,
                signal=signal,
                steps=1,
                step_index=step_index,
            )
            actual = float(snapshot.state)
            gains.append(
                abs(actual - state)
                - abs(actual - features["predicted_state"])
            )
            state = actual
        fixed_signal_rows.append(float(np.mean(gains)))

    fixed = np.asarray(fixed_signal_rows)

    summary = {
        "experiment": "organism_self_prediction_policy_v74",
        "episodes": args.episodes,
        "train_episodes": args.train_episodes,
        "observer_samples": args.observer_samples,
        "policy_reloaded_without_retraining": True,
        "learned_self_prediction_gain": learned_gain,
        "blinded_self_prediction_gain": float(blind.mean()),
        "fixed_self_prediction_gain": float(fixed.mean()),
        "random_self_prediction_gain": float(random.mean()),
        "learned_minus_blind_p": sign_p(learned - blind, 74071),
        "learned_minus_fixed_p": sign_p(learned - fixed, 74072),
        "learned_minus_random_p": sign_p(learned - random, 74073),
        "objective_is_self_referential": True,
        "objective_is_still_protocol_defined": True,
        "external_attractor_target_removed_from_primary_objective": True,
        "semantic_input_during_probe": False,
    }

    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

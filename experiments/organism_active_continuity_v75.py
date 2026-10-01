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
PERTURBATION = 0.50
WARMUP_STEPS = 8
RECOVERY_STEPS = 12


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


def self_prediction_gain(
    observer: SelfObserver,
    bridge: DynamicStateBridge,
    *,
    state: float,
    signal: float,
    step_index: int,
) -> tuple[dict[str, float], float]:
    features = candidate_features(observer, state=state, signal=signal)
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
    persistence_error = abs(actual - state)
    return (
        {
            **features,
            "actual_next_state": actual,
            "model_prediction_error": float(model_error),
            "persistence_baseline_error": float(persistence_error),
        },
        float(persistence_error - model_error),
    )


def train_recovery_policy(
    observer: SelfObserver,
    *,
    seed: int,
    episodes: int,
    recovery_steps: int,
) -> SelfPolicy:
    policy = SelfPolicy(ridge=1e-3)
    rng = np.random.default_rng(seed)

    for episode in range(episodes):
        bridge = DynamicStateBridge(DynamicsConfig(), seed=seed + episode)
        state = float(rng.uniform(-0.8, 0.8))

        for step_index in range(WARMUP_STEPS):
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

        perturbation = float(
            rng.choice(np.asarray([-PERTURBATION, PERTURBATION]))
        )
        state = float(np.clip(state + perturbation, -1.0, 1.0))

        for recovery_index in range(recovery_steps):
            step_index = WARMUP_STEPS + recovery_index
            for signal in SIGNALS:
                features, utility = self_prediction_gain(
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
        candidate_features(observer, state=effective_state, signal=signal)
        for signal in SIGNALS
    ]
    return float(policy.choose(candidates)["signal"])


def choose_fixed_policy(observer: SelfObserver, *, state: float) -> float:
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


def warmup_state(
    bridge: DynamicStateBridge,
    *,
    seed: int,
) -> tuple[float, int]:
    rng = np.random.default_rng(seed)
    state = float(rng.uniform(-0.8, 0.8))
    for step_index in range(WARMUP_STEPS):
        snapshot = bridge.advance(
            previous_state=state,
            state=state,
            memory=0.0,
            pressure=0.0,
            signal=float(rng.choice(SIGNALS)),
            steps=1,
            step_index=step_index,
        )
        state = snapshot.state
    return state, WARMUP_STEPS


def recovery_episode(
    *,
    policy: SelfPolicy | None,
    observer: SelfObserver,
    seed: int,
    state_blind: bool = False,
    fixed: bool = False,
    random_policy: bool = False,
    perturbation: float = PERTURBATION,
    recovery_steps: int = RECOVERY_STEPS,
) -> dict[str, float | list[float]]:
    bridge = DynamicStateBridge(DynamicsConfig(), seed=seed)
    state, step_index = warmup_state(bridge, seed=seed + 1000)
    reference_state = float(state)
    pre_perturbation_action = (
        choose_learned_policy(
            policy,
            observer,
            state=reference_state,
            state_blind=state_blind,
        )
        if policy is not None
        else 0.0
    )
    state = float(np.clip(state + perturbation, -1.0, 1.0))

    rng = np.random.default_rng(seed + 5000)
    gains = []
    continuity_scores = []
    actions = []

    for offset in range(recovery_steps):
        current_step = step_index + offset
        if fixed:
            signal = choose_fixed_policy(observer, state=state)
        elif random_policy:
            signal = float(rng.choice(SIGNALS))
        else:
            if policy is None:
                raise ValueError("policy is required unless random_policy=True")
            signal = choose_learned_policy(
                policy,
                observer,
                state=state,
                state_blind=state_blind,
            )

        _, gain = self_prediction_gain(
            observer,
            bridge,
            state=state,
            signal=signal,
            step_index=current_step,
        )
        snapshot = bridge.advance(
            previous_state=state,
            state=state,
            memory=0.0,
            pressure=0.0,
            signal=signal,
            steps=1,
            step_index=current_step,
        )

        actual = float(snapshot.state)
        gains.append(float(gain))
        continuity_scores.append(
            float(1.0 / (1.0 + abs(actual - reference_state)))
        )
        actions.append(float(signal))
        state = actual

    first_action = actions[0]
    return {
        "mean_recovery_self_prediction_gain": float(np.mean(gains)),
        "mean_continuity_index": float(np.mean(continuity_scores)),
        "final_continuity_index": float(continuity_scores[-1]),
        "first_action": float(first_action),
        "pre_perturbation_action": float(pre_perturbation_action),
        "action_response": float(first_action != pre_perturbation_action),
        "mean_abs_action": float(np.mean(np.abs(actions))),
        "actions": actions,
        "perturbation": float(perturbation),
    }


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


def run_first_action_response(
    *,
    policy: SelfPolicy,
    observer: SelfObserver,
    seed: int,
    state_blind: bool,
) -> float:
    positive = recovery_episode(
        policy=policy,
        observer=observer,
        seed=seed,
        state_blind=state_blind,
        perturbation=PERTURBATION,
        recovery_steps=1,
    )["first_action"]
    negative = recovery_episode(
        policy=policy,
        observer=observer,
        seed=seed,
        state_blind=state_blind,
        perturbation=-PERTURBATION,
        recovery_steps=1,
    )["first_action"]
    return float(positive != negative)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=64)
    ap.add_argument("--train-episodes", type=int, default=64)
    ap.add_argument("--observer-samples", type=int, default=512)
    ap.add_argument("--recovery-steps", type=int, default=RECOVERY_STEPS)
    ap.add_argument(
        "--out",
        default="results/organism_active_continuity_v75",
    )
    args = ap.parse_args()

    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    observer = train_self_observer(seed=75001, samples=args.observer_samples)
    policy = train_recovery_policy(
        observer,
        seed=75002,
        episodes=args.train_episodes,
        recovery_steps=args.recovery_steps,
    )

    policy_path = out / "active_continuity_policy.json"
    policy_path.write_text(
        json.dumps(policy.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    restored_policy = SelfPolicy.from_dict(
        json.loads(policy_path.read_text(encoding="utf-8"))
    )

    learned_rows = [
        recovery_episode(
            policy=restored_policy,
            observer=observer,
            seed=75003 + episode,
            recovery_steps=args.recovery_steps,
        )
        for episode in range(args.episodes)
    ]
    blind_rows = [
        recovery_episode(
            policy=restored_policy,
            observer=observer,
            seed=75003 + episode,
            state_blind=True,
            recovery_steps=args.recovery_steps,
        )
        for episode in range(args.episodes)
    ]
    fixed_rows = [
        recovery_episode(
            policy=None,
            observer=observer,
            seed=75003 + episode,
            fixed=True,
            recovery_steps=args.recovery_steps,
        )
        for episode in range(args.episodes)
    ]
    random_rows = [
        recovery_episode(
            policy=None,
            observer=observer,
            seed=75003 + episode,
            random_policy=True,
            recovery_steps=args.recovery_steps,
        )
        for episode in range(args.episodes)
    ]

    learned_gain = np.asarray(
        [row["mean_recovery_self_prediction_gain"] for row in learned_rows],
        dtype=float,
    )
    blind_gain = np.asarray(
        [row["mean_recovery_self_prediction_gain"] for row in blind_rows],
        dtype=float,
    )
    fixed_gain = np.asarray(
        [row["mean_recovery_self_prediction_gain"] for row in fixed_rows],
        dtype=float,
    )
    random_gain = np.asarray(
        [row["mean_recovery_self_prediction_gain"] for row in random_rows],
        dtype=float,
    )

    learned_continuity = np.asarray(
        [row["mean_continuity_index"] for row in learned_rows],
        dtype=float,
    )
    blind_continuity = np.asarray(
        [row["mean_continuity_index"] for row in blind_rows],
        dtype=float,
    )
    fixed_continuity = np.asarray(
        [row["mean_continuity_index"] for row in fixed_rows],
        dtype=float,
    )
    random_continuity = np.asarray(
        [row["mean_continuity_index"] for row in random_rows],
        dtype=float,
    )

    response = np.asarray(
        [
            run_first_action_response(
                policy=restored_policy,
                observer=observer,
                seed=75003 + episode,
                state_blind=False,
            )
            for episode in range(args.episodes)
        ],
        dtype=float,
    )
    blind_response = np.asarray(
        [
            run_first_action_response(
                policy=restored_policy,
                observer=observer,
                seed=75003 + episode,
                state_blind=True,
            )
            for episode in range(args.episodes)
        ],
        dtype=float,
    )

    summary = {
        "experiment": "organism_active_continuity_v75",
        "episodes": args.episodes,
        "train_episodes": args.train_episodes,
        "observer_samples": args.observer_samples,
        "recovery_steps": args.recovery_steps,
        "perturbation_magnitude": PERTURBATION,
        "policy_reloaded_without_retraining": True,
        "learned_mean_recovery_self_prediction_gain": float(learned_gain.mean()),
        "blinded_mean_recovery_self_prediction_gain": float(blind_gain.mean()),
        "fixed_mean_recovery_self_prediction_gain": float(fixed_gain.mean()),
        "random_mean_recovery_self_prediction_gain": float(random_gain.mean()),
        "learned_minus_blind_recovery_gain_p": sign_p(
            learned_gain - blind_gain, 75071
        ),
        "learned_minus_fixed_recovery_gain_p": sign_p(
            learned_gain - fixed_gain, 75072
        ),
        "learned_minus_random_recovery_gain_p": sign_p(
            learned_gain - random_gain, 75073
        ),
        "learned_mean_continuity_index": float(learned_continuity.mean()),
        "blinded_mean_continuity_index": float(blind_continuity.mean()),
        "fixed_mean_continuity_index": float(fixed_continuity.mean()),
        "random_mean_continuity_index": float(random_continuity.mean()),
        "learned_minus_blind_continuity_p": sign_p(
            learned_continuity - blind_continuity, 75074
        ),
        "learned_minus_fixed_continuity_p": sign_p(
            learned_continuity - fixed_continuity, 75075
        ),
        "learned_minus_random_continuity_p": sign_p(
            learned_continuity - random_continuity, 75076
        ),
        "state_dependent_first_action_response_rate": float(response.mean()),
        "state_blind_first_action_response_rate": float(blind_response.mean()),
        "state_dependent_minus_blind_response_p": sign_p(
            response - blind_response, 75077
        ),
        "primary_objective_is_self_prediction_recovery": True,
        "continuity_index_is_secondary_evaluation_only": True,
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

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
TRAIN_PERTURBATIONS = (0.25, 0.75)
NARROW_TRAIN_PERTURBATIONS = (0.50,)
IN_DOMAIN_PERTURBATIONS = (0.25, 0.75)
OOD_PERTURBATIONS = (0.35, 0.55, 0.85)
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


def train_policy(
    observer: SelfObserver,
    *,
    seed: int,
    episodes: int,
    recovery_steps: int,
    perturbations: tuple[float, ...],
) -> SelfPolicy:
    policy = SelfPolicy(ridge=1e-3)
    rng = np.random.default_rng(seed)

    for episode in range(episodes):
        bridge = DynamicStateBridge(
            DynamicsConfig(),
            seed=seed + episode,
        )
        state, step_index = warmup_state(
            bridge,
            seed=seed + 1000 + episode,
        )
        perturbation = float(
            rng.choice(
                np.asarray(
                    [
                        -value
                        for value in perturbations
                    ]
                    + list(perturbations),
                    dtype=float,
                )
            )
        )
        state = float(np.clip(state + perturbation, -1.0, 1.0))

        for recovery_index in range(recovery_steps):
            current_step = step_index + recovery_index
            for signal in SIGNALS:
                features, utility = self_prediction_gain(
                    observer,
                    bridge,
                    state=state,
                    signal=signal,
                    step_index=current_step,
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
                step_index=current_step,
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


def recovery_episode(
    *,
    policy: SelfPolicy | None,
    observer: SelfObserver,
    seed: int,
    perturbation: float,
    state_blind: bool = False,
    fixed: bool = False,
    random_policy: bool = False,
    recovery_steps: int = RECOVERY_STEPS,
) -> dict[str, float | list[float]]:
    bridge = DynamicStateBridge(DynamicsConfig(), seed=seed)
    state, step_index = warmup_state(
        bridge,
        seed=seed + 1000,
    )
    reference_state = float(state)
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

    return {
        "mean_recovery_self_prediction_gain": float(np.mean(gains)),
        "mean_continuity_index": float(np.mean(continuity_scores)),
        "final_continuity_index": float(continuity_scores[-1]),
        "first_action": float(actions[0]),
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


def paired_rows(
    *,
    arm,
    observer: SelfObserver,
    policy: SelfPolicy | None,
    perturbations: tuple[float, ...],
    episodes: int,
    base_seed: int,
    state_blind: bool = False,
    fixed: bool = False,
    random_policy: bool = False,
) -> dict[float, dict[str, np.ndarray]]:
    result = {}
    for magnitude_index, magnitude in enumerate(perturbations):
        rows = []
        for episode in range(episodes):
            seed = base_seed + magnitude_index * 10000 + episode
            rows.append(
                arm(
                    policy=policy,
                    observer=observer,
                    seed=seed,
                    perturbation=magnitude,
                    state_blind=state_blind,
                    fixed=fixed,
                    random_policy=random_policy,
                )
            )
        result[magnitude] = {
            "gain": np.asarray(
                [row["mean_recovery_self_prediction_gain"] for row in rows],
                dtype=float,
            ),
            "continuity": np.asarray(
                [row["mean_continuity_index"] for row in rows],
                dtype=float,
            ),
        }
    return result


def flatten_metric(
    grouped: dict[float, dict[str, np.ndarray]],
    key: str,
) -> np.ndarray:
    return np.concatenate(
        [grouped[magnitude][key] for magnitude in grouped]
    )


def response_rate(
    policy: SelfPolicy,
    observer: SelfObserver,
    *,
    magnitude: float,
    episodes: int,
    state_blind: bool,
    base_seed: int,
) -> float:
    differences = []
    for episode in range(episodes):
        seed = base_seed + episode
        positive = recovery_episode(
            policy=policy,
            observer=observer,
            seed=seed,
            perturbation=magnitude,
            state_blind=state_blind,
            recovery_steps=1,
        )["first_action"]
        negative = recovery_episode(
            policy=policy,
            observer=observer,
            seed=seed,
            perturbation=-magnitude,
            state_blind=state_blind,
            recovery_steps=1,
        )["first_action"]
        differences.append(float(positive != negative))
    return float(np.mean(differences))


def summarize_generalization(
    *,
    learned: dict[float, dict[str, np.ndarray]],
    narrow: dict[float, dict[str, np.ndarray]],
    blind: dict[float, dict[str, np.ndarray]],
    fixed: dict[float, dict[str, np.ndarray]],
    random_policy: dict[float, dict[str, np.ndarray]],
    perturbations: tuple[float, ...],
) -> dict[str, float]:
    learned_gain = flatten_metric(learned, "gain")
    narrow_gain = flatten_metric(narrow, "gain")
    blind_gain = flatten_metric(blind, "gain")
    fixed_gain = flatten_metric(fixed, "gain")
    random_gain = flatten_metric(random_policy, "gain")

    learned_cont = flatten_metric(learned, "continuity")
    narrow_cont = flatten_metric(narrow, "continuity")
    blind_cont = flatten_metric(blind, "continuity")
    fixed_cont = flatten_metric(fixed, "continuity")
    random_cont = flatten_metric(random_policy, "continuity")

    train_key = tuple(IN_DOMAIN_PERTURBATIONS)
    ood_key = tuple(OOD_PERTURBATIONS)
    _ = train_key, ood_key

    id_learned = flatten_metric(
        {m: learned[m] for m in IN_DOMAIN_PERTURBATIONS},
        "gain",
    )
    id_random = flatten_metric(
        {m: random_policy[m] for m in IN_DOMAIN_PERTURBATIONS},
        "gain",
    )
    ood_learned = flatten_metric(
        {m: learned[m] for m in OOD_PERTURBATIONS},
        "gain",
    )
    ood_random = flatten_metric(
        {m: random_policy[m] for m in OOD_PERTURBATIONS},
        "gain",
    )
    id_advantage = float(np.mean(id_learned - id_random))
    ood_advantage = float(np.mean(ood_learned - ood_random))

    return {
        "learned_mean_gain_all": float(learned_gain.mean()),
        "narrow_mean_gain_all": float(narrow_gain.mean()),
        "blinded_mean_gain_all": float(blind_gain.mean()),
        "fixed_mean_gain_all": float(fixed_gain.mean()),
        "random_mean_gain_all": float(random_gain.mean()),
        "learned_minus_narrow_gain_p": sign_p(
            learned_gain - narrow_gain,
            76071,
        ),
        "learned_minus_blind_gain_p": sign_p(
            learned_gain - blind_gain,
            76072,
        ),
        "learned_minus_fixed_gain_p": sign_p(
            learned_gain - fixed_gain,
            76073,
        ),
        "learned_minus_random_gain_p": sign_p(
            learned_gain - random_gain,
            76074,
        ),
        "learned_mean_continuity_all": float(learned_cont.mean()),
        "narrow_mean_continuity_all": float(narrow_cont.mean()),
        "blinded_mean_continuity_all": float(blind_cont.mean()),
        "fixed_mean_continuity_all": float(fixed_cont.mean()),
        "random_mean_continuity_all": float(random_cont.mean()),
        "learned_minus_narrow_continuity_p": sign_p(
            learned_cont - narrow_cont,
            76075,
        ),
        "learned_minus_blind_continuity_p": sign_p(
            learned_cont - blind_cont,
            76076,
        ),
        "learned_minus_fixed_continuity_p": sign_p(
            learned_cont - fixed_cont,
            76077,
        ),
        "learned_minus_random_continuity_p": sign_p(
            learned_cont - random_cont,
            76078,
        ),
        "id_learned_minus_random_gain": id_advantage,
        "ood_learned_minus_random_gain": ood_advantage,
        "ood_minus_id_advantage": float(ood_advantage - id_advantage),
        "ood_advantage_retention_fraction": (
            float(ood_advantage / id_advantage)
            if abs(id_advantage) > 1e-12
            else float("nan")
        ),
        "ood_perturbation_count": float(len(perturbations)),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes-per-condition", type=int, default=64)
    ap.add_argument("--train-episodes", type=int, default=64)
    ap.add_argument("--observer-samples", type=int, default=512)
    ap.add_argument("--recovery-steps", type=int, default=RECOVERY_STEPS)
    ap.add_argument(
        "--out",
        default="results/organism_generalized_active_continuity_v76",
    )
    args = ap.parse_args()

    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    observer = train_self_observer(seed=76001, samples=args.observer_samples)

    generalized_policy = train_policy(
        observer,
        seed=76002,
        episodes=args.train_episodes,
        recovery_steps=args.recovery_steps,
        perturbations=TRAIN_PERTURBATIONS,
    )
    narrow_policy = train_policy(
        observer,
        seed=76003,
        episodes=args.train_episodes,
        recovery_steps=args.recovery_steps,
        perturbations=NARROW_TRAIN_PERTURBATIONS,
    )

    generalized_path = out / "generalized_policy.json"
    narrow_path = out / "narrow_policy.json"
    generalized_path.write_text(
        json.dumps(generalized_policy.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    narrow_path.write_text(
        json.dumps(narrow_policy.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    restored_generalized = SelfPolicy.from_dict(
        json.loads(generalized_path.read_text(encoding="utf-8"))
    )
    restored_narrow = SelfPolicy.from_dict(
        json.loads(narrow_path.read_text(encoding="utf-8"))
    )

    test_perturbations = IN_DOMAIN_PERTURBATIONS + OOD_PERTURBATIONS

    learned = paired_rows(
        arm=recovery_episode,
        observer=observer,
        policy=restored_generalized,
        perturbations=test_perturbations,
        episodes=args.episodes_per_condition,
        base_seed=76010,
    )
    narrow = paired_rows(
        arm=recovery_episode,
        observer=observer,
        policy=restored_narrow,
        perturbations=test_perturbations,
        episodes=args.episodes_per_condition,
        base_seed=76010,
    )
    blind = paired_rows(
        arm=recovery_episode,
        observer=observer,
        policy=restored_generalized,
        perturbations=test_perturbations,
        episodes=args.episodes_per_condition,
        base_seed=76010,
        state_blind=True,
    )
    fixed = paired_rows(
        arm=recovery_episode,
        observer=observer,
        policy=None,
        perturbations=test_perturbations,
        episodes=args.episodes_per_condition,
        base_seed=76010,
        fixed=True,
    )
    random_policy = paired_rows(
        arm=recovery_episode,
        observer=observer,
        policy=None,
        perturbations=test_perturbations,
        episodes=args.episodes_per_condition,
        base_seed=76010,
        random_policy=True,
    )

    summary = {
        "experiment": "organism_generalized_active_continuity_v76",
        "episodes_per_condition": args.episodes_per_condition,
        "train_episodes": args.train_episodes,
        "observer_samples": args.observer_samples,
        "recovery_steps": args.recovery_steps,
        "training_perturbations": list(TRAIN_PERTURBATIONS),
        "narrow_training_perturbation": list(NARROW_TRAIN_PERTURBATIONS),
        "in_domain_test_perturbations": list(IN_DOMAIN_PERTURBATIONS),
        "ood_test_perturbations": list(OOD_PERTURBATIONS),
        "policy_reloaded_without_retraining": True,
        **summarize_generalization(
            learned=learned,
            narrow=narrow,
            blind=blind,
            fixed=fixed,
            random_policy=random_policy,
            perturbations=OOD_PERTURBATIONS,
        ),
        "ood_state_dependent_first_action_response_rate": response_rate(
            restored_generalized,
            observer,
            magnitude=0.55,
            episodes=args.episodes_per_condition,
            state_blind=False,
            base_seed=76100,
        ),
        "ood_state_blind_first_action_response_rate": response_rate(
            restored_generalized,
            observer,
            magnitude=0.55,
            episodes=args.episodes_per_condition,
            state_blind=True,
            base_seed=76100,
        ),
        "objective_is_self_prediction_gain": True,
        "continuity_index_is_secondary_evaluation_only": True,
        "ood_perturbations_unseen_during_training": True,
        "generalization_is_evaluated_without_continuity_labels": True,
        "objective_is_still_protocol_defined": True,
        "external_attractor_target_removed_from_primary_objective": True,
        "semantic_input_during_probe": False,
    }

    condition_rows = {}
    for magnitude in test_perturbations:
        condition_rows[str(magnitude)] = {
            "learned_gain": float(learned[magnitude]["gain"].mean()),
            "narrow_gain": float(narrow[magnitude]["gain"].mean()),
            "blinded_gain": float(blind[magnitude]["gain"].mean()),
            "fixed_gain": float(fixed[magnitude]["gain"].mean()),
            "random_gain": float(random_policy[magnitude]["gain"].mean()),
            "learned_continuity": float(
                learned[magnitude]["continuity"].mean()
            ),
            "narrow_continuity": float(
                narrow[magnitude]["continuity"].mean()
            ),
            "blinded_continuity": float(
                blind[magnitude]["continuity"].mean()
            ),
            "fixed_continuity": float(
                fixed[magnitude]["continuity"].mean()
            ),
            "random_continuity": float(
                random_policy[magnitude]["continuity"].mean()
            ),
        }
    summary["conditions"] = condition_rows

    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

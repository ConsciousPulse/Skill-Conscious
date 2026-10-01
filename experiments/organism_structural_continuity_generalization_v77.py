from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
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
WARMUP_MIN = -0.25
WARMUP_MAX = 0.25

TRAIN_STRUCTURES = ("single_impulse",)
IN_DOMAIN_STRUCTURES = ("single_impulse",)
OOD_STRUCTURES = (
    "split_impulse",
    "reversal_pulse",
    "delayed_impulse",
)


@dataclass(frozen=True)
class DynamicContext:
    previous_state: float
    state: float
    memory: float
    pressure: float
    step_index: int


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
    context: DynamicContext,
    signal: float,
) -> tuple[dict[str, float], float, DynamicContext]:
    features = candidate_features(
        observer,
        state=context.state,
        signal=signal,
    )
    snapshot = bridge.advance(
        previous_state=context.previous_state,
        state=context.state,
        memory=context.memory,
        pressure=context.pressure,
        signal=signal,
        steps=1,
        step_index=context.step_index,
    )
    actual = float(snapshot.state)
    model_error = abs(actual - features["predicted_state"])
    persistence_error = abs(actual - context.state)
    return (
        {
            **features,
            "actual_next_state": actual,
            "model_prediction_error": float(model_error),
            "persistence_baseline_error": float(persistence_error),
        },
        float(persistence_error - model_error),
        DynamicContext(
            previous_state=float(snapshot.previous_state),
            state=float(snapshot.state),
            memory=float(snapshot.memory),
            pressure=float(snapshot.pressure),
            step_index=int(snapshot.steps),
        ),
    )


def warmup_context(
    bridge: DynamicStateBridge,
    *,
    seed: int,
) -> DynamicContext:
    rng = np.random.default_rng(seed)
    state = float(rng.uniform(WARMUP_MIN, WARMUP_MAX))
    context = DynamicContext(
        previous_state=state,
        state=state,
        memory=0.0,
        pressure=0.0,
        step_index=0,
    )

    for step_index in range(WARMUP_STEPS):
        snapshot = bridge.advance(
            previous_state=context.previous_state,
            state=context.state,
            memory=context.memory,
            pressure=context.pressure,
            signal=float(rng.choice(SIGNALS)),
            steps=1,
            step_index=step_index,
        )
        context = DynamicContext(
            previous_state=float(snapshot.previous_state),
            state=float(snapshot.state),
            memory=float(snapshot.memory),
            pressure=float(snapshot.pressure),
            step_index=int(snapshot.steps),
        )

    return context


def apply_perturbation_structure(
    bridge: DynamicStateBridge,
    *,
    context: DynamicContext,
    structure: str,
    sign: float,
) -> tuple[DynamicContext, float, float]:
    reference_state = float(context.state)
    delta = float(sign * PERTURBATION)
    target_state = float(np.clip(reference_state + delta, -1.0, 1.0))

    if structure == "single_impulse":
        return (
            DynamicContext(
                previous_state=context.state,
                state=target_state,
                memory=context.memory,
                pressure=context.pressure,
                step_index=context.step_index,
            ),
            reference_state,
            target_state,
        )

    if structure == "split_impulse":
        half = 0.5 * delta
        first_state = float(np.clip(context.state + half, -1.0, 1.0))
        mid = DynamicContext(
            previous_state=context.state,
            state=first_state,
            memory=context.memory,
            pressure=context.pressure,
            step_index=context.step_index,
        )
        natural = bridge.advance(
            previous_state=mid.previous_state,
            state=mid.state,
            memory=mid.memory,
            pressure=mid.pressure,
            signal=0.0,
            steps=1,
            step_index=mid.step_index,
        )
        second_context = DynamicContext(
            previous_state=float(natural.previous_state),
            state=float(natural.state),
            memory=float(natural.memory),
            pressure=float(natural.pressure),
            step_index=int(natural.steps),
        )
        return (
            DynamicContext(
                previous_state=second_context.state,
                state=target_state,
                memory=second_context.memory,
                pressure=second_context.pressure,
                step_index=second_context.step_index,
            ),
            reference_state,
            target_state,
        )

    if structure == "reversal_pulse":
        overshoot = 1.5 * delta
        first_state = float(np.clip(context.state + overshoot, -1.0, 1.0))
        mid = DynamicContext(
            previous_state=context.state,
            state=first_state,
            memory=context.memory,
            pressure=context.pressure,
            step_index=context.step_index,
        )
        natural = bridge.advance(
            previous_state=mid.previous_state,
            state=mid.state,
            memory=mid.memory,
            pressure=mid.pressure,
            signal=0.0,
            steps=1,
            step_index=mid.step_index,
        )
        return (
            DynamicContext(
                previous_state=float(natural.state),
                state=target_state,
                memory=float(natural.memory),
                pressure=float(natural.pressure),
                step_index=int(natural.steps),
            ),
            reference_state,
            target_state,
        )

    if structure == "delayed_impulse":
        natural = bridge.advance(
            previous_state=context.previous_state,
            state=context.state,
            memory=context.memory,
            pressure=context.pressure,
            signal=0.0,
            steps=1,
            step_index=context.step_index,
        )
        return (
            DynamicContext(
                previous_state=float(natural.state),
                state=target_state,
                memory=float(natural.memory),
                pressure=float(natural.pressure),
                step_index=int(natural.steps),
            ),
            reference_state,
            target_state,
        )

    raise ValueError(f"unknown perturbation structure: {structure}")


def train_policy(
    observer: SelfObserver,
    *,
    seed: int,
    episodes: int,
    recovery_steps: int,
) -> SelfPolicy:
    policy = SelfPolicy(ridge=1e-3)
    rng = np.random.default_rng(seed)

    for episode in range(episodes):
        bridge = DynamicStateBridge(
            DynamicsConfig(),
            seed=seed + episode,
        )
        context = warmup_context(
            bridge,
            seed=seed + 1000 + episode,
        )
        sign = float(rng.choice(np.asarray([-1.0, 1.0])))
        context, _, _ = apply_perturbation_structure(
            bridge,
            context=context,
            structure=TRAIN_STRUCTURES[0],
            sign=sign,
        )

        for _ in range(recovery_steps):
            for signal in SIGNALS:
                features, utility, _ = self_prediction_gain(
                    observer,
                    bridge,
                    context=context,
                    signal=signal,
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
            _, _, context = self_prediction_gain(
                observer,
                bridge,
                context=context,
                signal=exploration_signal,
            )

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
    structure: str,
    state_blind: bool = False,
    fixed: bool = False,
    random_policy: bool = False,
    recovery_steps: int = RECOVERY_STEPS,
) -> dict[str, float | str | list[float]]:
    bridge = DynamicStateBridge(DynamicsConfig(), seed=seed)
    context = warmup_context(bridge, seed=seed + 1000)
    sign_rng = np.random.default_rng(seed + 2000)
    sign = float(sign_rng.choice(np.asarray([-1.0, 1.0])))
    context, reference_state, target_state = apply_perturbation_structure(
        bridge,
        context=context,
        structure=structure,
        sign=sign,
    )

    rng = np.random.default_rng(seed + 5000)
    gains = []
    continuity_scores = []
    actions = []

    for _ in range(recovery_steps):
        if fixed:
            signal = choose_fixed_policy(observer, state=context.state)
        elif random_policy:
            signal = float(rng.choice(SIGNALS))
        else:
            if policy is None:
                raise ValueError("policy is required unless random_policy=True")
            signal = choose_learned_policy(
                policy,
                observer,
                state=context.state,
                state_blind=state_blind,
            )

        _, gain, context = self_prediction_gain(
            observer,
            bridge,
            context=context,
            signal=signal,
        )
        gains.append(float(gain))
        continuity_scores.append(
            float(1.0 / (1.0 + abs(context.state - reference_state)))
        )
        actions.append(float(signal))

    return {
        "mean_recovery_self_prediction_gain": float(np.mean(gains)),
        "mean_continuity_index": float(np.mean(continuity_scores)),
        "final_continuity_index": float(continuity_scores[-1]),
        "first_action": float(actions[0]),
        "mean_abs_action": float(np.mean(np.abs(actions))),
        "actions": actions,
        "structure": structure,
        "terminal_target_error": float(abs(context.state - target_state)),
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
    observer: SelfObserver,
    policy: SelfPolicy | None,
    structures: tuple[str, ...],
    episodes: int,
    base_seed: int,
    state_blind: bool = False,
    fixed: bool = False,
    random_policy: bool = False,
) -> dict[str, dict[str, np.ndarray]]:
    result = {}
    for structure_index, structure in enumerate(structures):
        rows = []
        for episode in range(episodes):
            rows.append(
                recovery_episode(
                    policy=policy,
                    observer=observer,
                    seed=base_seed + structure_index * 10000 + episode,
                    structure=structure,
                    state_blind=state_blind,
                    fixed=fixed,
                    random_policy=random_policy,
                )
            )
        result[structure] = {
            "gain": np.asarray(
                [row["mean_recovery_self_prediction_gain"] for row in rows],
                dtype=float,
            ),
            "continuity": np.asarray(
                [row["mean_continuity_index"] for row in rows],
                dtype=float,
            ),
            "terminal_error": np.asarray(
                [row["terminal_target_error"] for row in rows],
                dtype=float,
            ),
        }
    return result


def flatten_metric(
    grouped: dict[str, dict[str, np.ndarray]],
    structures: tuple[str, ...],
    key: str,
) -> np.ndarray:
    return np.concatenate([grouped[s][key] for s in structures])


def response_by_structure(
    policy: SelfPolicy,
    observer: SelfObserver,
    *,
    structure: str,
    episodes: int,
    base_seed: int,
    state_blind: bool,
) -> float:
    differences = []
    for episode in range(episodes):
        seed = base_seed + episode
        positive = recovery_episode(
            policy=policy,
            observer=observer,
            seed=seed + 10000,
            structure=structure,
            state_blind=state_blind,
            recovery_steps=1,
        )["first_action"]
        negative = recovery_episode(
            policy=policy,
            observer=observer,
            seed=seed + 20000,
            structure=structure,
            state_blind=state_blind,
            recovery_steps=1,
        )["first_action"]
        differences.append(float(positive != negative))
    return float(np.mean(differences))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes-per-condition", type=int, default=64)
    ap.add_argument("--train-episodes", type=int, default=64)
    ap.add_argument("--observer-samples", type=int, default=512)
    ap.add_argument("--recovery-steps", type=int, default=RECOVERY_STEPS)
    ap.add_argument(
        "--out",
        default="results/organism_structural_continuity_generalization_v77",
    )
    args = ap.parse_args()

    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    observer = train_self_observer(seed=77001, samples=args.observer_samples)
    policy = train_policy(
        observer,
        seed=77002,
        episodes=args.train_episodes,
        recovery_steps=args.recovery_steps,
    )

    policy_path = out / "structural_generalization_policy.json"
    policy_path.write_text(
        json.dumps(policy.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    restored_policy = SelfPolicy.from_dict(
        json.loads(policy_path.read_text(encoding="utf-8"))
    )

    test_structures = IN_DOMAIN_STRUCTURES + OOD_STRUCTURES

    learned = paired_rows(
        observer=observer,
        policy=restored_policy,
        structures=test_structures,
        episodes=args.episodes_per_condition,
        base_seed=77010,
    )
    blind = paired_rows(
        observer=observer,
        policy=restored_policy,
        structures=test_structures,
        episodes=args.episodes_per_condition,
        base_seed=77010,
        state_blind=True,
    )
    fixed = paired_rows(
        observer=observer,
        policy=None,
        structures=test_structures,
        episodes=args.episodes_per_condition,
        base_seed=77010,
        fixed=True,
    )
    random_policy = paired_rows(
        observer=observer,
        policy=None,
        structures=test_structures,
        episodes=args.episodes_per_condition,
        base_seed=77010,
        random_policy=True,
    )

    learned_all_gain = flatten_metric(learned, test_structures, "gain")
    blind_all_gain = flatten_metric(blind, test_structures, "gain")
    fixed_all_gain = flatten_metric(fixed, test_structures, "gain")
    random_all_gain = flatten_metric(random_policy, test_structures, "gain")

    learned_ood_gain = flatten_metric(learned, OOD_STRUCTURES, "gain")
    random_ood_gain = flatten_metric(random_policy, OOD_STRUCTURES, "gain")
    learned_id_gain = flatten_metric(learned, IN_DOMAIN_STRUCTURES, "gain")
    random_id_gain = flatten_metric(random_policy, IN_DOMAIN_STRUCTURES, "gain")

    learned_all_cont = flatten_metric(learned, test_structures, "continuity")
    random_all_cont = flatten_metric(random_policy, test_structures, "continuity")

    condition_summary = {}
    for structure in test_structures:
        condition_summary[structure] = {
            "learned_gain": float(learned[structure]["gain"].mean()),
            "blinded_gain": float(blind[structure]["gain"].mean()),
            "fixed_gain": float(fixed[structure]["gain"].mean()),
            "random_gain": float(random_policy[structure]["gain"].mean()),
            "learned_continuity": float(learned[structure]["continuity"].mean()),
            "random_continuity": float(random_policy[structure]["continuity"].mean()),
            "terminal_target_error_mean": float(
                learned[structure]["terminal_error"].mean()
            ),
        }

    id_advantage = float(np.mean(learned_id_gain - random_id_gain))
    ood_advantage = float(np.mean(learned_ood_gain - random_ood_gain))

    summary = {
        "experiment": "organism_structural_continuity_generalization_v77",
        "episodes_per_condition": args.episodes_per_condition,
        "train_episodes": args.train_episodes,
        "observer_samples": args.observer_samples,
        "recovery_steps": args.recovery_steps,
        "perturbation_magnitude": PERTURBATION,
        "training_structures": list(TRAIN_STRUCTURES),
        "in_domain_structures": list(IN_DOMAIN_STRUCTURES),
        "ood_structures": list(OOD_STRUCTURES),
        "policy_reloaded_without_retraining": True,
        "learned_mean_gain_all": float(learned_all_gain.mean()),
        "blinded_mean_gain_all": float(blind_all_gain.mean()),
        "fixed_mean_gain_all": float(fixed_all_gain.mean()),
        "random_mean_gain_all": float(random_all_gain.mean()),
        "learned_minus_blind_gain_p": sign_p(
            learned_all_gain - blind_all_gain, 77071
        ),
        "learned_minus_fixed_gain_p": sign_p(
            learned_all_gain - fixed_all_gain, 77072
        ),
        "learned_minus_random_gain_p": sign_p(
            learned_all_gain - random_all_gain, 77073
        ),
        "learned_id_minus_random_gain": id_advantage,
        "learned_ood_minus_random_gain": ood_advantage,
        "ood_advantage_retention_fraction": (
            float(ood_advantage / id_advantage)
            if abs(id_advantage) > 1e-12
            else float("nan")
        ),
        "learned_mean_continuity_all": float(learned_all_cont.mean()),
        "random_mean_continuity_all": float(random_all_cont.mean()),
        "learned_minus_random_continuity_p": sign_p(
            learned_all_cont - random_all_cont, 77074
        ),
        "ood_state_dependent_first_action_response_rate": response_by_structure(
            restored_policy,
            observer,
            structure="reversal_pulse",
            episodes=args.episodes_per_condition,
            base_seed=77100,
            state_blind=False,
        ),
        "ood_state_blind_first_action_response_rate": response_by_structure(
            restored_policy,
            observer,
            structure="reversal_pulse",
            episodes=args.episodes_per_condition,
            base_seed=77100,
            state_blind=True,
        ),
        "objective_is_self_prediction_gain": True,
        "continuity_index_is_secondary_evaluation_only": True,
        "ood_structures_unseen_during_training": True,
        "matched_terminal_state_across_structures": True,
        "generalization_is_evaluated_without_continuity_labels": True,
        "objective_is_still_protocol_defined": True,
        "external_attractor_target_removed_from_primary_objective": True,
        "semantic_input_during_probe": False,
        "conditions": condition_summary,
    }

    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

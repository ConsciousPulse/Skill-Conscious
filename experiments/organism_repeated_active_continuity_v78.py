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

TRAIN_SCHEDULES = ("single_impulse",)
IN_DOMAIN_SCHEDULES = ("single_impulse",)
OOD_SCHEDULES = (
    "double_same_sign",
    "double_alternating",
    "triple_alternating",
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


def apply_single_impulse(
    *,
    context: DynamicContext,
    sign: float,
) -> tuple[DynamicContext, float, float]:
    reference_state = float(context.state)
    delta = float(sign * PERTURBATION)
    target_state = float(np.clip(reference_state + delta, -1.0, 1.0))
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


def schedule_signs(
    schedule: str,
    *,
    seed: int,
) -> tuple[float, ...]:
    rng = np.random.default_rng(seed)
    base = float(rng.choice(np.asarray([-1.0, 1.0])))
    if schedule == "single_impulse":
        return (base,)
    if schedule == "double_same_sign":
        return (base, base)
    if schedule == "double_alternating":
        return (base, -base)
    if schedule == "triple_alternating":
        return (base, -base, base)
    raise ValueError(f"unknown perturbation schedule: {schedule}")


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
        context, _, _ = apply_single_impulse(
            context=context,
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


def recovery_sequence(
    *,
    policy: SelfPolicy | None,
    observer: SelfObserver,
    seed: int,
    schedule: str,
    state_blind: bool = False,
    fixed: bool = False,
    random_policy: bool = False,
    recovery_steps: int = RECOVERY_STEPS,
) -> dict[str, object]:
    bridge = DynamicStateBridge(DynamicsConfig(), seed=seed)
    context = warmup_context(bridge, seed=seed + 1000)
    signs = schedule_signs(schedule, seed=seed + 2000)

    rng = np.random.default_rng(seed + 5000)
    event_gains: list[float] = []
    event_continuities: list[float] = []
    event_first_actions: list[float] = []
    intervention_target_errors: list[float] = []
    final_target_errors: list[float] = []

    for sign in signs:
        context, reference_state, target_state = apply_single_impulse(
            context=context,
            sign=sign,
        )
        intervention_target_errors.append(
            float(abs(context.state - target_state))
        )

        gains: list[float] = []
        continuity_scores: list[float] = []
        first_action: float | None = None

        for _ in range(recovery_steps):
            if fixed:
                signal = choose_fixed_policy(observer, state=context.state)
            elif random_policy:
                signal = float(rng.choice(SIGNALS))
            else:
                if policy is None:
                    raise ValueError(
                        "policy is required unless random_policy=True"
                    )
                signal = choose_learned_policy(
                    policy,
                    observer,
                    state=context.state,
                    state_blind=state_blind,
                )

            if first_action is None:
                first_action = float(signal)

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

        event_gains.append(float(np.mean(gains)))
        event_continuities.append(float(np.mean(continuity_scores)))
        event_first_actions.append(float(first_action))
        final_target_errors.append(
            float(abs(context.state - target_state))
        )

    return {
        "mean_recovery_self_prediction_gain": float(np.mean(event_gains)),
        "mean_continuity_index": float(np.mean(event_continuities)),
        "event_gains": event_gains,
        "event_continuities": event_continuities,
        "first_actions": event_first_actions,
        "intervention_target_errors": intervention_target_errors,
        "final_target_errors": final_target_errors,
        "schedule": schedule,
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
    schedules: tuple[str, ...],
    episodes: int,
    base_seed: int,
    state_blind: bool = False,
    fixed: bool = False,
    random_policy: bool = False,
) -> dict[str, dict[str, np.ndarray]]:
    result = {}
    for schedule_index, schedule in enumerate(schedules):
        rows = []
        for episode in range(episodes):
            rows.append(
                recovery_sequence(
                    policy=policy,
                    observer=observer,
                    seed=base_seed + schedule_index * 10000 + episode,
                    schedule=schedule,
                    state_blind=state_blind,
                    fixed=fixed,
                    random_policy=random_policy,
                )
            )
        result[schedule] = {
            "gain": np.asarray(
                [row["mean_recovery_self_prediction_gain"] for row in rows],
                dtype=float,
            ),
            "continuity": np.asarray(
                [row["mean_continuity_index"] for row in rows],
                dtype=float,
            ),
            "intervention_target_error": np.asarray(
                [
                    max(row["intervention_target_errors"])
                    for row in rows
                ],
                dtype=float,
            ),
            "final_target_error": np.asarray(
                [np.mean(row["final_target_errors"]) for row in rows],
                dtype=float,
            ),
            "second_event_gain": np.asarray(
                [
                    row["event_gains"][1]
                    if len(row["event_gains"]) > 1
                    else row["event_gains"][0]
                    for row in rows
                ],
                dtype=float,
            ),
            "first_event_gain": np.asarray(
                [row["event_gains"][0] for row in rows],
                dtype=float,
            ),
        }
    return result


def flatten_metric(
    grouped: dict[str, dict[str, np.ndarray]],
    schedules: tuple[str, ...],
    key: str,
) -> np.ndarray:
    return np.concatenate([grouped[s][key] for s in schedules])


def first_action_response_by_event(
    policy: SelfPolicy,
    observer: SelfObserver,
    *,
    schedule: str,
    episodes: int,
    base_seed: int,
    state_blind: bool,
    event_index: int,
) -> float:
    differences = []
    for episode in range(episodes):
        seed = base_seed + episode
        signs = schedule_signs(schedule, seed=seed + 2000)
        if event_index >= len(signs):
            continue

        bridge = DynamicStateBridge(DynamicsConfig(), seed=seed)
        context = warmup_context(bridge, seed=seed + 1000)

        for index, sign in enumerate(signs):
            pre_event_context = context

            actual_context, _, _ = apply_single_impulse(
                context=pre_event_context,
                sign=sign,
            )

            if index == event_index:
                positive_context, _, _ = apply_single_impulse(
                    context=pre_event_context,
                    sign=1.0,
                )
                negative_context, _, _ = apply_single_impulse(
                    context=pre_event_context,
                    sign=-1.0,
                )
                positive = choose_learned_policy(
                    policy,
                    observer,
                    state=positive_context.state,
                    state_blind=state_blind,
                )
                negative = choose_learned_policy(
                    policy,
                    observer,
                    state=negative_context.state,
                    state_blind=state_blind,
                )
                differences.append(float(positive != negative))
                break

            context = actual_context
            for _ in range(RECOVERY_STEPS):
                signal = choose_learned_policy(
                    policy,
                    observer,
                    state=context.state,
                    state_blind=state_blind,
                )
                _, _, context = self_prediction_gain(
                    observer,
                    bridge,
                    context=context,
                    signal=signal,
                )

    return float(np.mean(differences)) if differences else 0.0

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes-per-condition", type=int, default=64)
    ap.add_argument("--train-episodes", type=int, default=64)
    ap.add_argument("--observer-samples", type=int, default=512)
    ap.add_argument("--recovery-steps", type=int, default=RECOVERY_STEPS)
    ap.add_argument(
        "--out",
        default="results/organism_repeated_active_continuity_v78",
    )
    args = ap.parse_args()

    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    observer = train_self_observer(seed=78001, samples=args.observer_samples)
    policy = train_policy(
        observer,
        seed=78002,
        episodes=args.train_episodes,
        recovery_steps=args.recovery_steps,
    )

    policy_path = out / "repeated_active_continuity_policy.json"
    policy_path.write_text(
        json.dumps(policy.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    restored_policy = SelfPolicy.from_dict(
        json.loads(policy_path.read_text(encoding="utf-8"))
    )

    test_schedules = IN_DOMAIN_SCHEDULES + OOD_SCHEDULES

    learned = paired_rows(
        observer=observer,
        policy=restored_policy,
        schedules=test_schedules,
        episodes=args.episodes_per_condition,
        base_seed=78010,
    )
    blind = paired_rows(
        observer=observer,
        policy=restored_policy,
        schedules=test_schedules,
        episodes=args.episodes_per_condition,
        base_seed=78010,
        state_blind=True,
    )
    fixed = paired_rows(
        observer=observer,
        policy=None,
        schedules=test_schedules,
        episodes=args.episodes_per_condition,
        base_seed=78010,
        fixed=True,
    )
    random_policy = paired_rows(
        observer=observer,
        policy=None,
        schedules=test_schedules,
        episodes=args.episodes_per_condition,
        base_seed=78010,
        random_policy=True,
    )

    learned_all_gain = flatten_metric(learned, test_schedules, "gain")
    blind_all_gain = flatten_metric(blind, test_schedules, "gain")
    fixed_all_gain = flatten_metric(fixed, test_schedules, "gain")
    random_all_gain = flatten_metric(random_policy, test_schedules, "gain")

    learned_ood_gain = flatten_metric(learned, OOD_SCHEDULES, "gain")
    random_ood_gain = flatten_metric(random_policy, OOD_SCHEDULES, "gain")
    learned_id_gain = flatten_metric(learned, IN_DOMAIN_SCHEDULES, "gain")
    random_id_gain = flatten_metric(random_policy, IN_DOMAIN_SCHEDULES, "gain")

    learned_all_cont = flatten_metric(learned, test_schedules, "continuity")
    random_all_cont = flatten_metric(random_policy, test_schedules, "continuity")

    learned_ood_second_gain = flatten_metric(
        learned,
        OOD_SCHEDULES,
        "second_event_gain",
    )
    learned_ood_first_gain = flatten_metric(
        learned,
        OOD_SCHEDULES,
        "first_event_gain",
    )

    condition_summary = {}
    for schedule in test_schedules:
        condition_summary[schedule] = {
            "learned_gain": float(learned[schedule]["gain"].mean()),
            "blinded_gain": float(blind[schedule]["gain"].mean()),
            "fixed_gain": float(fixed[schedule]["gain"].mean()),
            "random_gain": float(random_policy[schedule]["gain"].mean()),
            "learned_continuity": float(
                learned[schedule]["continuity"].mean()
            ),
            "random_continuity": float(
                random_policy[schedule]["continuity"].mean()
            ),
            "intervention_target_error_mean": float(
                learned[schedule]["intervention_target_error"].mean()
            ),
            "final_state_target_error_mean": float(
                learned[schedule]["final_target_error"].mean()
            ),
            "first_event_gain": float(
                learned[schedule]["first_event_gain"].mean()
            ),
            "second_event_gain": float(
                learned[schedule]["second_event_gain"].mean()
            ),
        }

    id_advantage = float(np.mean(learned_id_gain - random_id_gain))
    ood_advantage = float(np.mean(learned_ood_gain - random_ood_gain))
    ood_second_minus_first = float(
        np.mean(learned_ood_second_gain - learned_ood_first_gain)
    )

    intervention_error_max = max(
        float(learned[schedule]["intervention_target_error"].max())
        for schedule in test_schedules
    )

    summary = {
        "experiment": "organism_repeated_active_continuity_v78",
        "episodes_per_condition": args.episodes_per_condition,
        "train_episodes": args.train_episodes,
        "observer_samples": args.observer_samples,
        "recovery_steps": args.recovery_steps,
        "perturbation_magnitude": PERTURBATION,
        "training_schedules": list(TRAIN_SCHEDULES),
        "in_domain_schedules": list(IN_DOMAIN_SCHEDULES),
        "ood_schedules": list(OOD_SCHEDULES),
        "policy_reloaded_without_retraining": True,
        "learned_mean_gain_all": float(learned_all_gain.mean()),
        "blinded_mean_gain_all": float(blind_all_gain.mean()),
        "fixed_mean_gain_all": float(fixed_all_gain.mean()),
        "random_mean_gain_all": float(random_all_gain.mean()),
        "learned_minus_blind_gain_p": sign_p(
            learned_all_gain - blind_all_gain, 78071
        ),
        "learned_minus_fixed_gain_p": sign_p(
            learned_all_gain - fixed_all_gain, 78072
        ),
        "learned_minus_random_gain_p": sign_p(
            learned_all_gain - random_all_gain, 78073
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
            learned_all_cont - random_all_cont, 78074
        ),
        "ood_second_minus_first_gain": ood_second_minus_first,
        "ood_state_dependent_first_action_response_event_1": first_action_response_by_event(
            restored_policy,
            observer,
            schedule="triple_alternating",
            episodes=args.episodes_per_condition,
            base_seed=78100,
            state_blind=False,
            event_index=0,
        ),
        "ood_state_dependent_first_action_response_event_2": first_action_response_by_event(
            restored_policy,
            observer,
            schedule="triple_alternating",
            episodes=args.episodes_per_condition,
            base_seed=78100,
            state_blind=False,
            event_index=1,
        ),
        "ood_state_blind_first_action_response_event_1": first_action_response_by_event(
            restored_policy,
            observer,
            schedule="triple_alternating",
            episodes=args.episodes_per_condition,
            base_seed=78100,
            state_blind=True,
            event_index=0,
        ),
        "ood_state_blind_first_action_response_event_2": first_action_response_by_event(
            restored_policy,
            observer,
            schedule="triple_alternating",
            episodes=args.episodes_per_condition,
            base_seed=78100,
            state_blind=True,
            event_index=1,
        ),
        "objective_is_self_prediction_gain": True,
        "continuity_index_is_secondary_evaluation_only": True,
        "ood_schedules_unseen_during_training": True,
        "repeated_perturbations_evaluated_without_retraining": True,
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

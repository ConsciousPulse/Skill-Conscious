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

from experiments.organism_repeated_active_continuity_v78 import (
    IN_DOMAIN_SCHEDULES,
    SIGNALS,
    apply_single_impulse,
    candidate_features,
    choose_learned_policy,
    schedule_signs,
    self_prediction_gain,
    sign_p,
    train_policy,
    train_self_observer,
    warmup_context,
)


RECOVERY_STEPS = 12
OOD_SCHEDULE = "triple_alternating"


def shifted_config() -> DynamicsConfig:
    return DynamicsConfig(
        relaxation=0.44,
        pressure_gain=0.75,
        cross_gain=1.10,
    )


def recovery_sequence(
    *,
    policy: SelfPolicy,
    observer: SelfObserver,
    seed: int,
    schedule: str,
    cfg: DynamicsConfig,
    online_update: bool,
    state_blind: bool = False,
    recovery_steps: int = RECOVERY_STEPS,
) -> dict[str, object]:
    bridge = DynamicStateBridge(cfg, seed=seed)
    context = warmup_context(bridge, seed=seed + 1000)
    signs = schedule_signs(schedule, seed=seed + 2000)

    adaptive_gains: list[float] = []
    adaptive_first_actions: list[float] = []
    continuity_scores: list[float] = []
    intervention_target_errors: list[float] = []
    event_gains: list[float] = []

    for sign in signs:
        context, reference_state, target_state = apply_single_impulse(
            context=context,
            sign=sign,
        )
        intervention_target_errors.append(
            float(abs(context.state - target_state))
        )

        gains: list[float] = []
        first_action: float | None = None

        for _ in range(recovery_steps):
            signal = choose_learned_policy(
                policy,
                observer,
                state=context.state,
                state_blind=state_blind,
            )
            if first_action is None:
                first_action = float(signal)

            features, gain, next_context = self_prediction_gain(
                observer,
                bridge,
                context=context,
                signal=signal,
            )

            if online_update:
                policy.observe(
                    SelfPolicy.features_for(
                        current_state=features["current_state"],
                        attractor_distance=features["attractor_distance"],
                        predicted_state=features["predicted_state"],
                        predicted_displacement=features["predicted_displacement"],
                        signal=features["signal"],
                    ),
                    gain,
                )

            context = next_context
            gains.append(float(gain))
            continuity_scores.append(
                float(1.0 / (1.0 + abs(context.state - reference_state)))
            )

        event_gains.append(float(np.mean(gains)))
        adaptive_gains.extend(gains)
        adaptive_first_actions.append(float(first_action))

    return {
        "mean_gain": float(np.mean(adaptive_gains)),
        "event_gains": event_gains,
        "first_actions": adaptive_first_actions,
        "continuity": float(np.mean(continuity_scores)),
        "intervention_target_errors": intervention_target_errors,
    }


def run_condition(
    *,
    observer: SelfObserver,
    frozen_policy: SelfPolicy,
    adaptive_policy: SelfPolicy,
    episodes: int,
    base_seed: int,
    schedule: str,
    cfg: DynamicsConfig,
    state_blind: bool = False,
) -> dict[str, np.ndarray]:
    frozen_rows = []
    adaptive_rows = []
    for episode in range(episodes):
        seed = base_seed + episode
        frozen_rows.append(
            recovery_sequence(
                policy=SelfPolicy.from_dict(frozen_policy.to_dict()),
                observer=observer,
                seed=seed,
                schedule=schedule,
                cfg=cfg,
                online_update=False,
                state_blind=state_blind,
                recovery_steps=RECOVERY_STEPS,
            )
        )
        adaptive_rows.append(
            recovery_sequence(
                policy=SelfPolicy.from_dict(adaptive_policy.to_dict()),
                observer=observer,
                seed=seed,
                schedule=schedule,
                cfg=cfg,
                online_update=True,
                state_blind=state_blind,
                recovery_steps=RECOVERY_STEPS,
            )
        )

    def arr(rows: list[dict[str, object]], key: str) -> np.ndarray:
        return np.asarray([row[key] for row in rows], dtype=float)

    def event_arr(rows: list[dict[str, object]], event: int) -> np.ndarray:
        return np.asarray(
            [float(row["event_gains"][event]) for row in rows],
            dtype=float,
        )

    event_count = len(adaptive_rows[0]["event_gains"])
    out = {
        "frozen_gain": arr(frozen_rows, "mean_gain"),
        "adaptive_gain": arr(adaptive_rows, "mean_gain"),
        "frozen_continuity": arr(frozen_rows, "continuity"),
        "adaptive_continuity": arr(adaptive_rows, "continuity"),
        "intervention_error": np.asarray(
            [
                max(row["intervention_target_errors"])
                for row in adaptive_rows
            ],
            dtype=float,
        ),
    }
    for event in range(event_count):
        out[f"frozen_event_{event + 1}"] = event_arr(frozen_rows, event)
        out[f"adaptive_event_{event + 1}"] = event_arr(adaptive_rows, event)

    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes-per-condition", type=int, default=64)
    ap.add_argument("--train-episodes", type=int, default=64)
    ap.add_argument("--observer-samples", type=int, default=512)
    ap.add_argument("--out", default="results/organism_online_self_policy_adaptation_v79")
    args = ap.parse_args()

    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    observer = train_self_observer(
        seed=79001,
        samples=args.observer_samples,
    )
    trained_policy = train_policy(
        observer,
        seed=79002,
        episodes=args.train_episodes,
        recovery_steps=RECOVERY_STEPS,
    )

    snapshot = json.loads(json.dumps(trained_policy.to_dict()))
    frozen_policy = SelfPolicy.from_dict(snapshot)
    adaptive_policy = SelfPolicy.from_dict(snapshot)

    policy_path = out / "initial_policy.json"
    policy_path.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    base = DynamicsConfig()
    shifted = shifted_config()

    in_domain = run_condition(
        observer=observer,
        frozen_policy=frozen_policy,
        adaptive_policy=adaptive_policy,
        episodes=args.episodes_per_condition,
        base_seed=79010,
        schedule="single_impulse",
        cfg=base,
    )

    shifted_single = run_condition(
        observer=observer,
        frozen_policy=frozen_policy,
        adaptive_policy=adaptive_policy,
        episodes=args.episodes_per_condition,
        base_seed=79110,
        schedule="single_impulse",
        cfg=shifted,
    )

    shifted_repeated = run_condition(
        observer=observer,
        frozen_policy=frozen_policy,
        adaptive_policy=adaptive_policy,
        episodes=args.episodes_per_condition,
        base_seed=79210,
        schedule=OOD_SCHEDULE,
        cfg=shifted,
    )

    adaptive_ood_late = shifted_repeated["adaptive_event_3"]
    frozen_ood_late = shifted_repeated["frozen_event_3"]
    adaptive_ood_early = shifted_repeated["adaptive_event_1"]
    frozen_ood_early = shifted_repeated["frozen_event_1"]

    summary = {
        "experiment": "organism_online_self_policy_adaptation_v79",
        "episodes_per_condition": args.episodes_per_condition,
        "train_episodes": args.train_episodes,
        "observer_samples": args.observer_samples,
        "recovery_steps": RECOVERY_STEPS,
        "training_schedule": "single_impulse",
        "ood_schedule": OOD_SCHEDULE,
        "policy_snapshot_shared_between_frozen_and_adaptive": True,
        "online_updates_use_only_observed_self_prediction_gain": True,
        "external_retraining_during_probe": False,
        "semantic_input_during_probe": False,
        "shifted_dynamics_parameters": {
            "relaxation": shifted.relaxation,
            "pressure_gain": shifted.pressure_gain,
            "cross_gain": shifted.cross_gain,
        },
        "in_domain_frozen_gain": float(in_domain["frozen_gain"].mean()),
        "in_domain_adaptive_gain": float(in_domain["adaptive_gain"].mean()),
        "shifted_single_frozen_gain": float(shifted_single["frozen_gain"].mean()),
        "shifted_single_adaptive_gain": float(shifted_single["adaptive_gain"].mean()),
        "shifted_repeated_frozen_gain": float(
            shifted_repeated["frozen_gain"].mean()
        ),
        "shifted_repeated_adaptive_gain": float(
            shifted_repeated["adaptive_gain"].mean()
        ),
        "ood_late_adaptation_lift": float(
            np.mean(adaptive_ood_late - frozen_ood_late)
        ),
        "ood_late_adaptation_p": sign_p(
            adaptive_ood_late - frozen_ood_late,
            79071,
        ),
        "ood_adaptive_late_minus_early": float(
            np.mean(adaptive_ood_late - adaptive_ood_early)
        ),
        "ood_frozen_late_minus_early": float(
            np.mean(frozen_ood_late - frozen_ood_early)
        ),
        "ood_differential_adaptation": float(
            np.mean(
                (adaptive_ood_late - adaptive_ood_early)
                - (frozen_ood_late - frozen_ood_early)
            )
        ),
        "ood_differential_adaptation_p": sign_p(
            (adaptive_ood_late - adaptive_ood_early)
            - (frozen_ood_late - frozen_ood_early),
            79072,
        ),
        "ood_adaptive_continuity": float(
            shifted_repeated["adaptive_continuity"].mean()
        ),
        "ood_frozen_continuity": float(
            shifted_repeated["frozen_continuity"].mean()
        ),
        "ood_continuity_p": sign_p(
            shifted_repeated["adaptive_continuity"]
            - shifted_repeated["frozen_continuity"],
            79073,
        ),
        "intervention_target_error_max": float(
            shifted_repeated["intervention_error"].max()
        ),
        "conditions": {
            "in_domain": {
                "frozen_gain": float(in_domain["frozen_gain"].mean()),
                "adaptive_gain": float(in_domain["adaptive_gain"].mean()),
            },
            "shifted_single": {
                "frozen_gain": float(shifted_single["frozen_gain"].mean()),
                "adaptive_gain": float(shifted_single["adaptive_gain"].mean()),
            },
            "shifted_repeated": {
                "frozen_gain": float(shifted_repeated["frozen_gain"].mean()),
                "adaptive_gain": float(
                    shifted_repeated["adaptive_gain"].mean()
                ),
                "frozen_event_1": float(
                    shifted_repeated["frozen_event_1"].mean()
                ),
                "frozen_event_2": float(
                    shifted_repeated["frozen_event_2"].mean()
                ),
                "frozen_event_3": float(
                    shifted_repeated["frozen_event_3"].mean()
                ),
                "adaptive_event_1": float(
                    shifted_repeated["adaptive_event_1"].mean()
                ),
                "adaptive_event_2": float(
                    shifted_repeated["adaptive_event_2"].mean()
                ),
                "adaptive_event_3": float(
                    shifted_repeated["adaptive_event_3"].mean()
                ),
            },
        },
    }

    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

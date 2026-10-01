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
    step = 0

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
    return observer


def evaluate_candidates(
    observer: SelfObserver,
    *,
    current_state: float,
    attractor: float,
    signal: float,
) -> dict[str, float]:
    prediction = observer.predict(
        previous_state=current_state,
        state=current_state,
        memory=0.0,
        pressure=0.0,
        last_input=signal,
        attractor_distance=abs(current_state - attractor),
        steps_delta=1,
    )
    return {
        "current_state": float(current_state),
        "attractor_distance": float(abs(current_state - attractor)),
        "predicted_state": float(prediction.predicted_state),
        "predicted_displacement": float(
            abs(prediction.predicted_state - current_state)
        ),
        "signal": float(signal),
    }


def actual_utility(
    bridge: DynamicStateBridge,
    *,
    current_state: float,
    signal: float,
    step_index: int,
    attractor: float,
) -> float:
    snap = bridge.advance(
        previous_state=current_state,
        state=current_state,
        memory=0.0,
        pressure=0.0,
        signal=signal,
        steps=1,
        step_index=step_index,
    )
    next_distance = abs(snap.state - attractor)
    displacement = abs(snap.state - current_state)
    return float(-(0.70 * next_distance + 0.30 * displacement))


def collect_training(
    observer: SelfObserver,
    *,
    seed: int,
    episodes: int,
    steps_per_episode: int,
) -> SelfPolicy:
    policy = SelfPolicy()
    rng = np.random.default_rng(seed)

    for episode in range(episodes):
        bridge = DynamicStateBridge(DynamicsConfig(), seed=seed + episode)
        state = float(rng.uniform(-0.8, 0.8))
        for step in range(steps_per_episode):
            candidates = [
                evaluate_candidates(
                    observer,
                    current_state=state,
                    attractor=bridge.cfg.attractor,
                    signal=signal,
                )
                for signal in SIGNALS
            ]
            for candidate in candidates:
                utility = actual_utility(
                    bridge,
                    current_state=state,
                    signal=candidate["signal"],
                    step_index=step,
                    attractor=bridge.cfg.attractor,
                )
                features = SelfPolicy.features_for(**candidate)
                policy.observe(features, utility)

            chosen = candidates[int(rng.integers(0, len(candidates)))]
            snap = bridge.advance(
                previous_state=state,
                state=state,
                memory=0.0,
                pressure=0.0,
                signal=chosen["signal"],
                steps=1,
                step_index=step,
            )
            state = snap.state

    return policy


def fixed_selector(observer: SelfObserver, state: float, attractor: float) -> float:
    selector = TrajectorySelector(attractor_weight=0.70, coherence_weight=0.30)
    candidates = selector.evaluate(
        observer,
        current_state=state,
        current_memory=0.0,
        current_pressure=0.0,
        current_input=0.0,
        current_attractor=attractor,
        steps_delta=1,
        signals=SIGNALS,
    )
    return float(selector.choose(candidates).signal)


def run_policy(
    policy: SelfPolicy,
    observer: SelfObserver,
    *,
    seed: int,
    episodes: int,
    state_blind: bool = False,
) -> tuple[float, list[float]]:
    episode_scores = []
    for episode in range(episodes):
        bridge = DynamicStateBridge(DynamicsConfig(), seed=seed + episode)
        rng = np.random.default_rng(seed + 5000 + episode)
        state = float(rng.uniform(-0.8, 0.8))
        total = 0.0

        for step in range(16):
            effective_state = 0.0 if state_blind else state
            candidates = [
                evaluate_candidates(
                    observer,
                    current_state=effective_state,
                    attractor=bridge.cfg.attractor,
                    signal=signal,
                )
                for signal in SIGNALS
            ]
            chosen = policy.choose(candidates)
            signal = chosen["signal"]
            snap = bridge.advance(
                previous_state=state,
                state=state,
                memory=0.0,
                pressure=0.0,
                signal=signal,
                steps=1,
                step_index=step,
            )
            total += -(
                0.70 * abs(snap.state - bridge.cfg.attractor)
                + 0.30 * abs(snap.state - state)
            )
            state = snap.state
        episode_scores.append(total / 16.0)

    return float(np.mean(episode_scores)), episode_scores


def run_fixed(
    observer: SelfObserver,
    *,
    seed: int,
    episodes: int,
) -> tuple[float, list[float]]:
    scores = []
    for episode in range(episodes):
        bridge = DynamicStateBridge(DynamicsConfig(), seed=seed + 10000 + episode)
        rng = np.random.default_rng(seed + 15000 + episode)
        state = float(rng.uniform(-0.8, 0.8))
        total = 0.0
        for step in range(16):
            signal = fixed_selector(observer, state, bridge.cfg.attractor)
            snap = bridge.advance(
                previous_state=state,
                state=state,
                memory=0.0,
                pressure=0.0,
                signal=signal,
                steps=1,
                step_index=step,
            )
            total += -(
                0.70 * abs(snap.state - bridge.cfg.attractor)
                + 0.30 * abs(snap.state - state)
            )
            state = snap.state
        scores.append(total / 16.0)
    return float(np.mean(scores)), scores


def sign_p(values: np.ndarray, seed: int) -> float:
    values = np.asarray(values, dtype=float)
    observed = abs(float(values.mean()))
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.asarray([-1.0, 1.0]), size=(20000, values.size))
    null = np.abs((signs * values).mean(axis=1))
    return float((np.count_nonzero(null >= observed) + 1) / 20001)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=64)
    ap.add_argument("--train-episodes", type=int, default=64)
    ap.add_argument("--observer-samples", type=int, default=512)
    ap.add_argument("--out", default="results/organism_self_policy_learning_v72")
    args = ap.parse_args()

    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    observer = train_self_observer(seed=72001, samples=args.observer_samples)
    policy = collect_training(
        observer,
        seed=72002,
        episodes=args.train_episodes,
        steps_per_episode=16,
    )

    policy_path = out / "self_policy.json"
    policy_path.write_text(
        json.dumps(policy.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    restored = SelfPolicy.from_dict(
        json.loads(policy_path.read_text(encoding="utf-8"))
    )

    learned_score, learned_rows = run_policy(
        restored,
        observer,
        seed=72003,
        episodes=args.episodes,
        state_blind=False,
    )
    blinded_score, blinded_rows = run_policy(
        restored,
        observer,
        seed=73003,
        episodes=args.episodes,
        state_blind=True,
    )
    fixed_score, fixed_rows = run_fixed(
        observer,
        seed=74003,
        episodes=args.episodes,
    )

    learned = np.asarray(learned_rows)
    blinded = np.asarray(blinded_rows)
    fixed = np.asarray(fixed_rows)

    random_rng = np.random.default_rng(75003)
    random_rows = []
    for value in range(args.episodes):
        bridge = DynamicStateBridge(DynamicsConfig(), seed=75003 + value)
        rng = np.random.default_rng(76003 + value)
        state = float(rng.uniform(-0.8, 0.8))
        total = 0.0
        for step in range(16):
            signal = float(rng.choice(SIGNALS))
            snap = bridge.advance(
                previous_state=state,
                state=state,
                memory=0.0,
                pressure=0.0,
                signal=signal,
                steps=1,
                step_index=step,
            )
            total += -(
                0.70 * abs(snap.state - bridge.cfg.attractor)
                + 0.30 * abs(snap.state - state)
            )
            state = snap.state
        random_rows.append(total / 16.0)

    random_scores = np.asarray(random_rows)

    summary = {
        "experiment": "organism_self_policy_learning_v72",
        "episodes": args.episodes,
        "train_episodes": args.train_episodes,
        "observer_samples": args.observer_samples,
        "policy_reloaded_without_retraining": True,
        "learned_policy_score": learned_score,
        "blinded_policy_score": float(blinded.mean()),
        "fixed_policy_score": fixed_score,
        "random_policy_score": float(random_scores.mean()),
        "learned_minus_fixed": float(learned.mean() - fixed.mean()),
        "learned_minus_random": float(learned.mean() - random_scores.mean()),
        "learned_minus_blinded_p": sign_p(learned - blinded, 72071),
        "learned_minus_fixed_p": sign_p(learned - fixed, 72072),
        "learned_minus_random_p": sign_p(learned - random_scores, 72073),
        "state_blind_control_present": True,
        "semantic_input_during_policy_probe": False,
        "objective_is_externally_defined": True,
    }

    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

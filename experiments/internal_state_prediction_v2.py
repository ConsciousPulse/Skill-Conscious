from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

from src.ontto.dynamics import Config, simulate


SEED = 42
N = 5000


def main() -> None:
    rng = np.random.default_rng(SEED)

    inputs = np.zeros(N)
    latent = 0.0

    # The input contains abrupt changes, while the internal trajectory
    # carries path-dependent state between them.
    for t in range(N):
        if rng.random() < 0.07:
            latent = float(rng.choice([-1.0, 1.0]))
        inputs[t] = latent

    run = simulate(inputs, Config(noise_std=0.0), seed=SEED)

    target = run["state"][1:]
    idx = np.arange(N - 1)

    features_internal = np.column_stack([
        run["input"][:-1],
        run["state"][:-1],
        run["memory"][:-1],
        run["pressure"][:-1],
        run["cross"][:-1],
        np.abs(run["score"][:-1]),
    ])

    features_input_only = run["input"][:-1].reshape(-1, 1)

    split = int(0.70 * len(idx))

    full = RandomForestRegressor(
        n_estimators=200,
        random_state=SEED,
        n_jobs=-1,
        min_samples_leaf=3,
    )
    base = RandomForestRegressor(
        n_estimators=200,
        random_state=SEED,
        n_jobs=-1,
        min_samples_leaf=3,
    )

    full.fit(features_internal[:split], target[:split])
    base.fit(features_input_only[:split], target[:split])

    pred_full = full.predict(features_internal[split:])
    pred_base = base.predict(features_input_only[split:])

    mse_full = float(mean_squared_error(target[split:], pred_full))
    mse_base = float(mean_squared_error(target[split:], pred_base))
    r2_full = float(r2_score(target[split:], pred_full))
    r2_base = float(r2_score(target[split:], pred_base))

    report = {
        "experiment": "internal_state_prediction_v2",
        "samples": int(len(idx) - split),
        "next_state_mse_internal_state": mse_full,
        "next_state_mse_input_only": mse_base,
        "next_state_r2_internal_state": r2_full,
        "next_state_r2_input_only": r2_base,
        "mse_reduction": float(1.0 - mse_full / max(mse_base, 1e-12)),
        "r2_gain": float(r2_full - r2_base),
    }

    assert np.isfinite(mse_full)
    assert np.isfinite(mse_base)
    assert np.isfinite(r2_full)
    assert np.isfinite(r2_base)

    output = Path("results/internal_state_prediction_v2.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=" * 72)
    print("CONSCIENCIA PARA IA — INTERNAL STATE PREDICTION V2")
    print("=" * 72)
    for key, value in report.items():
        print(f"{key}: {value}")
    print(f"RESULT: {output}")
    print("=" * 72)


if __name__ == "__main__":
    main()

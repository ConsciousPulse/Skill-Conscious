from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.ontto.dynamics import Config, simulate


SEEDS = list(range(20))
CANDIDATE = {
    "beta_memory": 0.998891,
    "relaxation": 1.1375,
    "pressure_gain": 0.175,
    "cross_gain": 0.25,
}
BASELINE = {
    "beta_memory": 0.92,
    "relaxation": 0.32,
    "pressure_gain": 0.55,
    "cross_gain": 0.85,
}


def make_cfg(params: dict[str, float], seed: int) -> Config:
    return Config(
        beta_memory=params["beta_memory"],
        relaxation=params["relaxation"],
        pressure_gain=params["pressure_gain"],
        cross_gain=params["cross_gain"],
        noise_std=0.01,
    )


def holdout_path_gap(cfg: Config, seed: int, protocol: int, steps: int = 520) -> float:
    rng = np.random.default_rng(seed + 10000 * protocol)
    suffix = np.sin(np.linspace(0, 4 * np.pi, 220)) * 0.7
    prefix_len = steps - len(suffix)

    if protocol == 0:
        a = np.ones(prefix_len)
        b = -np.ones(prefix_len)
    elif protocol == 1:
        a = np.where(np.arange(prefix_len) % 2 == 0, 1.0, -1.0)
        b = np.ones(prefix_len)
    elif protocol == 2:
        a = np.where(rng.random(prefix_len) < 0.15, -1.0, 1.0)
        b = np.where(rng.random(prefix_len) < 0.05, 1.0, -1.0)
    else:
        a = np.sign(np.sin(np.linspace(0, 18 * np.pi, prefix_len)))
        b = np.sign(np.sin(np.linspace(0, 6 * np.pi, prefix_len) + 1.7))

    run_a = simulate(np.r_[a, suffix], cfg, seed=seed)
    run_b = simulate(np.r_[b, suffix], cfg, seed=seed)

    return float(np.mean(np.abs(run_a["state"][-180:] - run_b["state"][-180:])))


def holdout_critical(cfg: Config, seed: int, protocol: int, steps: int = 800, warmup: int = 250) -> float:
    u = np.zeros(steps)

    if protocol == 0:
        u[120:180] = 0.7
        u[350:430] = -1.0
        u[600:650] = 0.4
    elif protocol == 1:
        u[80:130] = -0.8
        u[280:340] = 1.0
        u[500:570] = 0.6
        u[700:730] = -0.4
    elif protocol == 2:
        u[150:230] = np.linspace(0, 1, 80)
        u[420:500] = np.linspace(1, -1, 80)
        u[650:690] = 0.8
    else:
        u[100:200] = np.sin(np.linspace(0, 3 * np.pi, 100))
        u[400:520] = -0.6
        u[650:760] = 0.5 * np.sin(np.linspace(0, 2 * np.pi, 110))

    run = simulate(u, cfg, seed=seed)
    q = run["q"][warmup:]
    cross = run["cross"][warmup:]

    high = cross >= np.quantile(cross, 0.75)
    low = cross <= np.quantile(cross, 0.25)

    return float(
        np.mean((q == "X")[high]) - np.mean((q == "X")[low])
    )


def evaluate(label: str, params: dict[str, float]) -> pd.DataFrame:
    rows = []

    for seed in SEEDS:
        cfg = make_cfg(params, seed)

        for protocol in range(4):
            rows.append(
                {
                    "label": label,
                    "seed": seed,
                    "protocol": protocol,
                    "path_gap": holdout_path_gap(cfg, seed, protocol),
                    "critical_lift": holdout_critical(cfg, seed, protocol),
                }
            )

    return pd.DataFrame(rows)


def summarize(frame: pd.DataFrame) -> dict[str, float | int | str]:
    return {
        "label": str(frame["label"].iloc[0]),
        "seed_count": int(frame["seed"].nunique()),
        "protocol_count": int(frame["protocol"].nunique()),
        "path_gap_mean": float(frame["path_gap"].mean()),
        "path_gap_sd": float(frame["path_gap"].std(ddof=1)),
        "path_gap_min": float(frame["path_gap"].min()),
        "critical_lift_mean": float(frame["critical_lift"].mean()),
        "critical_lift_sd": float(frame["critical_lift"].std(ddof=1)),
        "critical_lift_min": float(frame["critical_lift"].min()),
        "positive_critical_fraction": float(
            np.mean(frame["critical_lift"] > 0)
        ),
    }


def main() -> None:
    out = Path("results/parametric_holdout_v1")
    out.mkdir(parents=True, exist_ok=True)

    candidate = evaluate("candidate", CANDIDATE)
    baseline = evaluate("baseline", BASELINE)

    all_rows = pd.concat([candidate, baseline], ignore_index=True)
    all_rows.to_csv(out / "raw.csv", index=False)

    candidate_summary = summarize(candidate)
    baseline_summary = summarize(baseline)

    summary = {
        "experiment": "parametric_holdout_v1",
        "candidate_parameters": CANDIDATE,
        "baseline_parameters": BASELINE,
        "candidate": candidate_summary,
        "baseline": baseline_summary,
        "path_gap_amplification": (
            candidate_summary["path_gap_mean"]
            / max(baseline_summary["path_gap_mean"], 1e-12)
        ),
        "critical_lift_ratio": (
            candidate_summary["critical_lift_mean"]
            / max(baseline_summary["critical_lift_mean"], 1e-12)
        ),
        "robust_positive_critical": (
            candidate_summary["positive_critical_fraction"] == 1.0
        ),
        "interpretation": (
            "Independent holdout protocols were not used during coarse/zoom search. "
            "The candidate is tested with new history and perturbation patterns."
        ),
    }

    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=" * 80)
    print("CONSCIENCIA PARA IA — PARAMETRIC HOLDOUT V1")
    print("=" * 80)

    for name, report in (
        ("CANDIDATE", candidate_summary),
        ("BASELINE", baseline_summary),
    ):
        print(f"\n{name}:")
        for key, value in report.items():
            print(f"  {key}={value}")

    print("\nGENERALIZATION:")
    print(f"  path_gap_amplification={summary['path_gap_amplification']:.3f}x")
    print(f"  critical_lift_ratio={summary['critical_lift_ratio']:.3f}x")
    print(f"  robust_positive_critical={summary['robust_positive_critical']}")

    print(f"\nRESULT: {out / 'summary.json'}")
    print("=" * 80)


if __name__ == "__main__":
    main()

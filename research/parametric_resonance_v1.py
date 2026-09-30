from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.ontto.dynamics import Config, simulate


SEED = 0
COARSE_SEEDS = [0]
VALIDATION_SEEDS = list(range(20))

OUT = Path("results/parametric_resonance_v1")
OUT.mkdir(parents=True, exist_ok=True)


def path_dependence(cfg: Config, seed: int = 0, steps: int = 420) -> float:
    prefix_len = steps - 180
    prefix_a = np.ones(prefix_len)
    prefix_b = -np.ones(prefix_len)
    suffix = np.ones(180)

    run_a = simulate(np.r_[prefix_a, suffix], cfg, seed=seed)
    run_b = simulate(np.r_[prefix_b, suffix], cfg, seed=seed)

    return float(np.mean(np.abs(run_a["state"][-150:] - run_b["state"][-150:])))


def critical_lift(
    cfg: Config,
    seed: int = 0,
    steps: int = 600,
    warmup: int = 200,
) -> tuple[float, float]:
    u = np.zeros(steps)
    u[80:160] = 1.0
    u[260:330] = -1.0
    u[420:460] = 0.7

    run = simulate(u, cfg, seed=seed)
    q = run["q"][warmup:]
    cross = run["cross"][warmup:]

    hi = cross >= np.quantile(cross, 0.75)
    lo = cross <= np.quantile(cross, 0.25)

    high = float(np.mean((q == "X")[hi])) if np.any(hi) else 0.0
    low = float(np.mean((q == "X")[lo])) if np.any(lo) else 0.0

    return high - low, float(np.mean(q == "X"))


def evaluate(
    beta: float,
    relaxation: float,
    pressure_gain: float,
    cross_gain: float,
    seed: int,
    noise_std: float,
) -> dict[str, float]:
    cfg = Config(
        beta_memory=float(beta),
        relaxation=float(relaxation),
        pressure_gain=float(pressure_gain),
        cross_gain=float(cross_gain),
        noise_std=float(noise_std),
    )

    gap = path_dependence(cfg, seed=seed)
    lift, x_occ = critical_lift(cfg, seed=seed)

    return {
        "beta": float(beta),
        "relaxation": float(relaxation),
        "pressure_gain": float(pressure_gain),
        "cross_gain": float(cross_gain),
        "path_gap": gap,
        "critical_lift": lift,
        "x_occupancy": x_occ,
        "resonance_score": gap * max(lift, 0.0),
    }


def sweep(
    betas,
    relaxations,
    pressure_gains,
    cross_gains,
    noise_std: float,
) -> pd.DataFrame:
    rows: list[dict[str, float]] = []

    for params in itertools.product(
        betas,
        relaxations,
        pressure_gains,
        cross_gains,
    ):
        for seed in COARSE_SEEDS:
            rows.append(
                evaluate(
                    *params,
                    seed=seed,
                    noise_std=noise_std,
                )
            )

    return pd.DataFrame(rows)


def exponential_fit(
    beta_values: np.ndarray,
    gap_values: np.ndarray,
) -> dict[str, float]:
    mask = (
        np.isfinite(beta_values)
        & np.isfinite(gap_values)
        & (gap_values > 0)
        & (beta_values >= 0.96)
    )

    x = beta_values[mask]
    y = np.log(gap_values[mask])

    coeff = np.polyfit(x, y, 1)
    slope, intercept = float(coeff[0]), float(coeff[1])

    predicted = intercept + slope * x
    ss_res = float(np.sum((y - predicted) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return {
        "n_points": int(len(x)),
        "log_slope": slope,
        "log_intercept": intercept,
        "r2": r2,
        "implied_multiplier_per_0_01_beta": float(np.exp(0.01 * slope)),
    }


def validate_candidate(
    label: str,
    params: tuple[float, float, float, float],
) -> dict[str, object]:
    beta, relaxation, pressure_gain, cross_gain = params

    rows = []
    for seed in VALIDATION_SEEDS:
        rows.append(
            evaluate(
                beta,
                relaxation,
                pressure_gain,
                cross_gain,
                seed=seed,
                noise_std=0.01,
            )
        )

    frame = pd.DataFrame(rows)

    return {
        "label": label,
        "beta": beta,
        "relaxation": relaxation,
        "pressure_gain": pressure_gain,
        "cross_gain": cross_gain,
        "seeds": len(VALIDATION_SEEDS),
        "path_gap_mean": float(frame["path_gap"].mean()),
        "path_gap_sd": float(frame["path_gap"].std(ddof=1)),
        "path_gap_min": float(frame["path_gap"].min()),
        "critical_lift_mean": float(frame["critical_lift"].mean()),
        "critical_lift_sd": float(frame["critical_lift"].std(ddof=1)),
        "critical_lift_min": float(frame["critical_lift"].min()),
        "positive_critical_fraction": float(
            np.mean(frame["critical_lift"] > 0)
        ),
        "x_occupancy_mean": float(frame["x_occupancy"].mean()),
    }


def main() -> None:
    # --------------------------------------------------------
    # 1) COARSE SWEEP
    # --------------------------------------------------------
    coarse_betas = [
        0.920, 0.950, 0.970, 0.980, 0.985,
        0.990, 0.993, 0.995, 0.997,
    ]
    coarse_relaxations = [0.32, 0.50, 0.65, 0.80, 0.85, 0.95, 1.10]
    coarse_pressure = [0.05, 0.15, 0.30, 0.55]
    coarse_cross = [0.25, 0.85, 1.40]

    coarse = sweep(
        coarse_betas,
        coarse_relaxations,
        coarse_pressure,
        coarse_cross,
        noise_std=0.0,
    )
    coarse.to_csv(OUT / "coarse.csv", index=False)

    top = coarse.sort_values(
        "resonance_score",
        ascending=False,
    ).head(8).copy()

    best = top.iloc[0]
    best_params = (
        float(best.beta),
        float(best.relaxation),
        float(best.pressure_gain),
        float(best.cross_gain),
    )

    # --------------------------------------------------------
    # 2) ZOOM AROUND THE BEST COARSE REGION
    # --------------------------------------------------------
    beta_center = best_params[0]
    relax_center = best_params[1]
    pressure_center = best_params[2]
    cross_center = best_params[3]

    zoom_betas = np.unique(
        np.round(
            np.linspace(
                max(0.90, beta_center - 0.004),
                min(0.9995, beta_center + 0.004),
                33,
            ),
            6,
        )
    )
    zoom_relax = np.unique(
        np.round(
            np.linspace(
                max(0.20, relax_center - 0.15),
                relax_center + 0.15,
                9,
            ),
            6,
        )
    )
    zoom_pressure = np.unique(
        np.round(
            np.linspace(
                max(0.01, pressure_center - 0.05),
                pressure_center + 0.05,
                5,
            ),
            6,
        )
    )

    zoom = sweep(
        zoom_betas,
        zoom_relax,
        zoom_pressure,
        [cross_center],
        noise_std=0.0,
    )
    zoom.to_csv(OUT / "zoom.csv", index=False)

    zoom_top = zoom.sort_values(
        "resonance_score",
        ascending=False,
    ).head(8).copy()

    zoom_best = zoom_top.iloc[0]
    resonance_params = (
        float(zoom_best.beta),
        float(zoom_best.relaxation),
        float(zoom_best.pressure_gain),
        float(zoom_best.cross_gain),
    )

    # --------------------------------------------------------
    # 3) FINE BETA SCAN + EXPONENTIAL FIT
    # --------------------------------------------------------
    fine_betas = np.round(np.linspace(0.94, 0.998, 59), 6)

    fine_rows = []
    for beta in fine_betas:
        cfg = Config(
            beta_memory=float(beta),
            relaxation=resonance_params[1],
            pressure_gain=resonance_params[2],
            cross_gain=resonance_params[3],
            noise_std=0.0,
        )
        fine_rows.append(
            {
                "beta": float(beta),
                "path_gap": path_dependence(cfg, seed=SEED),
                "critical_lift": critical_lift(cfg, seed=SEED)[0],
            }
        )

    fine = pd.DataFrame(fine_rows)
    fine.to_csv(OUT / "fine_beta.csv", index=False)

    exp_fit = exponential_fit(
        fine["beta"].to_numpy(),
        fine["path_gap"].to_numpy(),
    )

    # --------------------------------------------------------
    # 4) VALIDATION AGAINST CONTROLS
    # --------------------------------------------------------
    candidates = {
        "resonance": resonance_params,
        "same_beta_default_dynamics": (
            resonance_params[0],
            0.32,
            0.55,
            0.85,
        ),
        "baseline_default_config": (
            0.92,
            0.32,
            0.55,
            0.85,
        ),
        "beta_minus_0_01": (
            max(0.90, resonance_params[0] - 0.01),
            resonance_params[1],
            resonance_params[2],
            resonance_params[3],
        ),
        "beta_plus_0_001": (
            min(0.9995, resonance_params[0] + 0.001),
            resonance_params[1],
            resonance_params[2],
            resonance_params[3],
        ),
    }

    validation = [
        validate_candidate(label, params)
        for label, params in candidates.items()
    ]

    val_frame = pd.DataFrame(validation)
    val_frame.to_csv(OUT / "validation.csv", index=False)

    resonance = val_frame[val_frame["label"] == "resonance"].iloc[0]
    baseline = val_frame[
        val_frame["label"] == "baseline_default_config"
    ].iloc[0]

    summary = {
        "experiment": "parametric_resonance_v1",
        "seed_coarse": SEED,
        "validation_seeds": VALIDATION_SEEDS,
        "coarse_points": int(len(coarse)),
        "zoom_points": int(len(zoom)),
        "resonance_parameters": {
            "beta_memory": resonance_params[0],
            "relaxation": resonance_params[1],
            "pressure_gain": resonance_params[2],
            "cross_gain": resonance_params[3],
        },
        "coarse_top": top.to_dict(orient="records"),
        "zoom_top": zoom_top.to_dict(orient="records"),
        "exponential_fit": exp_fit,
        "validation": validation,
        "path_gap_amplification_vs_baseline": float(
            resonance["path_gap_mean"] /
            max(baseline["path_gap_mean"], 1e-12)
        ),
        "critical_lift_ratio_vs_baseline": float(
            resonance["critical_lift_mean"] /
            max(baseline["critical_lift_mean"], 1e-12)
        ),
        "validation_rule": (
            "The resonance candidate is considered robust in this experiment "
            "only when all validation seeds retain positive critical_lift and "
            "the candidate remains materially separated from the baseline."
        ),
        "interpretation": (
            "This experiment searches for nonlinear parameter regimes. "
            "An exponential fit describes an empirical scaling of the measured "
            "path-dependence observable over the fitted beta interval; it is "
            "not by itself evidence of consciousness or a physical law."
        ),
    }

    (OUT / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=" * 80)
    print("CONSCIENCIA PARA IA — PARAMETRIC RESONANCE V1")
    print("=" * 80)

    print("\nCOARSE:")
    print(f"  points={len(coarse)}")
    print(
        "  best="
        f"beta={best_params[0]:.6f} "
        f"relax={best_params[1]:.6f} "
        f"pressure={best_params[2]:.6f} "
        f"cross={best_params[3]:.6f}"
    )
    print(
        f"  path_gap={float(best.path_gap):.6f} "
        f"critical_lift={float(best.critical_lift):.6f} "
        f"score={float(best.resonance_score):.6f}"
    )

    print("\nZOOM:")
    print(f"  points={len(zoom)}")
    print(
        "  best="
        f"beta={resonance_params[0]:.6f} "
        f"relax={resonance_params[1]:.6f} "
        f"pressure={resonance_params[2]:.6f} "
        f"cross={resonance_params[3]:.6f}"
    )
    print(
        f"  path_gap={float(zoom_best.path_gap):.6f} "
        f"critical_lift={float(zoom_best.critical_lift):.6f} "
        f"score={float(zoom_best.resonance_score):.6f}"
    )

    print("\nEXPONENTIAL FIT:")
    for key, value in exp_fit.items():
        print(f"  {key}={value}")

    print("\nVALIDATION:")
    for row in validation:
        print(
            f"  {row['label']}: "
            f"path_gap={row['path_gap_mean']:.6f}±{row['path_gap_sd']:.6f}; "
            f"critical_lift={row['critical_lift_mean']:.6f}±{row['critical_lift_sd']:.6f}; "
            f"positive_fraction={row['positive_critical_fraction']:.3f}"
        )

    print("\nAMPLIFICATION:")
    print(
        f"  path_gap_vs_baseline="
        f"{summary['path_gap_amplification_vs_baseline']:.3f}x"
    )
    print(
        f"  critical_lift_vs_baseline="
        f"{summary['critical_lift_ratio_vs_baseline']:.3f}x"
    )
    print(f"\nRESULT: {OUT / 'summary.json'}")
    print("=" * 80)


if __name__ == "__main__":
    main()

from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT = Path("results/state_lesion_v15")
OUT.mkdir(parents=True, exist_ok=True)

REGIMES = {
    "critical": {"beta_memory": .998606, "relaxation": 1.205, "pressure_gain": .125, "cross_gain": .15},
    "holdout_critical": {"beta_memory": .9976, "relaxation": 1.10, "pressure_gain": .125, "cross_gain": .20},
    "persistence": {"beta_memory": .99730, "relaxation": 1.205, "pressure_gain": .125, "cross_gain": .15},
    "baseline": {"beta_memory": .92, "relaxation": .32, "pressure_gain": .55, "cross_gain": .85},
}

# 0.0 = intact donor context; 1.0 = complete replacement by the common context.
DOSES = [0.0, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 1.0]
SEEDS = range(20)
N_HISTORY = 300
N_FUTURE = 120
IDENTITY_WINDOW = 60

def history(pair, seed, n=N_HISTORY):
    rng = np.random.default_rng(seed + 1000 * pair)
    if pair == 0:
        return np.ones(n), -np.ones(n)
    if pair == 1:
        return np.where(np.arange(n) % 2 == 0, 1.0, -1.0), np.ones(n)
    if pair == 2:
        return (
            np.where(rng.random(n) < .12, -1.0, 1.0),
            np.where(rng.random(n) < .06, 1.0, -1.0),
        )
    return (
        np.sign(np.sin(np.linspace(0, 18 * np.pi, n))),
        np.sign(np.sin(np.linspace(0, 6 * np.pi, n) + 1.7)),
    )

def extract(cfg, seed, inp):
    r = simulate(np.r_[inp, np.zeros(N_FUTURE)], cfg, seed=seed)
    i = N_HISTORY
    return {
        "state_prev": float(r["state"][i - 2]),
        "state": float(r["state"][i - 1]),
        "memory": float(r["memory"][i - 1]),
        "pressure": float(r["pressure"][i - 1]),
    }

def cont(cfg, ctx, seed):
    return simulate(
        np.zeros(N_FUTURE),
        cfg,
        seed=seed,
        initial_prev_state=ctx["state_prev"],
        initial_state=ctx["state"],
        initial_memory=ctx["memory"],
        initial_pressure=ctx["pressure"],
    )

def dist(a, b):
    return float(np.mean(np.abs(a["state"][:IDENTITY_WINDOW] - b["state"][:IDENTITY_WINDOW])))

def affinity(run, ref_a, ref_b):
    da, db = dist(run, ref_a), dist(run, ref_b)
    return float((db - da) / max(da + db, 1e-12))

def interpolate_context(donor, common, lesion, dose):
    ctx = dict(donor)
    if lesion == "state":
        for k in ("state_prev", "state"):
            ctx[k] = (1.0 - dose) * donor[k] + dose * common[k]
    elif lesion == "memory":
        ctx["memory"] = (1.0 - dose) * donor["memory"] + dose * common["memory"]
    elif lesion == "pressure":
        ctx["pressure"] = (1.0 - dose) * donor["pressure"] + dose * common["pressure"]
    else:
        raise ValueError(lesion)
    return ctx

def main():
    rows = []
    for regime, params in REGIMES.items():
        cfg = Config(**params, noise_std=.01)
        for pair in range(4):
            for seed in SEEDS:
                a = extract(cfg, seed, history(pair, seed)[0])
                b = extract(cfg, seed, history(pair, seed)[1])
                ra, rb = cont(cfg, a, seed), cont(cfg, b, seed)
                common = {k: (a[k] + b[k]) / 2.0 for k in a}
                for donor_name, donor in [("A", a), ("B", b)]:
                    expected = 1 if donor_name == "A" else -1
                    for lesion in ("state", "memory", "pressure"):
                        for dose in DOSES:
                            ctx = interpolate_context(donor, common, lesion, dose)
                            run = cont(cfg, ctx, seed)
                            aff = affinity(run, ra, rb)
                            ref = ra if donor_name == "A" else rb
                            pred_error = float(np.mean(np.abs(run["state"][:IDENTITY_WINDOW] - ref["state"][:IDENTITY_WINDOW])))
                            rows.append({
                                "regime": regime, "pair": pair, "seed": seed, "donor": donor_name,
                                "lesion": lesion, "dose": dose, "affinity": aff, "abs_affinity": abs(aff),
                                "correct": int(np.sign(aff) == expected),
                                "prediction_mae_vs_donor": pred_error,
                                "state_context_distance": float(np.mean([
                                    abs(ctx["state_prev"] - common["state_prev"]),
                                    abs(ctx["state"] - common["state"]),
                                ])),
                                "memory_context_distance": abs(ctx["memory"] - common["memory"]),
                                "pressure_context_distance": abs(ctx["pressure"] - common["pressure"]),
                            })
    raw = pd.DataFrame(rows)
    raw.to_csv(OUT / "raw.csv", index=False)
    summary = raw.groupby(["regime", "lesion", "dose"], as_index=False).agg(
        identity_accuracy=("correct", "mean"),
        abs_affinity=("abs_affinity", "mean"),
        affinity=("affinity", "mean"),
        prediction_mae=("prediction_mae_vs_donor", "mean"),
        prediction_mae_sd=("prediction_mae_vs_donor", "std"),
    )
    summary.to_csv(OUT / "summary.csv", index=False)
    full = summary[np.isclose(summary["dose"], 1.0)]
    selectivity = []
    for regime in REGIMES:
        s = full[full["regime"] == regime].set_index("lesion")
        intact = summary[(summary["regime"] == regime) & np.isclose(summary["dose"], 0.0)]
        intact_acc = float(intact.identity_accuracy.iloc[0])
        row = {"regime": regime, "intact_accuracy": intact_acc}
        for lesion in ("state", "memory", "pressure"):
            row[f"{lesion}_full_lesion_accuracy"] = float(s.loc[lesion, "identity_accuracy"])
            row[f"{lesion}_accuracy_loss"] = intact_acc - float(s.loc[lesion, "identity_accuracy"])
        selectivity.append(row)
    selectivity_df = pd.DataFrame(selectivity)
    selectivity_df.to_csv(OUT / "selectivity.csv", index=False)
    result = {
        "experiment": "state_lesion_v15",
        "design": {
            "history_pairs": 4, "seeds_per_pair": len(list(SEEDS)), "doses": DOSES,
            "lesions": ["state", "memory", "pressure"], "future_input": "exactly zero",
            "matched_noise_seed": True, "identity_window": IDENTITY_WINDOW,
            "lesion_definition": "interpolate one selected donor context component toward the A/B common context",
        },
        "selectivity": selectivity_df.to_dict("records"),
    }
    (OUT / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("SELECTIVITY")
    print(selectivity_df.to_string(index=False))
    print("\nSUMMARY")
    print(summary.to_string(index=False))

if __name__ == "__main__":
    main()
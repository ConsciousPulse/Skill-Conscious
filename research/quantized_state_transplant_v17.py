from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT = Path("results/quantized_state_transplant_v17")
OUT.mkdir(parents=True, exist_ok=True)

# Deliberately uses the six V12 blind-holdout parameter points.
PARAMS = [
    {"name":"p1","beta_memory":.9967,"relaxation":1.15,"pressure_gain":.125,"cross_gain":.15},
    {"name":"p2","beta_memory":.9971,"relaxation":1.20,"pressure_gain":.150,"cross_gain":.20},
    {"name":"p3","beta_memory":.9976,"relaxation":1.10,"pressure_gain":.125,"cross_gain":.20},
    {"name":"p4","beta_memory":.9979,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.15},
    {"name":"p5","beta_memory":.9982,"relaxation":1.12,"pressure_gain":.175,"cross_gain":.20},
    {"name":"p6","beta_memory":.9989,"relaxation":1.18,"pressure_gain":.150,"cross_gain":.20},
]
SEEDS = range(10)
N_HISTORY = 300
N_FUTURE = 120
WINDOW = 60
BITS = [1, 2, 3, 4, 6, 8]

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
        np.zeros(N_FUTURE), cfg, seed=seed,
        initial_prev_state=ctx["state_prev"],
        initial_state=ctx["state"],
        initial_memory=ctx["memory"],
        initial_pressure=ctx["pressure"],
    )

def quantize(x, bits):
    levels = 2 ** bits
    step = 2.0 / (levels - 1)
    y = np.clip(x, -1.0, 1.0)
    return float(-1.0 + np.round((y + 1.0) / step) * step)

def dist(a, b):
    return float(np.mean(np.abs(a["state"][:WINDOW] - b["state"][:WINDOW])))

def affinity(run, ref_a, ref_b):
    da, db = dist(run, ref_a), dist(run, ref_b)
    return float((db - da) / max(da + db, 1e-12))

def main():
    rows = []
    for pp in PARAMS:
        cfg = Config(**{k:v for k,v in pp.items() if k != "name"}, noise_std=.01)
        for pair in range(4):
            for seed in SEEDS:
                a = extract(cfg, seed, history(pair, seed)[0])
                b = extract(cfg, seed, history(pair, seed)[1])
                ra, rb = cont(cfg, a, seed), cont(cfg, b, seed)
                common = {k: (a[k] + b[k]) / 2.0 for k in a}
                for donor_name, donor in [("A", a), ("B", b)]:
                    expected = 1 if donor_name == "A" else -1
                    for mode, bits in [("state_only_full", None)] + [("state_only_quantized", b) for b in BITS]:
                        ctx = dict(common)
                        if bits is None:
                            ctx["state_prev"], ctx["state"] = donor["state_prev"], donor["state"]
                        else:
                            ctx["state_prev"] = quantize(donor["state_prev"], bits)
                            ctx["state"] = quantize(donor["state"], bits)
                        run = cont(cfg, ctx, seed)
                        aff = affinity(run, ra, rb)
                        ref = ra if donor_name == "A" else rb
                        rows.append({
                            "param": pp["name"], "beta": pp["beta_memory"],
                            "relaxation": pp["relaxation"], "pressure_gain": pp["pressure_gain"],
                            "cross_gain": pp["cross_gain"], "pair": pair, "seed": seed,
                            "donor": donor_name, "mode": mode, "bits": bits if bits is not None else np.nan,
                            "affinity": aff, "abs_affinity": abs(aff),
                            "correct": int(np.sign(aff) == expected),
                            "prediction_mae_vs_donor": float(np.mean(np.abs(run["state"][:WINDOW] - ref["state"][:WINDOW]))),
                        })
    raw = pd.DataFrame(rows)
    raw.to_csv(OUT / "raw.csv", index=False)
    summary = raw.groupby(["param","mode","bits"], dropna=False, as_index=False).agg(
        identity_accuracy=("correct","mean"),
        abs_affinity=("abs_affinity","mean"),
        affinity=("affinity","mean"),
        prediction_mae=("prediction_mae_vs_donor","mean"))
    pooled = raw.groupby(["mode","bits"], dropna=False, as_index=False).agg(
        identity_accuracy=("correct","mean"),
        abs_affinity=("abs_affinity","mean"),
        affinity=("affinity","mean"),
        prediction_mae=("prediction_mae_vs_donor","mean"))
    summary.to_csv(OUT / "by_param.csv", index=False)
    pooled.to_csv(OUT / "pooled.csv", index=False)
    payload = {
        "experiment":"quantized_state_transplant_v17",
        "design":{
            "blind_parameter_points":6, "history_pairs":4, "seeds_per_pair":10,
            "future_input":"exactly zero", "matched_noise_seed":True,
            "receiver_memory_and_pressure":"common A/B midpoint",
            "receiver_state":"donor state, optionally quantized",
            "bits":BITS,
        },
        "pooled":pooled.to_dict("records"),
        "by_param":summary.to_dict("records"),
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("POOLED")
    print(pooled.to_string(index=False))
    print("\nBY PARAM")
    print(summary.to_string(index=False))

if __name__ == "__main__":
    main()
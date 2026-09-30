from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.ontto.dynamics import Config, simulate

OUT = Path("results/minimal_state_v16")
OUT.mkdir(parents=True, exist_ok=True)

REGIMES = {
    "critical": {"beta_memory": .998606, "relaxation": 1.205, "pressure_gain": .125, "cross_gain": .15},
    "holdout_critical": {"beta_memory": .9976, "relaxation": 1.10, "pressure_gain": .125, "cross_gain": .20},
    "persistence": {"beta_memory": .99730, "relaxation": 1.205, "pressure_gain": .125, "cross_gain": .15},
    "baseline": {"beta_memory": .92, "relaxation": .32, "pressure_gain": .55, "cross_gain": .85},
}

SEEDS = range(20)
N_HISTORY = 300
N_FUTURE = 120
WINDOW = 60

# Uniform quantization over the natural tanh state range [-1, 1].
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

def interpolate_state(a, b, mode, bits=None):
    out = dict(a)
    if mode == "full":
        return out
    if mode == "current_only":
        out["state_prev"] = b["state_prev"]
        return out
    if mode == "previous_only":
        out["state"] = b["state"]
        return out
    if mode == "state_zero":
        out["state_prev"] = b["state_prev"]
        out["state"] = b["state"]
        return out
    if mode == "quantized":
        out["state_prev"] = quantize(out["state_prev"], bits)
        out["state"] = quantize(out["state"], bits)
        return out
    raise ValueError(mode)

def dist(a, b):
    return float(np.mean(np.abs(a["state"][:WINDOW] - b["state"][:WINDOW])))

def affinity(run, ref_a, ref_b):
    da, db = dist(run, ref_a), dist(run, ref_b)
    return float((db - da) / max(da + db, 1e-12))

def main():
    rows = []
    for regime, params in REGIMES.items():
        cfg = Config(**params, noise_std=.01)
        for pair in range(4):
            for seed in SEEDS:
                a = extract(cfg, seed, history(pair, seed)[0])
                b = extract(cfg, seed, history(pair, seed)[1])
                ra, rb = cont(cfg, a, seed), cont(cfg, b, seed)
                for donor_name, donor in [("A", a), ("B", b)]:
                    expected = 1 if donor_name == "A" else -1
                    common = {k: (a[k] + b[k]) / 2.0 for k in a}
                    # Structural bottlenecks: preserve one temporal state slot.
                    for mode in ("full", "current_only", "previous_only", "state_zero"):
                        ctx = interpolate_state(donor, common, mode)
                        run = cont(cfg, ctx, seed)
                        aff = affinity(run, ra, rb)
                        ref = ra if donor_name == "A" else rb
                        rows.append({
                            "regime": regime, "pair": pair, "seed": seed, "donor": donor_name,
                            "mode": mode, "bits": np.nan, "affinity": aff,
                            "abs_affinity": abs(aff), "correct": int(np.sign(aff) == expected),
                            "prediction_mae": float(np.mean(np.abs(run["state"][:WINDOW] - ref["state"][:WINDOW]))),
                        })
                    # Precision bottleneck: keep both temporal slots, quantize only state.
                    for bits in BITS:
                        ctx = interpolate_state(donor, common, "quantized", bits=bits)
                        run = cont(cfg, ctx, seed)
                        aff = affinity(run, ra, rb)
                        ref = ra if donor_name == "A" else rb
                        rows.append({
                            "regime": regime, "pair": pair, "seed": seed, "donor": donor_name,
                            "mode": "quantized", "bits": bits, "affinity": aff,
                            "abs_affinity": abs(aff), "correct": int(np.sign(aff) == expected),
                            "prediction_mae": float(np.mean(np.abs(run["state"][:WINDOW] - ref["state"][:WINDOW]))),
                        })
    raw = pd.DataFrame(rows)
    raw.to_csv(OUT / "raw.csv", index=False)
    summary = (
        raw.groupby(["regime", "mode", "bits"], dropna=False, as_index=False)
        .agg(identity_accuracy=("correct", "mean"),
             abs_affinity=("abs_affinity", "mean"),
             affinity=("affinity", "mean"),
             prediction_mae=("prediction_mae", "mean"))
    )
    summary.to_csv(OUT / "summary.csv", index=False)

    structural = summary[summary["mode"].isin(["full", "current_only", "previous_only", "state_zero"])]
    quant = summary[summary["mode"] == "quantized"].copy()
    quant["bit_error_from_full"] = np.nan
    for regime in REGIMES:
        full = float(structural[(structural["regime"] == regime) & (structural["mode"] == "full")].identity_accuracy.iloc[0])
        mask = quant["regime"] == regime
        quant.loc[mask, "bit_error_from_full"] = full - quant.loc[mask, "identity_accuracy"]
    structural.to_csv(OUT / "structural.csv", index=False)
    quant.to_csv(OUT / "quantization.csv", index=False)

    payload = {
        "experiment": "minimal_state_v16",
        "design": {
            "history_pairs": 4, "seeds_per_pair": len(list(SEEDS)),
            "future_input": "exactly zero", "matched_noise_seed": True,
            "structural_modes": ["full", "current_only", "previous_only", "state_zero"],
            "quantization_bits": BITS, "quantizer_range": [-1.0, 1.0],
        },
        "structural": structural.to_dict("records"),
        "quantization": quant.to_dict("records"),
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("STRUCTURAL")
    print(structural.to_string(index=False))
    print("\nQUANTIZATION")
    print(quant.to_string(index=False))

if __name__ == "__main__":
    main()
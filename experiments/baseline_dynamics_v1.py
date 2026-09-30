import json
from pathlib import Path

import numpy as np

from src.ontto.dynamics import Config, metrics, simulate


SEED = 0
STEPS = 200
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

cfg = Config(
    beta_memory=0.85,
    alpha_pressure=0.20,
    pressure_gain=0.15,
    pressure_cap=2.0,
    theta0=0.20,
    theta_pressure=0.10,
    noise_std=0.0,
    attractor=0.0,
    attractor_gain=0.12,
    coupling_gain=0.20,
    cross_gain=0.25,
    relaxation=0.10,
    use_memory=True,
    use_pressure=True,
    use_cross=True,
    use_x=True,
    use_attractor=True,
)

inputs = np.zeros(STEPS, dtype=float)
inputs[20:40] = 1.0
inputs[80:100] = -1.0
inputs[140:155] = 0.65

result = simulate(inputs=inputs, cfg=cfg, seed=SEED)
report = metrics(result, warmup=100)

required = [
    "input", "state", "memory", "pressure", "score", "q",
    "L3", "L6", "L9", "Lx", "cross", "theta",
]
for key in required:
    assert key in result, f"missing series: {key}"
    assert len(result[key]) == STEPS, f"invalid length for {key}"

unique_q = sorted({str(x) for x in result["q"]})

payload = {
    "experiment": "baseline_dynamics_v1",
    "seed": SEED,
    "steps": STEPS,
    "input_segments": [
        {"start": 0, "end": 19, "value": 0.0},
        {"start": 20, "end": 39, "value": 1.0},
        {"start": 40, "end": 79, "value": 0.0},
        {"start": 80, "end": 99, "value": -1.0},
        {"start": 100, "end": 139, "value": 0.0},
        {"start": 140, "end": 154, "value": 0.65},
        {"start": 155, "end": 199, "value": 0.0},
    ],
    "metrics": {
        key: float(value) for key, value in report.items()
    },
    "unique_q": unique_q,
    "commit_placeholder": "recorded by GitHub Actions workflow",
}

output = RESULTS_DIR / "baseline_dynamics_v1.json"
output.write_text(
    json.dumps(payload, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 70)
print("CONSCIENCIA PARA IA — BASELINE DYNAMICS V1")
print("=" * 70)
print(f"steps={STEPS}")
print(f"seed={SEED}")
print("metrics:")
for key, value in report.items():
    print(f"  {key}={value}")
print(f"unique_q={unique_q}")
print(f"artifact={output}")
print("=" * 70)

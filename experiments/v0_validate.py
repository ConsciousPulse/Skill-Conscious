import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

from src.ontto.dynamics import Config, simulate, common_attractor_simulation, metrics

SEED = 42
N = 6000
WARMUP = 500

rng = np.random.default_rng(SEED)

# Structured binary input with two regimes.
u = np.empty(N)
state = 1.0
for t in range(N):
    if rng.random() < (0.03 if t < N // 2 else 0.11):
        state *= -1.0
    u[t] = state

full = simulate(u, Config(), seed=SEED)

baseline_cfg = Config(
    use_memory=False,
    use_pressure=False,
    use_cross=False,
    use_x=False,
    use_attractor=False,
)
baseline = simulate(u, baseline_cfg, seed=SEED)

print("FULL", metrics(full, WARMUP))
print("BASELINE", metrics(baseline, WARMUP))

# Same suffix, different histories.
prefix_a = np.ones(200)
prefix_b = -np.ones(200)
suffix = np.ones(60)
path_cfg = Config(beta_memory=0.97)
run_a = simulate(np.r_[prefix_a, suffix], path_cfg, seed=SEED)
run_b = simulate(np.r_[prefix_b, suffix], path_cfg, seed=SEED)
gap = np.mean(np.abs(run_a["state"][201:260] - run_b["state"][201:260]))
print("PATH_DEPENDENCE_MEAN_STATE_GAP", float(gap))

# Common-attractor coupling.
inputs = rng.choice([-1.0, 1.0], size=(8, N))
ca = common_attractor_simulation(inputs, n_agents=8, cfg=Config(coupling_gain=0.4), seed=SEED)
ca0 = common_attractor_simulation(inputs, n_agents=8, cfg=Config(coupling_gain=0.0), seed=SEED)

spread = float(np.mean(np.std(ca["states"][:, -500:], axis=0)))
spread0 = float(np.mean(np.std(ca0["states"][:, -500:], axis=0)))
print("COMMON_ATTRACTOR_SPREAD_COUPLED", spread)
print("COMMON_ATTRACTOR_SPREAD_UNCOUPLED", spread0)
print("COMMON_ATTRACTOR_SPREAD_REDUCTION", float(1.0 - spread / spread0))

# External predictor: current internal state vs input alone.
q = full["q"]
mask = np.array([x in (0, 1) for x in q])
X = np.column_stack([
    full["state"],
    full["memory"],
    full["pressure"],
    full["cross"],
    np.abs(full["score"]),
    full["input"],
])
X = X[:-1][mask[:-1]]
y = np.array([1 if x == 1 else 0 for x in q[1:][mask[:-1]]])

split = int(0.7 * len(X))
clf = LogisticRegression(max_iter=1000)
clf.fit(X[:split], y[:split])
full_acc = float(accuracy_score(y[split:], clf.predict(X[split:])))

X_input = full["input"][:-1][mask[:-1]].reshape(-1, 1)
clf0 = LogisticRegression(max_iter=1000)
clf0.fit(X_input[:split], y[:split])
base_acc = float(accuracy_score(y[split:], clf0.predict(X_input[split:])))

print("EXTERNAL_NEXT_OUTPUT_ACCURACY_FULL_STATE", full_acc)
print("EXTERNAL_NEXT_OUTPUT_ACCURACY_INPUT_ONLY", base_acc)
print("SELF_STATE_INFORMATION_GAIN", float(full_acc - base_acc))

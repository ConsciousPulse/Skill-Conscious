from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
import numpy as np

# Research note: v5 memory-lifetime scans use this same dynamics implementation.


@dataclass
class Config:
    beta_memory: float = 0.92
    alpha_pressure: float = 0.94
    pressure_gain: float = 0.55
    pressure_cap: float = 4.0
    theta0: float = 0.20
    theta_pressure: float = 0.10
    noise_std: float = 0.025
    attractor: float = 0.0
    attractor_gain: float = 0.18
    coupling_gain: float = 0.12
    cross_gain: float = 0.85
    relaxation: float = 0.32
    use_memory: bool = True
    use_pressure: bool = True
    use_cross: bool = True
    use_x: bool = True
    use_attractor: bool = True


def simulate(inputs: np.ndarray, cfg: Config | None = None, seed: int = 0,
             initial_state: float = 0.0, shared_attractor: float | None = None,
             initial_prev_state: float | None = None, initial_memory: float = 0.0,
             initial_pressure: float = 0.0) -> Dict[str, np.ndarray]:
    """Simulate one relational agent.

    L3/L6/L9/Lx are operational analogues inspired by project terminology.
    They are not claims about physical quantum operators.
    """
    cfg = cfg or Config()
    rng = np.random.default_rng(seed)
    u = np.asarray(inputs, dtype=float)
    n = len(u)
    r = np.zeros(n)
    m = np.zeros(n)
    p = np.zeros(n)
    z = np.zeros(n)
    q = np.empty(n, dtype=object)
    l3 = np.zeros(n)
    l6 = np.zeros(n)
    l9 = np.zeros(n)
    lx = np.zeros(n)
    theta = np.zeros(n)
    cross = np.zeros(n)

    r[0] = initial_prev_state if initial_prev_state is not None else initial_state
    if n > 1:
        r[1] = initial_state
        m[1] = initial_memory
        p[1] = initial_pressure
    target = cfg.attractor if shared_attractor is None else shared_attractor
    q[0] = 1 if r[0] >= 0 else 0

    for t in range(2, n):
        if cfg.use_memory:
            m[t] = cfg.beta_memory * m[t - 1] + (1 - cfg.beta_memory) * u[t - 1]

        grad = r[t - 1] - r[t - 2]
        curv = r[t - 1] - 2 * r[t - 2] + (r[t - 3] if t >= 3 else 0.0)
        flip = float(u[t] != u[t - 1])
        disagree = float(np.sign(u[t]) != np.sign(m[t - 1])) if cfg.use_memory else 0.0

        l3[t] = -(r[t - 1] - 0.18 * m[t])
        l6[t] = -(r[t - 1] - np.tanh(m[t])) + 0.50 * (grad ** 2) * np.sign(grad if abs(grad) > 1e-12 else 1.0)
        l9[t] = abs(curv) * np.sign(r[t - 1] if abs(r[t - 1]) > 1e-12 else 1.0)
        lx[t] = (grad ** 2) * curv if cfg.use_cross else 0.0
        cross[t] = abs(np.tanh(cfg.cross_gain * lx[t]))

        transition_pressure = 0.7 * flip + 0.5 * disagree + 0.8 * cross[t] + 0.3 * abs(np.tanh(3 * curv))
        if cfg.use_pressure:
            p[t] = min(cfg.pressure_cap, cfg.alpha_pressure * p[t - 1] + cfg.pressure_gain * transition_pressure)

        attractor_term = cfg.attractor_gain * (target - r[t - 1]) if cfg.use_attractor else 0.0

        z[t] = (
            0.85 * u[t]
            + 0.75 * l3[t]
            + 0.85 * np.tanh(l6[t])
            - 0.65 * np.tanh(2.0 * l9[t])
            + 0.95 * np.tanh(cfg.cross_gain * lx[t])
            + 0.55 * np.tanh(m[t])
            + attractor_term
            - 0.20 * p[t]
            + rng.normal(0.0, cfg.noise_std)
        )

        r[t] = np.tanh(r[t - 1] + cfg.relaxation * z[t])
        theta[t] = cfg.theta0 + cfg.theta_pressure * (np.tanh(p[t]) if cfg.use_pressure else 0.0)

        if cfg.use_x and abs(z[t]) <= theta[t]:
            q[t] = "X"
        elif z[t] > theta[t]:
            q[t] = 1
        else:
            q[t] = 0

    return {
        "input": u, "state": r, "memory": m, "pressure": p, "score": z, "q": q,
        "L3": l3, "L6": l6, "L9": l9, "Lx": lx, "cross": cross, "theta": theta,
    }


def common_attractor_simulation(inputs: np.ndarray, n_agents: int = 8,
                                cfg: Config | None = None, seed: int = 0) -> Dict[str, np.ndarray]:
    """Couple agents through a shared attractor estimate."""
    cfg = cfg or Config()
    rng = np.random.default_rng(seed)
    inputs = np.asarray(inputs, dtype=float)
    n = inputs.shape[1]
    states = np.zeros((n_agents, n))
    outputs = np.empty((n_agents, n), dtype=object)
    attractor_trace = np.zeros(n)
    memories = np.zeros(n_agents)
    init = rng.normal(0, 0.55, size=n_agents)

    for t in range(n):
        mean_state = float(np.mean(states[:, t - 1])) if t > 0 else 0.0
        attractor_trace[t] = mean_state
        for a in range(n_agents):
            if t == 0:
                states[a, t] = np.tanh(init[a])
                outputs[a, t] = 1 if states[a, t] >= 0 else 0
                continue

            prev = states[a, t - 1]
            memories[a] = cfg.beta_memory * memories[a] + (1 - cfg.beta_memory) * inputs[a, t - 1]
            delta = prev - states[a, t - 2] if t >= 2 else 0.0
            local_drive = 0.7 * inputs[a, t] + 0.55 * np.tanh(memories[a])
            coupling = cfg.coupling_gain * (mean_state - prev)
            noise = rng.normal(0, cfg.noise_std)
            states[a, t] = np.tanh(prev + cfg.relaxation * (local_drive + coupling + noise))

            theta = cfg.theta0 + 0.06 * abs(delta)
            score = states[a, t]
            outputs[a, t] = "X" if (cfg.use_x and abs(score) <= theta) else (1 if score > 0 else 0)

    return {"states": states, "q": outputs, "attractor": attractor_trace}


def metrics(run: Dict[str, np.ndarray], warmup: int = 100) -> Dict[str, float]:
    q = run["q"][warmup:]
    state = run["state"][warmup:]
    cross = run["cross"][warmup:]
    out = {
        "x_occupancy": float(np.mean(q == "X")),
        "mean_abs_state": float(np.mean(np.abs(state))),
        "state_variance": float(np.var(state)),
    }
    hi = cross >= np.quantile(cross, 0.75)
    lo = cross <= np.quantile(cross, 0.25)
    out["x_given_high_cross"] = float(np.mean((q == "X")[hi])) if np.any(hi) else np.nan
    out["x_given_low_cross"] = float(np.mean((q == "X")[lo])) if np.any(lo) else np.nan
    out["critical_lift"] = out["x_given_high_cross"] - out["x_given_low_cross"]
    return out

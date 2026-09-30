import numpy as np

from src.ontto.dynamics import Config, simulate, common_attractor_simulation


def test_shapes():
    u = np.sign(np.sin(np.linspace(0, 30, 500)))
    run = simulate(u, Config(), seed=1)
    assert len(run["state"]) == 500
    assert len(run["q"]) == 500


def test_memory_changes_trajectory():
    u = np.ones(600)
    u[300:] = -1
    a = simulate(u, Config(use_memory=True), seed=2)
    b = simulate(u, Config(use_memory=False), seed=2)
    assert not np.allclose(a["state"], b["state"])


def test_common_attractor_exists():
    rng = np.random.default_rng(3)
    inputs = rng.choice([-1.0, 1.0], size=(6, 800))
    out = common_attractor_simulation(inputs, n_agents=6, seed=4)
    assert out["states"].shape == (6, 800)

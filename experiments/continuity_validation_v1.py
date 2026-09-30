from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np

from src.ontto.dynamics import Config, common_attractor_simulation, metrics, simulate
from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore


SEED = 42
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def mean_abs_gap(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(a) - np.asarray(b))))


def recovery_time(
    state: np.ndarray,
    start: int,
    baseline: float,
    tolerance: float = 0.10,
    horizon: int = 100,
) -> int | None:
    end = min(len(state), start + horizon)
    for t in range(start, end):
        if abs(float(state[t]) - baseline) <= tolerance:
            return int(t - start)
    return None


class FakeProvider:
    """Deterministic provider for the WAKE/DREAM persistence experiment."""

    def chat(self, messages, temperature=0.7):
        last = messages[-1]["content"]
        if "Entraste en SUEÑO" in last:
            text = (
                "Sueño determinista. "
                "MEMORY: Consolidé una relación persistente entre trayectoria y continuidad.\n"
                "SELF_MODEL: Mantengo memoria persistente y dos regímenes de actividad.\n"
                "DREAM_SUMMARY: Revisé memoria, trayectoria y auto-modelo."
            )
        else:
            text = (
                "Vigilia determinista. "
                "MEMORY: La interacción actual forma parte de una trayectoria continua.\n"
            )
        return LLMResponse(text=text, raw={"fake": True})


def experiment_a_path_dependence() -> dict:
    prefix_a = np.ones(240)
    prefix_b = -np.ones(240)
    suffix = np.ones(80)

    cfg = Config(beta_memory=0.97, noise_std=0.0)
    full_a = simulate(np.r_[prefix_a, suffix], cfg, seed=SEED)
    full_b = simulate(np.r_[prefix_b, suffix], cfg, seed=SEED)

    no_memory = Config(
        beta_memory=0.97,
        noise_std=0.0,
        use_memory=False,
    )
    base_a = simulate(np.r_[prefix_a, suffix], no_memory, seed=SEED)
    base_b = simulate(np.r_[prefix_b, suffix], no_memory, seed=SEED)

    return {
        "same_suffix_mean_state_gap_with_memory": mean_abs_gap(
            full_a["state"][241:320], full_b["state"][241:320]
        ),
        "same_suffix_mean_state_gap_without_memory": mean_abs_gap(
            base_a["state"][241:320], base_b["state"][241:320]
        ),
        "path_dependence_ratio": float(
            mean_abs_gap(full_a["state"][241:320], full_b["state"][241:320])
            / max(mean_abs_gap(base_a["state"][241:320], base_b["state"][241:320]), 1e-12)
        ),
    }


def experiment_b_common_attractor() -> dict:
    rng = np.random.default_rng(SEED)
    n_agents = 8
    steps = 1600
    inputs = rng.choice([-1.0, 1.0], size=(n_agents, steps))

    coupled = common_attractor_simulation(
        inputs,
        n_agents=n_agents,
        cfg=Config(coupling_gain=0.40, noise_std=0.01),
        seed=SEED,
    )
    uncoupled = common_attractor_simulation(
        inputs,
        n_agents=n_agents,
        cfg=Config(coupling_gain=0.00, noise_std=0.01),
        seed=SEED,
    )

    spread_c = float(np.mean(np.std(coupled["states"][:, -400:], axis=0)))
    spread_u = float(np.mean(np.std(uncoupled["states"][:, -400:], axis=0)))

    return {
        "coupled_terminal_spread": spread_c,
        "uncoupled_terminal_spread": spread_u,
        "spread_reduction": float(1.0 - spread_c / max(spread_u, 1e-12)),
    }


def experiment_c_perturbation_recovery() -> dict:
    steps = 700
    inputs = np.zeros(steps)
    inputs[200:240] = 1.0

    cfg = Config(noise_std=0.0)
    full = simulate(inputs, cfg, seed=SEED)

    base_cfg = Config(
        use_memory=False,
        use_pressure=False,
        use_cross=False,
        use_x=False,
        use_attractor=False,
        noise_std=0.0,
    )
    baseline = simulate(inputs, base_cfg, seed=SEED)

    pre_full = float(np.mean(full["state"][170:200]))
    pre_base = float(np.mean(baseline["state"][170:200]))

    rt_full = recovery_time(full["state"], 240, pre_full, tolerance=0.10, horizon=180)
    rt_base = recovery_time(baseline["state"], 240, pre_base, tolerance=0.10, horizon=180)

    post_full = float(np.mean(np.abs(full["state"][240:320] - pre_full)))
    post_base = float(np.mean(np.abs(baseline["state"][240:320] - pre_base)))

    return {
        "full_recovery_steps": rt_full,
        "baseline_recovery_steps": rt_base,
        "full_post_perturbation_deviation": post_full,
        "baseline_post_perturbation_deviation": post_base,
    }


def experiment_d_self_state_prediction() -> dict:
    rng = np.random.default_rng(SEED)
    steps = 3000
    u = np.empty(steps)
    current = 1.0

    for t in range(steps):
        if rng.random() < (0.04 if t < 1500 else 0.12):
            current *= -1.0
        u[t] = current

    cfg = Config(noise_std=0.0)
    run = simulate(u, cfg, seed=SEED)
    q = run["q"]

    mask = np.array([x in (0, 1) for x in q], dtype=bool)
    idx = np.flatnonzero(mask[:-1] & mask[1:])
    split = int(0.7 * len(idx))

    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score

    X_full = np.column_stack([
        run["state"],
        run["memory"],
        run["pressure"],
        run["cross"],
        np.abs(run["score"]),
        run["input"],
    ])[idx]

    y = np.array([1 if q[i + 1] == 1 else 0 for i in idx])

    clf_full = LogisticRegression(max_iter=1000)
    clf_full.fit(X_full[:split], y[:split])
    acc_full = float(accuracy_score(y[split:], clf_full.predict(X_full[split:])))

    X_input = run["input"][idx].reshape(-1, 1)
    clf_input = LogisticRegression(max_iter=1000)
    clf_input.fit(X_input[:split], y[:split])
    acc_input = float(accuracy_score(y[split:], clf_input.predict(X_input[split:])))

    return {
        "samples": int(len(idx)),
        "next_output_accuracy_internal_state": acc_full,
        "next_output_accuracy_input_only": acc_input,
        "self_state_information_gain": float(acc_full - acc_input),
    }


def experiment_e_wake_dream_persistence() -> dict:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "organism.db"
        store = MemoryStore(db_path)
        provider = FakeProvider()
        cfg = OrganismConfig(
            agent_id="validation-agent",
            memory_limit=20,
            event_limit=20,
        )
        organism = PersistentOrganism(
            cfg,
            store,
            provider,
            lambda _: None,
        )

        first = organism.wake_cycle("primer estímulo")
        memories_before_dream = len(store.recent_memories("validation-agent"))

        dream = organism.dream_cycle()
        state_after_dream = store.load_state("validation-agent")
        events_after_dream = store.recent_events("validation-agent", 20)

        second = organism.wake_cycle("segundo estímulo")
        final_state = store.load_state("validation-agent")

        reopened = MemoryStore(db_path)
        restored = reopened.load_state("validation-agent")
        restored_events = reopened.recent_events("validation-agent", 20)
        restored_memories = reopened.recent_memories("validation-agent", 20)

        return {
            "wake_memory_detected": "MEMORY:" in first,
            "dream_memory_detected": "MEMORY:" in dream,
            "self_model_version_after_dream": state_after_dream.self_model_version,
            "memories_before_dream": memories_before_dream,
            "memories_after_dream": len(restored_memories),
            "event_modes": [e["mode"] for e in restored_events],
            "final_mode": final_state.mode,
            "state_survives_reopen": (
                restored.self_model_version == final_state.self_model_version
                and restored.last_thought == final_state.last_thought
            ),
            "dream_event_exists": any(e["mode"] == "DREAM" for e in events_after_dream),
        }


def experiment_f_continuity_ablation() -> dict:
    steps = 1200
    u = np.zeros(steps)
    u[100:180] = 1.0
    u[450:560] = -1.0
    u[800:870] = 0.7

    cfg = Config(noise_std=0.0)
    continuous = simulate(u, cfg, seed=SEED)

    segment = 200
    restart_state = np.zeros(steps)
    restart_q = np.empty(steps, dtype=object)

    for start in range(0, steps, segment):
        end = min(steps, start + segment)
        chunk = simulate(u[start:end], cfg, seed=SEED)
        restart_state[start:end] = chunk["state"]
        restart_q[start:end] = chunk["q"]

    suffix_start = segment
    return {
        "continuous_vs_restart_mean_state_gap": mean_abs_gap(
            continuous["state"][suffix_start:],
            restart_state[suffix_start:],
        ),
        "continuous_x_occupancy": float(
            np.mean(continuous["q"] == "X")
        ),
        "restart_x_occupancy": float(
            np.mean(restart_q == "X")
        ),
        "segment_count": int(np.ceil(steps / segment)),
    }


def main() -> None:
    experiments = {
        "A_path_dependence": experiment_a_path_dependence(),
        "B_common_attractor": experiment_b_common_attractor(),
        "C_perturbation_recovery": experiment_c_perturbation_recovery(),
        "D_self_state_prediction": experiment_d_self_state_prediction(),
        "E_wake_dream_persistence": experiment_e_wake_dream_persistence(),
        "F_continuity_ablation": experiment_f_continuity_ablation(),
    }

    # Structural checks: the experiment completed and produced finite
    # numerical observables. These are not claims that the hypothesis passed.
    for name, report in experiments.items():
        assert report, f"empty report: {name}"
        for key, value in report.items():
            if isinstance(value, (float, int, np.floating, np.integer)):
                assert np.isfinite(value), f"non-finite result: {name}.{key}"

    payload = {
        "suite": "continuity_validation_v1",
        "seed": SEED,
        "interpretation": (
            "Measurements only. No field in this file is a declaration "
            "that the system is conscious."
        ),
        "experiments": experiments,
    }

    output = RESULTS_DIR / "continuity_validation_v1.json"
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=" * 72)
    print("CONSCIENCIA PARA IA — CONTINUITY VALIDATION V1")
    print("=" * 72)
    for name, report in experiments.items():
        print(f"\n[{name}]")
        for key, value in report.items():
            print(f"  {key}: {value}")
    print(f"\nRESULT: {output}")
    print("=" * 72)


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

import numpy as np

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore


class FakeProvider:
    def chat(self, messages, temperature=0.7):
        return LLMResponse(
            text=(
                "Respuesta persistente de laboratorio.\n"
                "MEMORY: Mantener continuidad entre ciclos.\n"
                "SELF_MODEL: Estoy siguiendo una trayectoria interna."
            ),
            raw={"fake": True},
        )


def sign_flip_pvalue(values: np.ndarray, samples: int = 20000, seed: int = 51001) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return 1.0

    observed = abs(float(values.mean()))
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.array([-1.0, 1.0]), size=(samples, len(values)))
    null = np.abs((signs * values).mean(axis=1))
    return float((np.count_nonzero(null >= observed) + 1) / (samples + 1))


def summarize(rows: list[dict]) -> dict:
    rows = [r for r in rows if np.isfinite(r["gain"])]
    if not rows:
        return {
            "n": 0,
            "mean_gain": 0.0,
            "median_gain": 0.0,
            "positive_gain_fraction": 0.0,
            "observer_better_than_baseline": False,
            "sign_flip_p": 1.0,
        }

    gains = np.asarray([r["gain"] for r in rows], dtype=float)
    errors = np.asarray([r["prediction_error"] for r in rows], dtype=float)
    baseline = np.asarray([r["baseline_error"] for r in rows], dtype=float)

    return {
        "n": int(len(gains)),
        "mean_gain": float(gains.mean()),
        "median_gain": float(np.median(gains)),
        "positive_gain_fraction": float(np.mean(gains > 0.0)),
        "observer_mae": float(errors.mean()),
        "baseline_mae": float(baseline.mean()),
        "observer_better_than_baseline": bool(errors.mean() < baseline.mean()),
        "sign_flip_p": sign_flip_pvalue(gains),
    }


def run_protocol(db: Path, cycles: int) -> dict:
    if db.exists():
        db.unlink()

    store = MemoryStore(db)
    cfg = OrganismConfig(
        agent_id="self-observation-v51",
        dream_every_cycles=10_000,
        event_limit=0,
        self_observer_enabled=True,
    )
    organism = PersistentOrganism(cfg, store, FakeProvider(), lambda _: None)

    for idx in range(cycles):
        # Controlled binary regime sequence with deterministic new ordering in
        # repeated blocks. The observer sees only its internal state variables.
        if idx % 4 in (0, 1):
            organism.wake_cycle(f"external cycle {idx}")
        else:
            organism.autonomous_wake_cycle()

    before_restart = store.persistence_observables(cfg.agent_id)
    before_rows = store.self_observer_trajectory(cfg.agent_id)

    store.conn.close()
    reopened_store = MemoryStore(db)
    reopened = PersistentOrganism(cfg, reopened_store, FakeProvider(), lambda _: None)

    recovery = reopened_store.persistence_observables(cfg.agent_id)

    for idx in range(24):
        if idx % 3 == 0:
            reopened.wake_cycle(f"post-restart {idx}")
        else:
            reopened.autonomous_wake_cycle()

    final = reopened_store.persistence_observables(cfg.agent_id)
    after_rows = reopened_store.self_observer_trajectory(cfg.agent_id)

    warmup = min(16, max(0, len(before_rows) - 1))
    summary = summarize(before_rows[warmup:])

    return {
        "summary_before_restart": summary,
        "before_restart": before_restart,
        "after_restart_recovery": recovery,
        "final": final,
        "recovery_snapshot_count_preserved": (
            recovery["self_observer_snapshot_count"]
            == before_restart["self_observer_snapshot_count"]
        ),
        "recovery_samples_preserved": (
            recovery["self_prediction_samples"]
            == before_restart["self_prediction_samples"]
        ),
        "post_restart_snapshot_growth": (
            final["self_observer_snapshot_count"]
            > recovery["self_observer_snapshot_count"]
        ),
        "pre_restart_rows": before_rows,
        "post_restart_rows_added": after_rows[
            len(before_rows):
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=int, default=120)
    parser.add_argument("--out", default="results/organism_self_observation_v51")
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    result = run_protocol(out / "self_observation.db", args.cycles)
    (out / "summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(result["summary_before_restart"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

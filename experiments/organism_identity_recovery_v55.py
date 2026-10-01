from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore


class FakeProvider:
    def chat(self, messages, temperature=0.7):
        return LLMResponse(
            text=(
                "Procesamiento de continuidad.\n"
                "MEMORY: conservar la relación estable del recorrido.\n"
                "SELF_MODEL: la identidad persiste mientras cambia mi estado."
            ),
            raw={"fake": True},
        )


def identity_signature(store: MemoryStore, agent_id: str) -> str:
    state = store.load_state(agent_id)
    memories = store.recent_memories(agent_id, 1000)
    payload = {
        "self_model": state.self_model,
        "self_model_version": state.self_model_version,
        "memories": memories,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def setup_base(db: Path, warmup: int, selection_enabled: bool) -> None:
    store = MemoryStore(db)
    cfg = OrganismConfig(
        agent_id="identity-v55",
        dream_every_cycles=10_000,
        event_limit=0,
        self_observer_enabled=True,
        self_selection_enabled=selection_enabled,
    )
    organism = PersistentOrganism(cfg, store, FakeProvider(), lambda _: None)

    for i in range(warmup):
        organism.wake_cycle(f"identity calibration {i}")
        organism.autonomous_wake_cycle()

    store.conn.close()


def run_case(
    db: Path,
    *,
    perturbation: float | None,
    selection_enabled: bool,
    recovery_cycles: int,
) -> dict:
    provider = FakeProvider()
    store = MemoryStore(db)
    cfg = OrganismConfig(
        agent_id="identity-v55",
        dream_every_cycles=10_000,
        event_limit=0,
        self_observer_enabled=True,
        self_selection_enabled=selection_enabled,
    )
    organism = PersistentOrganism(cfg, store, provider, lambda _: None)

    before = store.load_state(cfg.agent_id)
    identity_before = identity_signature(store, cfg.agent_id)

    if perturbation is not None:
        state = store.load_state(cfg.agent_id)
        state.dynamic_state = float(perturbation)
        state.dynamic_prev_state = float(perturbation)
        state.dynamic_pressure = 3.8
        state.dynamic_attractor_distance = abs(
            float(perturbation) - float(state.attractor)
        )
        store.save_state(cfg.agent_id, state)

    post_perturb = store.load_state(cfg.agent_id)
    recovery_time = None

    for step in range(1, recovery_cycles + 1):
        organism.autonomous_wake_cycle()
        state = store.load_state(cfg.agent_id)
        if (
            recovery_time is None
            and abs(state.dynamic_state - before.dynamic_state) <= 0.05
        ):
            recovery_time = step

    after = store.load_state(cfg.agent_id)
    identity_after = identity_signature(store, cfg.agent_id)

    return {
        "perturbation": perturbation,
        "selection_enabled": selection_enabled,
        "recovery_time": recovery_time,
        "final_state": after.dynamic_state,
        "baseline_state": before.dynamic_state,
        "final_state_error": abs(after.dynamic_state - before.dynamic_state),
        "identity_preserved": identity_before == identity_after,
        "self_model_version_before": before.self_model_version,
        "self_model_version_after": after.self_model_version,
        "memory_count_before": store.memory_count(cfg.agent_id),
        "dynamic_steps": after.dynamic_steps,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=12)
    parser.add_argument("--warmup", type=int, default=24)
    parser.add_argument("--recovery-cycles", type=int, default=40)
    parser.add_argument("--out", default="results/organism_identity_recovery_v55")
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    rows = []

    for replicate in range(args.replicates):
        for enabled in (False, True):
            for perturbation in (-0.95, 0.95):
                db = out / f"r{replicate}_s{int(enabled)}_p{perturbation:+.2f}.db"
                setup_base(db, args.warmup, selection_enabled=enabled)
                rows.append(
                    run_case(
                        db,
                        perturbation=perturbation,
                        selection_enabled=enabled,
                        recovery_cycles=args.recovery_cycles,
                    )
                )

    perturbed = rows
    recovered = [row for row in perturbed if row["recovery_time"] is not None]

    summary = {
        "experiment": "organism_identity_recovery_v55",
        "replicates": args.replicates,
        "warmup": args.warmup,
        "recovery_cycles": args.recovery_cycles,
        "identity_preservation_fraction": sum(
            row["identity_preserved"] for row in rows
        ) / len(rows),
        "recovery_fraction": len(recovered) / len(rows),
        "mean_recovery_time": (
            sum(row["recovery_time"] for row in recovered) / len(recovered)
            if recovered else None
        ),
        "mean_final_state_error": (
            sum(row["final_state_error"] for row in rows) / len(rows)
        ),
        "selection_enabled_recovery_fraction": sum(
            row["recovery_time"] is not None
            for row in rows
            if row["selection_enabled"]
        ) / max(1, sum(row["selection_enabled"] for row in rows)),
        "selection_disabled_recovery_fraction": sum(
            row["recovery_time"] is not None
            for row in rows
            if not row["selection_enabled"]
        ) / max(1, sum(not row["selection_enabled"] for row in rows)),
        "result_status": "empirical_result_pending",
    }

    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out / "runs.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

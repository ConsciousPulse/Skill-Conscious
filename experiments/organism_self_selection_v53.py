from __future__ import annotations

import argparse
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
                "Respuesta de continuidad.\n"
                "MEMORY: conservar trayectoria.\n"
                "SELF_MODEL: mi estado cambia según el recorrido."
            ),
            raw={"fake": True},
        )


def make_base(path: Path, warmup_cycles: int) -> None:
    store = MemoryStore(path)
    cfg = OrganismConfig(
        agent_id="receiver",
        dream_every_cycles=10_000,
        event_limit=0,
        self_observer_enabled=True,
        self_selection_enabled=False,
    )
    organism = PersistentOrganism(cfg, store, FakeProvider(), lambda _: None)

    for i in range(warmup_cycles):
        organism.wake_cycle(f"calibration {i}")
        organism.autonomous_wake_cycle()

    store.conn.close()


def run_condition(path: Path, enabled: bool, provider: FakeProvider) -> dict:
    store = MemoryStore(path)
    cfg = OrganismConfig(
        agent_id="receiver",
        dream_every_cycles=10_000,
        event_limit=0,
        self_observer_enabled=True,
        self_selection_enabled=enabled,
    )
    organism = PersistentOrganism(cfg, store, provider, lambda _: None)

    before = store.persistence_observables("receiver")
    organism.autonomous_wake_cycle()
    after = store.persistence_observables("receiver")
    event = store.recent_events("receiver", 1)[0]

    return {
        "enabled": enabled,
        "before": before,
        "after": after,
        "event": event,
        "chosen_signal": event["payload"]["self_selection"]["chosen_signal"],
        "predicted_candidates": event["payload"]["self_selection"]["candidates"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("fake",), default="fake")
    parser.add_argument("--replicates", type=int, default=12)
    parser.add_argument("--warmup", type=int, default=24)
    parser.add_argument("--out", default="results/organism_self_selection_v53")
    args = parser.parse_args()

    if args.replicates < 1 or args.warmup < 2:
        raise SystemExit("replicates must be >=1 and warmup must be >=2")

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    enabled_rows = []
    control_rows = []

    for replicate in range(1, args.replicates + 1):
        base = out / f"base_{replicate}.db"
        on_db = out / f"on_{replicate}.db"
        off_db = out / f"off_{replicate}.db"

        make_base(base, args.warmup)
        shutil.copy2(base, on_db)
        shutil.copy2(base, off_db)

        provider = FakeProvider()
        enabled_rows.append(run_condition(on_db, True, provider))
        control_rows.append(run_condition(off_db, False, provider))

    selected_nonzero = [
        row["chosen_signal"] for row in enabled_rows if abs(row["chosen_signal"]) > 0
    ]
    control_signals = [0.0 for _ in control_rows]
    state_deltas = [
        abs(on["after"]["dynamic_state"] - off["after"]["dynamic_state"])
        for on, off in zip(enabled_rows, control_rows)
    ]

    summary = {
        "experiment": "organism_self_selection_v53",
        "replicates": args.replicates,
        "warmup_cycles": args.warmup,
        "selection_enabled_nonzero_fraction": (
            len(selected_nonzero) / len(enabled_rows)
        ),
        "mean_enabled_vs_control_state_delta": (
            sum(state_deltas) / len(state_deltas)
        ),
        "all_controls_zero_signal": all(signal == 0.0 for signal in control_signals),
        "selection_used_counterfactual_candidates": all(
            len(row["predicted_candidates"]) == 3 for row in enabled_rows
        ),
        "empirical_causal_effect_pending": True,
    }

    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out / "runs.json").write_text(
        json.dumps(
            {"enabled": enabled_rows, "control": control_rows},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

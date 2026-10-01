from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

from src.ontto.bridge import DynamicStateBridge
from src.ontto.dynamics import Config as DynamicsConfig
from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore, OntologicalState

STABLE_MEMORIES = (
    "STABLE continuity anchor persists across the recent trajectory.",
    "STABLE continuity anchor preserves the same route.",
    "STABLE identity remains coupled to the persistent route.",
    "STABLE continuity keeps the trajectory coherent.",
)
FRONTIER_MEMORIES = (
    "FRONTIER change opens a divergent trajectory.",
    "FRONTIER exploration breaks the previous route.",
    "FRONTIER identity adapts to a new direction.",
    "FRONTIER divergence keeps the trajectory exploratory.",
)
STABLE_DREAM = "DREAM_TRACE STABLE continuity anchor persists."
FRONTIER_DREAM = "DREAM_TRACE FRONTIER divergence opens a new route."


class DreamTraceProvider:
    def __init__(self, condition: str):
        self.condition = condition

    def chat(self, messages, temperature=0.7):
        if self.condition == "stable":
            memory = STABLE_DREAM
            self_model = "SELF_MODEL: I preserve stable continuity across the dream."
            summary = "Dream consolidated stable continuity."
        else:
            memory = FRONTIER_DREAM
            self_model = "SELF_MODEL: I preserve exploratory divergence across the dream."
            summary = "Dream consolidated frontier divergence."
        return LLMResponse(
            text=(
                "Deterministic dream consolidation.\n"
                f"MEMORY: {memory}\n"
                f"{self_model}\n"
                f"DREAM_SUMMARY: {summary}"
            ),
            raw={"fake": True, "condition": self.condition},
        )


@dataclass(frozen=True)
class CoreTrace:
    previous_state: float
    state: float

    def as_features(self) -> np.ndarray:
        return np.asarray([self.previous_state, self.state], dtype=float)


def make_base(path: Path, seed: int, condition: str) -> OntologicalState:
    store = MemoryStore(path)
    cfg = OrganismConfig(
        agent_id="receiver",
        dynamic_seed=seed,
        dream_every_cycles=10_000,
        event_limit=16,
        self_observer_enabled=True,
        self_selection_enabled=False,
        semantic_dynamic_bridge_enabled=False,
        semantic_self_model_bridge_enabled=False,
        dream_semantic_bridge_enabled=True,
    )
    provider = DreamTraceProvider(condition)
    organism = PersistentOrganism(cfg, store, provider, lambda _: None)

    memories = STABLE_MEMORIES if condition == "stable" else FRONTIER_MEMORIES
    for memory in memories:
        store.add_memory("receiver", memory, importance=0.65)

    organism.dream_cycle()
    state = store.load_state("receiver")
    store.conn.close()
    return state


def total_semantic_ablation(state: OntologicalState) -> OntologicalState:
    # Keep only the numeric dynamic core produced by DREAM.
    state.self_model = ""
    state.self_model_version = 0
    state.last_thought = ""
    state.memory_strength = 0.0
    state.dynamic_memory = 0.0
    state.dynamic_pressure = 0.0
    state.dynamic_last_input = 0.0
    state.mode = "WAKE"
    return state


def delete_semantic_surfaces(path: Path) -> OntologicalState:
    store = MemoryStore(path)
    store.conn.execute("DELETE FROM memories WHERE agent_id='receiver'")
    store.conn.execute("DELETE FROM events WHERE agent_id='receiver'")
    store.conn.execute("DELETE FROM dream_cycles WHERE agent_id='receiver'")
    store.conn.execute("DELETE FROM snapshots WHERE agent_id='receiver'")
    store.conn.execute("DELETE FROM dynamic_snapshots WHERE agent_id='receiver'")
    store.conn.execute("DELETE FROM self_observer_snapshots WHERE agent_id='receiver'")
    store.conn.execute("DELETE FROM input_queue WHERE agent_id='receiver'")
    state = total_semantic_ablation(store.load_state("receiver"))
    store.save_state("receiver", state)
    store.conn.close()
    return state


def run_zero_input_trace(state: OntologicalState, seed: int, steps: int = 12) -> np.ndarray:
    bridge = DynamicStateBridge(DynamicsConfig(), seed=seed)
    previous = state.dynamic_prev_state
    current = state.dynamic_state
    memory = state.dynamic_memory
    pressure = state.dynamic_pressure
    step_index = state.dynamic_steps
    traces = []

    for _ in range(steps):
        snap = bridge.advance(
            previous_state=previous,
            state=current,
            memory=memory,
            pressure=pressure,
            signal=0.0,
            steps=1,
            step_index=step_index,
        )
        previous = snap.previous_state
        current = snap.state
        memory = snap.memory
        pressure = snap.pressure
        step_index = snap.steps
        traces.append(CoreTrace(previous, current))

    return np.asarray([trace.as_features() for trace in traces], dtype=float)


def build_swapped_state(target: OntologicalState, source: OntologicalState) -> OntologicalState:
    target.dynamic_prev_state = source.dynamic_prev_state
    target.dynamic_state = source.dynamic_state
    target.dynamic_steps = source.dynamic_steps
    return total_semantic_ablation(target)


def trace_features(trace: np.ndarray) -> np.ndarray:
    # Preserve temporal structure while keeping the feature space small and
    # explicitly numeric.
    return np.concatenate(
        [
            trace[:, 0],
            trace[:, 1],
            np.diff(trace[:, 1], prepend=trace[0, 1]),
        ]
    )


def sign_flip_p(values: list[float] | np.ndarray, seed: int) -> float:
    values = np.asarray(values, dtype=float)
    if not len(values):
        return 1.0
    observed = abs(float(values.mean()))
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.asarray([-1.0, 1.0]), size=(20000, len(values)))
    null = np.abs((signs * values).mean(axis=1))
    return float((np.count_nonzero(null >= observed) + 1) / 20001)


def loo_scores(samples: list[tuple[str, int, np.ndarray]]) -> tuple[list[float], list[float]]:
    accuracies = []
    swap_accuracies = []
    for held_out in range(24):
        train = [row for i, row in enumerate(samples) if i // 4 != held_out]
        test = [row for i, row in enumerate(samples) if i // 4 == held_out]
        x_train = np.asarray([trace_features(row[2]) for row in train])
        y_train = np.asarray([1 if row[0] == "stable" else 0 for row in train])
        model = LogisticRegression(
            solver="liblinear",
            C=1.0,
            random_state=0,
            max_iter=2000,
        )
        model.fit(x_train, y_train)

        own_test = test[:2]
        swap_test = test[2:]
        own_acc = np.mean([
            int(model.predict(trace_features(row[2]).reshape(1, -1))[0] == (1 if row[0] == "stable" else 0))
            for row in own_test
        ])
        swap_acc = np.mean([
            int(model.predict(trace_features(row[2]).reshape(1, -1))[0] == (1 if row[1] == 0 else 1))
            for row in swap_test
        ])
        accuracies.append(float(own_acc))
        swap_accuracies.append(float(swap_acc))
    return accuracies, swap_accuracies


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicates", type=int, default=24)
    ap.add_argument("--trace-steps", type=int, default=12)
    ap.add_argument("--out", default="results/organism_dream_state_trace_v67")
    args = ap.parse_args()

    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    samples = []
    dream_signal_deltas = []
    dream_state_deltas = []
    raw_rows = []

    for replicate in range(args.replicates):
        seed = 9701 + replicate
        stable_db = out / f"stable_{replicate}.db"
        frontier_db = out / f"frontier_{replicate}.db"

        stable_state = make_base(stable_db, seed, "stable")
        frontier_state = make_base(frontier_db, seed, "frontier")

        stable_store = MemoryStore(stable_db)
        stable_event = stable_store.recent_events("receiver", 1)[0]
        frontier_store = MemoryStore(frontier_db)
        frontier_event = frontier_store.recent_events("receiver", 1)[0]
        stable_bridge = stable_event["payload"]["semantic_bridge"]
        frontier_bridge = frontier_event["payload"]["semantic_bridge"]
        dream_signal_deltas.append(
            float(stable_bridge["signal"] - frontier_bridge["signal"])
        )
        dream_state_deltas.append(
            float(stable_state.dynamic_state - frontier_state.dynamic_state)
        )
        stable_store.conn.close()
        frontier_store.conn.close()

        stable_state = delete_semantic_surfaces(stable_db)
        frontier_state = delete_semantic_surfaces(frontier_db)

        stable_own = run_zero_input_trace(stable_state, seed, args.trace_steps)
        frontier_own = run_zero_input_trace(frontier_state, seed, args.trace_steps)

        stable_swap = run_zero_input_trace(
            build_swapped_state(stable_state, frontier_state), seed, args.trace_steps
        )
        frontier_swap = run_zero_input_trace(
            build_swapped_state(frontier_state, stable_state), seed, args.trace_steps
        )

        samples.extend(
            [
                ("stable", 1, stable_own),
                ("frontier", 0, frontier_own),
                ("stable", 0, stable_swap),
                ("frontier", 1, frontier_swap),
            ]
        )
        raw_rows.append(
            {
                "replicate": replicate,
                "seed": seed,
                "dream_signal_delta": dream_signal_deltas[-1],
                "dream_state_delta": dream_state_deltas[-1],
                "stable_own_final_state": float(stable_own[-1, 1]),
                "frontier_own_final_state": float(frontier_own[-1, 1]),
                "stable_swap_final_state": float(stable_swap[-1, 1]),
                "frontier_swap_final_state": float(frontier_swap[-1, 1]),
            }
        )

    own_accuracy, swap_accuracy = loo_scores(samples)
    own_centered = np.asarray(own_accuracy) - 0.5
    swap_centered = np.asarray(swap_accuracy) - 0.5

    summary = {
        "experiment": "organism_dream_state_trace_v67",
        "replicates": args.replicates,
        "trace_steps": args.trace_steps,
        "semantic_ablation": True,
        "dream_signal_delta_mean": float(np.mean(dream_signal_deltas)),
        "dream_state_delta_mean": float(np.mean(dream_state_deltas)),
        "post_ablation_own_accuracy": float(np.mean(own_accuracy)),
        "post_ablation_own_accuracy_p": sign_flip_p(own_centered, 67001),
        "state_swap_following_accuracy": float(np.mean(swap_accuracy)),
        "state_swap_following_p": sign_flip_p(swap_centered, 67002),
        "all_memories_removed_before_probe": True,
        "self_model_cleared_before_probe": True,
        "semantic_text_input_during_probe": False,
    }

    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out / "runs.json").write_text(
        json.dumps(raw_rows, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

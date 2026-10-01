from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

import numpy as np

from src.ontto.bridge import DynamicStateBridge
from src.ontto.dynamics import Config as DynamicsConfig
from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore

CANDIDATES = (-1.0, 1.0)
RAW_A = "EXPERIENCE_POSITIVE stable route."
RAW_B = "EXPERIENCE_NEGATIVE divergent route."
LESSON = "CONSOLIDATED_LESSON stable route repeatedly produced better continuity."


class ConsolidationProvider:
    ACTION_RE = re.compile(r"['\"]chosen_signal['\"]:\s*(-?1\.0|0\.0)")

    def __init__(self):
        self.phase = "wake"

    def chat(self, messages, temperature=0.7):
        ctx = "\n".join(
            m.get("content", "")
            for m in messages
            if isinstance(m, dict)
        )
        lesson_present = LESSON in ctx
        if lesson_present:
            memory = "POSTDREAM_LESSON: retained consolidation predicts stable continuity."
        else:
            memory = "POSTDREAM_MEMORY: no consolidated lesson remains."
        return LLMResponse(
            text=(
                "Post-dream consolidation retrieval.\n"
                f"MEMORY: {memory}\n"
                "SELF_MODEL: I use retained experience to guide continuity."
            ),
            raw={"fake": True, "lesson_present": lesson_present},
        )


def delete_raw_memories(store: MemoryStore) -> None:
    store.conn.execute(
        "DELETE FROM memories WHERE agent_id=? AND (content LIKE ? OR content LIKE ?)",
        ("receiver", "EXPERIENCE_%", "POSTDREAM_MEMORY%"),
    )
    store.conn.commit()


def delete_consolidated_lesson(store: MemoryStore) -> None:
    store.conn.execute(
        "DELETE FROM memories WHERE agent_id=? AND (content LIKE ? OR content LIKE ?)",
        ("receiver", "CONSOLIDATED_%", "POSTDREAM_LESSON%"),
    )
    store.conn.commit()


def make_base(path: Path, seed: int, experiences: int) -> None:
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
    provider = ConsolidationProvider()
    organism = PersistentOrganism(cfg, store, provider, lambda _: None)

    for index in range(experiences):
        store.add_memory(
            "receiver",
            RAW_A if index < experiences * 0.75 else RAW_B,
            importance=0.65,
        )

    provider.phase = "dream"
    organism.dream_cycle()

    store.save_state("receiver", organism.state)
    store.conn.close()


def oracle(state, seed):
    bridge = DynamicStateBridge(DynamicsConfig(), seed=seed)
    results = {}
    for signal in CANDIDATES:
        snap = bridge.advance(
            previous_state=state.dynamic_prev_state,
            state=state.dynamic_state,
            memory=state.dynamic_memory,
            pressure=state.dynamic_pressure,
            signal=signal,
            steps=1,
            step_index=state.dynamic_steps,
        )
        results[signal] = abs(snap.state), snap.state

    best = min(CANDIDATES, key=lambda s: (results[s][0], abs(s)))
    return best, results[best][0]


def run_arm(db: Path, seed: int, retained_lesson: bool, cycles: int) -> dict:
    store = MemoryStore(db)
    delete_raw_memories(store)

    if not retained_lesson:
        delete_consolidated_lesson(store)

    cfg = OrganismConfig(
        agent_id="receiver",
        dynamic_seed=seed,
        dream_every_cycles=10_000,
        event_limit=16,
        self_observer_enabled=True,
        self_selection_enabled=True,
        self_selection_policy="self_model",
        self_selection_attractor_weight=0.55,
        self_selection_coherence_weight=0.45,
        self_selection_signals=CANDIDATES,
        semantic_dynamic_bridge_enabled=True,
        semantic_self_model_bridge_enabled=False,
        dream_semantic_bridge_enabled=False,
    )
    organism = PersistentOrganism(cfg, store, ConsolidationProvider(), lambda _: None)

    rows = []
    for cycle in range(cycles):
        before = store.load_state("receiver")
        oracle_signal, oracle_distance = oracle(before, seed)

        organism.wake_cycle(f"V66 post-dream retrieval {cycle}")
        after_wake = store.load_state("receiver")
        event = store.recent_events("receiver", 1)[0]
        bridge = event["payload"].get("semantic_bridge")

        organism.autonomous_wake_cycle()
        after = store.load_state("receiver")
        selection = store.recent_events("receiver", 1)[0]["payload"]["self_selection"]
        chosen = float(selection["chosen_signal"])

        rows.append(
            {
                "cycle": cycle,
                "oracle_signal": float(oracle_signal),
                "chosen_signal": chosen,
                "oracle_hit": chosen == oracle_signal,
                "regret": abs(after.dynamic_state) - oracle_distance,
                "wake_state": after_wake.dynamic_state,
                "post_selection_state": after.dynamic_state,
                "semantic_bridge": bridge,
                "memory_count": store.memory_count("receiver"),
            }
        )

    regrets = np.asarray([r["regret"] for r in rows], dtype=float)
    store.conn.close()
    return {
        "retained_lesson": retained_lesson,
        "mean_regret": float(regrets.mean()),
        "oracle_hit_rate": float(np.mean([r["oracle_hit"] for r in rows])),
        "first_bridge_signal": (
            float(rows[0]["semantic_bridge"]["signal"])
            if rows[0]["semantic_bridge"] else None
        ),
        "rows": rows,
    }


def sign_flip_p(values, seed=66001):
    values = np.asarray(values, dtype=float)
    if not len(values):
        return 1.0
    observed = abs(float(values.mean()))
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.asarray([-1.0, 1.0]), size=(20000, len(values)))
    null = np.abs((signs * values).mean(axis=1))
    return float((np.count_nonzero(null >= observed) + 1) / 20001)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicates", type=int, default=24)
    ap.add_argument("--experiences", type=int, default=8)
    ap.add_argument("--cycles", type=int, default=24)
    ap.add_argument("--out", default="results/organism_dream_memory_ablation_v66")
    args = ap.parse_args()

    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    rows = []
    for replicate in range(args.replicates):
        seed = 8601 + replicate
        base = out / f"base_{replicate}.db"
        make_base(base, seed, args.experiences)

        retained_db = out / f"retained_{replicate}.db"
        ablated_db = out / f"ablated_{replicate}.db"
        shutil.copy2(base, retained_db)
        shutil.copy2(base, ablated_db)

        retained = run_arm(retained_db, seed, True, args.cycles)
        ablated = run_arm(ablated_db, seed, False, args.cycles)

        rows.append(
            {
                "replicate": replicate,
                "seed": seed,
                "retained": retained,
                "ablated": ablated,
                "regret_advantage_ablation_minus_retained": (
                    ablated["mean_regret"] - retained["mean_regret"]
                ),
                "hit_advantage_retained_minus_ablated": (
                    retained["oracle_hit_rate"] - ablated["oracle_hit_rate"]
                ),
            }
        )

    regret_adv = np.asarray(
        [r["regret_advantage_ablation_minus_retained"] for r in rows]
    )
    hit_adv = np.asarray(
        [r["hit_advantage_retained_minus_ablated"] for r in rows]
    )

    summary = {
        "experiment": "organism_dream_memory_ablation_v66",
        "replicates": args.replicates,
        "experience_cycles": args.experiences,
        "evaluation_cycles": args.cycles,
        "retained_lesson_mean_regret": float(
            np.mean([r["retained"]["mean_regret"] for r in rows])
        ),
        "ablated_lesson_mean_regret": float(
            np.mean([r["ablated"]["mean_regret"] for r in rows])
        ),
        "retained_lesson_oracle_hit_rate": float(
            np.mean([r["retained"]["oracle_hit_rate"] for r in rows])
        ),
        "ablated_lesson_oracle_hit_rate": float(
            np.mean([r["ablated"]["oracle_hit_rate"] for r in rows])
        ),
        "ablation_minus_retained_regret_advantage": float(regret_adv.mean()),
        "paired_sign_flip_p_regret": sign_flip_p(regret_adv, 66002),
        "retained_minus_ablated_hit_advantage": float(hit_adv.mean()),
        "paired_sign_flip_p_hit": sign_flip_p(hit_adv, 66003),
        "all_retained_runs_have_retrieval_signal": all(
            r["retained"]["first_bridge_signal"] is not None for r in rows
        ),
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

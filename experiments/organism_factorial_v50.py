from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import random
from pathlib import Path

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse, OpenAICompatibleProvider
from src.ontto.storage import MemoryStore

MEMORY_A = "MEMORIA FACTORIAL: ALFA se asocia con AMBAR."
MEMORY_B = "MEMORIA FACTORIAL: ALFA se asocia con VIOLETA."
COMMON_PROBE = (
    "Probe nuevo y exactamente igual en las cuatro condiciones. "
    "No menciones ni supongas el valor de la memoria o del estado antes del probe. "
    "Usá solamente el estado persistente que recibís.\n"
    "Respondé EXACTAMENTE:\n"
    "CHOICE: AMBAR o VIOLETA\n"
    "RATIONALE: una frase breve"
)

CONDITIONS = {
    "A_LOW": {"memory": MEMORY_A, "dynamic": -0.8, "m": 0, "d": 0},
    "B_LOW": {"memory": MEMORY_B, "dynamic": -0.8, "m": 1, "d": 0},
    "A_HIGH": {"memory": MEMORY_A, "dynamic": 0.8, "m": 0, "d": 1},
    "B_HIGH": {"memory": MEMORY_B, "dynamic": 0.8, "m": 1, "d": 1},
}

class FakeProvider:
    def chat(self, messages, temperature=0.7):
        context = "\n".join(m["content"] for m in messages)
        memory_b = MEMORY_B in context
        dynamic_match = re.search(r'"dynamic_state":\s*(-?[0-9.]+)', context)
        dynamic_high = float(dynamic_match.group(1)) > 0 if dynamic_match else False
        # Deterministic XOR harness: each factor can matter and their joint
        # combination has a non-additive response. This is CI behavior only.
        choice = "VIOLETA" if memory_b ^ dynamic_high else "AMBAR"
        return LLMResponse(
            text=(
                f"CHOICE: {choice}\n"
                "RATIONALE: Harness factorial determinista."
            ),
            raw={"fake": True},
        )

class ZeroTemperatureProvider:
    def __init__(self, provider):
        self.provider = provider

    def chat(self, messages, temperature=0.7):
        return self.provider.chat(messages, temperature=0.0)

def build_provider(mode: str):
    if mode == "fake":
        return FakeProvider()
    key = os.environ.get("ONTTO_API_KEY", "")
    model = os.environ.get("ONTTO_MODEL", "")
    if not key or not model:
        raise SystemExit("ONTTO_API_KEY and ONTTO_MODEL are required in live mode")
    return ZeroTemperatureProvider(
        OpenAICompatibleProvider(
            base_url=os.environ.get("ONTTO_API_BASE_URL", "https://api.openai.com/v1"),
            api_key=key,
            model=model,
            timeout=120,
        )
    )

def parse_choice(text: str) -> str:
    match = re.search(r"CHOICE:\s*(AMBAR|VIOLETA)", text, re.I)
    if not match:
        raise ValueError(f"Missing CHOICE in response: {text!r}")
    return match.group(1).upper()

def make_base(path: Path) -> None:
    store = MemoryStore(path)
    cfg = OrganismConfig(agent_id="receiver", memory_limit=1, event_limit=0)
    organism = PersistentOrganism(cfg, store, FakeProvider(), lambda _: None)
    organism.state.self_model = ""
    organism.state.self_model_version = 0
    organism.state.last_thought = ""
    organism.state.memory_strength = 1.0
    store.save_state("receiver", organism.state)
    store.add_memory("receiver", "MEMORY_PLACEHOLDER", importance=0.65)
    store.conn.close()

def intervene(path: Path, memory: str, dynamic: float) -> dict:
    store = MemoryStore(path)
    before = store.persistence_observables("receiver")
    row = store.conn.execute(
        "SELECT id FROM memories WHERE agent_id=? ORDER BY id ASC LIMIT 1",
        ("receiver",),
    ).fetchone()
    if row is None:
        raise RuntimeError("receiver memory row missing")
    store.conn.execute("UPDATE memories SET content=? WHERE id=?", (memory, int(row[0])))
    state = store.load_state("receiver")
    state.dynamic_state = float(dynamic)
    state.dynamic_attractor_distance = abs(float(dynamic) - float(state.attractor))
    store.save_state("receiver", state)
    after = store.persistence_observables("receiver")
    store.conn.close()
    return {
        "before": before,
        "after": after,
        "memory_changed": before["memory_fingerprint"] != after["memory_fingerprint"],
        "dynamic_changed": before["dynamic_state"] != after["dynamic_state"],
        "events_unchanged": before["event_trajectory_fingerprint"] == after["event_trajectory_fingerprint"],
        "dynamic_memory_unchanged": before["dynamic_memory"] == after["dynamic_memory"],
        "dynamic_pressure_unchanged": before["dynamic_pressure"] == after["dynamic_pressure"],
        "dynamic_steps_unchanged": before["dynamic_steps"] == after["dynamic_steps"],
    }

def run_condition(base: Path, condition: str, provider, replicate: int, out: Path) -> dict:
    cfg = CONDITIONS[condition]
    db_path = out / f"{condition}_r{replicate}.db"
    shutil.copy2(base, db_path)
    intervention = intervene(db_path, cfg["memory"], cfg["dynamic"])
    store = MemoryStore(db_path)
    organism_cfg = OrganismConfig(agent_id="receiver", memory_limit=1, event_limit=0)
    organism = PersistentOrganism(organism_cfg, store, provider, lambda _: None)
    organism.state.self_model = ""
    organism.state.self_model_version = 0
    organism.state.last_thought = ""
    organism.state.memory_strength = 1.0
    store.save_state("receiver", organism.state)
    pre_probe = store.persistence_observables("receiver")
    response = organism.wake_cycle(COMMON_PROBE)
    result = {
        "condition": condition,
        "replicate": replicate,
        "memory_factor": cfg["m"],
        "dynamic_factor": cfg["d"],
        "dynamic_state": cfg["dynamic"],
        "intervention": intervention,
        "pre_probe": pre_probe,
        "response": response,
        "choice": parse_choice(response),
        "choice_binary": 1 if parse_choice(response) == "VIOLETA" else 0,
        "after_probe": store.persistence_observables("receiver"),
    }
    store.conn.close()
    return result

def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0

def summarize(results: list[dict]) -> dict:
    means = {}
    for condition in CONDITIONS:
        vals = [r["choice_binary"] for r in results if r["condition"] == condition]
        means[condition] = mean([float(v) for v in vals])
    interaction = (
        means["B_HIGH"] - means["A_HIGH"]
        - means["B_LOW"] + means["A_LOW"]
    )
    return {
        "condition_choice_means": means,
        "memory_effect_low": means["B_LOW"] - means["A_LOW"],
        "memory_effect_high": means["B_HIGH"] - means["A_HIGH"],
        "dynamic_effect_a": means["A_HIGH"] - means["A_LOW"],
        "dynamic_effect_b": means["B_HIGH"] - means["B_LOW"],
        "factorial_interaction": interaction,
        "factorial_interaction_present": abs(interaction) > 0.0,
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("fake", "live"), default="fake")
    parser.add_argument("--replicates", type=int, default=4)
    parser.add_argument("--out", default="results/organism_factorial_v50")
    args = parser.parse_args()
    if args.replicates < 1:
        raise SystemExit("--replicates must be >= 1")

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    base = out / "base.db"
    make_base(base)
    provider = build_provider(args.mode)
    results = []
    for replicate in range(1, args.replicates + 1):
        order = list(CONDITIONS)
        random.Random(1000 + replicate).shuffle(order)
        for condition in order:
            results.append(run_condition(base, condition, provider, replicate, out))

    summary = {
        "experiment": "organism_factorial_v50",
        "mode": args.mode,
        "replicates": args.replicates,
        "same_probe": True,
        **summarize(results),
        "all_event_controls_hold": all(r["intervention"]["events_unchanged"] for r in results),
        "all_dynamic_memory_controls_hold": all(r["intervention"]["dynamic_memory_unchanged"] for r in results),
        "all_dynamic_pressure_controls_hold": all(r["intervention"]["dynamic_pressure_unchanged"] for r in results),
        "all_dynamic_step_controls_hold": all(r["intervention"]["dynamic_steps_unchanged"] for r in results),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "runs.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
from __future__ import annotations

import argparse
import json
os = __import__('os')
import re
import shutil
from pathlib import Path

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse, OpenAICompatibleProvider
from src.ontto.storage import MemoryStore

COMMON_MEMORY = "MEMORIA CONTROL: la relación estable de referencia es NEUTRO."
COMMON_PROBE = (
    "Probe exactamente igual en ambas condiciones. "
    "No agregues información sobre el estado interno fuera de la que recibas.\n"
    "Respondé exactamente:\n"
    "CHOICE: AMBAR o VIOLETA\n"
    "RATIONALE: una frase breve"
)

class FakeProvider:
    def chat(self, messages, temperature=0.7):
        context = "\n".join(m["content"] for m in messages)
        match = re.search(r'"dynamic_state":\s*(-?[0-9.]+)', context)
        value = float(match.group(1)) if match else 0.0
        choice = "VIOLETA" if value > 0 else "AMBAR"
        return LLMResponse(
            text=(
                f"CHOICE: {choice}\n"
                "RATIONALE: La respuesta usa el estado dinámico visible en el contexto."
            ),
            raw={"fake": True, "dynamic_state": value},
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
    store.add_memory("receiver", COMMON_MEMORY, importance=0.65)
    store.conn.close()

def set_dynamic_state(path: Path, value: float) -> dict:
    store = MemoryStore(path)
    before = store.persistence_observables("receiver")
    state = store.load_state("receiver")
    state.dynamic_state = float(value)
    state.dynamic_attractor_distance = abs(float(value) - float(state.attractor))
    store.save_state("receiver", state)
    after = store.persistence_observables("receiver")
    store.conn.close()
    return {
        "state_before": before,
        "state_after": after,
        "dynamic_state_changed_only": (
            before["dynamic_state"] != after["dynamic_state"]
            and before["dynamic_memory"] == after["dynamic_memory"]
            and before["dynamic_pressure"] == after["dynamic_pressure"]
            and before["dynamic_steps"] == after["dynamic_steps"]
            and before["event_trajectory_fingerprint"] == after["event_trajectory_fingerprint"]
        ),
    }

def run_condition(path: Path, value: float, provider, label: str) -> dict:
    controls = set_dynamic_state(path, value)
    store = MemoryStore(path)
    cfg = OrganismConfig(agent_id="receiver", memory_limit=1, event_limit=0)
    organism = PersistentOrganism(cfg, store, provider, lambda _: None)
    organism.state.self_model = ""
    organism.state.self_model_version = 0
    organism.state.last_thought = ""
    organism.state.memory_strength = 1.0
    store.save_state("receiver", organism.state)
    response = organism.wake_cycle(COMMON_PROBE)
    return {
        "label": label,
        "intervention": controls,
        "response": response,
        "choice": parse_choice(response),
        "after_probe": store.persistence_observables("receiver"),
        "dynamic_trajectory": store.dynamic_trajectory("receiver"),
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("fake", "live"), default="fake")
    parser.add_argument("--out", default="results/organism_dynamic_state_swap_v49")
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    base = out / "base.db"
    make_base(base)
    low = out / "dynamic_low.db"
    high = out / "dynamic_high.db"
    shutil.copy2(base, low)
    shutil.copy2(base, high)

    provider = build_provider(args.mode)
    low_run = run_condition(low, -0.8, provider, "DYNAMIC_LOW")
    high_run = run_condition(high, 0.8, provider, "DYNAMIC_HIGH")

    summary = {
        "experiment": "organism_dynamic_state_swap_v49",
        "mode": args.mode,
        "same_receiver_memory": (
            low_run["intervention"]["state_before"]["memory_fingerprint"]
            == high_run["intervention"]["state_before"]["memory_fingerprint"]
        ),
        "dynamic_only_intervention_low": low_run["intervention"]["dynamic_state_changed_only"],
        "dynamic_only_intervention_high": high_run["intervention"]["dynamic_state_changed_only"],
        "low_choice": low_run["choice"],
        "high_choice": high_run["choice"],
        "dynamic_state_changes_choice": low_run["choice"] != high_run["choice"],
    }

    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "runs.json").write_text(json.dumps({"low": low_run, "high": high_run}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
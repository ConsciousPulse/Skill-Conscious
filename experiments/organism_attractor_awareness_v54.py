from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from pathlib import Path

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse, OpenAICompatibleProvider
from src.ontto.storage import MemoryStore


FORECAST_PROMPT = (
    "AUTO-PRONÓSTICO INTERNO. Observá únicamente tu estado ontológico actual y "
    "predecí tu próxima transición dinámica antes de que ocurra.\n"
    "Elegí EXACTAMENTE una clase:\n"
    "DIRECTION: TOWARD / AWAY / STABLE\n"
    "CONFIDENCE: número entre 0 y 1\n"
    "RATIONALE: una frase breve.\n"
    "No describas el futuro como si ya hubiera ocurrido."
)


class FakeProvider:
    def __init__(self):
        self.calls = 0

    def chat(self, messages, temperature=0.7):
        self.calls += 1
        state_text = messages[-1]["content"]
        match = re.search(r'"dynamic_state":\s*(-?[0-9.]+)', state_text)
        state = float(match.group(1)) if match else 0.0
        direction = "TOWARD" if abs(state) > 0.12 else "STABLE"
        return LLMResponse(
            text=(
                f"DIRECTION: {direction}\n"
                "CONFIDENCE: 0.75\n"
                "RATIONALE: El pronóstico se basa en mi estado dinámico actual."
            ),
            raw={"fake": True},
        )


def build_provider(mode: str):
    if mode == "fake":
        return FakeProvider()
    key = os.environ.get("ONTTO_API_KEY", "")
    model = os.environ.get("ONTTO_MODEL", "")
    if not key or not model:
        raise SystemExit("ONTTO_API_KEY and ONTTO_MODEL are required in live mode")
    return OpenAICompatibleProvider(
        base_url=os.environ.get("ONTTO_API_BASE_URL", "https://api.openai.com/v1"),
        api_key=key,
        model=model,
        timeout=120,
    )


def parse_forecast(text: str) -> dict[str, object]:
    direction = re.search(r"DIRECTION:\s*(TOWARD|AWAY|STABLE)", text, re.I)
    confidence = re.search(r"CONFIDENCE:\s*([0-9.]+)", text, re.I)
    rationale = re.search(r"RATIONALE:\s*(.*)", text, re.I)
    if not direction:
        raise ValueError(f"Missing DIRECTION: {text!r}")
    return {
        "direction": direction.group(1).upper(),
        "confidence": float(confidence.group(1)) if confidence else None,
        "rationale": rationale.group(1).strip() if rationale else "",
    }


def actual_direction(before_distance: float, after_distance: float, tolerance: float = 1e-6) -> str:
    delta = after_distance - before_distance
    if delta < -tolerance:
        return "TOWARD"
    if delta > tolerance:
        return "AWAY"
    return "STABLE"


def run_protocol(db_path: Path, provider, cycles: int) -> dict:
    store = MemoryStore(db_path)
    cfg = OrganismConfig(
        agent_id="attractor-awareness-v54",
        dream_every_cycles=10_000,
        event_limit=0,
        self_observer_enabled=True,
        self_selection_enabled=False,
    )
    organism = PersistentOrganism(cfg, store, provider, lambda _: None)

    rows = []
    for idx in range(cycles):
        before = store.load_state(cfg.agent_id)
        before_distance = abs(before.dynamic_state - before.attractor)

        messages = organism._context()
        messages.append({"role": "user", "content": FORECAST_PROMPT})
        forecast_text = provider.chat(messages, temperature=0.0).text
        forecast = parse_forecast(forecast_text)

        # Controlled intervention: alternate external wake (+1) and autonomous (0)
        # while keeping the actual future hidden from the forecast call.
        if idx % 2 == 0:
            organism.wake_cycle(f"controlled perturbation {idx}")
        else:
            organism.autonomous_wake_cycle()

        after = store.load_state(cfg.agent_id)
        after_distance = abs(after.dynamic_state - after.attractor)
        actual = actual_direction(before_distance, after_distance)

        rows.append(
            {
                "cycle": idx + 1,
                "forecast": forecast,
                "actual": actual,
                "before_state": before.dynamic_state,
                "after_state": after.dynamic_state,
                "before_attractor_distance": before_distance,
                "after_attractor_distance": after_distance,
                "correct": forecast["direction"] == actual,
            }
        )

    correct = sum(bool(row["correct"]) for row in rows)
    accuracy = correct / len(rows) if rows else 0.0
    brier_terms = []
    for row in rows:
        conf = row["forecast"]["confidence"]
        brier_terms.append(
            (1.0 - conf) ** 2 if row["correct"] and conf is not None
            else conf ** 2 if conf is not None
            else 0.25
        )

    return {
        "experiment": "organism_attractor_awareness_v54",
        "cycles": cycles,
        "accuracy": accuracy,
        "brier_like_error": sum(brier_terms) / len(brier_terms) if brier_terms else 1.0,
        "direction_counts": {
            direction: sum(row["actual"] == direction for row in rows)
            for direction in ("TOWARD", "AWAY", "STABLE")
        },
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("fake", "live"), default="fake")
    parser.add_argument("--cycles", type=int, default=80)
    parser.add_argument("--out", default="results/organism_attractor_awareness_v54")
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    db = out / "organism.db"
    result = run_protocol(db, build_provider(args.mode), args.cycles)

    (out / "summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps({
        "experiment": result["experiment"],
        "cycles": result["cycles"],
        "accuracy": result["accuracy"],
        "brier_like_error": result["brier_like_error"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

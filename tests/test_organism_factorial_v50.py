import json
import sys
from pathlib import Path

from experiments.organism_factorial_v50 import main


def test_v50_fake_factorial(tmp_path: Path, monkeypatch):
    out = tmp_path / "v50"
    monkeypatch.setattr(sys, "argv", ["organism_factorial_v50.py", "--mode", "fake", "--replicates", "2", "--out", str(out)])
    main()
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["replicates"] == 2
    assert summary["same_probe"] is True
    assert summary["all_event_controls_hold"] is True
    assert summary["all_dynamic_memory_controls_hold"] is True
    assert summary["all_dynamic_pressure_controls_hold"] is True
    assert summary["all_dynamic_step_controls_hold"] is True
    assert summary["factorial_interaction_present"] is True

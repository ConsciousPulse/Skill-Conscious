import json
import sys
from pathlib import Path

from experiments.organism_dynamic_state_swap_v49 import main


def test_v49_fake_dynamic_state_swap(tmp_path: Path, monkeypatch):
    out = tmp_path / "v49"
    monkeypatch.setattr(sys, "argv", ["organism_dynamic_state_swap_v49.py", "--mode", "fake", "--out", str(out)])
    main()
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["same_receiver_memory"] is True
    assert summary["dynamic_only_intervention_low"] is True
    assert summary["dynamic_only_intervention_high"] is True
    assert summary["dynamic_state_changes_choice"] is True

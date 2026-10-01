import json
import sys
from pathlib import Path

from experiments.organism_dream_consolidation_v65 import main


def test_v65_dream_consolidation(tmp_path: Path, monkeypatch):
    out = tmp_path / "v65"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "organism_dream_consolidation_v65.py",
            "--replicates", "4",
            "--warmup", "4",
            "--experiences", "6",
            "--cycles", "6",
            "--out", str(out),
        ],
    )
    main()
    summary=json.loads((out/"summary.json").read_text(encoding="utf-8"))
    assert summary["replicates"] == 4
    assert summary["all_dream_bridge_runs_have_bridge"] is True
    assert 0.0 <= summary["paired_sign_flip_p_dream_bridge_regret"] <= 1.0
    assert 0.0 <= summary["paired_sign_flip_p_dream_bridge_hit"] <= 1.0
    assert 0.0 <= summary["paired_sign_flip_p_dream_vs_no_dream_regret"] <= 1.0

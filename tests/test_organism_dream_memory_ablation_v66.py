import json
import sys
from pathlib import Path

from experiments.organism_dream_memory_ablation_v66 import main


def test_v66_dream_memory_ablation(tmp_path: Path, monkeypatch):
    out = tmp_path / "v66"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "organism_dream_memory_ablation_v66.py",
            "--replicates", "4",
            "--experiences", "6",
            "--cycles", "6",
            "--out", str(out),
        ],
    )
    main()
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["replicates"] == 4
    assert summary["all_retained_runs_have_retrieval_signal"] is True
    assert 0.0 <= summary["paired_sign_flip_p_regret"] <= 1.0
    assert 0.0 <= summary["paired_sign_flip_p_hit"] <= 1.0

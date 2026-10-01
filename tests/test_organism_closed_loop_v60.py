import json
import sys
from pathlib import Path

from experiments.organism_closed_loop_v60 import main


def test_v60_closed_loop_protocol(tmp_path: Path, monkeypatch):
    out = tmp_path / "v60"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "organism_closed_loop_v60.py",
            "--replicates",
            "4",
            "--warmup",
            "8",
            "--cycles",
            "8",
            "--out",
            str(out),
        ],
    )

    main()

    summary = json.loads(
        (out / "summary.json").read_text(encoding="utf-8")
    )

    assert summary["replicates"] == 4
    assert summary["candidate_signals"] == [-1.0, 1.0]
    assert summary["all_runs_have_two_candidates"] is True
    assert summary["paired_sign_flip_p_mean_regret"] >= 0.0
    assert 0.0 <= summary["self_model_oracle_hit_rate"] <= 1.0
    assert 0.0 <= summary["random_oracle_hit_rate"] <= 1.0

import json
import sys
from pathlib import Path

from experiments.organism_self_model_selection_v57 import main


def test_v57_oracle_compared_selection(tmp_path: Path, monkeypatch):
    out = tmp_path / "v57"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "organism_self_model_selection_v57.py",
            "--replicates",
            "4",
            "--warmup",
            "12",
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
    assert summary["all_predictions_have_two_candidates"] is True
    assert 0.0 <= summary["self_model_oracle_hit_rate"] <= 1.0
    assert 0.0 <= summary["random_oracle_hit_rate"] <= 1.0
    assert summary["paired_sign_flip_p"] >= 0.0

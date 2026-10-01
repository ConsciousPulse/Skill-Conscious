import json
import sys
from pathlib import Path

from experiments.organism_meta_self_model_v61 import main


def test_v61_metacognitive_self_model(tmp_path: Path, monkeypatch):
    out = tmp_path / "v61"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "organism_meta_self_model_v61.py",
            "--replicates",
            "4",
            "--warmup",
            "12",
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
    assert summary["all_arms_have_two_candidates"] is True
    assert summary["paired_sign_flip_p_regret"] >= 0.0
    assert summary["paired_sign_flip_p_hit"] >= 0.0
    assert 0.0 <= summary["meta_self_model_oracle_hit_rate"] <= 1.0
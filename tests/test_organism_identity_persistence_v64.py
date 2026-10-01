import json
import sys
from pathlib import Path

from experiments.organism_identity_persistence_v64 import main


def test_v64_identity_persistence(tmp_path: Path, monkeypatch):
    out = tmp_path / "v64"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "organism_identity_persistence_v64.py",
            "--replicates",
            "4",
            "--warmup",
            "4",
            "--encode-cycles",
            "6",
            "--perturb-cycles",
            "2",
            "--ablation-cycles",
            "6",
            "--out",
            str(out),
        ],
    )

    main()

    summary = json.loads(
        (out / "summary.json").read_text(encoding="utf-8")
    )

    assert summary["replicates"] == 4
    assert summary["chance_accuracy"] == 0.5
    assert summary["all_folds_have_two_identity_classes"] is True
    assert 0.0 <= summary["paired_sign_flip_p_on_minus_off_accuracy"] <= 1.0
    assert 0.0 <= summary["bridge_on_above_chance_sign_flip_p"] <= 1.0

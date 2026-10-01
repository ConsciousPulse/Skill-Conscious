import json
import sys
from pathlib import Path

from experiments.organism_identity_recovery_v55 import main


def test_v55_identity_recovery_harness(tmp_path: Path, monkeypatch):
    out = tmp_path / "v55"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "organism_identity_recovery_v55.py",
            "--replicates",
            "2",
            "--warmup",
            "8",
            "--recovery-cycles",
            "12",
            "--out",
            str(out),
        ],
    )

    main()

    summary = json.loads(
        (out / "summary.json").read_text(encoding="utf-8")
    )

    assert summary["replicates"] == 2
    assert 0.0 <= summary["identity_preservation_fraction"] <= 1.0
    assert 0.0 <= summary["recovery_fraction"] <= 1.0
    assert summary["mean_final_state_error"] >= 0.0

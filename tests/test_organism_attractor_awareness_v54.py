import json
import sys
from pathlib import Path

from experiments.organism_attractor_awareness_v54 import main


def test_v54_fake_attractor_forecast(tmp_path: Path, monkeypatch):
    out = tmp_path / "v54"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "organism_attractor_awareness_v54.py",
            "--mode",
            "fake",
            "--cycles",
            "30",
            "--out",
            str(out),
        ],
    )

    main()

    summary = json.loads(
        (out / "summary.json").read_text(encoding="utf-8")
    )

    assert summary["cycles"] == 30
    assert 0.0 <= summary["accuracy"] <= 1.0
    counts = summary["direction_counts"]
    assert counts["TOWARD"] + counts["AWAY"] + counts["STABLE"] == 30

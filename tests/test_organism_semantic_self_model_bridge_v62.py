import json
import sys
from pathlib import Path

from experiments.organism_semantic_self_model_bridge_v62 import main


def test_v62_semantic_self_model_bridge(tmp_path: Path, monkeypatch):
    out = tmp_path / "v62"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "organism_semantic_self_model_bridge_v62.py",
            "--replicates",
            "4",
            "--out",
            str(out),
        ],
    )

    main()

    summary = json.loads(
        (out / "summary.json").read_text(encoding="utf-8")
    )

    assert summary["replicates"] == 4
    assert summary["bridge_off_isolates_effect"] is True
    assert summary["bridge_transduces_self_model_difference"] is True
    assert summary["self_model_persists_in_all_on_runs"] is True
    assert summary["self_model_versions_recorded"] is True
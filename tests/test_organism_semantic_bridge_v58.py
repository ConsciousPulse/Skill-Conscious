import json
import sys
from pathlib import Path

from experiments.organism_semantic_bridge_v58 import main


def test_v58_semantic_bridge_is_causal(tmp_path: Path, monkeypatch):
    out = tmp_path / "v58"
    monkeypatch.setattr(
        sys,
        "argv",
        ["organism_semantic_bridge_v58.py", "--out", str(out)],
    )

    main()

    summary = json.loads(
        (out / "summary.json").read_text(encoding="utf-8")
    )

    assert summary["matched_probe"] is True
    assert summary["bridge_off_isolates_effect"] is True
    assert summary["bridge_transduces_memory_difference"] is True
    assert summary["semantic_omega_difference"] > 0.0
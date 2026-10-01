import json
import sys
from pathlib import Path

from experiments.organism_semantic_self_model_v59 import main


def test_v59_factorial_protocol(tmp_path: Path, monkeypatch):
    out = tmp_path / "v59"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "organism_semantic_self_model_v59.py",
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
    assert summary["interaction_sign_flip_p"] >= 0.0
    assert 0.0 <= summary["self_model_oracle_hit_rate_bridge_off"] <= 1.0
    assert 0.0 <= summary["self_model_oracle_hit_rate_bridge_on"] <= 1.0

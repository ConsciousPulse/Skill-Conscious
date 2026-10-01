import json
import sys
from pathlib import Path

from experiments.organism_causal_self_model_loop_v63 import main


def test_v63_causal_self_model_loop(tmp_path: Path, monkeypatch):
    out = tmp_path / "v63"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "organism_causal_self_model_loop_v63.py",
            "--replicates",
            "4",
            "--warmup",
            "10",
            "--cycles",
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
    assert summary["candidate_signals"] == [-1.0, 1.0]
    assert summary["all_arms_have_two_candidates"] is True
    assert summary["all_bridge_on_runs_persist_self_model"] is True
    assert 0.0 <= summary["paired_sign_flip_p_selection_advantage"] <= 1.0
    assert 0.0 <= summary["paired_sign_flip_p_bridge_regret"] <= 1.0
    assert 0.0 <= summary["paired_sign_flip_p_bridge_hit"] <= 1.0

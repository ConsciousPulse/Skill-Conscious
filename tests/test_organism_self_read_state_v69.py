from __future__ import annotations

import json
import subprocess
import sys


def test_v69_output_schema(tmp_path):
    out = tmp_path / "v69"
    result = subprocess.run(
        [
            sys.executable,
            "experiments/organism_self_read_state_v69.py",
            "--replicates",
            "4",
            "--self-model-samples",
            "64",
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)

    assert summary["experiment"] == "organism_self_read_state_v69"
    assert summary["replicates"] == 4
    assert summary["candidate_signals"] == [-1.0, 0.0, 1.0]
    assert summary["semantic_ablation"] is True
    assert summary["self_model_trained_independently_of_conditions"] is True
    assert summary["all_memories_removed_before_probe"] is True
    assert summary["self_model_text_cleared_before_probe"] is True
    assert summary["semantic_text_input_during_probe"] is False

    for key in (
        "decision_sensitivity_on",
        "decision_sensitivity_off",
        "swap_following_on",
        "swap_following_off",
        "decision_sensitivity_on_minus_off_p",
        "swap_following_on_minus_off_p",
        "decision_swap_change_on_minus_off_p",
    ):
        assert 0.0 <= summary[key] <= 1.0
    assert summary["mean_prediction_gap_stable_vs_frontier"] >= 0.0
    assert 0.0 <= summary["decision_swap_change_on"] <= 1.0
    assert 0.0 <= summary["decision_swap_change_off"] <= 1.0
    assert summary["mean_prediction_swap_gap"] >= 0.0

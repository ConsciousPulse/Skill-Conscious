from __future__ import annotations

import json
import subprocess
import sys


def test_v69_output_schema(tmp_path):
    out = tmp_path / "v69"
    result = subprocess.run(
        [
            sys.executable,
            "experiments/organism_self_state_readout_v69.py",
            "--replicates",
            "4",
            "--calibration-cycles",
            "12",
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)
    assert summary["experiment"] == "organism_self_state_readout_v69"
    assert summary["replicates"] == 4
    assert summary["semantic_ablation"] is True
    assert summary["all_memories_removed_before_probe"] is True
    assert summary["self_model_text_cleared_before_probe"] is True
    assert summary["numeric_self_model_frozen_before_dream"] is True
    assert summary["semantic_text_input_during_probe"] is False
    assert 0.0 <= summary["observer_models_identical_fraction"] <= 1.0
    assert summary["read_score_delta_mean"] >= 0.0
    assert summary["prediction_delta_mean"] >= 0.0
    assert 0.0 <= summary["read_vs_clamped_action_change_fraction"] <= 1.0
    assert 0.0 <= summary["state_swap_policy_following_fraction"] <= 1.0

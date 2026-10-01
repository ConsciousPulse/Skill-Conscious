from __future__ import annotations

import json
import subprocess
import sys


def test_v75_output_schema(tmp_path):
    out = tmp_path / "v75"
    result = subprocess.run(
        [
            sys.executable,
            "experiments/organism_active_continuity_v75.py",
            "--episodes",
            "8",
            "--train-episodes",
            "8",
            "--observer-samples",
            "64",
            "--recovery-steps",
            "4",
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)
    assert summary["experiment"] == "organism_active_continuity_v75"
    assert summary["policy_reloaded_without_retraining"] is True
    assert summary["primary_objective_is_self_prediction_recovery"] is True
    assert summary["continuity_index_is_secondary_evaluation_only"] is True
    assert summary["objective_is_still_protocol_defined"] is True
    assert summary["external_attractor_target_removed_from_primary_objective"] is True
    assert summary["semantic_input_during_probe"] is False

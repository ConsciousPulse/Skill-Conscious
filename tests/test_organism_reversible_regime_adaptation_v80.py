from __future__ import annotations

import json
import subprocess
import sys


def test_v80_output_schema(tmp_path):
    out = tmp_path / "v80"
    result = subprocess.run(
        [
            sys.executable,
            "experiments/organism_reversible_regime_adaptation_v80.py",
            "--episodes-per-condition",
            "2",
            "--train-episodes",
            "2",
            "--observer-samples",
            "32",
            "--recovery-steps",
            "2",
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)

    assert summary["experiment"] == "organism_reversible_regime_adaptation_v80"
    assert summary["policy_snapshot_shared_between_frozen_and_adaptive"] is True
    assert summary["online_updates_use_only_observed_self_prediction_gain"] is True
    assert summary["external_retraining_during_probe"] is False
    assert summary["semantic_input_during_probe"] is False
    assert summary["reversible_nonstationary_protocol"] is True
    assert summary["stages"] == ["base", "shift_a", "shift_b", "base_return"]
    assert summary["primary_endpoint"] == "base_return_event_3_adaptive_minus_frozen"
    assert summary["max_intervention_target_error"] < 1e-12
    assert set(summary["conditions"]) == {
        "base",
        "shift_a",
        "shift_b",
        "base_return",
    }

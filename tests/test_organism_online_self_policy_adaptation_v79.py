from __future__ import annotations

import json
import subprocess
import sys


def test_v79_output_schema(tmp_path):
    out = tmp_path / "v79"
    result = subprocess.run(
        [
            sys.executable,
            "experiments/organism_online_self_policy_adaptation_v79.py",
            "--episodes-per-condition",
            "4",
            "--train-episodes",
            "4",
            "--observer-samples",
            "64",
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)

    assert summary["experiment"] == "organism_online_self_policy_adaptation_v79"
    assert summary["policy_snapshot_shared_between_frozen_and_adaptive"] is True
    assert summary["online_updates_use_only_observed_self_prediction_gain"] is True
    assert summary["external_retraining_during_probe"] is False
    assert summary["semantic_input_during_probe"] is False
    assert summary["training_schedule"] == "single_impulse"
    assert summary["ood_schedule"] == "triple_alternating"
    assert summary["intervention_target_error_max"] < 1e-12
    assert summary["shifted_dynamics_parameters"]["relaxation"] != 0.32
    assert summary["shifted_dynamics_parameters"]["pressure_gain"] != 0.55
    assert summary["shifted_dynamics_parameters"]["cross_gain"] != 0.85
    assert "shifted_repeated" in summary["conditions"]
    assert "adaptive_event_3" in summary["conditions"]["shifted_repeated"]

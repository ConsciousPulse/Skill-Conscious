from __future__ import annotations

import json
import subprocess
import sys


def test_v78_output_schema(tmp_path):
    out = tmp_path / "v78"
    result = subprocess.run(
        [
            sys.executable,
            "experiments/organism_repeated_active_continuity_v78.py",
            "--episodes-per-condition",
            "4",
            "--train-episodes",
            "4",
            "--observer-samples",
            "64",
            "--recovery-steps",
            "3",
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)

    assert summary["experiment"] == "organism_repeated_active_continuity_v78"
    assert summary["policy_reloaded_without_retraining"] is True
    assert summary["objective_is_self_prediction_gain"] is True
    assert summary["continuity_index_is_secondary_evaluation_only"] is True
    assert summary["ood_schedules_unseen_during_training"] is True
    assert summary["repeated_perturbations_evaluated_without_retraining"] is True
    assert summary["generalization_is_evaluated_without_continuity_labels"] is True
    assert summary["objective_is_still_protocol_defined"] is True
    assert summary["external_attractor_target_removed_from_primary_objective"] is True
    assert summary["semantic_input_during_probe"] is False

    assert summary["training_schedules"] == ["single_impulse"]
    assert summary["in_domain_schedules"] == ["single_impulse"]
    assert set(summary["ood_schedules"]) == {
        "double_same_sign",
        "double_alternating",
        "triple_alternating",
    }
    assert len(summary["conditions"]) == 4
    assert summary["intervention_target_error_max"] < 1e-12
    for condition in summary["conditions"].values():
        assert condition["intervention_target_error_mean"] < 1e-12
        assert "first_event_gain" in condition
        assert "second_event_gain" in condition

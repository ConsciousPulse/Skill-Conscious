from __future__ import annotations

import json
import subprocess
import sys


def test_v76_output_schema(tmp_path):
    out = tmp_path / "v76"
    result = subprocess.run(
        [
            sys.executable,
            "experiments/organism_generalized_active_continuity_v76.py",
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
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (f"stdout={result.stdout}\nstderr={result.stderr}")
    summary = json.loads(result.stdout)

    assert summary["experiment"] == "organism_generalized_active_continuity_v76"
    assert summary["policy_reloaded_without_retraining"] is True
    assert summary["objective_is_self_prediction_gain"] is True
    assert summary["continuity_index_is_secondary_evaluation_only"] is True
    assert summary["ood_perturbations_unseen_during_training"] is True
    assert summary["generalization_is_evaluated_without_continuity_labels"] is True
    assert summary["objective_is_still_protocol_defined"] is True
    assert summary["external_attractor_target_removed_from_primary_objective"] is True
    assert summary["semantic_input_during_probe"] is False

    assert set(summary["training_perturbations"]) == {0.25, 0.75}
    assert set(summary["in_domain_test_perturbations"]) == {0.25, 0.75}
    assert set(summary["ood_test_perturbations"]) == {0.35, 0.55, 0.85}
    assert len(summary["conditions"]) == 5

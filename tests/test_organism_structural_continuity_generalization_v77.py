from __future__ import annotations

import json
import subprocess
import sys


def test_v77_output_schema(tmp_path):
    out = tmp_path / "v77"
    result = subprocess.run(
        [
            sys.executable,
            "experiments/organism_structural_continuity_generalization_v77.py",
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

    assert summary["experiment"] == "organism_structural_continuity_generalization_v77"
    assert summary["policy_reloaded_without_retraining"] is True
    assert summary["objective_is_self_prediction_gain"] is True
    assert summary["continuity_index_is_secondary_evaluation_only"] is True
    assert summary["ood_structures_unseen_during_training"] is True
    assert summary["matched_terminal_state_across_structures"] is True
    assert summary["generalization_is_evaluated_without_continuity_labels"] is True
    assert summary["objective_is_still_protocol_defined"] is True
    assert summary["external_attractor_target_removed_from_primary_objective"] is True
    assert summary["semantic_input_during_probe"] is False

    assert summary["training_structures"] == ["single_impulse"]
    assert summary["in_domain_structures"] == ["single_impulse"]
    assert set(summary["ood_structures"]) == {
        "split_impulse",
        "reversal_pulse",
        "delayed_impulse",
    }
    assert len(summary["conditions"]) == 4

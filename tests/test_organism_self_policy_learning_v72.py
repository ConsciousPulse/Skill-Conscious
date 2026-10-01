from __future__ import annotations

import json
import subprocess
import sys


def test_v72_output_schema(tmp_path):
    out = tmp_path / "v72"
    result = subprocess.run(
        [
            sys.executable,
            "experiments/organism_self_policy_learning_v72.py",
            "--episodes",
            "8",
            "--train-episodes",
            "8",
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
    assert summary["experiment"] == "organism_self_policy_learning_v72"
    assert summary["policy_reloaded_without_retraining"] is True
    assert summary["state_blind_control_present"] is True
    assert summary["semantic_input_during_policy_probe"] is False
    assert summary["objective_is_externally_defined"] is True

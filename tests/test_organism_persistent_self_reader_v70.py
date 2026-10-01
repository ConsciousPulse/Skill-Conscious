from __future__ import annotations

import json
import subprocess
import sys


def test_v70_output_schema(tmp_path):
    out = tmp_path / "v70"
    result = subprocess.run(
        [
            sys.executable,
            "experiments/organism_persistent_self_reader_v70.py",
            "--replicates",
            "4",
            "--reader-samples",
            "64",
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)
    assert summary["experiment"] == "organism_persistent_self_reader_v70"
    assert summary["model_survived_restart"] is True
    assert summary["restart_prediction_max_abs_error"] <= 1e-12
    assert summary["restart_sample_count_before"] == summary["restart_sample_count_after"]
    assert 0.0 <= summary["condition_model_load_exact_fraction"] <= 1.0
    assert 0.0 <= summary["decision_sensitivity_on"] <= 1.0
    assert 0.0 <= summary["decision_sensitivity_off"] <= 1.0
    assert 0.0 <= summary["decision_swap_change_on"] <= 1.0

from __future__ import annotations

import json
import subprocess
import sys


def test_v71_output_schema(tmp_path):
    out = tmp_path / "v71"
    result = subprocess.run(
        [
            sys.executable,
            "experiments/organism_integrated_self_reader_v71.py",
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
    assert summary["experiment"] == "organism_integrated_self_reader_v71"
    assert summary["model_survived_restart_and_sleep"] is True
    assert summary["semantic_ablation_completed_before_probe"] is True
    assert summary["integrated_self_reader_used_automatically"] is True
    assert summary["all_memories_removed_before_probe"] is True
    assert summary["self_model_text_cleared_before_probe"] is True
    assert summary["manual_self_model_copy"] is False
    assert 0.0 <= summary["decision_sensitivity_on"] <= 1.0
    assert 0.0 <= summary["decision_sensitivity_blind"] <= 1.0
    assert 0.0 <= summary["decision_swap_change_on"] <= 1.0

from __future__ import annotations

import json
import subprocess
import sys


def test_v73_output_schema(tmp_path):
    out = tmp_path / "v73"
    result = subprocess.run(
        [
            sys.executable,
            "experiments/organism_integrated_self_policy_v73.py",
            "--replicates",
            "4",
            "--observer-samples",
            "64",
            "--train-episodes",
            "8",
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)
    assert summary["experiment"] == "organism_integrated_self_policy_v73"
    assert summary["policy_persisted_inside_organism_store"] is True
    assert summary["model_and_policy_recovered_after_restart"] is True
    assert summary["learned_policy_used_automatically_after_sleep"] is True
    assert summary["semantic_input_during_probe"] is False
    assert summary["manual_policy_copy_after_restart"] is False

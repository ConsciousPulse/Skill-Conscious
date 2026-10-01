from __future__ import annotations

import json
import subprocess
import sys


def test_v68_output_schema(tmp_path):
    out = tmp_path / "v68"
    result = subprocess.run(
        [
            sys.executable,
            "experiments/organism_dream_state_persistence_v68.py",
            "--replicates",
            "4",
            "--horizons",
            "0,1,2",
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)
    assert summary["experiment"] == "organism_dream_state_persistence_v68"
    assert summary["replicates"] == 4
    assert summary["horizons"] == [0, 1, 2]
    assert summary["all_memories_removed_before_probe"] is True
    assert summary["self_model_cleared_before_probe"] is True
    assert summary["semantic_text_input_during_probe"] is False
    for row in summary["results"]:
        assert 0.0 <= row["own_accuracy"] <= 1.0
        assert 0.0 <= row["state_swap_following_accuracy"] <= 1.0
        assert 0.0 <= row["own_p"] <= 1.0
        assert 0.0 <= row["state_swap_p"] <= 1.0
        assert 0.0 <= row["swap_core_exact_match_fraction"] <= 1.0

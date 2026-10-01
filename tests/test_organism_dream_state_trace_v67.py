from __future__ import annotations

import json
import subprocess
import sys


def test_v67_output_schema(tmp_path):
    out = tmp_path / "v67"
    result = subprocess.run(
        [
            sys.executable,
            "experiments/organism_dream_state_trace_v67.py",
            "--replicates",
            "4",
            "--trace-steps",
            "6",
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)
    assert summary["experiment"] == "organism_dream_state_trace_v67"
    assert summary["replicates"] == 4
    assert 0.0 <= summary["post_ablation_own_accuracy"] <= 1.0
    assert 0.0 <= summary["state_swap_following_accuracy"] <= 1.0
    assert 0.0 <= summary["post_ablation_own_accuracy_p"] <= 1.0
    assert 0.0 <= summary["state_swap_following_p"] <= 1.0
    assert summary["all_memories_removed_before_probe"] is True
    assert summary["self_model_cleared_before_probe"] is True
    assert summary["semantic_text_input_during_probe"] is False
    assert 0.0 <= summary["swap_core_exact_match_fraction"] <= 1.0

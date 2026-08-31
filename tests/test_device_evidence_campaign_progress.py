from __future__ import annotations

from types import SimpleNamespace

from local_llm_server.device_evidence_campaign import _PASS, _phase
from scripts.run_device_evidence_campaign import ProgressDeviceEvidenceCampaign


def _args(tmp_path):
    return SimpleNamespace(
        output_dir=str(tmp_path / "evidence"),
        scope="minimum-l2",
        model_a="model-a",
        model_b=None,
    )


def test_live_progress_prints_phase_start_and_completion(capsys, tmp_path) -> None:
    campaign = ProgressDeviceEvidenceCampaign(_args(tmp_path))

    result = campaign._run_phase(
        "example_phase",
        lambda: _phase(_PASS, reason="bounded check completed"),
    )

    assert result["status"] == _PASS
    output = capsys.readouterr().out
    assert "START  example_phase" in output
    assert "PASS  example_phase" in output
    assert "bounded check completed" in output
    assert "s)" in output


def test_live_progress_keeps_exception_paths_private(capsys, tmp_path) -> None:
    campaign = ProgressDeviceEvidenceCampaign(_args(tmp_path))

    def fail():
        raise RuntimeError("failed at /Users/alice/private/model.gguf")

    campaign._run_phase("private_failure", fail)

    output = capsys.readouterr().out
    assert "private_failure" in output
    assert "RuntimeError" in output
    assert "alice" not in output
    assert "model.gguf" not in output

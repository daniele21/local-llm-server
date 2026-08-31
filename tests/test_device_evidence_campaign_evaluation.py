from __future__ import annotations

import argparse
import json
from pathlib import Path

from local_llm_server import device_evidence_campaign as campaign_module
from local_llm_server.device_evidence_campaign import DeviceEvidenceCampaign, _FAIL, _PASS


def _args(tmp_path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        model_a="model-a",
        model_a_path="/private/model-a.gguf",
        model_b="model-b",
        model_b_path="/private/model-b.gguf",
        backend="llama_cpp",
        multi_model_backend="llama_server",
        request_estimate_mib=64.0,
        scope="full",
        host="127.0.0.1",
        port=18000,
        startup_timeout=1.0,
        request_timeout=1.0,
        evaluation_timeout=1.0,
        output_dir=str(tmp_path / "evidence"),
    )


def _report(run_id: str) -> dict:
    sample_ids = [f"sample-{index:02d}" for index in range(10)]
    return {
        "manifest": {
            "run_id": run_id,
            "test_set_identity": "d" * 64,
            "sample_ids": sample_ids,
            "model": "model-a",
            "runtime_fingerprint": "f" * 64,
            "reasoning_profile": {
                "requested": "off",
                "runtime_mode": "switchable",
                "effective": "off",
                "request_override": True,
            },
        },
        "complete": True,
        "results": [
            {
                "sample_id": sample_id,
                "succeeded": True,
                "scores": [{"name": "objective", "value": 1.0, "passed": True}],
                "metrics": {"wall_time_seconds": 0.1},
            }
            for sample_id in sample_ids
        ],
    }


def test_evaluation_consumes_api_envelope_and_persists_canonical_reports(monkeypatch, tmp_path: Path) -> None:
    runner = DeviceEvidenceCampaign(_args(tmp_path))
    responses = iter(
        [
            (200, {"evidence_grade": True, "report": _report("run-a")}),
            (200, {"evidence_grade": True, "report": _report("run-b")}),
        ]
    )
    monkeypatch.setattr(campaign_module, "_request_json", lambda *_args, **_kwargs: next(responses))

    result = runner._evaluation("http://127.0.0.1:18000")

    assert result["status"] == _PASS
    assert result["checks"]["canonical_report_envelope"] is True
    assert result["checks"]["api_evidence_grade"] is True
    persisted_a = json.loads((runner.output_dir / "evaluation-off-a.json").read_text(encoding="utf-8"))
    persisted_b = json.loads((runner.output_dir / "evaluation-off-b.json").read_text(encoding="utf-8"))
    assert persisted_a["manifest"]["run_id"] == "run-a"
    assert persisted_b["manifest"]["run_id"] == "run-b"
    assert "report" not in persisted_a
    assert "evidence_grade" not in persisted_a


def test_evaluation_rejects_noncanonical_or_non_evidence_grade_envelope(monkeypatch, tmp_path: Path) -> None:
    runner = DeviceEvidenceCampaign(_args(tmp_path))
    responses = iter(
        [
            (200, {"evidence_grade": False, "report": _report("run-a")}),
            (200, {"evidence_grade": True, "report": _report("run-b")}),
        ]
    )
    monkeypatch.setattr(campaign_module, "_request_json", lambda *_args, **_kwargs: next(responses))

    result = runner._evaluation("http://127.0.0.1:18000")

    assert result["status"] == _FAIL
    assert result["checks"]["canonical_report_envelope"] is True
    assert result["checks"]["api_evidence_grade"] is False

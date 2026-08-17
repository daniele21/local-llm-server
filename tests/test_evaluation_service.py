from __future__ import annotations

import json
from pathlib import Path

import pytest

from local_llm_server.core.contracts import ErrorCode, InferenceError
from local_llm_server.evaluation_service import (
    EvaluationRunRequest,
    EvaluationService,
    EvaluationStore,
    report_to_dict,
)
from local_llm_server.runtime import ModelRuntimeManager
from local_llm_server.runtime_evidence import RuntimeIdentitySnapshot, attach_runtime_identity


class _Engine:
    backend = "fake"

    def __init__(self):
        self.calls = 0

    def complete(self, payload):
        self.calls += 1
        return {
            "choices": [
                {
                    "message": {"role": "assistant", "content": "wrong"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 3, "completion_tokens": 1},
        }

    def close(self):
        pass


def _manager(*, fingerprint: bool = False):
    engine = _Engine()
    cfg = {
        "model": "demo",
        "model_id": "org/demo",
        "backend": "fake",
        "model_path": "/demo",
        "max_concurrent_requests": 1,
    }
    manager = ModelRuntimeManager(default_model="demo")
    runtime = manager.add(cfg, engine)
    if fingerprint:
        attach_runtime_identity(
            runtime,
            RuntimeIdentitySnapshot("a" * 64, {"artifact_key": "b" * 64}, 1.0),
        )
    return manager, engine


def test_service_lists_builtin_test_set():
    manager, _ = _manager()
    [test_set] = EvaluationService(manager).list_test_sets()
    assert test_set["id"] == "general-purpose"
    assert test_set["sample_count"] == 20
    assert len(str(test_set["identity"])) == 64


def test_service_runs_ten_samples_on_resident_runtime_and_persists_report(tmp_path: Path):
    manager, engine = _manager(fingerprint=True)
    store = EvaluationStore(tmp_path / "runs")
    service = EvaluationService(manager, store=store)

    outcome = service.run(
        EvaluationRunRequest(model="demo", sample_count=10, seed=42)
    )

    assert outcome.report.complete is True
    assert len(outcome.report.results) == 10
    assert engine.calls == 10
    assert outcome.evidence_grade is True
    assert outcome.report.manifest.runtime_fingerprint == "a" * 64
    assert outcome.persisted_path is not None

    payload = json.loads(Path(outcome.persisted_path).read_text(encoding="utf-8"))
    assert payload["manifest"]["runtime_fingerprint"] == "a" * 64
    assert payload["manifest"]["content_retained"] is True
    assert payload["complete"] is True
    assert len(payload["results"]) == 10
    assert all(result["content"]["input"] for result in payload["results"])
    assert all(result["content"]["expected"] for result in payload["results"])
    assert all("output" in result["content"] for result in payload["results"])
    assert all("content" not in result for result in report_to_dict(outcome.report)["results"])
    assert store.list_run_ids() == (outcome.report.manifest.run_id,)


def test_service_can_exclude_model_output_from_local_history(tmp_path: Path):
    manager, _ = _manager()
    store = EvaluationStore(tmp_path / "runs")
    outcome = EvaluationService(manager, store=store).run(
        EvaluationRunRequest(model="demo", sample_count=10, retain_content=False)
    )

    payload = json.loads(Path(outcome.persisted_path).read_text(encoding="utf-8"))
    assert payload["manifest"]["content_retained"] is False
    assert all(result["content"]["input"] for result in payload["results"])
    assert all(result["content"]["expected"] for result in payload["results"])
    assert all("output" not in result["content"] for result in payload["results"])


def test_run_without_identity_is_exploratory_not_evidence_grade():
    manager, _ = _manager(fingerprint=False)
    outcome = EvaluationService(manager).run(
        EvaluationRunRequest(model="demo", sample_count=10, seed=0)
    )
    assert outcome.evidence_grade is False
    assert outcome.report.manifest.runtime_fingerprint is None


def test_sample_count_must_be_multiple_of_ten_and_fit_dataset():
    with pytest.raises(ValueError, match="multiple of 10"):
        EvaluationRunRequest(model="demo", sample_count=5)

    manager, _ = _manager()
    with pytest.raises(ValueError, match="exceeds dataset size"):
        EvaluationService(manager).run(
            EvaluationRunRequest(model="demo", sample_count=30)
        )


def test_nonresident_model_is_rejected_before_starting_run():
    manager, _ = _manager()
    with pytest.raises(InferenceError) as exc_info:
        EvaluationService(manager).run(
            EvaluationRunRequest(model="missing", sample_count=10)
        )
    assert exc_info.value.code is ErrorCode.MODEL_NOT_RESIDENT

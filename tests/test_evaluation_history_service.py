from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from local_llm_server.evaluation_history_api import install_evaluation_history_api
from local_llm_server.evaluation_history_service import EvaluationHistoryService


def _report(
    run_id: str,
    *,
    fingerprint: str | None = "a" * 64,
    model: str = "demo",
    sample_ids=("s1", "s2"),
    scores=(0.5, 0.5),
    wall=(2.0, 2.0),
):
    return {
        "manifest": {
            "run_id": run_id,
            "model": model,
            "test_set_id": "general-purpose",
            "test_set_version": "1",
            "test_set_identity": "t" * 64,
            "sample_ids": list(sample_ids),
            "seed": 0,
            "runtime_fingerprint": fingerprint,
        },
        "complete": True,
        "results": [
            {
                "sample_id": sample_id,
                "succeeded": True,
                "scores": [{"name": "objective", "value": scores[index], "passed": scores[index] == 1.0}],
                "error_code": None,
                "metrics": {
                    "wall_time_seconds": wall[index],
                    "prompt_tokens": 10,
                    "completion_tokens": 2,
                },
            }
            for index, sample_id in enumerate(sample_ids)
        ],
    }


def _write(root: Path, payload: dict):
    root.mkdir(parents=True, exist_ok=True)
    run_id = payload["manifest"]["run_id"]
    path = root / f"{run_id}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_history_service_lists_valid_reports_and_skips_corrupt_files(tmp_path: Path):
    root = tmp_path / "runs"
    _write(root, _report("run-a"))
    _write(root, _report("run-b"))
    (root / "broken.json").write_text("not-json", encoding="utf-8")

    service = EvaluationHistoryService(root)
    summaries = service.list_summaries()

    assert {item.summary.run_id for item in summaries} == {"run-a", "run-b"}
    assert all(item.summary.objective_quality_mean == 0.5 for item in summaries)


def test_history_service_loads_exact_run_and_blocks_path_traversal(tmp_path: Path):
    root = tmp_path / "runs"
    _write(root, _report("run-a"))
    service = EvaluationHistoryService(root)

    assert service.load_report("run-a")["manifest"]["run_id"] == "run-a"
    with pytest.raises(ValueError, match="invalid run_id"):
        service.load_report("../secret")


def test_history_service_comparison_preserves_descriptive_only_semantics(tmp_path: Path):
    root = tmp_path / "runs"
    _write(root, _report("baseline", fingerprint="a" * 64, scores=(0.5, 0.5)))
    _write(root, _report("candidate", fingerprint="b" * 64, scores=(1.0, 0.5)))

    comparison = EvaluationHistoryService(root).compare("baseline", "candidate")

    assert comparison.comparable is True
    assert comparison.evidence_grade is True
    assert comparison.attribution_safe is False
    assert comparison.deltas["objective_quality_mean"] == 0.25
    assert any("descriptive only" in reason for reason in comparison.reasons)


def test_history_api_lists_loads_and_compares_runs(tmp_path: Path):
    root = tmp_path / "runs"
    _write(root, _report("baseline", scores=(0.5, 0.5), wall=(2.0, 2.0)))
    _write(root, _report("candidate", scores=(1.0, 0.5), wall=(1.0, 1.0)))

    app = FastAPI()
    install_evaluation_history_api(app, root=root)
    client = TestClient(app)

    history = client.get("/api/v1/evaluation/history")
    assert history.status_code == 200
    assert {item["run_id"] for item in history.json()["runs"]} == {"baseline", "candidate"}

    loaded = client.get("/api/v1/evaluation/history/baseline")
    assert loaded.status_code == 200
    assert loaded.json()["manifest"]["run_id"] == "baseline"

    comparison = client.get(
        "/api/v1/evaluation/history/compare",
        params={"baseline": "baseline", "candidate": "candidate"},
    )
    assert comparison.status_code == 200
    payload = comparison.json()
    assert payload["comparable"] is True
    assert payload["attribution_safe"] is True
    assert payload["deltas"]["objective_quality_mean"] == 0.25
    assert payload["deltas"]["mean_wall_time_seconds"] == -1.0


def test_history_api_rejects_self_comparison_and_missing_run(tmp_path: Path):
    root = tmp_path / "runs"
    _write(root, _report("baseline"))
    app = FastAPI()
    install_evaluation_history_api(app, root=root)
    client = TestClient(app)

    self_compare = client.get(
        "/api/v1/evaluation/history/compare",
        params={"baseline": "baseline", "candidate": "baseline"},
    )
    assert self_compare.status_code == 400

    missing = client.get("/api/v1/evaluation/history/missing")
    assert missing.status_code == 404

from __future__ import annotations

import json
from pathlib import Path

import pytest

from local_llm_server.state_backup import (
    build_archive,
    export_state,
    restore_state,
    validate_archive,
)


def _evaluation_payload(run_id: str = "run-1") -> dict[str, object]:
    return {
        "manifest": {
            "run_id": run_id,
            "test_set_id": "general-purpose",
            "test_set_version": "1.0.0",
            "test_set_identity": "fixture-identity",
            "sample_ids": [],
            "model": "fixture-model",
            "task_types": ["chat"],
            "seed": 0,
            "runtime_fingerprint": None,
            "reasoning_profile": None,
            "content_retained": False,
        },
        "complete": True,
        "results": [],
    }


def _test_set_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "id": "custom",
        "version": "v1",
        "provenance": {"note": "fixture"},
        "samples": [
            {
                "id": f"sample-{index}",
                "task": "chat",
                "input": f"input {index}",
                "expected": {"exact": "OK"},
                "tags": ["fixture"],
            }
            for index in range(10)
        ],
    }


def _receipt_payload() -> dict[str, object]:
    return {
        "logical_id": "fixture-model",
        "artifact_path": "/private/local/model.gguf",
        "sha256": "a" * 64,
        "size_bytes": 123,
        "mtime_ns": 456,
        "inode": None,
        "device": None,
    }


def _seed_state(evaluation_root: Path, receipt_root: Path) -> None:
    evaluation_root.mkdir(parents=True)
    (evaluation_root / "run-1.json").write_text(
        json.dumps(_evaluation_payload()), encoding="utf-8"
    )
    test_sets = evaluation_root / "test_sets"
    test_sets.mkdir()
    (test_sets / "custom@v1.json").write_text(
        json.dumps(_test_set_payload()), encoding="utf-8"
    )
    receipt_root.mkdir(parents=True)
    (receipt_root / "receipt.json").write_text(
        json.dumps(_receipt_payload()), encoding="utf-8"
    )
    (evaluation_root / "unowned-model-weight.gguf").write_bytes(
        b"not server-owned JSON state"
    )


def test_state_archive_round_trip_is_bounded_and_allow_listed(tmp_path: Path) -> None:
    source_eval = tmp_path / "source-eval"
    source_receipts = tmp_path / "source-receipts"
    _seed_state(source_eval, source_receipts)
    archive_path = tmp_path / "backup.json"

    export_state(
        archive_path,
        evaluation_root=source_eval,
        receipt_root=source_receipts,
    )
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    validated = validate_archive(archive)
    assert set(validated) == {
        "evaluation_reports",
        "custom_test_sets",
        "artifact_verification_receipts",
    }
    serialized = archive_path.read_text(encoding="utf-8")
    assert "unowned-model-weight.gguf" not in serialized

    target_eval = tmp_path / "target-eval"
    target_receipts = tmp_path / "target-receipts"
    counts = restore_state(
        archive_path,
        evaluation_root=target_eval,
        receipt_root=target_receipts,
    )

    assert counts == {
        "evaluation_reports": 1,
        "custom_test_sets": 1,
        "artifact_verification_receipts": 1,
    }
    assert json.loads((target_eval / "run-1.json").read_text()) == _evaluation_payload()
    assert json.loads((target_eval / "test_sets/custom@v1.json").read_text()) == _test_set_payload()
    assert json.loads((target_receipts / "receipt.json").read_text()) == _receipt_payload()


def test_future_archive_schema_fails_before_any_target_write(tmp_path: Path) -> None:
    source_eval = tmp_path / "source-eval"
    source_receipts = tmp_path / "source-receipts"
    _seed_state(source_eval, source_receipts)
    archive = build_archive(evaluation_root=source_eval, receipt_root=source_receipts)
    archive["schema_version"] = 999
    path = tmp_path / "future.json"
    path.write_text(json.dumps(archive), encoding="utf-8")
    target_eval = tmp_path / "target-eval"
    target_receipts = tmp_path / "target-receipts"

    with pytest.raises(ValueError, match="unsupported state archive"):
        restore_state(path, evaluation_root=target_eval, receipt_root=target_receipts)

    assert not target_eval.exists()
    assert not target_receipts.exists()


def test_restore_conflict_is_detected_before_new_files_are_written(tmp_path: Path) -> None:
    source_eval = tmp_path / "source-eval"
    source_receipts = tmp_path / "source-receipts"
    _seed_state(source_eval, source_receipts)
    archive_path = tmp_path / "backup.json"
    export_state(archive_path, evaluation_root=source_eval, receipt_root=source_receipts)

    target_eval = tmp_path / "target-eval"
    target_eval.mkdir()
    existing = target_eval / "run-1.json"
    existing.write_text('{"keep": true}', encoding="utf-8")
    target_receipts = tmp_path / "target-receipts"

    with pytest.raises(FileExistsError):
        restore_state(
            archive_path,
            evaluation_root=target_eval,
            receipt_root=target_receipts,
        )

    assert existing.read_text(encoding="utf-8") == '{"keep": true}'
    assert not (target_eval / "test_sets").exists()
    assert not target_receipts.exists()


def test_checksum_or_traversal_tampering_is_rejected(tmp_path: Path) -> None:
    source_eval = tmp_path / "source-eval"
    source_receipts = tmp_path / "source-receipts"
    _seed_state(source_eval, source_receipts)
    archive = build_archive(evaluation_root=source_eval, receipt_root=source_receipts)
    archive["categories"]["evaluation_reports"][0]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="checksum mismatch"):
        validate_archive(archive)

    archive = build_archive(evaluation_root=source_eval, receipt_root=source_receipts)
    archive["categories"]["evaluation_reports"][0]["name"] = "../escape.json"
    with pytest.raises(ValueError, match="unsafe"):
        validate_archive(archive)


def test_legacy_and_versioned_receipts_are_accepted(tmp_path: Path) -> None:
    source_eval = tmp_path / "eval"
    source_eval.mkdir()
    receipts = tmp_path / "receipts"
    receipts.mkdir()
    (receipts / "legacy.json").write_text(json.dumps(_receipt_payload()), encoding="utf-8")
    versioned = {"schema_version": 1, "receipt": _receipt_payload()}
    (receipts / "versioned.json").write_text(json.dumps(versioned), encoding="utf-8")

    archive = build_archive(evaluation_root=source_eval, receipt_root=receipts)
    assert len(archive["categories"]["artifact_verification_receipts"]) == 2

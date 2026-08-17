from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tests" / "e2e" / "prepare_failure_evidence.py"

spec = importlib.util.spec_from_file_location("prepare_failure_evidence", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_failure_evidence_keeps_identity_and_drops_sensitive_error_payloads() -> None:
    report = {
        "suites": [
            {
                "file": "/private/tmp/work/tests/e2e/studio.spec.js",
                "specs": [
                    {
                        "title": "critical journey",
                        "ok": False,
                        "tests": [
                            {
                                "results": [
                                    {
                                        "status": "failed",
                                        "duration": 123,
                                        "error": {"message": "SECRET PROMPT /Users/alice/private.txt"},
                                        "stdout": ["SECRET OUTPUT"],
                                    }
                                ]
                            }
                        ],
                    }
                ],
            }
        ]
    }
    manifest = module.build_manifest(
        report,
        {
            "SOURCE_HEAD_SHA": "abc123",
            "GITHUB_SHA": "merge456",
            "GITHUB_RUN_ID": "77",
            "GITHUB_RUN_ATTEMPT": "2",
            "GITHUB_WORKFLOW": "CI",
            "GITHUB_JOB": "browser-e2e",
            "GITHUB_EVENT_NAME": "pull_request",
        },
    )

    serialized = str(manifest)
    assert manifest["identity"]["source_head_sha"] == "abc123"
    assert manifest["tests"][0]["file"] == "tests/e2e/studio.spec.js"
    assert manifest["tests"][0]["outcomes"] == [{"status": "failed", "duration_ms": 123}]
    assert "SECRET" not in serialized
    assert "/Users/alice" not in serialized
    assert manifest["privacy"]["absolute_paths_retained"] is False


def test_absolute_non_test_paths_are_not_retained() -> None:
    report = {
        "suites": [
            {
                "file": "/Users/alice/project/other/private.spec.js",
                "specs": [{"title": "x", "ok": False, "tests": []}],
            }
        ]
    }
    manifest = module.build_manifest(report, {})
    assert manifest["tests"][0]["file"] is None

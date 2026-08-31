from __future__ import annotations

import pytest

from local_llm_server.evidence_identity import build_evidence_identity


def test_evidence_identity_has_reproducible_fingerprints_and_unique_run_identity() -> None:
    common = {
        "evidence_kind": "ci_microbenchmark",
        "workload": {"name": "scheduler_roundtrip", "iterations": 100},
        "configuration": {"queue_capacity": 4, "max_concurrency": 2},
        "environment_class": "hosted-linux-x64-python3.11",
        "source_revision": "abc123",
        "runtime_identity": {"python": "3.11", "implementation": "cpython"},
    }
    first = build_evidence_identity(**common, run_id="run-a", generated_at="2026-08-17T20:00:00+00:00")
    second = build_evidence_identity(**common, run_id="run-b", generated_at="2026-08-17T20:01:00+00:00")

    assert first.workload_fingerprint == second.workload_fingerprint
    assert first.configuration_fingerprint == second.configuration_fingerprint
    assert first.runtime_fingerprint == second.runtime_fingerprint
    assert first.comparison_key == second.comparison_key
    assert first.evidence_id != second.evidence_id
    assert first.to_dict()["source_revision"] == "abc123"


def test_evidence_identity_rejects_sensitive_payload_keys() -> None:
    with pytest.raises(ValueError, match="sensitive identity key"):
        build_evidence_identity(
            evidence_kind="hardware",
            workload={"prompt": "do not retain me"},
            configuration={"cycles": 3},
            environment_class="representative-macos-arm64",
            source_revision=None,
        )

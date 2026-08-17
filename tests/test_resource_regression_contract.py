import json
from pathlib import Path

from scripts.verify_resource_regression import PATH, validate


def test_repository_resource_regression_contract_is_valid() -> None:
    payload = json.loads(PATH.read_text(encoding="utf-8"))
    assert validate(payload) == []


def test_contract_rejects_missing_heap_claim_and_native_boundary() -> None:
    payload = {
        "schema_version": 1,
        "evidence_class": "hosted-deterministic-python",
        "claims": [],
        "non_claims": [],
    }
    errors = validate(payload)
    assert any("claims must be a non-empty array" in error for error in errors)

import json

from scripts.verify_fault_injection import PATH, validate


def test_repository_fault_injection_matrix_is_valid() -> None:
    payload = json.loads(PATH.read_text(encoding="utf-8"))
    assert validate(payload) == []


def test_fault_matrix_rejects_missing_critical_domains() -> None:
    payload = {
        "schema_version": 1,
        "owner": "test",
        "required_domains": [],
        "faults": [],
        "non_claims": ["one", "two", "three"],
    }
    errors = validate(payload)
    assert any("required_domains" in error for error in errors)
    assert any("faults must be a non-empty array" in error for error in errors)

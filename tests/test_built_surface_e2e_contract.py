import json

from scripts.verify_built_surface_e2e import PATH, validate


def test_repository_built_surface_e2e_contract_is_valid() -> None:
    payload = json.loads(PATH.read_text(encoding="utf-8"))
    assert validate(payload) == []


def test_contract_rejects_source_only_surface_and_prompt_retention() -> None:
    payload = {
        "schema_version": 1,
        "surface": "source-checkout",
        "workflow": "missing.yml",
        "workflow_marker": "missing",
        "smoke_runner": "missing.py",
        "journey_runner": "missing.py",
        "journey": {},
        "privacy": {"retain_prompt_or_output": True, "retain_private_paths": False},
        "non_claims": [],
    }
    errors = validate(payload)
    assert any("fresh-installed-wheel" in error for error in errors)
    assert any("privacy policy" in error for error in errors)

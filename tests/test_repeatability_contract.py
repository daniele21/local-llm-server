from __future__ import annotations

import json

from scripts.verify_repeatability_contracts import PATH, validate
from tests.e2e.lifecycle import OwnedRunState, stale_owned_roots


def test_multiple_owned_e2e_runs_leave_no_owned_temp_roots() -> None:
    before = set(stale_owned_roots())
    created = []
    for _ in range(5):
        state = OwnedRunState.create()
        created.append(state.root)
        assert state.owns_root() is True
        state.cleanup()
        assert state.root.exists() is False
    assert set(stale_owned_roots()) == before
    assert len(set(created)) == 5


def test_repository_repeatability_contract_is_valid() -> None:
    payload = json.loads(PATH.read_text(encoding="utf-8"))
    assert validate(payload) == []


def test_repeatability_contract_rejects_missing_lifecycles() -> None:
    payload = {
        "schema_version": 1,
        "owner": "test",
        "required_lifecycles": [],
        "contracts": [],
        "non_claims": ["one", "two", "three"],
    }
    errors = validate(payload)
    assert any("required_lifecycles" in error for error in errors)
    assert any("contracts must be a non-empty array" in error for error in errors)

from __future__ import annotations

from datetime import date
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_security_exceptions.py"
EXCEPTIONS = ROOT / ".engineering" / "security-exceptions.json"

spec = importlib.util.spec_from_file_location("verify_security_exceptions", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_repository_security_exception_contract_is_valid() -> None:
    payload = json.loads(EXCEPTIONS.read_text(encoding="utf-8"))
    assert module.validate(payload, today=date(2026, 8, 17)) == []


def test_exception_contract_rejects_expired_and_unowned_exception() -> None:
    payload = json.loads(EXCEPTIONS.read_text(encoding="utf-8"))
    payload["exceptions"][0]["expires_on"] = "2026-08-16"
    payload["exceptions"][0]["owner"] = ""

    errors = module.validate(payload, today=date(2026, 8, 17))

    assert any("expired on 2026-08-16" in error for error in errors)
    assert any("owner must be non-empty" in error for error in errors)


def test_exception_contract_rejects_duplicate_ids_and_missing_controls() -> None:
    payload = json.loads(EXCEPTIONS.read_text(encoding="utf-8"))
    duplicate = dict(payload["exceptions"][0])
    payload["exceptions"].append(duplicate)
    payload["exceptions"][0]["compensating_controls"] = []

    errors = module.validate(payload, today=date(2026, 8, 17))

    assert any("duplicate exception id" in error for error in errors)
    assert any("compensating_controls" in error for error in errors)

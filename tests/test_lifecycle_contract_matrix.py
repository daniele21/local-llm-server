from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_lifecycle_contracts.py"
MATRIX = ROOT / ".engineering" / "lifecycle-contracts.json"

spec = importlib.util.spec_from_file_location("verify_lifecycle_contracts", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_repository_lifecycle_contract_matrix_is_valid() -> None:
    payload = json.loads(MATRIX.read_text(encoding="utf-8"))
    assert module.validate(payload) == []


def test_matrix_rejects_missing_test_function_and_critical_phase() -> None:
    payload = json.loads(MATRIX.read_text(encoding="utf-8"))
    payload["contracts"][0]["test"] = "tests/test_runtime_resource_admission.py::test_missing"
    payload["contracts"] = [
        item for item in payload["contracts"] if item["phase"] != "timeout"
    ]

    errors = module.validate(payload)

    assert any("test function not found" in error for error in errors)
    assert any("critical lifecycle phases missing evidence" in error for error in errors)

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_performance_budgets.py"
BUDGETS = ROOT / ".engineering" / "performance-budgets.json"

spec = importlib.util.spec_from_file_location("verify_performance_budgets", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_repository_performance_budget_contract_is_valid() -> None:
    payload = json.loads(BUDGETS.read_text(encoding="utf-8"))
    assert module.validate(payload) == []


def test_budget_contract_rejects_unbounded_and_duplicate_entries() -> None:
    payload = json.loads(BUDGETS.read_text(encoding="utf-8"))
    duplicate = dict(payload["budgets"][0])
    duplicate["maximum"] = 0
    payload["budgets"].append(duplicate)

    errors = module.validate(payload)

    assert any("duplicate budget id" in error for error in errors)
    assert any("maximum must be a positive number" in error for error in errors)


def test_device_metrics_cannot_be_silently_dropped() -> None:
    payload = json.loads(BUDGETS.read_text(encoding="utf-8"))
    payload["representative_device_metrics"]["required"].remove("peak_memory_bytes")

    errors = module.validate(payload)

    assert any("canonical metric set" in error for error in errors)

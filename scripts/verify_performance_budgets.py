#!/usr/bin/env python3
"""Validate the repository-owned performance/resource budget contract."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUDGET_PATH = ROOT / ".engineering" / "performance-budgets.json"
ALLOWED_CLASSES = {
    "operational-hard-limit",
    "resource-cardinality-default",
    "resource-capacity-default",
    "storage-retention-hard-limit",
}
ALLOWED_UNITS = {"seconds", "requests", "tokens", "builds", "days", "bytes"}
REQUIRED_DEVICE_METRICS = {
    "startup_time_seconds",
    "time_to_first_token_seconds",
    "decode_tokens_per_second",
    "peak_memory_bytes",
    "post_unload_memory_bytes",
    "shutdown_time_seconds",
}


def validate(payload: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["root must be an object"]
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not isinstance(payload.get("owner"), str) or not str(payload.get("owner")).strip():
        errors.append("owner must be non-empty")

    raw_budgets = payload.get("budgets")
    if not isinstance(raw_budgets, list) or not raw_budgets:
        errors.append("budgets must be a non-empty array")
        raw_budgets = []

    seen: set[str] = set()
    for index, item in enumerate(raw_budgets):
        prefix = f"budgets[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        budget_id = item.get("id")
        if not isinstance(budget_id, str) or not budget_id.strip():
            errors.append(f"{prefix}.id must be non-empty")
        elif budget_id in seen:
            errors.append(f"duplicate budget id: {budget_id}")
        else:
            seen.add(budget_id)
        if item.get("class") not in ALLOWED_CLASSES:
            errors.append(f"{prefix}.class is invalid")
        if item.get("unit") not in ALLOWED_UNITS:
            errors.append(f"{prefix}.unit is invalid")
        maximum = item.get("maximum")
        if isinstance(maximum, bool) or not isinstance(maximum, (int, float)) or maximum <= 0:
            errors.append(f"{prefix}.maximum must be a positive number")
        if item.get("ci_enforceable") is not True:
            errors.append(f"{prefix}.ci_enforceable must be true for repository budgets")
        for key in ("metric", "source"):
            if not isinstance(item.get(key), str) or not str(item.get(key)).strip():
                errors.append(f"{prefix}.{key} must be non-empty")

    device = payload.get("representative_device_metrics")
    if not isinstance(device, dict):
        errors.append("representative_device_metrics must be an object")
    else:
        required = device.get("required")
        if not isinstance(required, list) or set(required) != REQUIRED_DEVICE_METRICS:
            errors.append("representative_device_metrics.required must match the canonical metric set")
        for key in ("threshold_policy", "evidence_owner"):
            if not isinstance(device.get(key), str) or not str(device.get(key)).strip():
                errors.append(f"representative_device_metrics.{key} must be non-empty")
    return errors


def main() -> int:
    try:
        payload = json.loads(BUDGET_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Performance budget check: FAIL: {exc}")
        return 1
    errors = validate(payload)
    print("Performance/resource budget contract")
    print(f"path: {BUDGET_PATH}")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

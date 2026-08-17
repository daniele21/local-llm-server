#!/usr/bin/env python3
"""Validate critical lifecycle contracts against concrete pytest functions."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / ".engineering" / "lifecycle-contracts.json"
ALLOWED_PHASES = {
    "startup",
    "startup_failure",
    "timeout",
    "cancellation",
    "completion_cleanup",
    "shutdown",
    "process_shutdown",
    "dependency_failure",
    "dependency_shutdown",
}
REQUIRED_PHASES = {
    "startup_failure",
    "timeout",
    "cancellation",
    "shutdown",
    "process_shutdown",
    "dependency_failure",
}


def _test_functions(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }


def validate(payload: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["root must be an object"]
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not isinstance(payload.get("owner"), str) or not payload.get("owner", "").strip():
        errors.append("owner must be non-empty")
    contracts = payload.get("contracts")
    if not isinstance(contracts, list) or not contracts:
        return errors + ["contracts must be a non-empty array"]

    seen_ids: set[str] = set()
    observed_phases: set[str] = set()
    path_cache: dict[Path, set[str]] = {}
    for index, raw in enumerate(contracts):
        prefix = f"contracts[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{prefix} must be an object")
            continue
        contract_id = raw.get("id")
        if not isinstance(contract_id, str) or not contract_id.strip():
            errors.append(f"{prefix}.id must be non-empty")
        elif contract_id in seen_ids:
            errors.append(f"duplicate lifecycle contract id: {contract_id}")
        else:
            seen_ids.add(contract_id)
        phase = raw.get("phase")
        if phase not in ALLOWED_PHASES:
            errors.append(f"{prefix}.phase is invalid")
        else:
            observed_phases.add(str(phase))
        if not isinstance(raw.get("claim"), str) or not raw.get("claim", "").strip():
            errors.append(f"{prefix}.claim must be non-empty")
        nodeid = raw.get("test")
        if not isinstance(nodeid, str) or "::" not in nodeid:
            errors.append(f"{prefix}.test must be a pytest file::function node id")
            continue
        relative, function = nodeid.split("::", 1)
        path = (ROOT / relative).resolve()
        if ROOT not in path.parents or path.suffix != ".py" or not path.is_file():
            errors.append(f"{prefix}.test file does not exist in repository: {relative}")
            continue
        functions = path_cache.setdefault(path, _test_functions(path))
        if function not in functions:
            errors.append(f"{prefix}.test function not found: {nodeid}")

    missing_phases = REQUIRED_PHASES - observed_phases
    if missing_phases:
        errors.append(f"critical lifecycle phases missing evidence: {sorted(missing_phases)}")
    non_claims = payload.get("explicit_non_claims")
    if not isinstance(non_claims, list) or len(non_claims) < 2 or not all(
        isinstance(item, str) and item.strip() for item in non_claims
    ):
        errors.append("explicit_non_claims must contain at least two non-empty strings")
    return errors


def main() -> int:
    try:
        payload = json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Lifecycle contract check: FAIL: {exc}")
        return 1
    errors = validate(payload)
    print("Critical lifecycle contract matrix")
    print(f"path: {PATH}")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        return 1
    print(f"RESULT: PASS ({len(payload['contracts'])} contract(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

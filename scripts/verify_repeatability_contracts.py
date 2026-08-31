#!/usr/bin/env python3
"""Validate repeatability/cleanliness contracts against pytest and workflow evidence."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / ".engineering" / "repeatability-contracts.json"
REQUIRED_LIFECYCLES = {"development", "test", "e2e", "build", "smoke", "runtime"}


def _test_functions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    }


def validate(payload: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["root must be an object"]
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    required = payload.get("required_lifecycles")
    if not isinstance(required, list) or set(required) != REQUIRED_LIFECYCLES:
        errors.append(f"required_lifecycles must be exactly {sorted(REQUIRED_LIFECYCLES)}")

    contracts = payload.get("contracts")
    if not isinstance(contracts, list) or not contracts:
        return errors + ["contracts must be a non-empty array"]
    seen_ids: set[str] = set()
    observed: set[str] = set()
    test_cache: dict[Path, set[str]] = {}
    for index, item in enumerate(contracts):
        prefix = f"contracts[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        contract_id = item.get("id")
        lifecycle = item.get("lifecycle")
        if not isinstance(contract_id, str) or not contract_id:
            errors.append(f"{prefix}.id must be non-empty")
        elif contract_id in seen_ids:
            errors.append(f"duplicate repeatability contract id: {contract_id}")
        else:
            seen_ids.add(contract_id)
        if lifecycle not in REQUIRED_LIFECYCLES:
            errors.append(f"{prefix}.lifecycle is invalid")
        else:
            observed.add(str(lifecycle))
        if not isinstance(item.get("claim"), str) or not item.get("claim", "").strip():
            errors.append(f"{prefix}.claim must be non-empty")
        evidence = item.get("evidence")
        if not isinstance(evidence, dict):
            errors.append(f"{prefix}.evidence must be an object")
            continue
        kind = evidence.get("kind")
        if kind == "pytest":
            nodeid = evidence.get("nodeid")
            if not isinstance(nodeid, str) or "::" not in nodeid:
                errors.append(f"{prefix}.evidence.nodeid must be file::function")
                continue
            relative, function = nodeid.split("::", 1)
            path = (ROOT / relative).resolve()
            if ROOT not in path.parents or path.suffix != ".py" or not path.is_file():
                errors.append(f"{prefix} pytest file missing: {relative}")
                continue
            functions = test_cache.setdefault(path, _test_functions(path))
            if function not in functions:
                errors.append(f"{prefix} pytest function missing: {nodeid}")
        elif kind == "workflow_marker":
            relative = evidence.get("path")
            marker = evidence.get("marker")
            if not isinstance(relative, str) or not isinstance(marker, str) or not marker:
                errors.append(f"{prefix} workflow evidence requires path and marker")
                continue
            path = (ROOT / relative).resolve()
            if ROOT not in path.parents or not path.is_file():
                errors.append(f"{prefix} workflow file missing: {relative}")
                continue
            if marker not in path.read_text(encoding="utf-8"):
                errors.append(f"{prefix} workflow marker missing: {marker!r}")
        else:
            errors.append(f"{prefix}.evidence.kind must be pytest or workflow_marker")

    missing = REQUIRED_LIFECYCLES - observed
    if missing:
        errors.append(f"repeatability lifecycles missing evidence: {sorted(missing)}")
    non_claims = payload.get("non_claims")
    if not isinstance(non_claims, list) or len(non_claims) < 3:
        errors.append("non_claims must contain at least three entries")
    return errors


def main() -> int:
    try:
        payload = json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Repeatability contract: FAIL: {exc}")
        return 1
    errors = validate(payload)
    print("Repeatability/cleanliness contract")
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

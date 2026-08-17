#!/usr/bin/env python3
"""Validate deterministic resource/memory regression claims and concrete tests."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / ".engineering" / "resource-regression.json"
REQUIRED_IDS = {
    "ledger-returns-empty",
    "rejected-admission-does-not-grow-ledger",
    "python-heap-retention-bounded",
}
REQUIRED_NON_CLAIMS = {
    "native backend memory reclamation",
    "Apple unified-memory reclamation",
    "RSS return-to-baseline",
}


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
    if payload.get("evidence_class") != "hosted-deterministic-python":
        errors.append("evidence_class must be hosted-deterministic-python")
    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        return errors + ["claims must be a non-empty array"]

    seen: set[str] = set()
    cache: dict[Path, set[str]] = {}
    for index, claim in enumerate(claims):
        prefix = f"claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{prefix} must be an object")
            continue
        claim_id = claim.get("id")
        if not isinstance(claim_id, str) or not claim_id:
            errors.append(f"{prefix}.id must be non-empty")
        elif claim_id in seen:
            errors.append(f"duplicate claim id: {claim_id}")
        else:
            seen.add(claim_id)
        nodeid = claim.get("test")
        if not isinstance(nodeid, str) or "::" not in nodeid:
            errors.append(f"{prefix}.test must be file::function")
            continue
        relative, function = nodeid.split("::", 1)
        test_path = (ROOT / relative).resolve()
        if ROOT not in test_path.parents or not test_path.is_file() or test_path.suffix != ".py":
            errors.append(f"{prefix}.test file is invalid: {relative}")
            continue
        functions = cache.setdefault(test_path, _test_functions(test_path))
        if function not in functions:
            errors.append(f"{prefix}.test function not found: {nodeid}")
        for key, value in claim.items():
            if key.endswith("iterations") or key.startswith("max_"):
                if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                    errors.append(f"{prefix}.{key} must be a positive integer")

    missing = REQUIRED_IDS - seen
    if missing:
        errors.append(f"required resource regression claims missing: {sorted(missing)}")
    non_claims = payload.get("non_claims")
    if not isinstance(non_claims, list) or not all(isinstance(item, str) and item for item in non_claims):
        errors.append("non_claims must be a non-empty string array")
    elif not REQUIRED_NON_CLAIMS.issubset(set(non_claims)):
        errors.append("non_claims must preserve native/unified-memory/RSS evidence boundary")
    return errors


def main() -> int:
    try:
        payload = json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Resource regression contract: FAIL: {exc}")
        return 1
    errors = validate(payload)
    print("Resource/memory regression contract")
    print(f"path: {PATH}")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        return 1
    print(f"RESULT: PASS ({len(payload['claims'])} claim(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

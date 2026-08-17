#!/usr/bin/env python3
"""Validate critical fault-injection claims against concrete pytest evidence."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / ".engineering" / "fault-injection.json"
REQUIRED_DOMAINS = {
    "resource_admission",
    "worker_lifecycle",
    "persistence_integrity",
    "pressure_policy",
    "request_admission",
    "request_lifecycle",
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
    if not isinstance(payload.get("owner"), str) or not payload.get("owner", "").strip():
        errors.append("owner must be non-empty")

    declared_required = payload.get("required_domains")
    if not isinstance(declared_required, list) or set(declared_required) != REQUIRED_DOMAINS:
        errors.append(f"required_domains must be exactly {sorted(REQUIRED_DOMAINS)}")

    faults = payload.get("faults")
    if not isinstance(faults, list) or not faults:
        return errors + ["faults must be a non-empty array"]
    seen_ids: set[str] = set()
    observed_domains: set[str] = set()
    cache: dict[Path, set[str]] = {}
    for index, raw in enumerate(faults):
        prefix = f"faults[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{prefix} must be an object")
            continue
        fault_id = raw.get("id")
        domain = raw.get("domain")
        if not isinstance(fault_id, str) or not fault_id.strip():
            errors.append(f"{prefix}.id must be non-empty")
        elif fault_id in seen_ids:
            errors.append(f"duplicate fault id: {fault_id}")
        else:
            seen_ids.add(fault_id)
        if domain not in REQUIRED_DOMAINS:
            errors.append(f"{prefix}.domain is invalid: {domain!r}")
        else:
            observed_domains.add(str(domain))
        for key in ("fault", "recovery_invariant"):
            if not isinstance(raw.get(key), str) or not raw.get(key, "").strip():
                errors.append(f"{prefix}.{key} must be non-empty")
        nodeid = raw.get("test")
        if not isinstance(nodeid, str) or "::" not in nodeid:
            errors.append(f"{prefix}.test must be a pytest file::function node id")
            continue
        relative, function = nodeid.split("::", 1)
        path = (ROOT / relative).resolve()
        if ROOT not in path.parents or path.suffix != ".py" or not path.is_file():
            errors.append(f"{prefix}.test file does not exist in repository: {relative}")
            continue
        functions = cache.setdefault(path, _test_functions(path))
        if function not in functions:
            errors.append(f"{prefix}.test function not found: {nodeid}")

    missing = REQUIRED_DOMAINS - observed_domains
    if missing:
        errors.append(f"critical fault domains missing evidence: {sorted(missing)}")
    non_claims = payload.get("non_claims")
    if not isinstance(non_claims, list) or len(non_claims) < 3 or not all(
        isinstance(item, str) and item.strip() for item in non_claims
    ):
        errors.append("non_claims must contain at least three non-empty strings")
    return errors


def main() -> int:
    try:
        payload = json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Fault-injection contract: FAIL: {exc}")
        return 1
    errors = validate(payload)
    print("Critical fault-injection matrix")
    print(f"path: {PATH}")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        return 1
    print(f"RESULT: PASS ({len(payload['faults'])} fault(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

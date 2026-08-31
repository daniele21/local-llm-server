#!/usr/bin/env python3
"""Machine-enforced architecture fitness checks for critical ownership boundaries."""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
from pathlib import Path
import sys
from typing import Any

POLICY_PATH = Path(".engineering/architecture-policy.json")
PACKAGE = "local_llm_server"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    return parser.parse_args()


def _load_policy(root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    path = root / POLICY_PATH
    if not path.is_file():
        return None, [f"missing architecture policy: {POLICY_PATH.as_posix()}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"invalid architecture policy: {exc}"]
    if not isinstance(value, dict):
        return None, ["architecture policy root must be an object"]
    return value, []


def _relative_import(file_path: Path, source_root: Path, node: ast.ImportFrom) -> str:
    rel = file_path.relative_to(source_root)
    package_parts = [PACKAGE, *rel.parts[:-1]]
    if node.level:
        trim = node.level - 1
        if trim > len(package_parts) - 1:
            return ""
        if trim:
            package_parts = package_parts[:-trim]
        if node.module:
            package_parts.extend(node.module.split("."))
        return ".".join(package_parts)
    return node.module or ""


def _imports(file_path: Path, source_root: Path) -> tuple[list[str], str | None]:
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    except (OSError, SyntaxError) as exc:
        return [], str(exc)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            resolved = _relative_import(file_path, source_root, node)
            if resolved:
                imports.append(resolved)
    return imports, None


def validate_architecture(root: Path) -> list[str]:
    policy, errors = _load_policy(root)
    if policy is None:
        return errors
    if policy.get("schema_version") != 1:
        errors.append("architecture policy schema_version must be 1")

    source_rel = policy.get("source_root")
    if not isinstance(source_rel, str) or not source_rel:
        errors.append("architecture policy source_root is required")
        return errors
    source_root = root / source_rel
    if not source_root.is_dir():
        errors.append(f"architecture source_root does not exist: {source_rel}")
        return errors

    owners = policy.get("owners")
    if not isinstance(owners, list) or not owners:
        errors.append("architecture policy owners must be a non-empty list")
    else:
        seen_boundaries: set[str] = set()
        seen_paths: set[str] = set()
        for index, owner in enumerate(owners):
            if not isinstance(owner, dict):
                errors.append(f"owner[{index}] must be an object")
                continue
            boundary = owner.get("boundary")
            path = owner.get("path")
            if not isinstance(boundary, str) or not boundary:
                errors.append(f"owner[{index}] boundary is required")
            elif boundary in seen_boundaries:
                errors.append(f"duplicate architecture boundary owner: {boundary}")
            else:
                seen_boundaries.add(boundary)
            if not isinstance(path, str) or not path:
                errors.append(f"owner[{index}] path is required")
            elif path in seen_paths:
                errors.append(f"multiple critical boundaries share the same canonical owner path: {path}")
            else:
                seen_paths.add(path)
                if not (root / path).exists():
                    errors.append(f"architecture owner path does not exist: {path}")

    rules = policy.get("rules")
    if not isinstance(rules, list) or not rules:
        errors.append("architecture policy rules must be a non-empty list")
        return errors

    seen_rule_ids: set[str] = set()
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            errors.append(f"rule[{index}] must be an object")
            continue
        rule_id = rule.get("id")
        paths = rule.get("paths")
        forbidden = rule.get("forbidden_import_prefixes")
        rationale = rule.get("rationale")
        if not isinstance(rule_id, str) or not rule_id:
            errors.append(f"rule[{index}] id is required")
            continue
        if rule_id in seen_rule_ids:
            errors.append(f"duplicate architecture rule id: {rule_id}")
            continue
        seen_rule_ids.add(rule_id)
        if not isinstance(paths, list) or not paths or not all(isinstance(item, str) and item for item in paths):
            errors.append(f"rule {rule_id} paths must be non-empty strings")
            continue
        if not isinstance(forbidden, list) or not forbidden or not all(isinstance(item, str) and item for item in forbidden):
            errors.append(f"rule {rule_id} forbidden_import_prefixes must be non-empty strings")
            continue
        if not isinstance(rationale, str) or not rationale.strip():
            errors.append(f"rule {rule_id} rationale is required")

        candidates = [
            path
            for path in source_root.rglob("*.py")
            if any(fnmatch.fnmatch(path.relative_to(source_root).as_posix(), pattern) for pattern in paths)
        ]
        if not candidates:
            errors.append(f"rule {rule_id} matches no Python files")
            continue
        for path in sorted(candidates):
            imported, parse_error = _imports(path, source_root)
            if parse_error:
                errors.append(f"cannot parse {path.relative_to(root)}: {parse_error}")
                continue
            for imported_name in imported:
                for prefix in forbidden:
                    if imported_name == prefix or imported_name.startswith(prefix + "."):
                        errors.append(
                            f"architecture rule {rule_id} violated: {path.relative_to(root)} imports {imported_name} (forbidden {prefix})"
                        )
    return errors


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    errors = validate_architecture(root)
    print("Architecture fitness")
    print(f"root: {root}")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

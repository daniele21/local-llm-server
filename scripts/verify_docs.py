#!/usr/bin/env python3
"""Bound documentation and disposable workstream state without external deps."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    return parser.parse_args()


def measure(path: Path, chars_per_token: int) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    return len(text.splitlines()), math.ceil(len(text) / chars_per_token)


def check_budget(path: Path, label: str, budget: dict[str, int], chars_per_token: int, errors: list[str]) -> None:
    if not path.is_file():
        return
    lines, tokens = measure(path, chars_per_token)
    if lines > budget["max_lines"]:
        errors.append(f"{label} too long: {lines} lines > {budget['max_lines']} ({path})")
    if tokens > budget["max_estimated_tokens"]:
        errors.append(f"{label} too expensive: ~{tokens} tokens > {budget['max_estimated_tokens']} ({path})")


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    policy_path = root / ".engineering/documentation-policy.json"
    if not policy_path.is_file():
        print("FAIL: missing .engineering/documentation-policy.json")
        return 1
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    chars_per_token = int(policy.get("estimated_token_characters", 4))
    budgets = policy["budgets"]
    errors: list[str] = []

    check_budget(root / "AGENTS.md", "root AGENTS", budgets["root_agents"], chars_per_token, errors)
    check_budget(root / "docs/current-state.md", "current state", budgets["current_state"], chars_per_token, errors)
    check_budget(root / "docs/architecture.md", "architecture", budgets["architecture"], chars_per_token, errors)

    for path in root.rglob("AGENTS.md"):
        if path == root / "AGENTS.md" or ".git" in path.parts:
            continue
        check_budget(path, "scoped AGENTS", budgets["scoped_agents"], chars_per_token, errors)

    feature_root = root / "docs/features"
    if feature_root.is_dir():
        for path in feature_root.glob("*.md"):
            if path.name != "README.md":
                check_budget(path, "feature doc", budgets["feature_doc"], chars_per_token, errors)

    workstream_root = root / "docs/workstreams"
    active_count = 0
    completed_markers = tuple(policy.get("completed_workstream_markers", []))
    if workstream_root.is_dir():
        for path in workstream_root.glob("*.md"):
            if path.name == "README.md" or path.name.startswith("_"):
                continue
            active_count += 1
            check_budget(path, "active workstream", budgets["active_workstream"], chars_per_token, errors)
            text = path.read_text(encoding="utf-8")
            if any(marker.lower() in text.lower() for marker in completed_markers):
                errors.append(
                    f"completed workstream kept as active documentation: {path.relative_to(root)}; finalize and delete by default"
                )

    print("Documentation health")
    print(f"active workstreams: {active_count}")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

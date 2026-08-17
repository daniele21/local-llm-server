#!/usr/bin/env python3
"""Bound documentation and detect deterministic documentation lifecycle drift."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re
import sys

_REVIEWED_RE = re.compile(r"^Last reviewed:\s*(\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE)
_MD_LINK_RE = re.compile(r"\]\(([^)#]+\.md)(?:#[^)]*)?\)")
_METADATA_PREFIXES = (
    "Status:",
    "Owner:",
    "Canonical scope:",
    "Read when:",
    "Last reviewed:",
    "Document type:",
)


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


def _check_freshness(path: Path, label: str, max_days: int, today: date, errors: list[str]) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    match = _REVIEWED_RE.search(text)
    if match is None:
        errors.append(f"{label} missing Last reviewed YYYY-MM-DD: {path}")
        return
    try:
        reviewed = date.fromisoformat(match.group(1))
    except ValueError:
        errors.append(f"{label} has invalid Last reviewed date: {path}")
        return
    age = (today - reviewed).days
    if age < 0:
        errors.append(f"{label} Last reviewed is in the future: {path}")
    elif age > max_days:
        errors.append(f"{label} stale: {age} days since review > {max_days} ({path})")


def _normalized_body(text: str) -> str:
    kept: list[str] = []
    for index, raw in enumerate(text.splitlines()):
        line = raw.strip()
        if index == 0 and line.startswith("# "):
            continue
        if any(line.startswith(prefix) for prefix in _METADATA_PREFIXES):
            continue
        if not line:
            continue
        kept.append(" ".join(line.split()))
    return "\n".join(kept)


def _check_canonical_scopes(root: Path, prefix: str, errors: list[str]) -> None:
    owners: dict[str, Path] = {}
    for path in sorted((root / "docs").rglob("*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.startswith(prefix):
                continue
            scope = line[len(prefix):].strip()
            if not scope:
                errors.append(f"empty canonical scope: {path.relative_to(root)}")
                break
            previous = owners.get(scope)
            if previous is not None and previous != path:
                errors.append(
                    f"duplicate canonical scope {scope!r}: {previous.relative_to(root)} and {path.relative_to(root)}"
                )
            else:
                owners[scope] = path
            break


def _check_duplicate_bodies(root: Path, minimum: int, errors: list[str]) -> None:
    seen: dict[str, Path] = {}
    for path in sorted((root / "docs").rglob("*.md")):
        body = _normalized_body(path.read_text(encoding="utf-8"))
        if len(body) < minimum:
            continue
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        previous = seen.get(digest)
        if previous is not None:
            errors.append(
                f"duplicate documentation body: {previous.relative_to(root)} and {path.relative_to(root)}"
            )
        else:
            seen[digest] = path


def _check_workstream_index(workstream_root: Path, active: set[str], errors: list[str]) -> None:
    index = workstream_root / "README.md"
    if not index.is_file():
        errors.append("missing docs/workstreams/README.md")
        return
    linked = {
        Path(match).name
        for match in _MD_LINK_RE.findall(index.read_text(encoding="utf-8"))
        if Path(match).name != "README.md"
    }
    for missing in sorted(active - linked):
        errors.append(f"active workstream missing from index: docs/workstreams/{missing}")
    for stale in sorted(linked - active):
        errors.append(f"workstream index points to missing/non-active file: docs/workstreams/{stale}")


def validate_documents(root: Path, *, today: date | None = None) -> tuple[list[str], int]:
    policy_path = root / ".engineering/documentation-policy.json"
    if not policy_path.is_file():
        return ["missing .engineering/documentation-policy.json"], 0
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid documentation policy: {exc}"], 0
    chars_per_token = int(policy.get("estimated_token_characters", 4))
    budgets = policy["budgets"]
    errors: list[str] = []
    current_day = today or date.today()

    current_state = root / "docs/current-state.md"
    architecture = root / "docs/architecture.md"
    check_budget(root / "AGENTS.md", "root AGENTS", budgets["root_agents"], chars_per_token, errors)
    check_budget(current_state, "current state", budgets["current_state"], chars_per_token, errors)
    check_budget(architecture, "architecture", budgets["architecture"], chars_per_token, errors)

    freshness = policy.get("freshness_days", {})
    if isinstance(freshness, dict):
        _check_freshness(current_state, "current state", int(freshness.get("current_state", 45)), current_day, errors)
        _check_freshness(architecture, "architecture", int(freshness.get("architecture", 180)), current_day, errors)

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
    active_files: set[str] = set()
    completed_markers = tuple(policy.get("completed_workstream_markers", []))
    if workstream_root.is_dir():
        for path in workstream_root.glob("*.md"):
            if path.name == "README.md" or path.name.startswith("_"):
                continue
            active_files.add(path.name)
            check_budget(path, "active workstream", budgets["active_workstream"], chars_per_token, errors)
            if isinstance(freshness, dict):
                _check_freshness(
                    path,
                    "active workstream",
                    int(freshness.get("active_workstream", 90)),
                    current_day,
                    errors,
                )
            text = path.read_text(encoding="utf-8")
            if any(marker.lower() in text.lower() for marker in completed_markers):
                errors.append(
                    f"completed workstream kept as active documentation: {path.relative_to(root)}; finalize and delete by default"
                )
        if policy.get("require_workstream_index_consistency", False):
            _check_workstream_index(workstream_root, active_files, errors)

    prefix = str(policy.get("canonical_scope_prefix", "Canonical scope:"))
    _check_canonical_scopes(root, prefix, errors)
    _check_duplicate_bodies(root, int(policy.get("duplicate_min_characters", 240)), errors)
    return errors, len(active_files)


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    errors, active_count = validate_documents(root)
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

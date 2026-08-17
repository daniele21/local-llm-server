#!/usr/bin/env python3
"""Zero-dependency structural checks for an adopted repository."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

CORE_SKILLS = (
    "plan-workstream", "structured-change", "validate-change", "finalize-workstream", "review-reference-quality",
)
REQUIRED = (
    "README.md", "AGENTS.md", "CONTRIBUTING.md", "SECURITY.md", ".editorconfig", ".gitignore",
    ".engineering/baseline.json", ".engineering/documentation-policy.json", ".engineering/commands.json",
    ".github/pull_request_template.md", ".github/workflows/repository-health.yml",
    "docs/README.md", "docs/architecture.md", "docs/current-state.md", "docs/features/README.md", "docs/adr/README.md",
    "docs/workstreams/README.md", "scripts/verify_operations.py",
)
PLACEHOLDER_MARKERS = ("<PROJECT_NAME>", "<REPLACE_WITH_", "<DESCRIBE_", "<LIST_")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--template-mode", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    errors: list[str] = []
    warnings: list[str] = []

    for rel in REQUIRED:
        if not (root / rel).is_file():
            errors.append(f"missing required file: {rel}")
    for name in CORE_SKILLS:
        rel = Path("skills") / name / "SKILL.md"
        if not (root / rel).is_file():
            errors.append(f"missing core skill: {rel.as_posix()}")

    baseline_path = root / ".engineering/baseline.json"
    if baseline_path.is_file():
        try:
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"invalid baseline.json: {exc}")
        else:
            if baseline.get("schema_version") != 1:
                errors.append("baseline schema_version must be 1")
            standard = baseline.get("standard", {})
            if standard.get("source") != "daniele21/repo-template-sw":
                errors.append("baseline standard.source must identify daniele21/repo-template-sw")
            if not standard.get("version"):
                errors.append("baseline standard.version is required")
            if baseline.get("target_level") not in {"L0", "L1", "L2"}:
                errors.append("target_level must be L0, L1 or L2")
            if not isinstance(baseline.get("profiles"), list):
                errors.append("profiles must be a list")
            skills = baseline.get("skills", {})
            for name in CORE_SKILLS:
                entry = skills.get(name)
                if not isinstance(entry, dict):
                    errors.append(f"baseline missing skill metadata: {name}")
                    continue
                if not entry.get("source_version"):
                    errors.append(f"skill {name} missing source_version")
                if not isinstance(entry.get("customized"), bool):
                    errors.append(f"skill {name} customized must be boolean")

    if not args.template_mode:
        for path in (root / "README.md", root / "AGENTS.md", root / "docs/architecture.md", root / "SECURITY.md"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for marker in PLACEHOLDER_MARKERS:
                if marker in text:
                    errors.append(f"unresolved adopter placeholder {marker} in {path.relative_to(root)}")

    common_generated = ("node_modules", ".venv", "build", "dist", "__pycache__")
    present = [name for name in common_generated if (root / name).exists()]
    if present:
        warnings.append("generated/local directories present in worktree: " + ", ".join(present))
    if not any((root / name).is_file() for name in ("LICENSE", "LICENSE.md", "LICENSE.txt")):
        warnings.append("no project license file detected; select an explicit license before public distribution")

    print("Repository baseline check")
    print(f"root: {root}")
    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s), {len(warnings)} warning(s))")
        return 1
    print(f"RESULT: PASS ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())

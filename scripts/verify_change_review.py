#!/usr/bin/env python3
"""Validate the machine-owned complexity/dependency review structure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

POLICY = Path(".engineering/change-review-policy.json")
REQUIRED_QUESTIONS = {"problem", "boundary", "surface", "simpler", "sunset"}


def validate_change_review(root: Path) -> list[str]:
    errors: list[str] = []
    path = root / POLICY
    if not path.is_file():
        return [f"missing change review policy: {POLICY}"]
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid change review policy: {exc}"]
    if not isinstance(policy, dict):
        return ["change review policy root must be an object"]
    if policy.get("schema_version") != 1:
        errors.append("change review policy schema_version must be 1")

    scopes = policy.get("meaningful_scopes")
    if not isinstance(scopes, list) or not scopes or not all(isinstance(item, str) and item.strip() for item in scopes):
        errors.append("meaningful_scopes must be a non-empty string list")
    elif len(scopes) != len(set(scopes)):
        errors.append("meaningful_scopes must be unique")

    questions = policy.get("questions")
    markers: list[str] = []
    ids: list[str] = []
    if not isinstance(questions, list):
        errors.append("questions must be a list")
    else:
        for index, item in enumerate(questions):
            if not isinstance(item, dict):
                errors.append(f"questions[{index}] must be an object")
                continue
            question_id = item.get("id")
            marker = item.get("marker")
            text = item.get("text")
            if not isinstance(question_id, str) or not question_id:
                errors.append(f"questions[{index}] id is required")
            else:
                ids.append(question_id)
            if not isinstance(marker, str) or not marker:
                errors.append(f"questions[{index}] marker is required")
            else:
                markers.append(marker)
            if not isinstance(text, str) or not text.strip():
                errors.append(f"questions[{index}] text is required")
        if set(ids) != REQUIRED_QUESTIONS:
            errors.append(f"question ids must be exactly {sorted(REQUIRED_QUESTIONS)}")
        if len(ids) != len(set(ids)):
            errors.append("question ids must be unique")
        if len(markers) != len(set(markers)):
            errors.append("question markers must be unique")

    template_rel = policy.get("template_path")
    if not isinstance(template_rel, str) or not template_rel:
        errors.append("template_path is required")
    else:
        template = root / template_rel
        if not template.is_file():
            errors.append(f"change review template does not exist: {template_rel}")
        else:
            content = template.read_text(encoding="utf-8")
            for marker in markers:
                token = f"<!-- {marker} -->"
                count = content.count(token)
                if count != 1:
                    errors.append(f"template must contain marker exactly once: {token} (found {count})")

    rule = policy.get("rule")
    if not isinstance(rule, str) or not rule.strip():
        errors.append("change review policy rule is required")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors = validate_change_review(root)
    print("Complexity/dependency review contract")
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

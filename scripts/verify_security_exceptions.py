#!/usr/bin/env python3
"""Fail closed when dependency vulnerability exceptions are malformed or expired."""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / ".engineering" / "security-exceptions.json"


def validate(payload: object, *, today: date | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["root must be an object"]
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    raw = payload.get("exceptions")
    if not isinstance(raw, list):
        return errors + ["exceptions must be an array"]

    current = today or date.today()
    seen: set[str] = set()
    for index, item in enumerate(raw):
        prefix = f"exceptions[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        vuln_id = item.get("id")
        if not isinstance(vuln_id, str) or not vuln_id.strip():
            errors.append(f"{prefix}.id must be non-empty")
        elif vuln_id in seen:
            errors.append(f"duplicate exception id: {vuln_id}")
        else:
            seen.add(vuln_id)
        for key in (
            "package",
            "affected_version",
            "owner",
            "reason",
            "reachability",
            "remediation",
        ):
            if not isinstance(item.get(key), str) or not str(item.get(key)).strip():
                errors.append(f"{prefix}.{key} must be non-empty")
        controls = item.get("compensating_controls")
        if not isinstance(controls, list) or not controls or not all(
            isinstance(value, str) and value.strip() for value in controls
        ):
            errors.append(f"{prefix}.compensating_controls must be a non-empty string array")
        aliases = item.get("aliases")
        if not isinstance(aliases, list) or not all(isinstance(value, str) and value for value in aliases):
            errors.append(f"{prefix}.aliases must be a string array")
        for key in ("review_by", "expires_on"):
            value = item.get(key)
            try:
                parsed = date.fromisoformat(str(value))
            except ValueError:
                errors.append(f"{prefix}.{key} must be YYYY-MM-DD")
                continue
            if key == "expires_on" and parsed < current:
                errors.append(f"{prefix} expired on {parsed.isoformat()}")
        try:
            review = date.fromisoformat(str(item.get("review_by")))
            expires = date.fromisoformat(str(item.get("expires_on")))
            if review > expires:
                errors.append(f"{prefix}.review_by must not be after expires_on")
        except ValueError:
            pass
    return errors


def main() -> int:
    try:
        payload = json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Security exception check: FAIL: {exc}")
        return 1
    errors = validate(payload)
    print("Security exception contract")
    print(f"path: {PATH}")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

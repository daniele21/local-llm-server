#!/usr/bin/env python3
"""Validate that the fresh-installed-wheel recovery journey remains wired."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / ".engineering" / "built-surface-e2e.json"


def validate(payload: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["root must be an object"]
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if payload.get("surface") != "fresh-installed-wheel":
        errors.append("surface must be fresh-installed-wheel")

    paths: dict[str, Path] = {}
    for key in ("workflow", "smoke_runner", "journey_runner"):
        raw = payload.get(key)
        if not isinstance(raw, str) or not raw:
            errors.append(f"{key} must be non-empty")
            continue
        path = (ROOT / raw).resolve()
        if ROOT not in path.parents or not path.is_file():
            errors.append(f"{key} does not exist in repository: {raw}")
        else:
            paths[key] = path

    marker = payload.get("workflow_marker")
    if isinstance(marker, str) and marker and "workflow" in paths:
        if marker not in paths["workflow"].read_text(encoding="utf-8"):
            errors.append("package-smoke workflow no longer owns the installed-surface smoke step")
    else:
        errors.append("workflow_marker must be non-empty")

    if "smoke_runner" in paths and "journey_runner" in paths:
        smoke_text = paths["smoke_runner"].read_text(encoding="utf-8")
        journey_name = paths["journey_runner"].name
        if journey_name not in smoke_text:
            errors.append("fresh-install smoke no longer invokes installed-surface journey")

    journey = payload.get("journey")
    if not isinstance(journey, dict):
        errors.append("journey must be an object")
    else:
        expected = {
            "healthy_before": True,
            "injected_failure": "model_not_resident",
            "expected_failure_status": 404,
            "retry": "valid_resident_model",
            "expected_retry_status": 200,
            "healthy_after": True,
            "synthetic_engine": True,
            "model_download": False,
        }
        for key, value in expected.items():
            if journey.get(key) != value:
                errors.append(f"journey.{key} must remain {value!r}")

    privacy = payload.get("privacy")
    if not isinstance(privacy, dict) or privacy.get("retain_prompt_or_output") is not False or privacy.get("retain_private_paths") is not False:
        errors.append("built-surface E2E privacy policy must prohibit prompt/output/private-path retention")
    non_claims = payload.get("non_claims")
    if not isinstance(non_claims, list) or len(non_claims) < 3:
        errors.append("non_claims must contain at least three entries")
    return errors


def main() -> int:
    try:
        payload = json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Built-surface E2E contract: FAIL: {exc}")
        return 1
    errors = validate(payload)
    print("Built/installed surface E2E contract")
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

#!/usr/bin/env python3
"""Zero-dependency validation for the E2E environment fidelity contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FIDELITY_ORDER = ["host_or_fake", "simulated_or_emulated", "representative_virtual", "representative_physical", "target_environment"]
FIDELITY_RANK = {name: index for index, name in enumerate(FIDELITY_ORDER)}
FIDELITY_CLASSES = set(FIDELITY_ORDER)
APPLICABILITY = {"required", "recommended", "n/a"}
AUTOMATION = {"automated", "real_environment"}
REAL_CONFIRMATION = {"required", "conditional", "not_required"}
REQUIRED_UI_MEDIA = {"screenshots", "video"}
PLACEHOLDER_MARKERS = ("<REPLACE_WITH_", "<PROJECT_")
REQUIRED_PRINCIPLES = (
    "final_environment_should_confirm_not_discover",
    "execution_capability_separate_from_environment_fidelity",
    "lowest_sufficient_test_level",
    "critical_journeys_only",
    "built_artifact_when_material",
    "residual_fidelity_gaps_explicit",
    "ui_journey_screenshot_and_video_artifacts_required",
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--template-mode", action="store_true")
    return parser.parse_args()


def non_empty(value):
    return isinstance(value, str) and bool(value.strip())


def string_list(value):
    return isinstance(value, list) and all(non_empty(item) for item in value)


def contains_placeholder(value):
    if isinstance(value, str):
        return any(marker in value for marker in PLACEHOLDER_MARKERS)
    if isinstance(value, list):
        return any(contains_placeholder(item) for item in value)
    if isinstance(value, dict):
        return any(contains_placeholder(item) for item in value.values())
    return False


def load(path, label, errors):
    if not path.is_file():
        errors.append(f"missing required file: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid {label}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} must contain an object")
        return {}
    return value


def index(items, label, errors):
    if not isinstance(items, list):
        errors.append(f"{label} must be a list")
        return {}
    result = {}
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{label}[{i}] must be an object")
            continue
        item_id = item.get("id")
        if not non_empty(item_id):
            errors.append(f"{label}[{i}].id is required")
        elif item_id in result:
            errors.append(f"duplicate {label} id: {item_id}")
        else:
            result[item_id] = item
    return result


def validate_refs(value, known, label, errors, allow_empty=False):
    if not string_list(value):
        errors.append(f"{label} must be a list of non-empty ids")
        return []
    if not value and not allow_empty:
        errors.append(f"{label} must not be empty")
    for ref in value:
        if ref not in known and not contains_placeholder(ref):
            errors.append(f"{label} references unknown id: {ref}")
    return list(value)


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    errors, warnings = [], []
    data = load(root / ".engineering/e2e.json", ".engineering/e2e.json", errors)
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("contract_version") != "0.1.1":
        errors.append("contract_version must be 0.1.1")

    applicability = data.get("applicability") if isinstance(data.get("applicability"), dict) else {}
    status = applicability.get("status")
    if status not in APPLICABILITY:
        errors.append(f"applicability.status must be one of {sorted(APPLICABILITY)}")
    if not non_empty(applicability.get("reason")):
        errors.append("applicability.reason is required")

    commands = load(root / ".engineering/commands.json", ".engineering/commands.json", errors)
    command_map = commands.get("commands") if isinstance(commands.get("commands"), dict) else {}
    command_entry = command_map.get("e2e") if isinstance(command_map, dict) else None
    command_status = command_entry.get("status") if isinstance(command_entry, dict) else None
    if not isinstance(command_entry, dict):
        errors.append("commands.json must declare commands.e2e")
    if status == "n/a" and command_status != "n/a":
        errors.append("E2E applicability n/a requires commands.e2e.status = n/a")
    elif status in {"required", "recommended"} and command_status == "n/a":
        errors.append("E2E-applicable repositories may not set commands.e2e.status = n/a")
    elif status == "required" and command_status not in {None, "required"}:
        errors.append("E2E applicability required requires commands.e2e.status = required")

    principles = data.get("principles") if isinstance(data.get("principles"), dict) else {}
    for key in REQUIRED_PRINCIPLES:
        if principles.get(key) is not True:
            errors.append(f"principles.{key} must be true")
    if data.get("fidelity_order") != FIDELITY_ORDER:
        errors.append("fidelity_order must match the canonical ordered fidelity classes")

    targets = index(data.get("target_environments"), "target_environments", errors)
    environments = index(data.get("execution_environments"), "execution_environments", errors)
    journeys = index(data.get("critical_journeys"), "critical_journeys", errors)
    if status in {"required", "recommended"} and (not targets or not environments or not journeys):
        errors.append("E2E-applicable repositories require target environments, execution environments and critical journeys")
    if status == "n/a" and (targets or environments or journeys):
        errors.append("E2E marked n/a must not declare target/execution environments or critical journeys")

    for target_id, target in targets.items():
        if not non_empty(target.get("platform")):
            errors.append(f"target_environments.{target_id}.platform is required")
        if not non_empty(target.get("description")):
            errors.append(f"target_environments.{target_id}.description is required")
        if not string_list(target.get("material_dimensions")) or not target.get("material_dimensions"):
            errors.append(f"target_environments.{target_id}.material_dimensions must be a non-empty string list")

    automated_ids = set()
    for env_id, env in environments.items():
        fidelity, automation = env.get("fidelity_class"), env.get("automation")
        if fidelity not in FIDELITY_CLASSES:
            errors.append(f"execution_environments.{env_id}.fidelity_class must be one of {FIDELITY_ORDER}")
        if automation not in AUTOMATION:
            errors.append(f"execution_environments.{env_id}.automation must be one of {sorted(AUTOMATION)}")
        elif automation == "automated":
            automated_ids.add(env_id)
        if not non_empty(env.get("platform")) or not non_empty(env.get("artifact_surface")):
            errors.append(f"execution_environments.{env_id} requires platform and artifact_surface")
        validate_refs(env.get("target_environment_refs"), set(targets), f"execution_environments.{env_id}.target_environment_refs", errors)
        if not string_list(env.get("known_gaps")):
            errors.append(f"execution_environments.{env_id}.known_gaps must be a string list")

    for journey_id, journey in journeys.items():
        if not non_empty(journey.get("claim")):
            errors.append(f"critical_journeys.{journey_id}.claim is required")
        ui_surface = journey.get("ui_surface")
        if not isinstance(ui_surface, bool):
            errors.append(f"critical_journeys.{journey_id}.ui_surface must be boolean")
        media = journey.get("required_media_artifacts")
        if not string_list(media):
            errors.append(f"critical_journeys.{journey_id}.required_media_artifacts must be a string list")
        elif ui_surface is True and set(media) != REQUIRED_UI_MEDIA:
            errors.append(f"critical_journeys.{journey_id}.required_media_artifacts must contain screenshots and video for UI journeys")
        elif ui_surface is False and media:
            errors.append(f"critical_journeys.{journey_id}.required_media_artifacts must be empty when ui_surface is false")
        validate_refs(journey.get("target_environment_refs"), set(targets), f"critical_journeys.{journey_id}.target_environment_refs", errors)
        auto_refs = validate_refs(journey.get("automated_environment_refs"), set(environments), f"critical_journeys.{journey_id}.automated_environment_refs", errors, allow_empty=True)
        ranks = []
        for ref in auto_refs:
            env = environments.get(ref)
            if env and env.get("automation") != "automated":
                errors.append(f"critical_journeys.{journey_id}.automated_environment_refs must reference automated environments: {ref}")
            if env and env.get("automation") == "automated" and env.get("fidelity_class") in FIDELITY_RANK:
                ranks.append(FIDELITY_RANK[env["fidelity_class"]])
        minimum = journey.get("minimum_automated_fidelity")
        if minimum not in FIDELITY_CLASSES:
            errors.append(f"critical_journeys.{journey_id}.minimum_automated_fidelity must be one of {FIDELITY_ORDER}")
        elif auto_refs and ranks and max(ranks) < FIDELITY_RANK[minimum]:
            errors.append(f"critical_journeys.{journey_id} does not reach minimum_automated_fidelity {minimum}")
        confirmation = journey.get("real_environment_confirmation")
        if confirmation not in REAL_CONFIRMATION:
            errors.append(f"critical_journeys.{journey_id}.real_environment_confirmation must be one of {sorted(REAL_CONFIRMATION)}")
        residual = journey.get("residual_gaps")
        if not string_list(residual):
            errors.append(f"critical_journeys.{journey_id}.residual_gaps must be a string list")
        if not auto_refs and not non_empty(journey.get("automation_gap_reason")):
            errors.append(f"critical_journeys.{journey_id} needs automated_environment_refs or an explicit automation_gap_reason")
        if auto_refs and not any(ref in automated_ids for ref in auto_refs):
            errors.append(f"critical_journeys.{journey_id} has no valid automated execution environment")
        if confirmation == "not_required" and residual:
            warnings.append(f"critical_journeys.{journey_id} declares residual gaps but real_environment_confirmation is not_required")

    if not args.template_mode and contains_placeholder(data):
        errors.append("unresolved adopter placeholder in .engineering/e2e.json")
    print("E2E environment fidelity contract check")
    print(f"root: {root}")
    print(f"applicability: {status}")
    print(f"commands.e2e.status: {command_status}")
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
    raise SystemExit(main())

#!/usr/bin/env python3
"""Zero-dependency validation for the E2E environment fidelity contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

FIDELITY_ORDER = [
    "host_or_fake",
    "simulated_or_emulated",
    "representative_virtual",
    "representative_physical",
    "target_environment",
]
FIDELITY_CLASSES = set(FIDELITY_ORDER)
FIDELITY_RANK = {name: index for index, name in enumerate(FIDELITY_ORDER)}
APPLICABILITY = {"required", "recommended", "n/a"}
AUTOMATION = {"automated", "real_environment"}
REAL_CONFIRMATION = {"required", "conditional", "not_required"}
PLACEHOLDER_MARKERS = ("<REPLACE_WITH_", "<PROJECT_")
REQUIRED_PRINCIPLES = (
    "final_environment_should_confirm_not_discover",
    "execution_capability_separate_from_environment_fidelity",
    "lowest_sufficient_test_level",
    "critical_journeys_only",
    "built_artifact_when_material",
    "residual_fidelity_gaps_explicit",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--template-mode", action="store_true")
    return parser.parse_args()


def non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def list_of_strings(value: object) -> bool:
    return isinstance(value, list) and all(non_empty_string(item) for item in value)


def contains_placeholder(value: object) -> bool:
    if isinstance(value, str):
        return any(marker in value for marker in PLACEHOLDER_MARKERS)
    if isinstance(value, list):
        return any(contains_placeholder(item) for item in value)
    if isinstance(value, dict):
        return any(contains_placeholder(item) for item in value.values())
    return False


def unique_ids(items: list[object], label: str, errors: list[str]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{label}[{index}] must be an object")
            continue
        item_id = item.get("id")
        if not non_empty_string(item_id):
            errors.append(f"{label}[{index}].id is required")
            continue
        if item_id in result:
            errors.append(f"duplicate {label} id: {item_id}")
            continue
        result[item_id] = item
    return result


def validate_refs(
    refs: object,
    known: set[str],
    label: str,
    errors: list[str],
    *,
    allow_empty: bool = False,
) -> list[str]:
    if not isinstance(refs, list) or not all(non_empty_string(ref) for ref in refs):
        errors.append(f"{label} must be a list of non-empty ids")
        return []
    if not refs and not allow_empty:
        errors.append(f"{label} must not be empty")
    for ref in refs:
        if ref not in known and not contains_placeholder(ref):
            errors.append(f"{label} references unknown id: {ref}")
    return refs


def read_json(path: Path, label: str, errors: list[str]) -> dict:
    if not path.is_file():
        errors.append(f"missing required file: {path.name if path.parent.name == '.engineering' else path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        errors.append(f"invalid {label}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} must contain a JSON object")
        return {}
    return value


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    path = root / ".engineering" / "e2e.json"
    errors: list[str] = []
    warnings: list[str] = []

    if not path.is_file():
        print("E2E environment fidelity contract check")
        print("FAIL: missing required file: .engineering/e2e.json")
        return 1

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print("E2E environment fidelity contract check")
        print(f"FAIL: invalid .engineering/e2e.json: {exc}")
        return 1

    if not isinstance(data, dict):
        print("E2E environment fidelity contract check")
        print("FAIL: .engineering/e2e.json must contain a JSON object")
        return 1

    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("contract_version") != "0.1.0":
        errors.append("contract_version must be 0.1.0")

    applicability = data.get("applicability")
    if not isinstance(applicability, dict):
        errors.append("applicability must be an object")
        applicability = {}
    status = applicability.get("status")
    if status not in APPLICABILITY:
        errors.append(f"applicability.status must be one of {sorted(APPLICABILITY)}")
    if not non_empty_string(applicability.get("reason")):
        errors.append("applicability.reason is required")

    commands_path = root / ".engineering" / "commands.json"
    commands_data = read_json(commands_path, ".engineering/commands.json", errors)
    commands_section = commands_data.get("commands") if commands_data else None
    if commands_data and not isinstance(commands_section, dict):
        errors.append("commands.json commands must be an object")
        command_entry = None
    else:
        command_entry = commands_section.get("e2e") if isinstance(commands_section, dict) else None
    command_status = command_entry.get("status") if isinstance(command_entry, dict) else None
    if commands_data and isinstance(commands_section, dict) and not isinstance(command_entry, dict):
        errors.append("commands.json must declare commands.e2e")
    elif status == "n/a" and command_status != "n/a":
        errors.append("E2E applicability n/a requires commands.e2e.status = n/a")
    elif status in {"required", "recommended"} and command_status == "n/a":
        errors.append("E2E-applicable repositories may not set commands.e2e.status = n/a")
    elif status == "required" and command_status not in {None, "required"}:
        errors.append("E2E applicability required requires commands.e2e.status = required")

    principles = data.get("principles")
    if not isinstance(principles, dict):
        errors.append("principles must be an object")
        principles = {}
    for key in REQUIRED_PRINCIPLES:
        if principles.get(key) is not True:
            errors.append(f"principles.{key} must be true")

    if data.get("fidelity_order") != FIDELITY_ORDER:
        errors.append("fidelity_order must match the canonical ordered fidelity classes")

    targets_raw = data.get("target_environments")
    executions_raw = data.get("execution_environments")
    journeys_raw = data.get("critical_journeys")
    if not isinstance(targets_raw, list):
        errors.append("target_environments must be a list")
        targets_raw = []
    if not isinstance(executions_raw, list):
        errors.append("execution_environments must be a list")
        executions_raw = []
    if not isinstance(journeys_raw, list):
        errors.append("critical_journeys must be a list")
        journeys_raw = []

    targets = unique_ids(targets_raw, "target_environments", errors)
    executions = unique_ids(executions_raw, "execution_environments", errors)
    journeys = unique_ids(journeys_raw, "critical_journeys", errors)

    if status == "n/a":
        if targets_raw or executions_raw or journeys_raw:
            errors.append("E2E marked n/a must not declare target/execution environments or critical journeys")
    elif status in {"required", "recommended"}:
        if not targets_raw:
            errors.append("E2E-applicable repositories must declare at least one target environment")
        if not executions_raw:
            errors.append("E2E-applicable repositories must declare at least one execution environment")
        if not journeys_raw:
            errors.append("E2E-applicable repositories must declare at least one critical journey")

    for target_id, target in targets.items():
        if not non_empty_string(target.get("platform")):
            errors.append(f"target_environments.{target_id}.platform is required")
        if not non_empty_string(target.get("description")):
            errors.append(f"target_environments.{target_id}.description is required")
        dimensions = target.get("material_dimensions")
        if not list_of_strings(dimensions) or not dimensions:
            errors.append(f"target_environments.{target_id}.material_dimensions must be a non-empty string list")

    automated_ids: set[str] = set()
    for environment_id, environment in executions.items():
        fidelity = environment.get("fidelity_class")
        if fidelity not in FIDELITY_CLASSES:
            errors.append(
                f"execution_environments.{environment_id}.fidelity_class must be one of {FIDELITY_ORDER}"
            )
        automation = environment.get("automation")
        if automation not in AUTOMATION:
            errors.append(
                f"execution_environments.{environment_id}.automation must be one of {sorted(AUTOMATION)}"
            )
        elif automation == "automated":
            automated_ids.add(environment_id)
        if not non_empty_string(environment.get("platform")):
            errors.append(f"execution_environments.{environment_id}.platform is required")
        if not non_empty_string(environment.get("artifact_surface")):
            errors.append(f"execution_environments.{environment_id}.artifact_surface is required")
        validate_refs(
            environment.get("target_environment_refs"),
            set(targets),
            f"execution_environments.{environment_id}.target_environment_refs",
            errors,
        )
        gaps = environment.get("known_gaps")
        if not isinstance(gaps, list) or not all(non_empty_string(gap) for gap in gaps):
            errors.append(f"execution_environments.{environment_id}.known_gaps must be a string list")

    for journey_id, journey in journeys.items():
        if not non_empty_string(journey.get("claim")):
            errors.append(f"critical_journeys.{journey_id}.claim is required")
        validate_refs(
            journey.get("target_environment_refs"),
            set(targets),
            f"critical_journeys.{journey_id}.target_environment_refs",
            errors,
        )
        automated_refs = validate_refs(
            journey.get("automated_environment_refs"),
            set(executions),
            f"critical_journeys.{journey_id}.automated_environment_refs",
            errors,
            allow_empty=True,
        )
        automated_fidelity_ranks: list[int] = []
        for ref in automated_refs:
            environment = executions.get(ref)
            if environment and environment.get("automation") != "automated":
                errors.append(
                    f"critical_journeys.{journey_id}.automated_environment_refs must reference automated environments: {ref}"
                )
            if environment and environment.get("automation") == "automated":
                fidelity = environment.get("fidelity_class")
                if fidelity in FIDELITY_RANK:
                    automated_fidelity_ranks.append(FIDELITY_RANK[fidelity])
        minimum = journey.get("minimum_automated_fidelity")
        if minimum not in FIDELITY_CLASSES:
            errors.append(
                f"critical_journeys.{journey_id}.minimum_automated_fidelity must be one of {FIDELITY_ORDER}"
            )
        elif automated_refs and automated_fidelity_ranks:
            if max(automated_fidelity_ranks) < FIDELITY_RANK[minimum]:
                errors.append(
                    f"critical_journeys.{journey_id} does not reach minimum_automated_fidelity {minimum}"
                )
        confirmation = journey.get("real_environment_confirmation")
        if confirmation not in REAL_CONFIRMATION:
            errors.append(
                f"critical_journeys.{journey_id}.real_environment_confirmation must be one of {sorted(REAL_CONFIRMATION)}"
            )
        residual = journey.get("residual_gaps")
        if not isinstance(residual, list) or not all(non_empty_string(gap) for gap in residual):
            errors.append(f"critical_journeys.{journey_id}.residual_gaps must be a string list")
        gap_reason = journey.get("automation_gap_reason")
        if not automated_refs and not non_empty_string(gap_reason):
            errors.append(
                f"critical_journeys.{journey_id} needs automated_environment_refs or an explicit automation_gap_reason"
            )
        if automated_refs and not any(ref in automated_ids for ref in automated_refs):
            errors.append(f"critical_journeys.{journey_id} has no valid automated execution environment")
        if confirmation == "not_required" and residual:
            warnings.append(
                f"critical_journeys.{journey_id} declares residual gaps but real_environment_confirmation is not_required"
            )

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
    sys.exit(main())

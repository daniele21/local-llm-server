#!/usr/bin/env python3
"""Zero-dependency validation for the project operating contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

COMMANDS = (
    "setup", "doctor", "dev", "check", "test", "e2e", "build", "smoke", "package", "stop", "clean",
)
REQUIRED_NON_NA = {"setup", "check", "test", "build", "clean"}
STATUSES = {"required", "recommended", "optional", "n/a"}
PLACEHOLDER_MARKERS = ("<REPLACE_WITH_", "<PROJECT_")
REQUIRED_CLEANUP_PATHS = {
    "success", "failure", "timeout", "cancellation", "interrupt", "partial-initialization",
}
REQUIRED_DELTA_DIMENSIONS = {
    "source", "dependencies", "toolchain", "configuration", "compatibility_migrations", "artifact_metrics", "validation",
}
REQUIRED_E2E_FLAGS = (
    "recommended_when_full_workflow_boundary_exists", "critical_journeys_prioritized",
    "lower_level_tests_remain_primary", "use_stack_native_tooling",
    "run_against_built_artifact_when_material", "failure_evidence_bounded", "zero_residue_required",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--template-mode", action="store_true")
    return parser.parse_args()


def expect_true(section: dict, key: str, errors: list[str], prefix: str) -> None:
    if section.get(key) is not True:
        errors.append(f"{prefix}.{key} must be true")


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    path = root / ".engineering" / "commands.json"
    errors: list[str] = []
    warnings: list[str] = []

    if not path.is_file():
        print("Project operating contract check\nFAIL: missing required file: .engineering/commands.json")
        return 1
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Project operating contract check\nFAIL: invalid .engineering/commands.json: {exc}")
        return 1

    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not data.get("contract_version"):
        errors.append("contract_version is required")

    commands = data.get("commands")
    if not isinstance(commands, dict):
        errors.append("commands must be an object")
        commands = {}
    for name in COMMANDS:
        entry = commands.get(name)
        if not isinstance(entry, dict):
            errors.append(f"missing command intent: {name}")
            continue
        status = entry.get("status")
        run = entry.get("run")
        if status not in STATUSES:
            errors.append(f"commands.{name}.status must be one of {sorted(STATUSES)}")
        if name in REQUIRED_NON_NA and status == "n/a":
            errors.append(f"commands.{name} may not be n/a")
        if status != "n/a" and (not isinstance(run, str) or not run.strip()):
            errors.append(f"commands.{name}.run is required when status is not n/a")
        if not args.template_mode and isinstance(run, str) and any(marker in run for marker in PLACEHOLDER_MARKERS):
            errors.append(f"unresolved command placeholder in commands.{name}.run")

    e2e = data.get("end_to_end") if isinstance(data.get("end_to_end"), dict) else {}
    if not e2e:
        errors.append("end_to_end must be an object")
    for key in REQUIRED_E2E_FLAGS:
        expect_true(e2e, key, errors, "end_to_end")

    identity = data.get("build_identity") if isinstance(data.get("build_identity"), dict) else {}
    if not identity:
        errors.append("build_identity must be an object")
    for key in ("unique_per_build", "source_revision_required", "dirty_state_required"):
        expect_true(identity, key, errors, "build_identity")
    for field in ("product", "product_version", "build_id", "source_revision"):
        if field not in set(identity.get("artifact_name_fields") or []):
            errors.append(f"build_identity.artifact_name_fields must include {field}")
    for field in ("project", "platform", "architecture", "channel", "variant"):
        if field not in set(identity.get("lineage_fields") or []):
            errors.append(f"build_identity.lineage_fields must include {field}")

    artifacts = data.get("artifact_lifecycle") if isinstance(data.get("artifact_lifecycle"), dict) else {}
    if not artifacts:
        errors.append("artifact_lifecycle must be an object")
    for key in ("immutable_successful_artifacts", "promote_only_after_success", "manifest_required", "release_artifacts_immutable"):
        expect_true(artifacts, key, errors, "artifact_lifecycle")
    if str(artifacts.get("checksum_algorithm", "")).lower() != "sha256":
        errors.append("artifact_lifecycle.checksum_algorithm must be sha256")
    keep = artifacts.get("local_keep_successful_per_lineage")
    if not isinstance(keep, int) or keep < 1:
        errors.append("artifact_lifecycle.local_keep_successful_per_lineage must be a positive integer")
    elif keep > 2:
        warnings.append("local artifact retention exceeds the default of 2 successful builds per lineage")
    retention = artifacts.get("ci_retention_days")
    if not isinstance(retention, int) or retention < 1:
        errors.append("artifact_lifecycle.ci_retention_days must be a positive integer")
    if not artifacts.get("ci_store"):
        errors.append("artifact_lifecycle.ci_store is required")
    if not artifacts.get("release_store"):
        errors.append("artifact_lifecycle.release_store is required")

    delta = data.get("build_delta") if isinstance(data.get("build_delta"), dict) else {}
    if not delta:
        errors.append("build_delta must be an object")
    expect_true(delta, "required", errors, "build_delta")
    expect_true(delta, "bundle_with_artifact", errors, "build_delta")
    if delta.get("compare_to") != "previous-successful-comparable-build":
        errors.append("build_delta.compare_to must be previous-successful-comparable-build")
    if not delta.get("output"):
        errors.append("build_delta.output is required")
    missing_dimensions = sorted(REQUIRED_DELTA_DIMENSIONS - set(delta.get("dimensions") or []))
    if missing_dimensions:
        errors.append("build_delta.dimensions missing: " + ", ".join(missing_dimensions))

    runtime = data.get("local_runtime") if isinstance(data.get("local_runtime"), dict) else {}
    if not runtime:
        errors.append("local_runtime must be an object")
    if runtime.get("applicable") is True:
        if runtime.get("bind_default") != "loopback":
            errors.append("local_runtime.bind_default must be loopback when local runtime is applicable")
        if runtime.get("port_strategy") != "configurable-with-collision-check":
            errors.append("local_runtime.port_strategy must be configurable-with-collision-check")
        for key in ("foreground_default", "readiness_required", "graceful_shutdown_required", "verify_no_project_listener_after_stop"):
            expect_true(runtime, key, errors, "local_runtime")

    ephemeral = data.get("ephemeral_resources") if isinstance(data.get("ephemeral_resources"), dict) else {}
    if not ephemeral:
        errors.append("ephemeral_resources must be an object")
    for key in ("run_identity", "isolated_workspace", "stale_resource_recovery", "ownership_required_before_cleanup", "post_cleanup_verification"):
        expect_true(ephemeral, key, errors, "ephemeral_resources")
    missing_cleanup = sorted(REQUIRED_CLEANUP_PATHS - set(ephemeral.get("cleanup_paths") or []))
    if missing_cleanup:
        errors.append("ephemeral_resources.cleanup_paths missing: " + ", ".join(missing_cleanup))

    print("Project operating contract check")
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

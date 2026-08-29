#!/usr/bin/env python3
"""Zero-dependency validation for the project operating contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

COMMANDS = (
    "setup",
    "doctor",
    "dev",
    "check",
    "test",
    "e2e",
    "build",
    "smoke",
    "package",
    "stop",
    "clean",
)

REQUIRED_NON_NA = {"setup", "check", "test", "build", "clean"}
STATUSES = {"required", "recommended", "optional", "n/a"}
PLACEHOLDER_MARKERS = ("<REPLACE_WITH_", "<PROJECT_")
REQUIRED_PUBLICATION_FLAGS = (
    "agent_preflight_required",
    "target_base_freshness_required",
    "full_diff_review_required",
    "material_ambiguity_must_be_resolved",
    "failure_root_cause_required",
    "execution_capability_classification_required",
    "blast_radius_profile_selection_required",
    "automatable_gates_must_not_be_delegated_to_user",
    "remote_automated_fallback_required_when_agent_local_unavailable",
    "deterministic_ci_command_parity_required",
    "non_automated_evidence_must_be_declared",
    "exact_head_evidence_required",
)
REQUIRED_EXECUTION_CLASSES = {"agent_local", "remote_automated", "real_environment"}
REQUIRED_VALIDATION_PROFILES = {"lean", "scoped", "strong", "full"}
REQUIRED_CLEANUP_PATHS = {
    "success",
    "failure",
    "timeout",
    "cancellation",
    "interrupt",
    "partial-initialization",
}
REQUIRED_DELTA_DIMENSIONS = {
    "source",
    "dependencies",
    "toolchain",
    "configuration",
    "compatibility_migrations",
    "artifact_metrics",
    "validation",
}
REQUIRED_E2E_FLAGS = (
    "recommended_when_full_workflow_boundary_exists",
    "critical_journeys_prioritized",
    "lower_level_tests_remain_primary",
    "use_stack_native_tooling",
    "run_against_built_artifact_when_material",
    "failure_evidence_bounded",
    "zero_residue_required",
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
        print("Project operating contract check")
        print("FAIL: missing required file: .engineering/commands.json")
        return 1

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print("Project operating contract check")
        print(f"FAIL: invalid .engineering/commands.json: {exc}")
        return 1

    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("contract_version") != "0.5.0":
        errors.append("contract_version must be 0.5.0")

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
        if not args.template_mode and isinstance(run, str):
            for marker in PLACEHOLDER_MARKERS:
                if marker in run:
                    errors.append(f"unresolved command placeholder in commands.{name}.run")

    publication = data.get("publication_gate")
    if not isinstance(publication, dict):
        errors.append("publication_gate must be an object")
        publication = {}
    for key in REQUIRED_PUBLICATION_FLAGS:
        expect_true(publication, key, errors, "publication_gate")

    execution = data.get("validation_execution")
    if not isinstance(execution, dict):
        errors.append("validation_execution must be an object")
        execution = {}
    classes = set(execution.get("classes") or [])
    missing_classes = sorted(REQUIRED_EXECUTION_CLASSES - classes)
    if missing_classes:
        errors.append("validation_execution.classes missing: " + ", ".join(missing_classes))
    expect_true(execution, "no_human_runner_for_automatable_gates", errors, "validation_execution")
    expect_true(execution, "remote_automation_required_when_agent_local_unavailable", errors, "validation_execution")

    profiles = data.get("validation_profiles")
    if not isinstance(profiles, dict):
        errors.append("validation_profiles must be an object")
        profiles = {}
    if profiles.get("default") != "auto":
        errors.append("validation_profiles.default must be auto")
    configured_profiles = set(profiles.get("profiles") or [])
    missing_profiles = sorted(REQUIRED_VALIDATION_PROFILES - configured_profiles)
    if missing_profiles:
        errors.append("validation_profiles.profiles missing: " + ", ".join(missing_profiles))
    selector = profiles.get("selector")
    if not isinstance(selector, str) or not selector.strip():
        errors.append("validation_profiles.selector is required")
    elif not args.template_mode and any(marker in selector for marker in PLACEHOLDER_MARKERS):
        errors.append("unresolved validation_profiles.selector placeholder")
    for key in (
        "unknown_executable_paths_fail_safe",
        "selector_changes_force_full",
        "promotion_validation_full",
        "automatic_escalation_allowed",
        "silent_downgrade_below_auto_forbidden",
        "report_selected_profile_and_reason",
    ):
        expect_true(profiles, key, errors, "validation_profiles")

    remote = data.get("remote_preflight")
    if not isinstance(remote, dict):
        errors.append("remote_preflight must be an object")
        remote = {}
    remote_status = remote.get("status")
    if remote_status not in {"required", "recommended", "n/a"}:
        errors.append("remote_preflight.status must be required, recommended or n/a")
    if remote_status != "n/a":
        trigger = remote.get("trigger")
        if not isinstance(trigger, str) or not trigger.strip():
            errors.append("remote_preflight.trigger is required when remote preflight is enabled")
        elif not args.template_mode and any(marker in trigger for marker in PLACEHOLDER_MARKERS):
            errors.append("unresolved remote_preflight.trigger placeholder")
        if remote.get("default_profile") != "auto":
            errors.append("remote_preflight.default_profile must be auto")
        for key in (
            "stronger_profile_override_allowed",
            "weaker_profile_override_requires_explicit_justification",
            "exact_head_required",
            "trusted_requesters_only",
            "same_repository_prs_only_by_default",
            "report_result_to_pr",
        ):
            expect_true(remote, key, errors, "remote_preflight")
        if remote.get("execution_job_write_credentials") is not False:
            errors.append("remote_preflight.execution_job_write_credentials must be false")

    e2e = data.get("end_to_end")
    if not isinstance(e2e, dict):
        errors.append("end_to_end must be an object")
        e2e = {}
    for key in REQUIRED_E2E_FLAGS:
        expect_true(e2e, key, errors, "end_to_end")

    identity = data.get("build_identity")
    if not isinstance(identity, dict):
        errors.append("build_identity must be an object")
        identity = {}
    for key in ("unique_per_build", "source_revision_required", "dirty_state_required"):
        expect_true(identity, key, errors, "build_identity")
    name_fields = set(identity.get("artifact_name_fields") or [])
    for field in ("product", "product_version", "build_id", "source_revision"):
        if field not in name_fields:
            errors.append(f"build_identity.artifact_name_fields must include {field}")
    lineage = set(identity.get("lineage_fields") or [])
    for field in ("project", "platform", "architecture", "channel", "variant"):
        if field not in lineage:
            errors.append(f"build_identity.lineage_fields must include {field}")

    artifacts = data.get("artifact_lifecycle")
    if not isinstance(artifacts, dict):
        errors.append("artifact_lifecycle must be an object")
        artifacts = {}
    for key in (
        "immutable_successful_artifacts",
        "promote_only_after_success",
        "manifest_required",
        "release_artifacts_immutable",
    ):
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

    delta = data.get("build_delta")
    if not isinstance(delta, dict):
        errors.append("build_delta must be an object")
        delta = {}
    expect_true(delta, "required", errors, "build_delta")
    expect_true(delta, "bundle_with_artifact", errors, "build_delta")
    if delta.get("compare_to") != "previous-successful-comparable-build":
        errors.append("build_delta.compare_to must be previous-successful-comparable-build")
    if not delta.get("output"):
        errors.append("build_delta.output is required")
    dimensions = set(delta.get("dimensions") or [])
    missing_dimensions = sorted(REQUIRED_DELTA_DIMENSIONS - dimensions)
    if missing_dimensions:
        errors.append("build_delta.dimensions missing: " + ", ".join(missing_dimensions))

    runtime = data.get("local_runtime")
    if not isinstance(runtime, dict):
        errors.append("local_runtime must be an object")
        runtime = {}
    if runtime.get("applicable") is True:
        if runtime.get("bind_default") != "loopback":
            errors.append("local_runtime.bind_default must be loopback when local runtime is applicable")
        if runtime.get("port_strategy") != "configurable-with-collision-check":
            errors.append("local_runtime.port_strategy must be configurable-with-collision-check")
        for key in (
            "foreground_default",
            "readiness_required",
            "graceful_shutdown_required",
            "verify_no_project_listener_after_stop",
        ):
            expect_true(runtime, key, errors, "local_runtime")

    ephemeral = data.get("ephemeral_resources")
    if not isinstance(ephemeral, dict):
        errors.append("ephemeral_resources must be an object")
        ephemeral = {}
    for key in (
        "run_identity",
        "isolated_workspace",
        "stale_resource_recovery",
        "ownership_required_before_cleanup",
        "post_cleanup_verification",
    ):
        expect_true(ephemeral, key, errors, "ephemeral_resources")
    cleanup_paths = set(ephemeral.get("cleanup_paths") or [])
    missing_cleanup = sorted(REQUIRED_CLEANUP_PATHS - cleanup_paths)
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

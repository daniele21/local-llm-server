#!/usr/bin/env python3
"""Validate the repo-template-sw 0.9.x operating contract."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

COMMANDS=("setup","doctor","dev","check","test","e2e","build","smoke","package","stop","clean")
STATUSES={"required","recommended","optional","n/a"}
PROFILES={"lean","scoped","strong","full"}
STAGES=["iteration","integration","release"]
EVIDENCE_FIELDS={"head","source_tree","target_base","required_gates","profile","e2e_environment"}

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--root",default="."); p.add_argument("--template-mode",action="store_true"); a=p.parse_args()
    path=Path(a.root)/".engineering/commands.json"; errors=[]
    try: data=json.loads(path.read_text())
    except Exception as exc: print(f"FAIL: invalid commands.json: {exc}"); return 1
    if data.get("schema_version")!=1: errors.append("schema_version must be 1")
    if data.get("contract_version")!="0.6.0": errors.append("contract_version must be 0.6.0")
    commands=data.get("commands",{})
    for name in COMMANDS:
        entry=commands.get(name)
        if not isinstance(entry,dict): errors.append(f"missing command intent: {name}"); continue
        if entry.get("status") not in STATUSES: errors.append(f"commands.{name}.status invalid")
        if entry.get("status")!="n/a" and not str(entry.get("run","")).strip(): errors.append(f"commands.{name}.run required")
    velocity=data.get("development_velocity",{})
    if velocity.get("stages")!=STAGES: errors.append("development_velocity.stages must be iteration,integration,release")
    if velocity.get("default_stage")!="iteration": errors.append("default development stage must be iteration")
    for key in ("parallel_development_prefers_early_convergence","stacked_publication_exception_only"):
        if velocity.get(key) is not True: errors.append(f"development_velocity.{key} must be true")
    if velocity.get("integration",{}).get("exact_head_required") is not True: errors.append("integration exact head required")
    if velocity.get("release",{}).get("full_validation_required") is not True: errors.append("release full validation required")
    pub=data.get("publication_gate",{})
    if pub.get("applies_from_stage")!="integration": errors.append("publication_gate.applies_from_stage must be integration")
    for key in ("agent_preflight_required","target_base_freshness_required","full_diff_review_required","failure_root_cause_required","execution_capability_classification_required","automatable_gates_must_not_be_delegated_to_user","exact_head_evidence_required"):
        if pub.get(key) is not True: errors.append(f"publication_gate.{key} must be true")
    profiles=data.get("validation_profiles",{})
    if profiles.get("default")!="auto" or not PROFILES.issubset(set(profiles.get("profiles",[]))): errors.append("validation profiles incomplete")
    if profiles.get("selector_output")!="risk_dimensions_and_required_gates": errors.append("selector must output risks and required gates")
    for key in ("profiles_are_shorthand","gate_selection_preferred_over_suite_selection","selector_changes_force_full","promotion_validation_full"):
        if profiles.get(key) is not True: errors.append(f"validation_profiles.{key} must be true")
    remote=data.get("remote_preflight",{})
    for key in ("exact_head_required","reuse_successful_equivalent_evidence","rerun_only_when_missing_stale_or_insufficient","post_merge_tree_equivalent_reuse_allowed","post_merge_tree_reuse_requires_same_target_base","direct_push_without_equivalent_evidence_must_validate","trusted_requesters_only","same_repository_prs_only_by_default","report_result_to_pr"):
        if remote.get(key) is not True: errors.append(f"remote_preflight.{key} must be true")
    if remote.get("execution_job_write_credentials") is not False: errors.append("remote execution write credentials must be false")
    if not EVIDENCE_FIELDS.issubset(set(remote.get("evidence_identity_fields",[]))): errors.append("remote evidence identity fields incomplete")
    e2e=data.get("end_to_end",{})
    if e2e.get("ui_evidence_modes") != ["assertions","screenshots","full_media"]: errors.append("UI evidence modes must be assertions/screenshots/full_media")
    if e2e.get("ui_evidence_selection")!="risk_based": errors.append("UI evidence selection must be risk_based")
    economics=data.get("validation_economics",{})
    if economics.get("status") not in {"recommended","required"} or economics.get("periodic_review") is not True: errors.append("validation economics must be enabled")
    runtime=data.get("local_runtime",{})
    if runtime.get("applicable") is True:
        for key in ("foreground_default","readiness_required","graceful_shutdown_required","verify_no_project_listener_after_stop"):
            if runtime.get(key) is not True: errors.append(f"local_runtime.{key} must be true")
    ephemeral=data.get("ephemeral_resources",{})
    for key in ("run_identity","isolated_workspace","stale_resource_recovery","ownership_required_before_cleanup","post_cleanup_verification"):
        if ephemeral.get(key) is not True: errors.append(f"ephemeral_resources.{key} must be true")
    print("Project operating contract check")
    for error in errors: print("FAIL:",error)
    print("RESULT:", "FAIL" if errors else "PASS")
    return 1 if errors else 0
if __name__=="__main__": sys.exit(main())

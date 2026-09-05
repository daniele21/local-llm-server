#!/usr/bin/env python3
"""Zero-dependency validation for the project operating contract."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
COMMANDS=("setup","doctor","dev","check","test","e2e","build","smoke","package","stop","clean")
REQUIRED_NON_NA={"setup","check","test","build","clean"}; STATUSES={"required","recommended","optional","n/a"}; PLACEHOLDER_MARKERS=("<REPLACE_WITH_","<PROJECT_")
REQUIRED_PUBLICATION_FLAGS=("agent_preflight_required","target_base_freshness_required","full_diff_review_required","material_ambiguity_must_be_resolved","failure_root_cause_required","execution_capability_classification_required","blast_radius_profile_selection_required","automatable_gates_must_not_be_delegated_to_user","remote_automated_fallback_required_when_agent_local_unavailable","deterministic_ci_command_parity_required","non_automated_evidence_must_be_declared","exact_head_evidence_required")
REQUIRED_EXECUTION_CLASSES={"agent_local","remote_automated","real_environment"}; REQUIRED_VALIDATION_PROFILES={"lean","scoped","strong","full"}; REQUIRED_DELIVERY_STAGES=["iteration","integration","release"]; REQUIRED_UI_EVIDENCE_MODES=["assertions","screenshots","full_media"]; REQUIRED_EVIDENCE_IDENTITY_FIELDS={"head","target_base","required_gates","profile","e2e_environment"}; REQUIRED_VALIDATION_ECONOMICS={"duration","flake_rate","unique_regression_signal","overlap"}; REQUIRED_CLEANUP_PATHS={"success","failure","timeout","cancellation","interrupt","partial-initialization"}; REQUIRED_DELTA_DIMENSIONS={"source","dependencies","toolchain","configuration","compatibility_migrations","artifact_metrics","validation"}; REQUIRED_E2E_FLAGS=("recommended_when_full_workflow_boundary_exists","critical_journeys_prioritized","lower_level_tests_remain_primary","use_stack_native_tooling","run_against_built_artifact_when_material","failure_evidence_bounded","zero_residue_required","incidental_ui_does_not_force_full_media","full_media_for_motion_timing_sequence_or_release_claims")
def parse_args():
 p=argparse.ArgumentParser();p.add_argument("--root",default=".");p.add_argument("--template-mode",action="store_true");return p.parse_args()
def t(s,k,e,p):
 if s.get(k) is not True:e.append(f"{p}.{k} must be true")
def f(s,k,e,p):
 if s.get(k) is not False:e.append(f"{p}.{k} must be false")
def pi(v):return isinstance(v,int) and not isinstance(v,bool) and v>0
def main():
 a=parse_args();root=Path(a.root).resolve();path=root/".engineering/commands.json";e=[];w=[]
 if not path.is_file():print("Project operating contract check\nFAIL: missing required file: .engineering/commands.json");return 1
 try:d=json.loads(path.read_text(encoding="utf-8"))
 except (json.JSONDecodeError,OSError) as x:print(f"Project operating contract check\nFAIL: invalid .engineering/commands.json: {x}");return 1
 if d.get("schema_version")!=1:e.append("schema_version must be 1")
 if d.get("contract_version")!="0.6.1":e.append("contract_version must be 0.6.1")
 c=d.get("commands")
 if not isinstance(c,dict):e.append("commands must be an object");c={}
 for n in COMMANDS:
  x=c.get(n)
  if not isinstance(x,dict):e.append(f"missing command intent: {n}");continue
  s=x.get("status");run=x.get("run")
  if s not in STATUSES:e.append(f"commands.{n}.status must be one of {sorted(STATUSES)}")
  if n in REQUIRED_NON_NA and s=="n/a":e.append(f"commands.{n} may not be n/a")
  if s!="n/a" and (not isinstance(run,str) or not run.strip()):e.append(f"commands.{n}.run is required when status is not n/a")
  if not a.template_mode and isinstance(run,str):
   for m in PLACEHOLDER_MARKERS:
    if m in run:e.append(f"unresolved command placeholder in commands.{n}.run")
 v=d.get("development_velocity")
 if not isinstance(v,dict):e.append("development_velocity must be an object");v={}
 if v.get("default_stage")!="iteration":e.append("development_velocity.default_stage must be iteration")
 if v.get("stages")!=REQUIRED_DELIVERY_STAGES:e.append("development_velocity.stages must be iteration, integration, release in that order")
 i=v.get("iteration") if isinstance(v.get("iteration"),dict) else {};g=v.get("integration") if isinstance(v.get("integration"),dict) else {};r=v.get("release") if isinstance(v.get("release"),dict) else {}
 if not pi(i.get("target_feedback_minutes")):e.append("development_velocity.iteration.target_feedback_minutes must be a positive integer")
 for k in ("exact_head_required","full_diff_review_required","durable_documentation_current_required","remote_preflight_required"):f(i,k,e,"development_velocity.iteration")
 if i.get("e2e_default")!="risk_only":e.append("development_velocity.iteration.e2e_default must be risk_only")
 if not pi(g.get("target_feedback_minutes")):e.append("development_velocity.integration.target_feedback_minutes must be a positive integer")
 for k in ("exact_head_required","full_diff_review_required","durable_documentation_current_required","remote_preflight_when_required_gates_unavailable_local","automated_e2e_required_when_affected","real_environment_deferred_to_release"):t(g,k,e,"development_velocity.integration")
 f(g,"real_environment_blocking",e,"development_velocity.integration")
 if g.get("e2e_default")!="affected_critical_journeys":e.append("development_velocity.integration.e2e_default must be affected_critical_journeys")
 for k in ("exact_head_required","full_diff_review_required","durable_documentation_current_required","full_validation_required","required_real_environment_blocking"):t(r,k,e,"development_velocity.release")
 if r.get("e2e_default")!="release_critical_journeys":e.append("development_velocity.release.e2e_default must be release_critical_journeys")
 t(v,"parallel_development_prefers_early_convergence",e,"development_velocity");t(v,"stacked_publication_exception_only",e,"development_velocity")
 pub=d.get("publication_gate") if isinstance(d.get("publication_gate"),dict) else {}
 if pub.get("applies_from_stage")!="integration":e.append("publication_gate.applies_from_stage must be integration")
 for k in REQUIRED_PUBLICATION_FLAGS:t(pub,k,e,"publication_gate")
 ex=d.get("validation_execution") if isinstance(d.get("validation_execution"),dict) else {};missing=sorted(REQUIRED_EXECUTION_CLASSES-set(ex.get("classes") or []))
 if missing:e.append("validation_execution.classes missing: "+", ".join(missing))
 t(ex,"no_human_runner_for_automatable_gates",e,"validation_execution");t(ex,"remote_automation_required_when_agent_local_unavailable",e,"validation_execution")
 p=d.get("validation_profiles") if isinstance(d.get("validation_profiles"),dict) else {}
 if p.get("default")!="auto":e.append("validation_profiles.default must be auto")
 missing=sorted(REQUIRED_VALIDATION_PROFILES-set(p.get("profiles") or []))
 if missing:e.append("validation_profiles.profiles missing: "+", ".join(missing))
 sel=p.get("selector")
 if not isinstance(sel,str) or not sel.strip():e.append("validation_profiles.selector is required")
 elif not a.template_mode and any(m in sel for m in PLACEHOLDER_MARKERS):e.append("unresolved validation_profiles.selector placeholder")
 if p.get("selector_output")!="risk_dimensions_and_required_gates":e.append("validation_profiles.selector_output must be risk_dimensions_and_required_gates")
 for k in ("profiles_are_shorthand","gate_selection_preferred_over_suite_selection","unknown_executable_paths_fail_safe","selector_changes_force_full","promotion_validation_full","automatic_escalation_allowed","silent_downgrade_below_auto_forbidden","report_selected_profile_and_reason"):t(p,k,e,"validation_profiles")
 rp=d.get("remote_preflight") if isinstance(d.get("remote_preflight"),dict) else {};rs=rp.get("status")
 if rs not in {"required","recommended","n/a"}:e.append("remote_preflight.status must be required, recommended or n/a")
 if rs!="n/a":
  if not isinstance(rp.get("trigger"),str) or not rp.get("trigger").strip():e.append("remote_preflight.trigger is required when remote preflight is enabled")
  if rp.get("default_profile")!="auto":e.append("remote_preflight.default_profile must be auto")
  for k in ("stronger_profile_override_allowed","weaker_profile_override_requires_explicit_justification","exact_head_required","reuse_successful_equivalent_evidence","rerun_only_when_missing_stale_or_insufficient","trusted_requesters_only","same_repository_prs_only_by_default","report_result_to_pr"):t(rp,k,e,"remote_preflight")
  missing=sorted(REQUIRED_EVIDENCE_IDENTITY_FIELDS-set(rp.get("evidence_identity_fields") or []))
  if missing:e.append("remote_preflight.evidence_identity_fields missing: "+", ".join(missing))
  if rp.get("execution_job_write_credentials") is not False:e.append("remote_preflight.execution_job_write_credentials must be false")
 ee=d.get("end_to_end") if isinstance(d.get("end_to_end"),dict) else {}
 for k in REQUIRED_E2E_FLAGS:t(ee,k,e,"end_to_end")
 if ee.get("ui_evidence_modes")!=REQUIRED_UI_EVIDENCE_MODES:e.append("end_to_end.ui_evidence_modes must be assertions, screenshots, full_media in that order")
 if ee.get("ui_evidence_selection")!="risk_based":e.append("end_to_end.ui_evidence_selection must be risk_based")
 eco=d.get("validation_economics") if isinstance(d.get("validation_economics"),dict) else {}
 if eco.get("status") not in {"required","recommended","optional","n/a"}:e.append("validation_economics.status must be required, recommended, optional or n/a")
 if eco.get("optimize_for")!="sufficient-confidence-per-feedback-time":e.append("validation_economics.optimize_for must be sufficient-confidence-per-feedback-time")
 if REQUIRED_VALIDATION_ECONOMICS-set(eco.get("dimensions") or []):e.append("validation_economics.dimensions incomplete")
 t(eco,"periodic_review",e,"validation_economics")
 bi=d.get("build_identity") if isinstance(d.get("build_identity"),dict) else {}
 for k in ("unique_per_build","source_revision_required","dirty_state_required"):t(bi,k,e,"build_identity")
 for q in ("product","product_version","build_id","source_revision"):
  if q not in set(bi.get("artifact_name_fields") or []):e.append(f"build_identity.artifact_name_fields must include {q}")
 for q in ("project","platform","architecture","channel","variant"):
  if q not in set(bi.get("lineage_fields") or []):e.append(f"build_identity.lineage_fields must include {q}")
 al=d.get("artifact_lifecycle") if isinstance(d.get("artifact_lifecycle"),dict) else {}
 for k in ("immutable_successful_artifacts","promote_only_after_success","manifest_required","release_artifacts_immutable"):t(al,k,e,"artifact_lifecycle")
 if str(al.get("checksum_algorithm","")).lower()!="sha256":e.append("artifact_lifecycle.checksum_algorithm must be sha256")
 if not pi(al.get("local_keep_successful_per_lineage")):e.append("artifact_lifecycle.local_keep_successful_per_lineage must be a positive integer")
 if not pi(al.get("ci_retention_days")):e.append("artifact_lifecycle.ci_retention_days must be a positive integer")
 if not al.get("ci_store"):e.append("artifact_lifecycle.ci_store is required")
 if not al.get("release_store"):e.append("artifact_lifecycle.release_store is required")
 bd=d.get("build_delta") if isinstance(d.get("build_delta"),dict) else {};t(bd,"required",e,"build_delta");t(bd,"bundle_with_artifact",e,"build_delta")
 if bd.get("compare_to")!="previous-successful-comparable-build":e.append("build_delta.compare_to must be previous-successful-comparable-build")
 if not bd.get("output"):e.append("build_delta.output is required")
 if REQUIRED_DELTA_DIMENSIONS-set(bd.get("dimensions") or []):e.append("build_delta.dimensions incomplete")
 lr=d.get("local_runtime") if isinstance(d.get("local_runtime"),dict) else {}
 if lr.get("applicable") is True:
  if lr.get("bind_default")!="loopback":e.append("local_runtime.bind_default must be loopback when local runtime is applicable")
  if lr.get("port_strategy")!="configurable-with-collision-check":e.append("local_runtime.port_strategy must be configurable-with-collision-check")
  for k in ("foreground_default","readiness_required","graceful_shutdown_required","verify_no_project_listener_after_stop"):t(lr,k,e,"local_runtime")
 ep=d.get("ephemeral_resources") if isinstance(d.get("ephemeral_resources"),dict) else {}
 for k in ("run_identity","isolated_workspace","stale_resource_recovery","ownership_required_before_cleanup","post_cleanup_verification"):t(ep,k,e,"ephemeral_resources")
 if REQUIRED_CLEANUP_PATHS-set(ep.get("cleanup_paths") or []):e.append("ephemeral_resources.cleanup_paths incomplete")
 print("Project operating contract check");print(f"root: {root}");[print(f"WARN: {x}") for x in w];[print(f"FAIL: {x}") for x in e]
 if e:print(f"RESULT: FAIL ({len(e)} error(s), {len(w)} warning(s))");return 1
 print(f"RESULT: PASS ({len(w)} warning(s))");return 0
if __name__=="__main__":sys.exit(main())

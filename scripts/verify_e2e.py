#!/usr/bin/env python3
"""Validate the repo-template-sw 0.2 E2E fidelity contract."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

FIDELITY=["host_or_fake","simulated_or_emulated","representative_virtual","representative_physical","target_environment"]
MODES=["assertions","screenshots","full_media"]
TRIGGERS={"motion_or_animation","timing_or_progression","navigation_or_transition_sequence","lifecycle_visibility","release_acceptance"}

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--root",default="."); p.add_argument("--template-mode",action="store_true"); a=p.parse_args()
    root=Path(a.root); errors=[]
    try: data=json.loads((root/".engineering/e2e.json").read_text())
    except Exception as exc: print(f"FAIL: invalid e2e.json: {exc}"); return 1
    if data.get("schema_version")!=1: errors.append("schema_version must be 1")
    if data.get("contract_version")!="0.2.0": errors.append("contract_version must be 0.2.0")
    app=data.get("applicability",{})
    if app.get("status") not in {"required","recommended","n/a"} or not str(app.get("reason","")).strip(): errors.append("invalid applicability")
    principles=data.get("principles",{})
    for key in ("final_environment_should_confirm_not_discover","execution_capability_separate_from_environment_fidelity","lowest_sufficient_test_level","critical_journeys_only","built_artifact_when_material","residual_fidelity_gaps_explicit","ui_evidence_risk_based"):
        if principles.get(key) is not True: errors.append(f"principles.{key} must be true")
    ui=data.get("ui_evidence",{})
    if ui.get("modes")!=MODES: errors.append("ui_evidence.modes invalid")
    if ui.get("default_mode") not in MODES: errors.append("ui_evidence.default_mode invalid")
    if ui.get("assertions_allowed_when_ui_incidental") is not True: errors.append("assertions must be allowed for incidental UI")
    if not TRIGGERS.issubset(set(ui.get("full_media_triggers",[]))): errors.append("full_media_triggers incomplete")
    if data.get("fidelity_order")!=FIDELITY: errors.append("fidelity_order invalid")
    targets={x.get("id") for x in data.get("target_environments",[]) if isinstance(x,dict)}
    envs={x.get("id"):x for x in data.get("execution_environments",[]) if isinstance(x,dict)}
    if app.get("status")!="n/a" and (not targets or not envs or not data.get("critical_journeys")): errors.append("applicable E2E contract needs targets, environments and journeys")
    for eid,env in envs.items():
        if env.get("fidelity_class") not in FIDELITY: errors.append(f"environment {eid} fidelity invalid")
        if env.get("automation") not in {"automated","real_environment"}: errors.append(f"environment {eid} automation invalid")
        if not set(env.get("target_environment_refs",[])).issubset(targets): errors.append(f"environment {eid} target refs invalid")
    for journey in data.get("critical_journeys",[]):
        if not isinstance(journey,dict) or not journey.get("id"): errors.append("journey id required"); continue
        jid=journey["id"]; ui_surface=journey.get("ui_surface"); mode=journey.get("minimum_ui_evidence_mode")
        if ui_surface is True and mode not in MODES: errors.append(f"journey {jid} UI mode invalid")
        if ui_surface is False and mode not in {None,"assertions"}: errors.append(f"journey {jid} non-UI mode invalid")
        if not set(journey.get("target_environment_refs",[])).issubset(targets): errors.append(f"journey {jid} target refs invalid")
        refs=journey.get("automated_environment_refs",[])
        if not set(refs).issubset(envs): errors.append(f"journey {jid} automated refs invalid")
        if journey.get("minimum_automated_fidelity") not in FIDELITY: errors.append(f"journey {jid} minimum fidelity invalid")
        if journey.get("real_environment_confirmation") not in {"required","conditional","not_required"}: errors.append(f"journey {jid} real confirmation invalid")
        if not refs and not str(journey.get("automation_gap_reason","")).strip(): errors.append(f"journey {jid} needs automation gap reason")
    print("E2E environment fidelity contract check")
    for error in errors: print("FAIL:",error)
    print("RESULT:","FAIL" if errors else "PASS")
    return 1 if errors else 0
if __name__=="__main__": sys.exit(main())

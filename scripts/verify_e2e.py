#!/usr/bin/env python3
"""Validate the repo-template-sw 0.9.2 E2E environment contract."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
FIDELITY=["host_or_fake","simulated_or_emulated","representative_virtual","representative_physical","target_environment"]
UI=["assertions","screenshots","full_media"]
TRIGGERS={"material_ui_integration_outcome","motion_or_animation","timing_or_progression","navigation_or_transition_sequence","lifecycle_visibility","release_acceptance"}
def expect(s,k,v,e,p):
    if s.get(k)!=v:e.append(f"{p}.{k} must be {v!r}")
def keyed(items,label,errors):
    out={}
    if not isinstance(items,list):errors.append(f"{label} must be a list");return out
    for x in items:
        if not isinstance(x,dict) or not str(x.get("id","")).strip():errors.append(f"{label} item id required");continue
        out[x["id"]]=x
    return out
def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--root",default=".");p.add_argument("--template-mode",action="store_true");a=p.parse_args();root=Path(a.root).resolve();errors=[]
    try:d=json.loads((root/".engineering/e2e.json").read_text());c=json.loads((root/".engineering/commands.json").read_text())
    except Exception as x:print(f"FAIL: invalid engineering JSON: {x}");return 1
    expect(d,"schema_version",1,errors,"e2e");expect(d,"contract_version","0.2.1",errors,"e2e")
    status=(d.get("applicability") or {}).get("status");cs=((c.get("commands") or {}).get("e2e") or {}).get("status")
    if status not in {"required","recommended","n/a"}:errors.append("applicability.status invalid")
    if status=="required" and cs!="required":errors.append("required E2E requires commands.e2e required")
    pol=d.get("stage_policy",{});i=pol.get("integration",{});r=pol.get("release",{})
    for k,v in {"automated_e2e_before_shared_integration":True,"real_environment_blocking":False,"real_environment_deferred_to_release":True,"material_ui_journey_minimum_evidence_mode":"full_media","incidental_ui_may_use_assertions":True}.items():expect(i,k,v,errors,"stage_policy.integration")
    for k,v in {"full_validation_required":True,"release_critical_e2e_required":True,"required_real_environment_blocking":True}.items():expect(r,k,v,errors,"stage_policy.release")
    ui=d.get("ui_evidence",{});expect(ui,"modes",UI,errors,"ui_evidence")
    if not TRIGGERS.issubset(set(ui.get("full_media_triggers") or [])):errors.append("ui_evidence.full_media_triggers incomplete")
    expect(d,"fidelity_order",FIDELITY,errors,"e2e")
    targets=keyed(d.get("target_environments"),"target_environments",errors);envs=keyed(d.get("execution_environments"),"execution_environments",errors);journeys=keyed(d.get("critical_journeys"),"critical_journeys",errors)
    for eid,x in envs.items():
        if x.get("fidelity_class") not in FIDELITY:errors.append(f"execution_environments.{eid}.fidelity_class invalid")
        if x.get("automation") not in {"automated","real_environment"}:errors.append(f"execution_environments.{eid}.automation invalid")
        for ref in x.get("target_environment_refs") or []:
            if ref not in targets:errors.append(f"execution_environments.{eid} unknown target {ref}")
    for jid,x in journeys.items():
        if x.get("ui_surface") is True and x.get("minimum_ui_evidence_mode") not in UI:errors.append(f"critical_journeys.{jid}.minimum_ui_evidence_mode invalid")
        if x.get("real_environment_confirmation") not in {"required","conditional","not_required"}:errors.append(f"critical_journeys.{jid}.real_environment_confirmation invalid")
        for ref in x.get("automated_environment_refs") or []:
            if ref not in envs:errors.append(f"critical_journeys.{jid} unknown automated environment {ref}")
            elif envs[ref].get("automation")!="automated":errors.append(f"critical_journeys.{jid} automated ref {ref} is not automated")
        if not (x.get("automated_environment_refs") or []) and not str(x.get("automation_gap_reason") or "").strip():errors.append(f"critical_journeys.{jid} needs automated refs or automation_gap_reason")
    print("E2E environment fidelity contract check");[print("FAIL:",x) for x in errors];print("RESULT:","FAIL" if errors else "PASS");return 1 if errors else 0
if __name__=="__main__":sys.exit(main())

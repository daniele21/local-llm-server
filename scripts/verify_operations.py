#!/usr/bin/env python3
"""Validate the repo-template-sw 0.9.2 operating contract."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
COMMANDS=("setup","doctor","dev","check","test","e2e","build","smoke","package","stop","clean")
STATUSES={"required","recommended","optional","n/a"}
def expect(s,k,v,e,p):
    if s.get(k)!=v:e.append(f"{p}.{k} must be {v!r}")
def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--root",default=".");p.add_argument("--template-mode",action="store_true");a=p.parse_args();root=Path(a.root).resolve();errors=[]
    try:d=json.loads((root/".engineering/commands.json").read_text())
    except Exception as x:print(f"FAIL: invalid commands.json: {x}");return 1
    expect(d,"schema_version",1,errors,"commands");expect(d,"contract_version","0.6.1",errors,"commands")
    c=d.get("commands",{})
    for n in COMMANDS:
        x=c.get(n)
        if not isinstance(x,dict):errors.append(f"commands.{n} missing");continue
        if x.get("status") not in STATUSES:errors.append(f"commands.{n}.status invalid")
        if n in {"setup","check","test","build","clean"} and x.get("status")=="n/a":errors.append(f"commands.{n} may not be n/a")
        if x.get("status")!="n/a" and not str(x.get("run","")).strip():errors.append(f"commands.{n}.run required")
    v=d.get("development_velocity",{});expect(v,"default_stage","iteration",errors,"development_velocity");expect(v,"stages",["iteration","integration","release"],errors,"development_velocity")
    it=v.get("iteration",{});i=v.get("integration",{});r=v.get("release",{})
    for k in ("exact_head_required","full_diff_review_required","durable_documentation_current_required","remote_preflight_required"):expect(it,k,False,errors,"development_velocity.iteration")
    expect(it,"e2e_default","risk_only",errors,"development_velocity.iteration")
    for k in ("exact_head_required","full_diff_review_required","durable_documentation_current_required","remote_preflight_when_required_gates_unavailable_local","automated_e2e_required_when_affected","real_environment_deferred_to_release"):expect(i,k,True,errors,"development_velocity.integration")
    expect(i,"real_environment_blocking",False,errors,"development_velocity.integration");expect(i,"e2e_default","affected_critical_journeys",errors,"development_velocity.integration")
    for k in ("exact_head_required","full_diff_review_required","durable_documentation_current_required","full_validation_required","required_real_environment_blocking"):expect(r,k,True,errors,"development_velocity.release")
    expect(r,"e2e_default","release_critical_journeys",errors,"development_velocity.release")
    print("Project operating contract check");[print("FAIL:",x) for x in errors];print("RESULT:","FAIL" if errors else "PASS");return 1 if errors else 0
if __name__=="__main__":sys.exit(main())

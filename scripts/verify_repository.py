#!/usr/bin/env python3
"""Structural repository checks with optional L1/L2 specialist fitness execution."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

CORE_SKILLS=("plan-workstream","structured-change","design-product-experience","validate-change","preflight-change","remote-preflight","finalize-workstream","review-reference-quality")
REQUIRED=("README.md","AGENTS.md","CONTRIBUTING.md","SECURITY.md",".editorconfig",".gitignore",".engineering/baseline.json",".engineering/documentation-policy.json",".engineering/commands.json",".engineering/e2e.json",".github/pull_request_template.md",".github/workflows/repository-health.yml","docs/README.md","docs/architecture.md","docs/current-state.md","docs/features/README.md","docs/adr/README.md","docs/workstreams/README.md","scripts/verify_operations.py","scripts/verify_e2e.py","scripts/verify_product_experience.py","scripts/select_validation_profile.py")
L1=("scripts/verify_performance_budgets.py","scripts/verify_lifecycle_contracts.py","scripts/verify_security_exceptions.py")
L2=("scripts/verify_architecture.py","scripts/verify_resource_regression.py","scripts/verify_fault_injection.py","scripts/verify_repeatability_contracts.py","scripts/verify_change_review.py","scripts/verify_built_surface_e2e.py","scripts/verify_product_experience.py","scripts/verify_product_ui_l2.py","scripts/verify_l2_evidence_bridge.py")
PLACEHOLDERS=("<PROJECT_NAME>","<REPLACE_WITH_","<DESCRIBE_","<LIST_")

def run_validator(root:Path, relative:str, level:str)->str|None:
    path=root/relative
    if not path.is_file(): return f"missing {level} fitness function: {relative}"
    proc=subprocess.run([sys.executable,str(path)],cwd=root,text=True,capture_output=True,check=False)
    if proc.returncode==0:
        if proc.stdout.strip(): print(f"\n--- {relative} ---\n{proc.stdout.strip()}")
        return None
    detail="\n".join(x.strip() for x in (proc.stdout,proc.stderr) if x.strip())
    return f"{level} fitness function failed: {relative}\n{detail}"

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--root",default="."); p.add_argument("--template-mode",action="store_true"); p.add_argument("--skip-specialists",action="store_true"); a=p.parse_args()
    root=Path(a.root).resolve(); errors=[]; warnings=[]
    for rel in REQUIRED:
        if not (root/rel).is_file(): errors.append(f"missing required file: {rel}")
    for name in CORE_SKILLS:
        if not (root/"skills"/name/"SKILL.md").is_file(): errors.append(f"missing core skill: skills/{name}/SKILL.md")
    target=None
    try: baseline=json.loads((root/".engineering/baseline.json").read_text())
    except Exception as exc: errors.append(f"invalid baseline.json: {exc}"); baseline={}
    if baseline:
        standard=baseline.get("standard",{})
        if baseline.get("schema_version")!=1: errors.append("baseline schema_version must be 1")
        if standard.get("source")!="daniele21/repo-template-sw": errors.append("baseline standard.source invalid")
        if standard.get("version")!="0.9.1": errors.append("baseline standard.version must be 0.9.1")
        target=baseline.get("target_level")
        if target not in {"L0","L1","L2"}: errors.append("target_level must be L0, L1 or L2")
        if not isinstance(baseline.get("profiles"),list): errors.append("profiles must be a list")
        skills=baseline.get("skills",{})
        for name in CORE_SKILLS:
            entry=skills.get(name)
            if not isinstance(entry,dict) or not entry.get("source_version") or not isinstance(entry.get("customized"),bool): errors.append(f"invalid skill metadata: {name}")
    if not a.template_mode:
        for path in (root/"README.md",root/"AGENTS.md",root/"docs/architecture.md",root/"SECURITY.md"):
            if path.is_file():
                text=path.read_text()
                for marker in PLACEHOLDERS:
                    if marker in text: errors.append(f"unresolved adopter placeholder {marker} in {path.relative_to(root)}")
        if not a.skip_specialists:
            if target in {"L1","L2"}:
                for rel in L1:
                    failure=run_validator(root,rel,"L1")
                    if failure: errors.append(failure)
            if target=="L2":
                for rel in L2:
                    failure=run_validator(root,rel,"L2")
                    if failure: errors.append(failure)
    present=[n for n in ("node_modules",".venv","build","dist","__pycache__") if (root/n).exists()]
    if present: warnings.append("generated/local directories present in worktree: "+", ".join(present))
    if not any((root/n).is_file() for n in ("LICENSE","LICENSE.md","LICENSE.txt")): warnings.append("no project license file detected")
    print("Repository baseline check"); print(f"root: {root}"); print(f"specialists: {'SKIPPED' if a.skip_specialists else 'ENABLED'}")
    for w in warnings: print("WARN:",w)
    for e in errors: print("FAIL:",e)
    print("RESULT:","FAIL" if errors else "PASS")
    return 1 if errors else 0
if __name__=="__main__": sys.exit(main())

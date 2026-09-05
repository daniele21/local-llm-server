#!/usr/bin/env python3
"""Structural repository checks with optional L1/L2 specialist fitness execution."""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
CORE_SKILLS=("plan-workstream","structured-change","design-product-experience","validate-change","preflight-change","remote-preflight","finalize-workstream","review-reference-quality")
REQUIRED=("README.md","AGENTS.md","CONTRIBUTING.md","SECURITY.md",".editorconfig",".gitignore",".engineering/baseline.json",".engineering/documentation-policy.json",".engineering/commands.json",".engineering/e2e.json",".github/pull_request_template.md",".github/workflows/repository-health.yml","docs/README.md","docs/architecture.md","docs/current-state.md","docs/features/README.md","docs/adr/README.md","docs/workstreams/README.md","scripts/verify_operations.py","scripts/verify_e2e.py","scripts/verify_stage_environment_policy.py","scripts/verify_product_experience.py","scripts/select_validation_profile.py")
L1=("scripts/verify_performance_budgets.py","scripts/verify_lifecycle_contracts.py","scripts/verify_security_exceptions.py")
L2=("scripts/verify_architecture.py","scripts/verify_resource_regression.py","scripts/verify_fault_injection.py","scripts/verify_repeatability_contracts.py","scripts/verify_change_review.py","scripts/verify_built_surface_e2e.py","scripts/verify_product_experience.py","scripts/verify_product_ui_l2.py","scripts/verify_l2_evidence_bridge.py")
PLACEHOLDERS=("<PROJECT_NAME>","<REPLACE_WITH_","<DESCRIBE_","<LIST_")
def run_validator(root:Path,relative:str,level:str)->str|None:
    path=root/relative
    if not path.is_file():return f"missing {level} fitness function: {relative}"
    proc=subprocess.run([sys.executable,str(path)],cwd=root,text=True,capture_output=True,check=False)
    if proc.returncode==0:
        if proc.stdout.strip():print(f"\n--- {relative} ---\n{proc.stdout.strip()}")
        return None
    detail="\n".join(x.strip() for x in (proc.stdout,proc.stderr) if x.strip())
    return f"{level} fitness function failed: {relative}\n{detail}"
def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--root",default=".");p.add_argument("--template-mode",action="store_true");p.add_argument("--skip-specialists",action="store_true");a=p.parse_args();root=Path(a.root).resolve();errors=[];warnings=[]
    for rel in REQUIRED:
        if not (root/rel).is_file():errors.append(f"missing required file: {rel}")
    for n in CORE_SKILLS:
        if not (root/"skills"/n/"SKILL.md").is_file():errors.append(f"missing core skill: skills/{n}/SKILL.md")
    target=None
    try:b=json.loads((root/".engineering/baseline.json").read_text())
    except Exception as x:errors.append(f"invalid baseline.json: {x}");b={}
    if b:
        s=b.get("standard",{})
        if b.get("schema_version")!=1:errors.append("baseline schema_version must be 1")
        if s.get("source")!="daniele21/repo-template-sw":errors.append("baseline standard.source invalid")
        if s.get("version")!="0.9.2":errors.append("baseline standard.version must be 0.9.2")
        if s.get("revision")!="8aa95d10254846e7d63f4bd5c60d61b18d21060c":errors.append("baseline standard.revision must match canonical 0.9.2 main")
        target=b.get("target_level")
        if target not in {"L0","L1","L2"}:errors.append("target_level must be L0, L1 or L2")
        if not isinstance(b.get("profiles"),list):errors.append("profiles must be a list")
        for n in CORE_SKILLS:
            e=b.get("skills",{}).get(n)
            if not isinstance(e,dict) or not e.get("source_version") or not isinstance(e.get("customized"),bool):errors.append(f"invalid skill metadata: {n}")
    if not a.template_mode:
        for path in (root/"README.md",root/"AGENTS.md",root/"docs/architecture.md",root/"SECURITY.md"):
            if path.is_file():
                text=path.read_text()
                for m in PLACEHOLDERS:
                    if m in text:errors.append(f"unresolved adopter placeholder {m} in {path.relative_to(root)}")
        if not a.skip_specialists:
            if target in {"L1","L2"}:
                for rel in L1:
                    f=run_validator(root,rel,"L1")
                    if f:errors.append(f)
            if target=="L2":
                for rel in L2:
                    f=run_validator(root,rel,"L2")
                    if f:errors.append(f)
    present=[n for n in ("node_modules",".venv","build","dist","__pycache__") if (root/n).exists()]
    if present:warnings.append("generated/local directories present in worktree: "+", ".join(present))
    if not any((root/n).is_file() for n in ("LICENSE","LICENSE.md","LICENSE.txt")):warnings.append("no project license file detected")
    print("Repository baseline check");print(f"root: {root}");print(f"specialists: {'SKIPPED' if a.skip_specialists else 'ENABLED'}");[print("WARN:",x) for x in warnings];[print("FAIL:",x) for x in errors];print("RESULT:","FAIL" if errors else "PASS");return 1 if errors else 0
if __name__=="__main__":sys.exit(main())

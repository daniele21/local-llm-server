#!/usr/bin/env python3
"""Select the narrowest safe validation profile from the changed-path blast radius."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

PROFILES = ("lean", "scoped", "strong", "full")
FULL_PREFIXES = (".github/workflows/",)
FULL_PATHS = {
    ".engineering/commands.json",
    "scripts/select_validation_profile.py",
    "scripts/verify_operations.py",
    "scripts/verify_repository.py",
    "pyproject.toml",
    "uv.lock",
    "package.json",
    "package-lock.json",
    "deploy.sh",
    "release.sh",
}
STRONG_PREFIXES = (
    "src/local_llm_server/core/",
    "src/local_llm_server/static/",
    "tests/e2e/",
    "tests/real_runtime/",
    "design/",
    ".engineering/",
    "scripts/verify_",
)
STRONG_PATHS = {"SECURITY.md", "AGENTS.md", "CONTRIBUTING.md"}
LEAN_PREFIXES = ("docs/",)
LEAN_PATHS = {"README.md", "CHANGELOG.md"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", default=os.getenv("VALIDATION_BASE_REF", "dev"))
    parser.add_argument("--head-ref", default=os.getenv("VALIDATION_HEAD_REF", "HEAD"))
    parser.add_argument("--profile", choices=("auto",) + PROFILES, default="auto")
    return parser.parse_args()


def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args], text=True, capture_output=True, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "git command failed")
    return proc.stdout.strip()


def changed_paths(base_ref: str, head_ref: str) -> list[str]:
    merge_base = git("merge-base", base_ref, head_ref)
    output = git("diff", "--name-only", f"{merge_base}...{head_ref}")
    return sorted({line.strip() for line in output.splitlines() if line.strip()})


def select(paths: list[str]) -> tuple[str, str]:
    if not paths:
        return "lean", "no changed paths detected"

    full = [
        path
        for path in paths
        if path in FULL_PATHS or path.startswith(FULL_PREFIXES)
    ]
    if full:
        return "full", "global validation/build/dependency/selector surface changed: " + ", ".join(full[:6])

    unknown_executable = [
        path
        for path in paths
        if Path(path).suffix in {".py", ".js", ".ts", ".sh", ".yml", ".yaml"}
        and not (
            path.startswith("src/")
            or path.startswith("tests/")
            or path.startswith("scripts/")
            or path.startswith(".github/")
        )
    ]
    if unknown_executable:
        return "full", "unknown executable path fails safe: " + ", ".join(unknown_executable[:6])

    strong = [
        path
        for path in paths
        if path in STRONG_PATHS or path.startswith(STRONG_PREFIXES)
    ]
    if strong:
        return "strong", "cross-boundary/runtime/E2E/product-contract surface changed: " + ", ".join(strong[:6])

    if all(path in LEAN_PATHS or path.startswith(LEAN_PREFIXES) for path in paths):
        return "lean", "documentation-only blast radius"

    owners = {path.split("/", 2)[0] for path in paths}
    if owners <= {"src", "tests"}:
        return "scoped", "contained implementation/test blast radius"

    return "strong", "mixed or unclassified repository surface; fail safe stronger"


def main() -> int:
    args = parse_args()
    try:
        paths = changed_paths(args.base_ref, args.head_ref)
    except RuntimeError as exc:
        result = {
            "profile": "full",
            "reason": f"unable to establish diff safely: {exc}",
            "base_ref": args.base_ref,
            "head_ref": args.head_ref,
            "changed_paths": [],
        }
        print(json.dumps(result, indent=2))
        return 0

    automatic, reason = select(paths)
    selected = automatic
    if args.profile != "auto":
        requested_rank = PROFILES.index(args.profile)
        auto_rank = PROFILES.index(automatic)
        if requested_rank < auto_rank:
            print(
                f"Requested profile {args.profile} is weaker than auto-selected {automatic}; refusing silent downgrade.",
                file=sys.stderr,
            )
            return 2
        selected = args.profile
        reason = f"explicit stronger override from auto={automatic}: {reason}"

    print(
        json.dumps(
            {
                "profile": selected,
                "auto_profile": automatic,
                "reason": reason,
                "base_ref": args.base_ref,
                "head_ref": args.head_ref,
                "changed_paths": paths,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

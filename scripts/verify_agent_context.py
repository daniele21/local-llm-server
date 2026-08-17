#!/usr/bin/env python3
"""Estimate mandatory coding-agent context cost from bounded repository guides."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    return parser.parse_args()


def estimate(path: Path, chars_per_token: int) -> int:
    if not path.is_file():
        return 0
    return math.ceil(len(path.read_text(encoding="utf-8")) / chars_per_token)


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    policy = json.loads((root / ".engineering/documentation-policy.json").read_text(encoding="utf-8"))
    chars_per_token = int(policy.get("estimated_token_characters", 4))
    targets = policy["context_targets"]

    root_tokens = estimate(root / "AGENTS.md", chars_per_token)
    scoped = [(p, estimate(p, chars_per_token)) for p in root.rglob("AGENTS.md") if p != root / "AGENTS.md" and ".git" not in p.parts]
    scoped_path, scoped_tokens = max(scoped, key=lambda item: item[1], default=(None, 0))
    workstreams = [(p, estimate(p, chars_per_token)) for p in (root / "docs/workstreams").glob("*.md") if p.name != "README.md" and not p.name.startswith("_")] if (root / "docs/workstreams").is_dir() else []
    work_path, work_tokens = max(workstreams, key=lambda item: item[1], default=(None, 0))

    bootstrap = root_tokens
    worst_focused = root_tokens + scoped_tokens + work_tokens
    errors: list[str] = []
    if bootstrap > targets["bootstrap_max_estimated_tokens"]:
        errors.append(f"bootstrap context ~{bootstrap} > {targets['bootstrap_max_estimated_tokens']} token target")
    if worst_focused > targets["root_scoped_workstream_max_estimated_tokens"]:
        errors.append(
            f"root+largest scoped+largest workstream ~{worst_focused} > {targets['root_scoped_workstream_max_estimated_tokens']} token target"
        )

    print("Agent context health")
    print(f"root AGENTS: ~{root_tokens} tokens")
    print(f"largest scoped AGENTS: ~{scoped_tokens} tokens" + (f" ({scoped_path.relative_to(root)})" if scoped_path else ""))
    print(f"largest active workstream: ~{work_tokens} tokens" + (f" ({work_path.relative_to(root)})" if work_path else ""))
    print(f"bootstrap cost: ~{bootstrap} tokens")
    print(f"worst focused routing bundle: ~{worst_focused} tokens")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env bash
set -euo pipefail

# Release flow:
# 1. require clean main and a canonical setup environment;
# 2. bump VERSION + pyproject.toml and refresh local-project metadata in uv.lock;
# 3. run deterministic tests and build the immutable release-candidate bundle;
# 4. commit exactly the version/lock identity files;
# 5. create a new annotated tag only when it does not already exist locally or remotely;
# 6. push without force. The tag-triggered workflow rebuilds from the committed lock.

current_branch="$(git branch --show-current)"
if [[ "$current_branch" != "main" ]]; then
  echo "Error: releases must start from main; current branch: $current_branch" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Error: working tree must be clean before a release." >&2
  exit 1
fi

echo "[*] Bumping patch version, synchronizing lock identity, testing and producing a local immutable build"
LOCAL_LLM_BUILD_CHANNEL=release-candidate ./deploy.sh --bump-patch

new_version="$(python3 - <<'PY'
import tomllib
from pathlib import Path
with Path("pyproject.toml").open("rb") as fh:
    project = str(tomllib.load(fh)["project"]["version"])
version_file = Path("VERSION").read_text(encoding="utf-8").strip()
if project != version_file:
    raise SystemExit(f"Version mismatch after bump: {project} != {version_file}")
print(project)
PY
)"
tag_name="v${new_version}"

if git rev-parse -q --verify "refs/tags/${tag_name}" >/dev/null; then
  echo "Error: local tag ${tag_name} already exists; tags are immutable." >&2
  exit 1
fi
if git ls-remote --exit-code --tags origin "refs/tags/${tag_name}" >/dev/null 2>&1; then
  echo "Error: remote tag ${tag_name} already exists; refusing to move it." >&2
  exit 1
fi

echo "[*] Committing release identity ${new_version}"
git add pyproject.toml VERSION uv.lock
git commit -m "chore: release version ${new_version}"

echo "[*] Creating immutable annotated tag ${tag_name}"
git tag -a "${tag_name}" -m "Release ${tag_name}"

echo "[*] Pushing main and tag without force"
git push origin main
git push origin "${tag_name}"

echo "[*] Release ${tag_name} pushed. GitHub Actions will rebuild from the committed lock and publish immutable assets."

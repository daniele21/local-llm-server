#!/usr/bin/env bash
#
# Release Automation Script for local-llm-server
# 
# Usage:
#   ./release.sh
#
# Description:
#   This script automates the creation of a new package release:
#   1. Verifies that you are on the 'main' branch.
#   2. Verifies that the git working directory is clean.
#   3. Runs './deploy.sh --bump-patch' to increment the patch version, execute tests,
#      and build the package wheels (retaining previous builds in dist/).
#   4. Commits the version bump files locally.
#   5. Creates an annotated git tag corresponding to the new version (e.g., v0.3.1).
#   6. Pushes the commit and tag to GitHub automatically to trigger the release workflow.
#
set -euo pipefail


# Ensure we are on the main branch
current_branch=$(git branch --show-current)
if [ "$current_branch" != "main" ]; then
  echo "Error: You must be on the 'main' branch to release. Currently on: $current_branch" >&2
  exit 1
fi

# Ensure working tree is clean
if ! git diff-index --quiet HEAD --; then
  echo "Error: Working tree is not clean. Commit or stash your changes first." >&2
  exit 1
fi

echo "[*] Running deploy.sh with --bump-patch to bump version, run tests, and build package..."
./deploy.sh --bump-patch

# Retrieve the new version from pyproject.toml
new_version=$(python3 -c '
import re
from pathlib import Path
match = re.search(r"version\s*=\s*\"([^\"]+)\"", Path("pyproject.toml").read_text(encoding="utf-8"))
print(match.group(1) if match else "")
')

if [ -z "$new_version" ]; then
  echo "Error: Could not retrieve new version from pyproject.toml" >&2
  exit 1
fi

tag_name="v$new_version"

echo "[*] Creating git commit for version $new_version..."
git add pyproject.toml uv.lock src/local_llm_server/server.py
git commit -m "chore: release version $new_version" || echo "[*] No changes to commit"

echo "[*] Creating Git tag $tag_name..."
git tag -f -a "$tag_name" -m "Release $tag_name"

echo "[*] Pushing commit to main..."
git push origin main

echo "[*] Pushing tag $tag_name..."
git push origin "$tag_name" --force

echo "[*] Release $tag_name successfully pushed! GitHub Actions will now build and deploy the release."

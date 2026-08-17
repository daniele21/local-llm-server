#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./deploy.sh [--bump-patch] [--skip-tests]

Build an immutable, uniquely identified wheel/sdist bundle from the already
synchronized project environment.

Options:
  --bump-patch   Increment patch version in pyproject.toml/VERSION and update
                 only the already-resolved local editable package version in
                 uv.lock. No dependency re-resolution is performed.
  --skip-tests   Build without running the deterministic pytest suite first.
  -h, --help     Show this help.
EOF
}

bump_patch=false
skip_tests=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bump-patch) bump_patch=true; shift ;;
    --skip-tests) skip_tests=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

run_uv() {
  # Reuse uv's platform-standard cache (or an explicitly provided
  # UV_CACHE_DIR). Canonical setup populates that cache.
  uv "$@"
}

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv is required. Run the canonical setup command first." >&2
  exit 1
fi

if [[ ! -x .venv/bin/python && ! -x .venv/Scripts/python.exe ]]; then
  echo "Error: project environment is missing. Run the canonical setup command first." >&2
  exit 1
fi

if [[ "$bump_patch" == true ]]; then
  current_version="$(python3 - <<'PY'
import re
from pathlib import Path

project = Path("pyproject.toml")
lock = Path("uv.lock")
project_content = project.read_text(encoding="utf-8")
lock_content = lock.read_text(encoding="utf-8")

match = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', project_content)
if not match:
    raise SystemExit("Could not find project version in pyproject.toml")
old = match.group(1)
parts = old.split(".")
if len(parts) != 3 or not all(part.isdigit() for part in parts):
    raise SystemExit(f"Expected semantic version X.Y.Z, found: {old}")
parts[-1] = str(int(parts[-1]) + 1)
new = ".".join(parts)

project_updated = project_content[: match.start(1)] + new + project_content[match.end(1) :]

# uv.lock already contains the fully resolved dependency graph. A release-only
# version bump must not reopen resolution. Update exactly the local editable
# project package block and fail closed if its expected identity is ambiguous.
package_pattern = re.compile(
    r'(?ms)(\[\[package\]\]\nname = "local-llm-server"\nversion = ")'
    + re.escape(old)
    + r'("\nsource = \{ editable = "\." \})'
)
lock_updated, replacements = package_pattern.subn(rf"\g<1>{new}\g<2>", lock_content)
if replacements != 1:
    raise SystemExit(
        "Expected exactly one local editable local-llm-server package entry "
        f"at version {old} in uv.lock; found {replacements}"
    )

project.write_text(project_updated, encoding="utf-8")
Path("VERSION").write_text(new + "\n", encoding="utf-8")
lock.write_text(lock_updated, encoding="utf-8")
print(new)
PY
)"
  echo "[*] Version bumped atomically to: ${current_version}"
  echo "[*] Verifying the resolved lock remains synchronized"
  run_uv lock --check
else
  current_version="$(python3 - <<'PY'
import tomllib
from pathlib import Path
with Path("pyproject.toml").open("rb") as fh:
    project = tomllib.load(fh)["project"]["version"]
version_file = Path("VERSION").read_text(encoding="utf-8").strip()
if project != version_file:
    raise SystemExit(f"Version mismatch: pyproject.toml={project}, VERSION={version_file}")
print(project)
PY
)"
  echo "[*] Building version: ${current_version}"
fi

if [[ "$skip_tests" != true ]]; then
  echo "[*] Running deterministic tests from the synchronized environment"
  run_uv run --no-sync pytest tests/ -v --tb=short
fi

echo "[*] Cleaning transient backend state only; successful dist builds are retained"
rm -rf build src/*.egg-info

echo "[*] Building staged immutable artifacts from the locked project toolchain"
run_uv run --no-sync python scripts/build_artifacts.py \
  --output-root dist \
  --channel "${LOCAL_LLM_BUILD_CHANNEL:-local}" \
  --variant "${LOCAL_LLM_BUILD_VARIANT:-wheel-sdist}"

echo "[*] Build complete. Successful builds are retained under dist/builds/ by lineage."

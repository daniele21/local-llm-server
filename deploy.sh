#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./deploy.sh [--bump-patch] [--skip-tests]

Build an immutable, uniquely identified wheel/sdist bundle from the already
synchronized project environment.

Options:
  --bump-patch   Increment patch version in pyproject.toml/VERSION and refresh
                 local-project metadata in uv.lock without network resolution.
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
  local temp_root="${TMPDIR:-/tmp}"
  UV_CACHE_DIR="${UV_CACHE_DIR:-${temp_root%/}/local-llm-uv-cache}" uv "$@"
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
content = project.read_text(encoding="utf-8")
match = re.search(r'version\s*=\s*"([^"]+)"', content)
if not match:
    raise SystemExit("Could not find project version in pyproject.toml")
old = match.group(1)
parts = old.split(".")
if len(parts) != 3 or not all(part.isdigit() for part in parts):
    raise SystemExit(f"Expected semantic version X.Y.Z, found: {old}")
parts[-1] = str(int(parts[-1]) + 1)
new = ".".join(parts)
project.write_text(content.replace(f'version = "{old}"', f'version = "{new}"', 1), encoding="utf-8")
Path("VERSION").write_text(new + "\n", encoding="utf-8")
print(new)
PY
)"
  echo "[*] Version bumped atomically to: ${current_version}"
  echo "[*] Synchronizing local project metadata in uv.lock without network resolution"
  run_uv lock --offline
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

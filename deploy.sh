#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./deploy.sh [--bump-patch] [--skip-tests]

Build local-llm-server distribution artifacts.

Options:
  --bump-patch   Increment the patch version in pyproject.toml before building.
  --skip-tests   Build without running pytest first.
  -h, --help     Show this help.
EOF
}

bump_patch=false
skip_tests=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bump-patch)
      bump_patch=true
      shift
      ;;
    --skip-tests)
      skip_tests=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

run_uv() {
  UV_CACHE_DIR="${UV_CACHE_DIR:-/private/tmp/local-llm-uv-cache}" uv "$@"
}

if [[ "$bump_patch" == true ]]; then
  current_version="$(python3 - <<'PY'
import re
from pathlib import Path

p = Path("pyproject.toml")
c = p.read_text(encoding="utf-8")
m = re.search(r'version\s*=\s*"([^"]+)"', c)
if not m:
    raise SystemExit("Could not find project version in pyproject.toml")

v = m.group(1)
parts = v.split(".")
if len(parts) != 3 or not all(part.isdigit() for part in parts):
    raise SystemExit(f"Expected semantic version X.Y.Z, found: {v}")

parts[-1] = str(int(parts[-1]) + 1)
nv = ".".join(parts)
p.write_text(c.replace(f'version = "{v}"', f'version = "{nv}"'), encoding="utf-8")
print(nv)
PY
)"
  echo "[*] Version bumped to: ${current_version}"
else
  current_version="$(python3 - <<'PY'
import re
from pathlib import Path

match = re.search(r'version\s*=\s*"([^"]+)"', Path("pyproject.toml").read_text(encoding="utf-8"))
print(match.group(1) if match else "unknown")
PY
)"
  echo "[*] Building version: ${current_version}"
fi

if [[ "$skip_tests" != true ]]; then
  echo "[*] Running tests"
  run_uv run pytest
fi

echo "[*] Cleaning previous build artifacts (retaining dist/)"
rm -rf build src/*.egg-info

echo "[*] Ensuring build backend is available"
run_uv pip install build setuptools wheel

echo "[*] Building sdist and wheel"
run_uv run python -m build --no-isolation

echo "[*] Verifying wheel contents"
VERSION="${current_version}" python3 - <<'PY'
import os
from pathlib import Path
from zipfile import ZipFile

version = os.environ.get("VERSION", "unknown")
normalized_version = version.replace("-", "_")
wheel = Path("dist") / f"local_llm_server-{normalized_version}-py3-none-any.whl"

if not wheel.exists():
    raise SystemExit(f"No wheel produced in dist/ for version {version} ({wheel})")

required = {
    "local_llm_server/audio.py",
    "local_llm_server/client.py",
    "local_llm_server/server.py",
    "local_llm_server/models_registry.yaml",
    "local_llm_server/static/index.html",
    "local_llm_server/static/app.js",
    "local_llm_server/static/components.js",
    "local_llm_server/static/config.js",
    "local_llm_server/static/styles.css",
}

with ZipFile(wheel) as zf:
    names = set(zf.namelist())

missing = sorted(required - names)
if missing:
    raise SystemExit("Wheel is missing required files:\n" + "\n".join(missing))

print(f"[*] Wheel verified: {wheel}")
PY

echo "[*] Build artifacts ready in dist/"

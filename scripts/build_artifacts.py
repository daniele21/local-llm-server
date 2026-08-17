#!/usr/bin/env python3
"""Build and promote uniquely identified local-llm-server distribution bundles.

The Python wheel/sdist filenames remain standards-compliant. Build identity lives in the
containing immutable bundle/directory plus build-manifest.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
import uuid
from zipfile import ZipFile

PRODUCT = "local-llm-server"
MANIFEST = "build-manifest.json"
CHANGELOG = "BUILD_CHANGELOG.md"
KEEP_SUCCESSFUL = 2


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, capture_output=True)


def project_version(root: Path) -> str:
    import tomllib

    with (root / "pyproject.toml").open("rb") as fh:
        return str(tomllib.load(fh)["project"]["version"])


def source_identity(root: Path) -> tuple[str, bool]:
    revision = run("git", "-C", str(root), "rev-parse", "--short=12", "HEAD").stdout.strip()
    dirty = bool(run("git", "-C", str(root), "status", "--porcelain", "--untracked-files=no").stdout.strip())
    return revision, dirty


def new_build_id(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


def safe_segment(value: str) -> str:
    normalized = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in value.strip())
    return normalized.strip("-") or "unknown"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_digest(root: Path, rel: str) -> str | None:
    path = root / rel
    return sha256_file(path) if path.is_file() else None


def verify_wheel(wheel: Path) -> None:
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
        raise RuntimeError("wheel is missing required files: " + ", ".join(missing))


def comparable_builds(lineage_dir: Path) -> list[Path]:
    if not lineage_dir.is_dir():
        return []
    candidates = [p for p in lineage_dir.iterdir() if p.is_dir() and (p / MANIFEST).is_file()]
    return sorted(candidates, key=lambda p: p.name)


def previous_manifest(lineage_dir: Path) -> dict | None:
    builds = comparable_builds(lineage_dir)
    if not builds:
        return None
    return json.loads((builds[-1] / MANIFEST).read_text(encoding="utf-8"))


def build_delta(current: dict, previous: dict | None) -> str:
    lines = ["# Build change log", ""]
    if previous is None:
        lines += ["No previous successful comparable local build is available.", ""]
    else:
        lines += [f"Compared with build `{previous.get('build_id', 'unknown')}`.", ""]
    dimensions = {
        "Source": (previous or {}).get("source", {}),
        "Dependencies": (previous or {}).get("dependencies", {}),
        "Toolchain": (previous or {}).get("toolchain", {}),
        "Configuration": (previous or {}).get("lineage", {}),
    }
    current_values = {
        "Source": current.get("source", {}),
        "Dependencies": current.get("dependencies", {}),
        "Toolchain": current.get("toolchain", {}),
        "Configuration": current.get("lineage", {}),
    }
    for title in ("Source", "Dependencies", "Toolchain", "Configuration"):
        changed = dimensions[title] != current_values[title]
        lines += [f"## {title}", "", "Changed." if changed and previous else "Unchanged or no prior baseline.", ""]
    lines += [
        "## Compatibility / migrations", "", "No compatibility migration is inferred automatically; release notes remain authoritative.", "",
        "## Artifact metrics", "", f"Files: {len(current.get('artifacts', []))}.", "",
        "## Validation", "", ", ".join(current.get("validation", [])) or "Build validation only.", "",
    ]
    return "\n".join(lines)


def promote(stage: Path, final: Path) -> None:
    if final.exists():
        raise FileExistsError(f"refusing to replace successful build: {final}")
    final.parent.mkdir(parents=True, exist_ok=True)
    stage.replace(final)


def enforce_retention(lineage_dir: Path, keep: int = KEEP_SUCCESSFUL) -> None:
    builds = comparable_builds(lineage_dir)
    for old in builds[:-keep]:
        shutil.rmtree(old)


def create_bundle(build_dir: Path, bundle_name: str) -> Path:
    bundle = build_dir / f"{bundle_name}.tar.gz"
    members = [p for p in build_dir.iterdir() if p.name != bundle.name]
    with tarfile.open(bundle, "w:gz") as tf:
        for path in sorted(members):
            tf.add(path, arcname=path.name)
    return bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-root", default="dist")
    parser.add_argument("--channel", default=os.environ.get("LOCAL_LLM_BUILD_CHANNEL", "local"))
    parser.add_argument("--variant", default=os.environ.get("LOCAL_LLM_BUILD_VARIANT", "wheel-sdist"))
    parser.add_argument("--skip-build", action="store_true", help="exercise metadata/promotion without invoking python -m build")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    output_root = (root / args.output_root).resolve()
    version = project_version(root)
    revision, dirty = source_identity(root)
    build_id = new_build_id()
    lineage = {
        "project": PRODUCT,
        "platform": safe_segment(sys.platform),
        "architecture": safe_segment(platform.machine()),
        "channel": safe_segment(args.channel),
        "variant": safe_segment(args.variant),
    }
    lineage_key = "--".join(lineage.values())
    lineage_dir = output_root / "builds" / lineage_key
    final_dir = lineage_dir / build_id
    previous = previous_manifest(lineage_dir)

    staging_root = output_root / ".staging"
    staging_root.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f"{build_id}-", dir=staging_root))

    try:
        package_dir = stage / "package"
        package_dir.mkdir()
        if not args.skip_build:
            subprocess.run([sys.executable, "-m", "build", "--outdir", str(package_dir)], cwd=root, check=True)
            wheels = sorted(package_dir.glob("*.whl"))
            if len(wheels) != 1:
                raise RuntimeError(f"expected one wheel, found {len(wheels)}")
            verify_wheel(wheels[0])

        artifacts = []
        for path in sorted(package_dir.iterdir()):
            if path.is_file():
                artifacts.append({"name": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)})

        manifest = {
            "schema_version": 1,
            "product": PRODUCT,
            "product_version": version,
            "build_id": build_id,
            "source": {"revision": revision, "dirty": dirty},
            "lineage": lineage,
            "dependencies": {
                "uv_lock_sha256": file_digest(root, "uv.lock"),
                "package_lock_sha256": file_digest(root, "package-lock.json"),
            },
            "toolchain": {"python": platform.python_version(), "implementation": platform.python_implementation()},
            "artifacts": artifacts,
            "validation": ["wheel-content-check"] if not args.skip_build else ["metadata-promotion-test"],
        }
        (stage / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (stage / CHANGELOG).write_text(build_delta(manifest, previous), encoding="utf-8")

        checksums = []
        for path in sorted(stage.rglob("*")):
            if path.is_file() and path.name != "SHA256SUMS":
                checksums.append(f"{sha256_file(path)}  {path.relative_to(stage).as_posix()}")
        (stage / "SHA256SUMS").write_text("\n".join(checksums) + "\n", encoding="utf-8")

        bundle_name = "-".join((PRODUCT, version, build_id, revision))
        create_bundle(stage, bundle_name)
        promote(stage, final_dir)
        enforce_retention(lineage_dir)
        print(final_dir)
        return 0
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


if __name__ == "__main__":
    raise SystemExit(main())

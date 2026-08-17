#!/usr/bin/env python3
"""Smoke-test one built wheel in a fresh lock-backed environment.

Hosted CI deliberately excludes llama-cpp-python because compiling the native
backend is not required to establish Python packaging/CLI integrity. All other
runtime packages are installed at the exact versions exported from uv.lock.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def _venv_python(root: Path) -> Path:
    candidate = root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not candidate.is_file():
        raise RuntimeError(f"fresh environment Python missing: {candidate}")
    return candidate


def _venv_command(root: Path, name: str) -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    candidate = root / ("Scripts" if os.name == "nt" else "bin") / f"{name}{suffix}"
    if not candidate.is_file():
        raise RuntimeError(f"installed command missing: {candidate}")
    return candidate


def _run(*args: str | Path) -> None:
    subprocess.run([str(arg) for arg in args], cwd=ROOT, check=True)


def _locked_runtime_requirements(target: Path) -> None:
    raw = target.with_suffix(".raw.txt")
    _run(
        "uv",
        "export",
        "--frozen",
        "--no-dev",
        "--no-emit-project",
        "--no-hashes",
        "--format",
        "requirements-txt",
        "--output-file",
        raw,
    )
    retained: list[str] = []
    excluded = 0
    for line in raw.read_text(encoding="utf-8").splitlines():
        if line.strip().lower().startswith("llama-cpp-python=="):
            excluded += 1
            continue
        retained.append(line)
    if excluded != 1:
        raise RuntimeError(
            f"expected exactly one locked llama-cpp-python requirement, found {excluded}"
        )
    target.write_text("\n".join(retained) + "\n", encoding="utf-8")


def smoke(wheel: Path, expected_version: str) -> None:
    wheel = wheel.resolve()
    if not wheel.is_file() or wheel.suffix != ".whl":
        raise ValueError(f"wheel does not exist: {wheel}")

    with tempfile.TemporaryDirectory(prefix="local-llm-install-smoke-") as raw_root:
        temp = Path(raw_root)
        env_root = temp / "venv"
        requirements = temp / "runtime-requirements.txt"
        _locked_runtime_requirements(requirements)
        _run("uv", "venv", env_root, "--python", sys.executable)
        python = _venv_python(env_root)
        _run(
            "uv", "pip", "install", "--python", python,
            "--no-deps", "--requirement", requirements,
        )
        _run("uv", "pip", "install", "--python", python, "--no-deps", wheel)
        _run(_venv_command(env_root, "local-llm"), "--help")

        code = """
import importlib.metadata as metadata
import importlib.resources as resources
import os
expected = os.environ['LOCAL_LLM_EXPECTED_VERSION']
version = metadata.version('local-llm-server')
assert version == expected, (version, expected)
root = resources.files('local_llm_server')
assert root.joinpath('models_registry.yaml').is_file()
assert root.joinpath('static/index.html').is_file()
eps = [ep for ep in metadata.entry_points(group='console_scripts') if ep.name == 'local-llm']
assert len(eps) == 1
print(f'installed artifact smoke passed for local-llm-server {version}')
"""
        subprocess.run(
            [str(python), "-c", code],
            cwd=temp,
            env={**os.environ, "LOCAL_LLM_EXPECTED_VERSION": expected_version},
            check=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--expected-version", required=True)
    args = parser.parse_args()
    smoke(args.wheel, args.expected_version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

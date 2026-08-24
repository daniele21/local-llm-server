from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _http_json(method: str, url: str, payload: dict[str, Any] | None, timeout: float) -> Any:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, method=method)
    request.add_header("Accept", "application/json")
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - loopback-only runner
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} returned HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{method} {url} returned non-JSON content") from exc


def _redacted_command(command: list[str], model_path: Path) -> list[str]:
    secret = str(model_path)
    return ["<MODEL_PATH>" if part == secret else part for part in command]


def _run_command(
    *,
    name: str,
    command: list[str],
    output_dir: Path,
    model_path: Path,
    env: dict[str, str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "name": name,
        "command": _redacted_command(command, model_path),
        "status": "planned" if dry_run else "running",
    }
    if dry_run:
        return record

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    stdout_path = output_dir / f"{name}.stdout.txt"
    stderr_path = output_dir / f"{name}.stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    record.update(
        {
            "returncode": completed.returncode,
            "status": "passed" if completed.returncode == 0 else "failed",
            "stdout": stdout_path.name,
            "stderr": stderr_path.name,
        }
    )
    return record


def _wait_for_server(base_url: str, process: subprocess.Popen[str], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    last_error = "not ready"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Local LLM Server exited during startup with code {process.returncode}")
        try:
            _http_json("GET", f"{base_url}/v1/models", None, timeout=5.0)
            return
        except RuntimeError as exc:
            last_error = str(exc)
            time.sleep(2.0)
    raise RuntimeError(f"Local LLM Server did not become ready: {last_error}")


def _http_step(
    *,
    name: str,
    method: str,
    url: str,
    payload: dict[str, Any] | None,
    output_dir: Path,
    timeout: float,
    dry_run: bool,
) -> dict[str, Any]:
    if dry_run:
        return {"name": name, "method": method, "url": url, "status": "planned"}
    try:
        response = _http_json(method, url, payload, timeout)
        _write_json(output_dir / f"{name}.json", response)
        return {"name": name, "status": "passed", "output": f"{name}.json"}
    except RuntimeError as exc:
        _write_json(output_dir / f"{name}.error.json", {"error": str(exc)})
        return {"name": name, "status": "failed", "error": str(exc)}


def _summarize_files(output_dir: Path) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "evidence-manifest.json":
            files.append(
                {
                    "path": str(path.relative_to(output_dir)),
                    "bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
            )
    return files


def _discover_performance_lab(explicit: Path | None) -> Path | None:
    if explicit is not None:
        return explicit.expanduser().resolve()
    sibling = Path.cwd().resolve().parent / "performance-lab"
    return sibling if sibling.exists() else None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the representative Mac evidence wave serially: artifact verification, TH-E1, "
            "EV-3, Performance Lab real-runtime smoke, HE-2 and RES-2."
        )
    )
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-path", required=True, type=Path)
    parser.add_argument("--backend", default="llama_cpp", choices=["llama_cpp"])
    parser.add_argument("--port", type=int, default=1235)
    parser.add_argument("--startup-timeout-seconds", type=float, default=900.0)
    parser.add_argument("--request-timeout-seconds", type=float, default=1800.0)
    parser.add_argument("--performance-lab-repo", type=Path, default=None)
    parser.add_argument("--performance-lab-python", default=sys.executable)
    parser.add_argument("--skip-performance-lab", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=None)
    return parser


def main() -> int:
    args = _parser().parse_args()
    model_path = args.model_path.expanduser().resolve()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir is not None
        else (Path.home() / ".local-llm-server" / "evidence" / f"representative-{timestamp}")
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    base_url = f"http://127.0.0.1:{args.port}"
    performance_lab_repo = _discover_performance_lab(args.performance_lab_repo)

    if not args.dry_run:
        if platform.system() != "Darwin":
            raise SystemExit("Representative acceptance is Mac-only; use --dry-run elsewhere.")
        if not model_path.is_file():
            raise SystemExit(f"Model file does not exist: {model_path}")
        if not args.skip_performance_lab:
            if performance_lab_repo is None:
                raise SystemExit("Performance Lab repo not found; pass --performance-lab-repo.")
            smoke = performance_lab_repo / "tests" / "real_runtime" / "smoke_local_llm_server.py"
            if not smoke.is_file():
                raise SystemExit(f"Performance Lab real-runtime smoke not found: {smoke}")

    steps: list[dict[str, Any]] = []
    python = sys.executable
    verification = [
        python,
        "-m",
        "local_llm_server.cli",
        "verify-artifact",
        args.model,
        "--model-path",
        str(model_path),
    ]
    steps.append(
        _run_command(
            name="artifact-verification",
            command=verification,
            output_dir=output_dir,
            model_path=model_path,
            dry_run=args.dry_run,
        )
    )

    server_command = [
        python,
        "-m",
        "local_llm_server.cli",
        "serve",
        "--model",
        args.model,
        "--model-path",
        str(model_path),
        "--backend",
        args.backend,
        "--host",
        "127.0.0.1",
        "--port",
        str(args.port),
        "--startup-timeout",
        str(int(args.startup_timeout_seconds)),
        "--enable-admin-api",
        "--no-download",
    ]

    server_ready = args.dry_run
    if args.dry_run:
        steps.append(
            {
                "name": "server",
                "status": "planned",
                "command": _redacted_command(server_command, model_path),
            }
        )
        server_process = None
        server_log = None
    else:
        server_log_path = output_dir / "local-llm-server.log"
        server_log = server_log_path.open("w", encoding="utf-8")
        server_process = subprocess.Popen(
            server_command,
            stdout=server_log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            _wait_for_server(base_url, server_process, args.startup_timeout_seconds)
            server_ready = True
            steps.append({"name": "server", "status": "passed", "log": server_log_path.name})
        except RuntimeError as exc:
            steps.append({"name": "server", "status": "failed", "error": str(exc)})

    try:
        if server_ready:
            steps.append(
                _http_step(
                    name="runtime-identity",
                    method="GET",
                    url=f"{base_url}/v1/runtime/identity",
                    payload=None,
                    output_dir=output_dir,
                    timeout=30.0,
                    dry_run=args.dry_run,
                )
            )
            steps.append(
                _http_step(
                    name="status-before",
                    method="GET",
                    url=f"{base_url}/status",
                    payload=None,
                    output_dir=output_dir,
                    timeout=30.0,
                    dry_run=args.dry_run,
                )
            )

            prompt = "Reply with a concise explanation of why local inference can improve privacy."
            common = {
                "model": args.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "show_thinking": False,
                "stream": False,
            }
            for name, enable in (("thinking-off-response", False), ("thinking-on-hidden-response", True)):
                payload = dict(common)
                payload["enable_thinking"] = enable
                steps.append(
                    _http_step(
                        name=name,
                        method="POST",
                        url=f"{base_url}/v1/chat/completions",
                        payload=payload,
                        output_dir=output_dir,
                        timeout=args.request_timeout_seconds,
                        dry_run=args.dry_run,
                    )
                )

            eval_payload = {
                "model": args.model,
                "test_set_id": "general-purpose",
                "test_set_version": "1.0.0",
                "sample_count": 10,
                "seed": 0,
                "reasoning_policy": "off",
            }
            for name in ("evaluation-off-a", "evaluation-off-b"):
                steps.append(
                    _http_step(
                        name=name,
                        method="POST",
                        url=f"{base_url}/api/v1/evaluation/runs",
                        payload=eval_payload,
                        output_dir=output_dir,
                        timeout=args.request_timeout_seconds,
                        dry_run=args.dry_run,
                    )
                )

            if not args.skip_performance_lab:
                if performance_lab_repo is None:
                    steps.append(
                        {
                            "name": "performance-lab-real-smoke",
                            "status": "planned" if args.dry_run else "failed",
                            "error": "Performance Lab repo not resolved",
                        }
                    )
                else:
                    smoke = performance_lab_repo / "tests" / "real_runtime" / "smoke_local_llm_server.py"
                    pl_output = output_dir / "performance-lab"
                    pl_output.mkdir(parents=True, exist_ok=True)
                    env = os.environ.copy()
                    existing = env.get("PYTHONPATH")
                    env["PYTHONPATH"] = (
                        str(performance_lab_repo / "src")
                        if not existing
                        else f"{performance_lab_repo / 'src'}{os.pathsep}{existing}"
                    )
                    pl_command = [
                        args.performance_lab_python,
                        str(smoke),
                        "--base-url",
                        base_url,
                        "--model",
                        args.model,
                        "--output-dir",
                        str(pl_output),
                    ]
                    steps.append(
                        _run_command(
                            name="performance-lab-real-smoke",
                            command=pl_command,
                            output_dir=output_dir,
                            model_path=model_path,
                            env=env,
                            dry_run=args.dry_run,
                        )
                    )

            steps.append(
                _http_step(
                    name="status-after-pl",
                    method="GET",
                    url=f"{base_url}/status",
                    payload=None,
                    output_dir=output_dir,
                    timeout=30.0,
                    dry_run=args.dry_run,
                )
            )
    finally:
        shutdown_record: dict[str, Any] = {"name": "server-shutdown", "status": "planned"}
        if not args.dry_run and server_process is not None:
            graceful = False
            if server_process.poll() is None:
                server_process.send_signal(signal.SIGINT)
                try:
                    server_process.wait(timeout=30.0)
                    graceful = True
                except subprocess.TimeoutExpired:
                    server_process.terminate()
                    try:
                        server_process.wait(timeout=10.0)
                    except subprocess.TimeoutExpired:
                        server_process.kill()
                        server_process.wait(timeout=10.0)
            else:
                graceful = server_process.returncode == 0
            shutdown_record = {
                "name": "server-shutdown",
                "status": "passed" if graceful else "failed",
                "graceful": graceful,
                "returncode": server_process.returncode,
            }
        steps.append(shutdown_record)
        if server_log is not None:
            server_log.close()

    reclamation_a = output_dir / "reclamation-a.json"
    reclamation_b = output_dir / "reclamation-b.json"
    for name, destination in (("reclamation-a", reclamation_a), ("reclamation-b", reclamation_b)):
        command = [
            python,
            "-m",
            "local_llm_server.cli",
            "evidence-reclamation",
            "--model",
            args.model,
            "--model-path",
            str(model_path),
            "--backend",
            args.backend,
            "--cycles",
            "3",
            "--max-tokens",
            "32",
            "--settle-seconds",
            "2",
            "--no-download",
            "--output",
            str(destination),
        ]
        steps.append(
            _run_command(
                name=name,
                command=command,
                output_dir=output_dir,
                model_path=model_path,
                dry_run=args.dry_run,
            )
        )

    review_command = [
        python,
        "-m",
        "local_llm_server.cli",
        "evidence-review",
        str(reclamation_a),
        str(reclamation_b),
        "--min-reports",
        "2",
        "--min-complete-cycles",
        "6",
        "--output",
        str(output_dir / "reclamation-review.json"),
    ]
    steps.append(
        _run_command(
            name="reclamation-review",
            command=review_command,
            output_dir=output_dir,
            model_path=model_path,
            dry_run=args.dry_run,
        )
    )

    resource_command = [
        python,
        "-m",
        "local_llm_server.resource_policy_smoke",
        "--model",
        args.model,
        "--model-path",
        str(model_path),
        "--backend",
        args.backend,
        "--max-tokens",
        "8",
        "--headroom-gib",
        "0.5",
        "--success-margin-gib",
        "0.5",
        "--host-safety-gib",
        "2.0",
        "--output",
        str(output_dir / "resource-policy-smoke.json"),
    ]
    steps.append(
        _run_command(
            name="resource-policy-smoke",
            command=resource_command,
            output_dir=output_dir,
            model_path=model_path,
            dry_run=args.dry_run,
        )
    )

    failed = [step["name"] for step in steps if step.get("status") == "failed"]
    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "model": args.model,
        "backend": args.backend,
        "base_url": base_url,
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "steps": steps,
        "failed_steps": failed,
        "files": [] if args.dry_run else _summarize_files(output_dir),
        "notes": [
            "Model path is intentionally omitted from the manifest.",
            "Keep the evidence directory local; it may contain prompts/model outputs.",
            "Do not generalize one-device or ten-sample observations into production claims.",
        ],
    }
    _write_json(output_dir / "evidence-manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

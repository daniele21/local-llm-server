"""One-shot representative Apple Silicon evidence campaign.

The campaign orchestrates the repository's existing real-device evidence owners. It
never weakens their thresholds, never enables automatic eviction, and never treats an
unsafe or incomplete environment as a successful hardware claim.

Private model paths and inference content may exist only in machine-local source
artifacts/logs. The campaign summary is bounded and path/content-free.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import signal
import socket
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .artifact_verification import public_verification_summary, verify_model_artifact
from .evaluation_history import compare_run_summaries, summarize_report_payload
from .hardware_evidence import HardwareEvidenceOptions, execute_hardware_reclamation_evidence
from .hardware_evidence_review import EvidenceReviewSettings, review_hardware_evidence
from .l2_evidence_bridge import capture_thinking_campaign, validate_hardware_bundle
from .multi_model_device_evidence import MultiModelDeviceEvidenceOptions, execute_multi_model_device_evidence
from .multi_model_evidence_review import (
    MultiModelReviewSettings,
    MultiModelReviewState,
    review_multi_model_evidence,
)
from .resource_policy_smoke import ResourcePolicySmokeOptions, execute_resource_policy_smoke
from .resources_macos import MacOSResourceObserver

_MIB = 1024**2
_GIB = 1024**3
_PASS = "PASS"
_FAIL = "FAIL"
_INCONCLUSIVE = "INCONCLUSIVE"
_SKIPPED = "SKIPPED"


class CampaignError(RuntimeError):
    """Raised for a campaign orchestration failure, not a product evidence verdict."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    return Path.home() / ".local-llm-server" / "evidence" / f"{stamp}-device-campaign"


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    target = path.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".tmp")
    temp.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temp.replace(target)
    return target


def _phase(
    status: str,
    *,
    reason: str,
    checks: Mapping[str, Any] | None = None,
    artifact: str | None = None,
    duration_seconds: float | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": status,
        "reason": reason,
        "checks": dict(checks or {}),
    }
    if artifact is not None:
        result["artifact"] = artifact
    if duration_seconds is not None:
        result["duration_seconds"] = round(duration_seconds, 3)
    return result


def _safe_exception_text(exc: BaseException) -> str:
    """Return a bounded error class/reason without serializing private paths."""
    text = str(exc).strip().replace("\n", " ")
    lowered = text.lower()
    if any(token in lowered for token in ("/users/", "/home/", "file://")) or "/" in text or "\\" in text:
        text = exc.__class__.__name__
    if len(text) > 220:
        text = text[:217] + "..."
    return text or exc.__class__.__name__


def _git_command(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=5.0,
    )
    if completed.returncode != 0:
        raise CampaignError("git source identity is unavailable")
    return completed.stdout.strip()


def _git_state() -> dict[str, Any]:
    return {
        "revision": _git_command("rev-parse", "HEAD"),
        "branch": _git_command("branch", "--show-current"),
        "tracked_clean": not bool(_git_command("status", "--porcelain", "--untracked-files=no")),
    }


def _snapshot_to_public(snapshot: Any) -> dict[str, Any]:
    def encode(value: Any) -> dict[str, Any]:
        return {
            "value": getattr(value, "value", None),
            "source": str(
                getattr(
                    getattr(value, "source", None),
                    "value",
                    getattr(value, "source", "unavailable"),
                )
            ),
            "unit": getattr(value, "unit", None),
        }

    return {
        "platform": getattr(snapshot, "platform", "unknown"),
        "total_memory_bytes": encode(getattr(snapshot, "total_memory_bytes", None)),
        "available_memory_bytes": encode(getattr(snapshot, "available_memory_bytes", None)),
        "process_rss_bytes": encode(getattr(snapshot, "process_rss_bytes", None)),
    }


def _port_is_free(host: str, port: int) -> bool:
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
    except OSError:
        return False
    finally:
        sock.close()
    return True


def _listener_closed(host: str, port: int) -> bool:
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex((host, port)) != 0:
                return True
        time.sleep(0.1)
    return False


def _request_json(
    url: str,
    *,
    method: str = "GET",
    payload: Mapping[str, Any] | None = None,
    timeout: float = 300.0,
) -> tuple[int, Mapping[str, Any]]:
    data = None
    headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - loopback campaign endpoint
            status = int(getattr(response, "status", 200))
            raw = response.read()
    except HTTPError as exc:
        status = int(exc.code)
        raw = exc.read()
    except URLError as exc:
        raise CampaignError(f"loopback request failed: {exc.reason}") from exc
    try:
        decoded = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CampaignError(f"loopback response was not JSON (status {status})") from exc
    if not isinstance(decoded, Mapping):
        raise CampaignError(f"loopback response was not an object (status {status})")
    return status, decoded


class _OwnedServer:
    """Own the temporary representative HTTP server and its process group."""

    def __init__(
        self,
        *,
        model: str,
        model_path: str | None,
        backend: str | None,
        host: str,
        port: int,
        output_dir: Path,
        startup_timeout: float,
    ) -> None:
        self.model = model
        self.model_path = model_path
        self.backend = backend
        self.host = host
        self.port = port
        self.output_dir = output_dir
        self.startup_timeout = startup_timeout
        self.process: subprocess.Popen[str] | None = None
        self._log_handle: Any | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self) -> None:
        if not _port_is_free(self.host, self.port):
            raise CampaignError("representative HTTP port is already in use")
        command = [
            sys.executable,
            "-m",
            "local_llm_server",
            "serve",
            "--model",
            self.model,
            "--host",
            self.host,
            "--port",
            str(self.port),
            "--enable-admin-api",
            "--no-download",
        ]
        if self.model_path is not None:
            command.extend(["--model-path", self.model_path])
        if self.backend is not None:
            command.extend(["--backend", self.backend])
        log_path = self.output_dir / "representative-server.log"
        self._log_handle = log_path.open("w", encoding="utf-8")
        self.process = subprocess.Popen(
            command,
            stdout=self._log_handle,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        deadline = time.monotonic() + self.startup_timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise CampaignError("representative server exited before readiness")
            try:
                status, payload = _request_json(f"{self.base_url}/health", timeout=2.0)
            except CampaignError:
                time.sleep(0.5)
                continue
            if status == 200 and payload.get("ok") is True:
                return
            time.sleep(0.5)
        raise CampaignError("representative server readiness timed out")

    def stop(self) -> dict[str, Any]:
        process = self.process
        if process is None:
            return {"owned_process_started": False, "graceful": True, "listener_closed": True}
        graceful = True
        hard_kill = False
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGINT)
                process.wait(timeout=20.0)
            except subprocess.TimeoutExpired:
                graceful = False
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    hard_kill = True
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5.0)
            except ProcessLookupError:
                pass
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None
        return {
            "owned_process_started": True,
            "exit_code": process.returncode,
            "graceful": graceful,
            "hard_kill_required": hard_kill,
            "listener_closed": _listener_closed(self.host, self.port),
            "diagnostic_log_retained_locally": True,
        }


class DeviceEvidenceCampaign:
    """Run the minimum L2 bundle and optional/full RRG-5 evidence in one command."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.output_dir = Path(args.output_dir).expanduser() if args.output_dir else _default_output_dir()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.summary_path = self.output_dir / "campaign-summary.json"
        self.summary: dict[str, Any] = {
            "schema_version": 1,
            "procedure": "representative_device_campaign_v1",
            "started_at": _utc_now(),
            "completed_at": None,
            "scope": args.scope,
            "models": {
                "primary": args.model_a,
                "secondary": args.model_b if args.scope == "full" else None,
            },
            "source": {},
            "environment": {},
            "phases": {},
            "minimum_l2_complete": False,
            "rrg5_complete": None if args.scope == "minimum-l2" else False,
            "complete": False,
            "automatic_eviction_exercised": False,
            "reclamation_safety_claim": False,
            "production_safety_claim": False,
            "privacy": {
                "model_paths_retained_in_summary": False,
                "prompt_or_output_retained_in_summary": False,
                "process_ids_retained_in_summary": False,
                "local_source_artifacts_may_contain_private_content": True,
            },
        }
        self._persist()

    def _persist(self) -> None:
        _atomic_write_json(self.summary_path, self.summary)

    def _record(self, name: str, result: Mapping[str, Any]) -> None:
        self.summary["phases"][name] = dict(result)
        self._persist()

    def _run_phase(self, name: str, function: Any) -> dict[str, Any]:
        started = time.monotonic()
        try:
            result = dict(function())
        except Exception as exc:  # noqa: BLE001 - campaign must retain failure state
            result = _phase(
                _FAIL,
                reason=_safe_exception_text(exc),
                duration_seconds=time.monotonic() - started,
            )
        else:
            result["duration_seconds"] = round(time.monotonic() - started, 3)
        self._record(name, result)
        return result

    def run(self) -> int:
        preflight = self._run_phase("preflight", self._preflight)
        if preflight["status"] != _PASS:
            return self._finalize()

        verify_primary = self._run_phase("verify_primary_artifact", self._verify_primary)
        if verify_primary["status"] != _PASS:
            return self._finalize()

        if self.args.scope == "full":
            verify_secondary = self._run_phase("verify_secondary_artifact", self._verify_secondary)
            if verify_secondary["status"] != _PASS:
                return self._finalize()
        else:
            self._record(
                "verify_secondary_artifact",
                _phase(_SKIPPED, reason="minimum-l2 scope does not require a second model"),
            )

        server = _OwnedServer(
            model=self.args.model_a,
            model_path=self.args.model_a_path,
            backend=self.args.backend,
            host=self.args.host,
            port=self.args.port,
            output_dir=self.output_dir,
            startup_timeout=self.args.startup_timeout,
        )
        server_cleanup_recorded = False
        try:
            start_result = self._run_phase("start_representative_server", lambda: self._start_server(server))
            if start_result["status"] == _PASS:
                self._run_phase("thinking_th_e1", lambda: self._thinking(server.base_url))
                self._run_phase("evaluation_ev_3", lambda: self._evaluation(server.base_url))
            else:
                self._record("thinking_th_e1", _phase(_SKIPPED, reason="representative server was not ready"))
                self._record("evaluation_ev_3", _phase(_SKIPPED, reason="representative server was not ready"))
            self._run_phase("stop_representative_server", lambda: self._stop_server(server))
            server_cleanup_recorded = True
        finally:
            if not server_cleanup_recorded:
                self._run_phase("stop_representative_server", lambda: self._stop_server(server))

        self._run_phase("reclamation_he_2", self._reclamation)
        self._run_phase("resource_policy_res_2", self._resource_policy)
        self._run_phase("validate_minimum_l2_bundle", self._validate_l2_bundle)

        if self.args.scope == "full":
            self._run_phase("multimodel_rrg_5", self._rrg5)
        else:
            self._record(
                "multimodel_rrg_5",
                _phase(_SKIPPED, reason="minimum-l2 scope explicitly excludes RRG-5"),
            )

        return self._finalize()

    def _preflight(self) -> Mapping[str, Any]:
        git = _git_state()
        snapshot = MacOSResourceObserver().snapshot() if platform.system().lower() == "darwin" else None
        system = platform.system().lower()
        machine = platform.machine().lower()
        architecture_ok = machine in {"arm64", "aarch64"}
        full_inputs_ok = True
        if self.args.scope == "full":
            full_inputs_ok = bool(
                self.args.model_b
                and self.args.model_b != self.args.model_a
                and self.args.request_estimate_mib is not None
                and self.args.request_estimate_mib > 0
            )
        port_free = _port_is_free(self.args.host, self.args.port)
        checks = {
            "macos": system == "darwin",
            "apple_silicon": architecture_ok,
            "git_branch_dev": git["branch"] == "dev",
            "tracked_tree_clean": git["tracked_clean"] is True,
            "full_scope_inputs": full_inputs_ok,
            "representative_port_free": port_free,
        }
        self.summary["source"] = git
        self.summary["environment"] = {
            "system": system,
            "release": platform.release(),
            "machine": machine,
            "python_version": platform.python_version(),
            "package_version": self._package_version(),
            "memory_before": _snapshot_to_public(snapshot) if snapshot is not None else None,
        }
        self._persist()
        if not checks["macos"] or not checks["apple_silicon"]:
            return _phase(
                _INCONCLUSIVE,
                reason="representative Apple Silicon macOS environment is required",
                checks=checks,
            )
        if not checks["git_branch_dev"] or not checks["tracked_tree_clean"]:
            return _phase(
                _INCONCLUSIVE,
                reason="run from a clean converged dev checkout so source identity is attributable",
                checks=checks,
            )
        if not full_inputs_ok:
            return _phase(
                _INCONCLUSIVE,
                reason="full scope requires a distinct second model and positive request estimate",
                checks=checks,
            )
        if not port_free:
            return _phase(
                _INCONCLUSIVE,
                reason="configured loopback port is already owned by another process",
                checks=checks,
            )
        return _phase(_PASS, reason="representative host and source preconditions satisfied", checks=checks)

    @staticmethod
    def _package_version() -> str | None:
        try:
            return metadata.version("local-llm-server")
        except metadata.PackageNotFoundError:
            return None

    def _verify_primary(self) -> Mapping[str, Any]:
        receipt = verify_model_artifact(self.args.model_a, model_path=self.args.model_a_path)
        return self._verification_phase(receipt, "primary")

    def _verify_secondary(self) -> Mapping[str, Any]:
        receipt = verify_model_artifact(self.args.model_b, model_path=self.args.model_b_path)
        return self._verification_phase(receipt, "secondary")

    @staticmethod
    def _verification_phase(receipt: Any, label: str) -> Mapping[str, Any]:
        public = public_verification_summary(receipt)
        checks = {
            "verification": public.get("verification"),
            "sha256_present": isinstance(public.get("sha256"), str) and len(public.get("sha256", "")) == 64,
            "size_bytes_positive": isinstance(public.get("size_bytes"), int) and public.get("size_bytes", 0) > 0,
        }
        ok = checks["sha256_present"] and checks["size_bytes_positive"]
        return _phase(
            _PASS if ok else _FAIL,
            reason=f"{label} artifact verified" if ok else f"{label} artifact verification incomplete",
            checks=checks,
        )

    @staticmethod
    def _start_server(server: _OwnedServer) -> Mapping[str, Any]:
        server.start()
        return _phase(
            _PASS,
            reason="owned representative server reached healthy readiness",
            checks={"health_ready": True, "owned_process": True},
            artifact="representative-server.log",
        )

    @staticmethod
    def _stop_server(server: _OwnedServer) -> Mapping[str, Any]:
        checks = server.stop()
        ok = bool(checks.get("listener_closed")) and not bool(checks.get("hard_kill_required"))
        return _phase(
            _PASS if ok else _FAIL,
            reason="owned server stopped and listener closed" if ok else "owned server cleanup was not fully graceful",
            checks=checks,
            artifact="representative-server.log",
        )

    def _thinking(self, base_url: str) -> Mapping[str, Any]:
        filename = "thinking-campaign.json"
        report = capture_thinking_campaign(
            base_url=base_url,
            model=self.args.model_a,
            output=self.output_dir / filename,
            timeout=self.args.request_timeout,
        )
        ok = report.get("complete") is True
        return _phase(
            _PASS if ok else _FAIL,
            reason="explicit thinking OFF/ON-hidden contract satisfied" if ok else "thinking campaign did not satisfy the bounded contract",
            checks={
                "complete": ok,
                "off_completed": report.get("off", {}).get("completed") if isinstance(report.get("off"), Mapping) else None,
                "on_hidden_completed": report.get("on_hidden", {}).get("completed") if isinstance(report.get("on_hidden"), Mapping) else None,
            },
            artifact=filename,
        )

    def _evaluation(self, base_url: str) -> Mapping[str, Any]:
        request = {
            "model": self.args.model_a,
            "test_set_id": "general-purpose",
            "test_set_version": "1.0.0",
            "sample_count": 10,
            "seed": 0,
            "reasoning_policy": "off",
        }
        status_a, report_a = _request_json(
            f"{base_url}/api/v1/evaluation/runs",
            method="POST",
            payload=request,
            timeout=self.args.evaluation_timeout,
        )
        _atomic_write_json(self.output_dir / "evaluation-off-a.json", report_a)
        status_b, report_b = _request_json(
            f"{base_url}/api/v1/evaluation/runs",
            method="POST",
            payload=request,
            timeout=self.args.evaluation_timeout,
        )
        _atomic_write_json(self.output_dir / "evaluation-off-b.json", report_b)
        comparable = False
        attribution_safe = False
        evidence_grade = False
        sample_count_ok = False
        try:
            summary_a = summarize_report_payload(report_a)
            summary_b = summarize_report_payload(report_b)
            comparison = compare_run_summaries(summary_a, summary_b)
            comparable = bool(comparison.comparable)
            attribution_safe = bool(comparison.attribution_safe)
            evidence_grade = bool(comparison.evidence_grade)
            sample_count_ok = summary_a.sample_count == 10 and summary_b.sample_count == 10
        except ValueError:
            pass
        checks = {
            "run_a_http_status": status_a,
            "run_b_http_status": status_b,
            "run_a_complete": report_a.get("complete") is True,
            "run_b_complete": report_b.get("complete") is True,
            "comparable": comparable,
            "attribution_safe": attribution_safe,
            "evidence_grade": evidence_grade,
            "sample_count_10_each": sample_count_ok,
        }
        ok = bool(
            status_a == 200
            and status_b == 200
            and checks["run_a_complete"]
            and checks["run_b_complete"]
            and comparable
            and attribution_safe
            and evidence_grade
            and sample_count_ok
        )
        return _phase(
            _PASS if ok else _FAIL,
            reason="two comparable verified OFF evaluations completed" if ok else "evaluation repeatability/attribution contract was not satisfied",
            checks=checks,
            artifact="evaluation-off-a.json,evaluation-off-b.json",
        )

    def _reclamation(self) -> Mapping[str, Any]:
        reports: list[Mapping[str, Any]] = []
        for suffix in ("a", "b"):
            report = execute_hardware_reclamation_evidence(
                HardwareEvidenceOptions(
                    model=self.args.model_a,
                    model_path=self.args.model_a_path,
                    backend=self.args.backend,
                    cycles=3,
                    max_tokens=32,
                    settle_seconds=2.0,
                    no_download=True,
                )
            )
            reports.append(report)
            _atomic_write_json(self.output_dir / f"reclamation-{suffix}.json", report)
        review = review_hardware_evidence(
            reports,
            settings=EvidenceReviewSettings(
                min_reports=2,
                min_complete_cycles=6,
                require_verified_identity=True,
                require_zero_error_cycles=True,
            ),
        ).to_public_dict()
        _atomic_write_json(self.output_dir / "reclamation-review.json", review)
        checks = {
            "report_count": review.get("report_count"),
            "compatible_report_count": review.get("compatible_report_count"),
            "complete_windows": review.get("complete_windows"),
            "error_cycles": review.get("error_cycles"),
            "automatic_eviction_recommendation": review.get("automatic_eviction_recommendation"),
            "production_safety_claim": review.get("production_safety_claim"),
            "state": review.get("state"),
        }
        ok = bool(
            review.get("report_count") == 2
            and review.get("compatible_report_count") == 2
            and isinstance(review.get("complete_windows"), int)
            and review.get("complete_windows", 0) >= 6
            and review.get("error_cycles") == 0
            and review.get("automatic_eviction_recommendation") == "not_provided"
            and review.get("production_safety_claim") is False
        )
        return _phase(
            _PASS if ok else _INCONCLUSIVE,
            reason="two compatible verified reclamation reports completed" if ok else "reclamation observation set is not acceptance-ready; raw observations are retained",
            checks=checks,
            artifact="reclamation-a.json,reclamation-b.json,reclamation-review.json",
        )

    def _resource_policy(self) -> Mapping[str, Any]:
        report = execute_resource_policy_smoke(
            ResourcePolicySmokeOptions(
                model=self.args.model_a,
                model_path=self.args.model_a_path,
                backend=self.args.backend,
                max_tokens=8,
                headroom_bytes=int(0.5 * _GIB),
                success_margin_bytes=int(0.5 * _GIB),
                host_safety_bytes=2 * _GIB,
            )
        )
        _atomic_write_json(self.output_dir / "resource-policy-smoke.json", report)
        success = report.get("success") if isinstance(report.get("success"), Mapping) else {}
        rejection = report.get("rejection") if isinstance(report.get("rejection"), Mapping) else {}
        checks = {
            "admission": success.get("admission"),
            "inference_http_status": success.get("inference_http_status"),
            "committed_bytes_positive": isinstance(success.get("committed_bytes"), int) and success.get("committed_bytes", 0) > 0,
            "committed_after_unload_zero": success.get("committed_bytes_after_unload") == 0,
            "reserved_after_unload_zero": success.get("reserved_bytes_after_unload") == 0,
            "health_after_unload_cold": success.get("health_ok_after_unload") is True and success.get("health_state_after_unload") == "cold",
            "insufficient_budget_rejected": rejection.get("admission") == "reject",
            "rejected_before_backend_load": rejection.get("backend_load_reached") is False,
            "automatic_eviction_exercised": report.get("automatic_eviction_exercised"),
        }
        ok = bool(
            success.get("admission") == "admit"
            and success.get("inference_http_status") == 200
            and checks["committed_bytes_positive"]
            and checks["committed_after_unload_zero"]
            and checks["reserved_after_unload_zero"]
            and checks["health_after_unload_cold"]
            and checks["insufficient_budget_rejected"]
            and checks["rejected_before_backend_load"]
            and report.get("automatic_eviction_exercised") is False
        )
        return _phase(
            _PASS if ok else _FAIL,
            reason="bounded resource admission/accounting/release/rejection contract satisfied" if ok else "resource-policy smoke violated an expected invariant",
            checks=checks,
            artifact="resource-policy-smoke.json",
        )

    def _validate_l2_bundle(self) -> Mapping[str, Any]:
        summary = validate_hardware_bundle(self.output_dir)
        _atomic_write_json(self.output_dir / "l2-device-bundle-summary.json", summary)
        complete = summary.get("complete") is True
        self.summary["minimum_l2_complete"] = complete
        self._persist()
        return _phase(
            _PASS if complete else _FAIL,
            reason="minimum L2 representative-device bundle is acceptance-ready" if complete else "minimum L2 representative-device bundle is incomplete or incompatible",
            checks={"complete": complete, "gates": summary.get("gates"), "errors": summary.get("errors")},
            artifact="l2-device-bundle-summary.json",
        )

    def _rrg5(self) -> Mapping[str, Any]:
        request_estimate_bytes = int(float(self.args.request_estimate_mib) * _MIB)
        reports: list[Mapping[str, Any]] = []
        safety_refused = False
        for suffix in ("a", "b"):
            report = execute_multi_model_device_evidence(
                MultiModelDeviceEvidenceOptions(
                    model_a=self.args.model_a,
                    model_b=self.args.model_b,
                    model_a_path=self.args.model_a_path,
                    model_b_path=self.args.model_b_path,
                    backend=self.args.multi_model_backend,
                    request_estimate_bytes=request_estimate_bytes,
                    cycles=2,
                    max_tokens=8,
                    headroom_bytes=int(0.5 * _GIB),
                    success_margin_bytes=int(0.5 * _GIB),
                    host_safety_bytes=2 * _GIB,
                    settle_seconds=2.0,
                )
            )
            reports.append(report)
            _atomic_write_json(self.output_dir / f"multimodel-{suffix}.json", report)
            safety_refused = safety_refused or report.get("status") == "refused_host_safety"
        review = review_multi_model_evidence(
            reports,
            settings=MultiModelReviewSettings(min_reports=2, min_complete_cycles=4),
        ).to_public_dict()
        _atomic_write_json(self.output_dir / "multimodel-review.json", review)
        complete = review.get("state") == MultiModelReviewState.SUFFICIENT_OBSERVATION_SET.value
        self.summary["rrg5_complete"] = complete
        self._persist()
        checks = {
            "report_a_complete": reports[0].get("complete") is True,
            "report_b_complete": reports[1].get("complete") is True,
            "review_state": review.get("state"),
            "complete_cycles": review.get("complete_cycles"),
            "transient_overlap_cycles": review.get("transient_overlap_cycles"),
            "clean_accounting_cycles": review.get("clean_accounting_cycles"),
            "shutdown_complete_reports": review.get("shutdown_complete_reports"),
            "automatic_eviction_recommendation": review.get("automatic_eviction_recommendation"),
            "reclamation_safety_claim": review.get("reclamation_safety_claim"),
            "host_safety_refused": safety_refused,
        }
        if safety_refused:
            status = _INCONCLUSIVE
            reason = "RRG-5 refused before backend construction because host-memory safety margin was not available"
        elif complete:
            status = _PASS
            reason = "repeated two-model residency/concurrency/accounting/shutdown observation set is sufficient"
        else:
            status = _FAIL
            reason = "RRG-5 repeated observation contract was not satisfied"
        return _phase(
            status,
            reason=reason,
            checks=checks,
            artifact="multimodel-a.json,multimodel-b.json,multimodel-review.json",
        )

    def _finalize(self) -> int:
        phases = self.summary.get("phases", {})
        minimum = self.summary.get("minimum_l2_complete") is True
        rrg5 = self.args.scope == "minimum-l2" or self.summary.get("rrg5_complete") is True
        complete = bool(minimum and rrg5)
        self.summary["complete"] = complete
        self.summary["completed_at"] = _utc_now()
        if platform.system().lower() == "darwin":
            try:
                self.summary["environment"]["memory_after"] = _snapshot_to_public(
                    MacOSResourceObserver().snapshot()
                )
            except Exception:  # noqa: BLE001 - final observation is optional
                self.summary["environment"]["memory_after"] = None
        self._persist()
        self._print_summary()
        if complete:
            return 0
        statuses = {
            result.get("status")
            for result in phases.values()
            if isinstance(result, Mapping)
        }
        return 1 if _FAIL in statuses else 2

    def _print_summary(self) -> None:
        print("\nRepresentative device evidence campaign")
        print("=" * 39)
        for name, result in self.summary["phases"].items():
            print(f"{result.get('status', '?'):>12}  {name}: {result.get('reason', '')}")
        print("-" * 39)
        print(f"minimum L2: {'PASS' if self.summary['minimum_l2_complete'] else 'NOT READY'}")
        if self.args.scope == "full":
            print(f"RRG-5:      {'PASS' if self.summary['rrg5_complete'] else 'NOT READY'}")
        print(f"overall:    {'PASS' if self.summary['complete'] else 'NOT READY'}")
        print(f"summary:    {self.summary_path}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the representative Apple Silicon evidence campaign end-to-end and "
            "produce a bounded PASS/FAIL/INCONCLUSIVE summary."
        )
    )
    parser.add_argument("--model-a", required=True, help="Primary registry model key.")
    parser.add_argument("--model-a-path", default=None, help="Optional local path for the primary artifact.")
    parser.add_argument("--model-b", default=None, help="Distinct second model key required by full RRG-5 scope.")
    parser.add_argument("--model-b-path", default=None, help="Optional local path for the second artifact.")
    parser.add_argument(
        "--backend",
        choices=["llama_cpp", "mlx", "llama_server", "mlx_vlm_server"],
        default=None,
        help="Backend override for minimum-L2 single-model phases; default uses repository config.",
    )
    parser.add_argument(
        "--multi-model-backend",
        choices=["llama_cpp", "mlx", "llama_server", "mlx_vlm_server"],
        default=None,
        help="Backend override for RRG-5; default uses repository config.",
    )
    parser.add_argument(
        "--request-estimate-mib",
        type=float,
        default=None,
        help="Required for full scope: configured/calibrated transient total per request in MiB.",
    )
    parser.add_argument(
        "--scope",
        choices=["full", "minimum-l2"],
        default="full",
        help="full also runs repeated two-model RRG-5; minimum-l2 runs TH-E1/EV-3/HE-2/RES-2 only.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--startup-timeout", type=float, default=300.0)
    parser.add_argument("--request-timeout", type=float, default=300.0)
    parser.add_argument("--evaluation-timeout", type=float, default=1800.0)
    parser.add_argument("--output-dir", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        campaign = DeviceEvidenceCampaign(args)
        return campaign.run()
    except KeyboardInterrupt:
        print("Campaign interrupted; inspect campaign-summary.json for retained phase state.", file=sys.stderr)
        return 130
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Campaign failed: {_safe_exception_text(exc)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

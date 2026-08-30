"""One-shot representative Apple Silicon evidence campaign.

The campaign only orchestrates existing evidence owners. It never lowers their
thresholds, enables automatic eviction, or converts unsafe/incomplete execution
into a hardware or production-safety claim.
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
from typing import Any, Callable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .artifact_verification import public_verification_summary, verify_model_artifact
from .evaluation_history import compare_run_summaries, summarize_report_payload
from .hardware_evidence import HardwareEvidenceOptions, execute_hardware_reclamation_evidence
from .hardware_evidence_review import EvidenceReviewSettings, review_hardware_evidence
from .l2_evidence_bridge import capture_thinking_campaign, validate_hardware_bundle
from .multi_model_device_evidence import MultiModelDeviceEvidenceOptions, execute_multi_model_device_evidence
from .multi_model_evidence_review import MultiModelReviewSettings, MultiModelReviewState, review_multi_model_evidence
from .resource_policy_smoke import ResourcePolicySmokeOptions, execute_resource_policy_smoke
from .resources_macos import MacOSResourceObserver

_MIB = 1024**2
_GIB = 1024**3
_PASS = "PASS"
_FAIL = "FAIL"
_INCONCLUSIVE = "INCONCLUSIVE"
_SKIPPED = "SKIPPED"
_MINIMUM_PHASES = ("thinking_th_e1", "evaluation_ev_3", "reclamation_he_2", "resource_policy_res_2")


class CampaignError(RuntimeError):
    """Campaign-level error with no private diagnostic payload."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    return Path.home() / ".local-llm-server" / "evidence" / f"{stamp}-device-campaign"


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    target = path.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(target)
    return target


def _phase(status: str, *, reason: str, checks: Mapping[str, Any] | None = None, artifact: str | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {"status": status, "reason": reason, "checks": dict(checks or {})}
    if artifact:
        value["artifact"] = artifact
    return value


def _safe_exception_text(exc: BaseException) -> str:
    text = str(exc).strip().replace("\n", " ")
    lowered = text.lower()
    if any(token in lowered for token in ("/users/", "/home/", "file://")) or "/" in text or "\\" in text:
        text = exc.__class__.__name__
    return (text[:217] + "...") if len(text) > 220 else (text or exc.__class__.__name__)


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, timeout=5, check=False)
    if result.returncode:
        raise CampaignError("git source identity is unavailable")
    return result.stdout.strip()


def _git_state() -> dict[str, Any]:
    return {
        "revision": _git("rev-parse", "HEAD"),
        "branch": _git("branch", "--show-current"),
        "tracked_clean": not bool(_git("status", "--porcelain", "--untracked-files=no")),
        "root": Path(_git("rev-parse", "--show-toplevel")).resolve(),
    }


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _resource(value: Any) -> dict[str, Any]:
    source = getattr(value, "source", None)
    return {
        "value": getattr(value, "value", None),
        "source": str(getattr(source, "value", source or "unavailable")),
        "unit": getattr(value, "unit", None),
    }


def _snapshot(snapshot: Any) -> dict[str, Any]:
    return {
        "platform": getattr(snapshot, "platform", "unknown"),
        "total_memory_bytes": _resource(getattr(snapshot, "total_memory_bytes", None)),
        "available_memory_bytes": _resource(getattr(snapshot, "available_memory_bytes", None)),
        "process_rss_bytes": _resource(getattr(snapshot, "process_rss_bytes", None)),
    }


def _port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            return True
        except OSError:
            return False


def _listener_closed(host: str, port: int) -> bool:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex((host, port)) != 0:
                return True
        time.sleep(0.1)
    return False


def _request_json(url: str, *, method: str = "GET", payload: Mapping[str, Any] | None = None, timeout: float = 300) -> tuple[int, Mapping[str, Any]]:
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - loopback-only by preflight
            status, raw = int(getattr(response, "status", 200)), response.read()
    except HTTPError as exc:
        status, raw = int(exc.code), exc.read()
    except URLError as exc:
        raise CampaignError(f"loopback request failed: {exc.reason}") from exc
    try:
        body = json.loads(raw.decode()) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CampaignError(f"loopback response was not JSON (status {status})") from exc
    if not isinstance(body, Mapping):
        raise CampaignError(f"loopback response was not an object (status {status})")
    return status, body


def _res2_refusal(exc: BaseException) -> bool:
    text = str(exc)
    return any(token in text for token in (
        "Bounded smoke refused:",
        "Measured available host memory is required",
        "Cannot run bounded resource smoke without a positive pre-load resource estimate",
        "RES-2 real-device smoke must run on macOS",
    ))


def _rrg5_refusal(exc: BaseException) -> bool:
    text = str(exc)
    return any(token in text for token in (
        "RRG-5 multi-model evidence must run on macOS",
        "Measured available host memory is required for RRG-5 evidence",
        "has no positive resident estimate for bounded RRG-5 evidence",
        "requires a current verified artifact receipt before RRG-5 evidence",
        "requires two runtime identities that can be resident together",
    ))


class _OwnedServer:
    """Own one temporary loopback server and its process group."""

    def __init__(self, *, model: str, model_path: str | None, backend: str | None, host: str, port: int, output_dir: Path, startup_timeout: float) -> None:
        self.model, self.model_path, self.backend = model, model_path, backend
        self.host, self.port = host, port
        self.output_dir, self.startup_timeout = output_dir, startup_timeout
        self.process: subprocess.Popen[str] | None = None
        self._log: Any | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self) -> None:
        if not _port_is_free(self.host, self.port):
            raise CampaignError("representative HTTP port is already in use")
        command = [sys.executable, "-m", "local_llm_server", "serve", "--model", self.model, "--host", self.host, "--port", str(self.port), "--enable-admin-api", "--no-download"]
        if self.model_path:
            command += ["--model-path", self.model_path]
        if self.backend:
            command += ["--backend", self.backend]
        self._log = (self.output_dir / "representative-server.log").open("w", encoding="utf-8")
        self.process = subprocess.Popen(command, stdout=self._log, stderr=subprocess.STDOUT, text=True, start_new_session=True)
        deadline = time.monotonic() + self.startup_timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise CampaignError("representative server exited before readiness")
            try:
                status, body = _request_json(f"{self.base_url}/health", timeout=2)
            except CampaignError:
                time.sleep(0.5)
                continue
            if status == 200 and body.get("ok") is True:
                return
            time.sleep(0.5)
        raise CampaignError("representative server readiness timed out")

    def stop(self) -> dict[str, Any]:
        process = self.process
        if process is None:
            return {"owned_process_started": False, "hard_kill_required": False, "listener_closed": True}
        graceful, hard_kill = True, False
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGINT)
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                graceful = False
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    hard_kill = True
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
            except ProcessLookupError:
                pass
        if self._log:
            self._log.close()
            self._log = None
        return {
            "owned_process_started": True,
            "exit_code": process.returncode,
            "graceful": graceful,
            "hard_kill_required": hard_kill,
            "listener_closed": _listener_closed(self.host, self.port),
            "diagnostic_log_retained_locally": True,
        }


class DeviceEvidenceCampaign:
    """Run minimum L2 evidence and optional RRG-5 with per-phase verdicts."""

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
            "models": {"primary": args.model_a, "secondary": args.model_b if args.scope == "full" else None},
            "source": {}, "environment": {}, "phases": {},
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
                "source_artifacts_should_not_be_committed_wholesale": True,
            },
        }
        self._persist()

    def _persist(self) -> None:
        _atomic_write_json(self.summary_path, self.summary)

    def _record(self, name: str, result: Mapping[str, Any]) -> None:
        self.summary["phases"][name] = dict(result)
        self._persist()

    def _run_phase(self, name: str, fn: Callable[[], Mapping[str, Any]], *, exception_status: str = _FAIL) -> dict[str, Any]:
        started = time.monotonic()
        try:
            result = dict(fn())
        except Exception as exc:  # noqa: BLE001 - preserve failure state
            result = _phase(exception_status, reason=_safe_exception_text(exc))
        result["duration_seconds"] = round(time.monotonic() - started, 3)
        self._record(name, result)
        return result

    def run(self) -> int:
        if self._run_phase("preflight", self._preflight, exception_status=_INCONCLUSIVE)["status"] != _PASS:
            return self._finalize()
        if self._run_phase("verify_primary_artifact", self._verify_primary, exception_status=_INCONCLUSIVE)["status"] != _PASS:
            return self._finalize()
        if self.args.scope == "full":
            if self._run_phase("verify_secondary_artifact", self._verify_secondary, exception_status=_INCONCLUSIVE)["status"] != _PASS:
                return self._finalize()
        else:
            self._record("verify_secondary_artifact", _phase(_SKIPPED, reason="minimum-l2 scope does not require a second model"))

        server = _OwnedServer(model=self.args.model_a, model_path=self.args.model_a_path, backend=self.args.backend, host=self.args.host, port=self.args.port, output_dir=self.output_dir, startup_timeout=self.args.startup_timeout)
        cleanup_recorded = False
        try:
            server_start = self._run_phase("start_representative_server", lambda: self._start_server(server))
            if server_start["status"] == _PASS:
                self._run_phase("thinking_th_e1", lambda: self._thinking(server.base_url))
                self._run_phase("evaluation_ev_3", lambda: self._evaluation(server.base_url))
            else:
                self._record("thinking_th_e1", _phase(_SKIPPED, reason="representative server was not ready"))
                self._record("evaluation_ev_3", _phase(_SKIPPED, reason="representative server was not ready"))
            self._run_phase("stop_representative_server", lambda: self._stop_server(server))
            cleanup_recorded = True
        finally:
            if not cleanup_recorded:
                self._run_phase("stop_representative_server", lambda: self._stop_server(server))

        self._run_phase("reclamation_he_2", self._reclamation)
        self._run_phase("resource_policy_res_2", self._resource_policy)
        self._run_phase("validate_minimum_l2_bundle", self._validate_l2_bundle)
        if self.args.scope == "full":
            self._run_phase("multimodel_rrg_5", self._rrg5)
        else:
            self._record("multimodel_rrg_5", _phase(_SKIPPED, reason="minimum-l2 scope explicitly excludes RRG-5"))
        return self._finalize()

    def _preflight(self) -> Mapping[str, Any]:
        git, system, machine = _git_state(), platform.system().lower(), platform.machine().lower()
        request_bytes = int(float(self.args.request_estimate_mib) * _MIB) if self.args.request_estimate_mib is not None else 0
        full_inputs = self.args.scope != "full" or bool(self.args.model_b and self.args.model_b != self.args.model_a and request_bytes > 0)
        loopback = self.args.host == "127.0.0.1"
        checks = {
            "macos": system == "darwin",
            "apple_silicon": machine in {"arm64", "aarch64"},
            "git_branch_dev": git["branch"] == "dev",
            "tracked_tree_clean": git["tracked_clean"] is True,
            "full_scope_inputs": full_inputs,
            "loopback_only": loopback,
            "evidence_directory_outside_repo": not _is_within(self.output_dir, git["root"]),
            "representative_port_free": loopback and _port_is_free(self.args.host, self.args.port),
        }
        memory = MacOSResourceObserver().snapshot() if system == "darwin" else None
        self.summary["source"] = {key: git[key] for key in ("revision", "branch", "tracked_clean")}
        self.summary["environment"] = {
            "system": system, "release": platform.release(), "machine": machine,
            "python_version": platform.python_version(), "package_version": self._package_version(),
            "memory_before": _snapshot(memory) if memory else None,
        }
        self._persist()
        reasons = [
            (checks["macos"] and checks["apple_silicon"], "representative Apple Silicon macOS environment is required"),
            (checks["git_branch_dev"] and checks["tracked_tree_clean"], "run from a clean converged dev checkout so source identity is attributable"),
            (checks["full_scope_inputs"], "full scope requires a distinct second model and positive request estimate"),
            (checks["loopback_only"], "representative campaign refuses non-loopback HTTP binding"),
            (checks["evidence_directory_outside_repo"], "evidence directory must stay outside the repository checkout"),
            (checks["representative_port_free"], "configured loopback port is already owned by another process"),
        ]
        for ok, reason in reasons:
            if not ok:
                return _phase(_INCONCLUSIVE, reason=reason, checks=checks)
        return _phase(_PASS, reason="representative host, source, privacy and listener preconditions satisfied", checks=checks)

    @staticmethod
    def _package_version() -> str | None:
        try:
            return metadata.version("local-llm-server")
        except metadata.PackageNotFoundError:
            return None

    def _verify_primary(self) -> Mapping[str, Any]:
        return self._verified(self.args.model_a, self.args.model_a_path, "primary")

    def _verify_secondary(self) -> Mapping[str, Any]:
        return self._verified(self.args.model_b, self.args.model_b_path, "secondary")

    @staticmethod
    def _verified(model: str, path: str | None, label: str) -> Mapping[str, Any]:
        public = public_verification_summary(verify_model_artifact(model, model_path=path))
        digest, size = public.get("sha256"), public.get("size_bytes")
        ok = public.get("verification") == "verified" and isinstance(digest, str) and len(digest) == 64 and isinstance(size, int) and not isinstance(size, bool) and size > 0
        return _phase(_PASS if ok else _INCONCLUSIVE, reason=f"{label} artifact {'verified' if ok else 'verification is not acceptance-ready'}", checks={"verification": public.get("verification"), "sha256_present": isinstance(digest, str) and len(digest) == 64, "size_bytes_positive": isinstance(size, int) and not isinstance(size, bool) and size > 0})

    @staticmethod
    def _start_server(server: _OwnedServer) -> Mapping[str, Any]:
        server.start()
        return _phase(_PASS, reason="owned representative server reached healthy readiness", checks={"health_ready": True, "owned_process": True}, artifact="representative-server.log")

    @staticmethod
    def _stop_server(server: _OwnedServer) -> Mapping[str, Any]:
        checks = server.stop()
        ok = bool(checks.get("listener_closed")) and not bool(checks.get("hard_kill_required"))
        return _phase(_PASS if ok else _FAIL, reason="owned server stopped and listener closed" if ok else "owned server cleanup required a hard kill or left its listener open", checks=checks, artifact="representative-server.log")

    def _thinking(self, base_url: str) -> Mapping[str, Any]:
        report = capture_thinking_campaign(base_url=base_url, model=self.args.model_a, output=self.output_dir / "thinking-campaign.json", timeout=self.args.request_timeout)
        ok = report.get("complete") is True
        return _phase(_PASS if ok else _FAIL, reason="explicit thinking OFF/ON-hidden contract satisfied" if ok else "thinking campaign did not satisfy the bounded contract", checks={"complete": ok}, artifact="thinking-campaign.json")

    def _evaluation(self, base_url: str) -> Mapping[str, Any]:
        request = {"model": self.args.model_a, "test_set_id": "general-purpose", "test_set_version": "1.0.0", "sample_count": 10, "seed": 0, "reasoning_policy": "off"}
        status_a, report_a = _request_json(f"{base_url}/api/v1/evaluation/runs", method="POST", payload=request, timeout=self.args.evaluation_timeout)
        _atomic_write_json(self.output_dir / "evaluation-off-a.json", report_a)
        status_b, report_b = _request_json(f"{base_url}/api/v1/evaluation/runs", method="POST", payload=request, timeout=self.args.evaluation_timeout)
        _atomic_write_json(self.output_dir / "evaluation-off-b.json", report_b)
        comparable = attribution = grade = samples = False
        try:
            a, b = summarize_report_payload(report_a), summarize_report_payload(report_b)
            comparison = compare_run_summaries(a, b)
            comparable, attribution, grade = bool(comparison.comparable), bool(comparison.attribution_safe), bool(comparison.evidence_grade)
            samples = a.sample_count == 10 and b.sample_count == 10
        except ValueError:
            pass
        ok = status_a == status_b == 200 and report_a.get("complete") is True and report_b.get("complete") is True and comparable and attribution and grade and samples
        return _phase(_PASS if ok else _FAIL, reason="two comparable verified OFF evaluations completed" if ok else "evaluation repeatability/attribution contract was not satisfied", checks={"run_a_http_status": status_a, "run_b_http_status": status_b, "comparable": comparable, "attribution_safe": attribution, "evidence_grade": grade, "sample_count_10_each": samples}, artifact="evaluation-off-a.json,evaluation-off-b.json")

    def _reclamation(self) -> Mapping[str, Any]:
        reports = []
        for suffix in ("a", "b"):
            report = execute_hardware_reclamation_evidence(HardwareEvidenceOptions(model=self.args.model_a, model_path=self.args.model_a_path, backend=self.args.backend, cycles=3, max_tokens=32, settle_seconds=2, no_download=True))
            reports.append(report)
            _atomic_write_json(self.output_dir / f"reclamation-{suffix}.json", report)
        review = review_hardware_evidence(reports, settings=EvidenceReviewSettings(min_reports=2, min_complete_cycles=6, require_verified_identity=True, require_zero_error_cycles=True)).to_public_dict()
        _atomic_write_json(self.output_dir / "reclamation-review.json", review)
        ok = review.get("report_count") == 2 and review.get("compatible_report_count") == 2 and isinstance(review.get("complete_windows"), int) and review.get("complete_windows", 0) >= 6 and review.get("error_cycles") == 0 and review.get("automatic_eviction_recommendation") == "not_provided" and review.get("production_safety_claim") is False
        return _phase(_PASS if ok else _INCONCLUSIVE, reason="two compatible verified reclamation reports completed; memory outcome remains observational" if ok else "reclamation observation set is not acceptance-ready; raw observations are retained", checks={key: review.get(key) for key in ("state", "report_count", "compatible_report_count", "complete_windows", "error_cycles", "automatic_eviction_recommendation", "production_safety_claim")}, artifact="reclamation-a.json,reclamation-b.json,reclamation-review.json")

    def _resource_policy(self) -> Mapping[str, Any]:
        try:
            report = execute_resource_policy_smoke(ResourcePolicySmokeOptions(model=self.args.model_a, model_path=self.args.model_a_path, backend=self.args.backend, max_tokens=8, headroom_bytes=int(0.5 * _GIB), success_margin_bytes=int(0.5 * _GIB), host_safety_bytes=2 * _GIB))
        except RuntimeError as exc:
            if _res2_refusal(exc):
                return _phase(_INCONCLUSIVE, reason="RES-2 refused before unsafe or unattributable execution", checks={"safety_refused": True})
            raise
        _atomic_write_json(self.output_dir / "resource-policy-smoke.json", report)
        success, rejection = report.get("success", {}), report.get("rejection", {})
        ok = isinstance(success, Mapping) and isinstance(rejection, Mapping) and success.get("admission") == "admit" and success.get("inference_http_status") == 200 and isinstance(success.get("committed_bytes"), int) and success.get("committed_bytes", 0) > 0 and success.get("committed_bytes_after_unload") == 0 and success.get("reserved_bytes_after_unload") == 0 and success.get("health_ok_after_unload") is True and success.get("health_state_after_unload") == "cold" and rejection.get("admission") == "reject" and rejection.get("backend_load_reached") is False and report.get("automatic_eviction_exercised") is False
        return _phase(_PASS if ok else _FAIL, reason="bounded resource admission/accounting/release/rejection contract satisfied" if ok else "resource-policy smoke violated an expected invariant", checks={"admission": success.get("admission"), "inference_http_status": success.get("inference_http_status"), "committed_after_unload": success.get("committed_bytes_after_unload"), "reserved_after_unload": success.get("reserved_bytes_after_unload"), "rejection": rejection.get("admission"), "rejected_before_backend_load": rejection.get("backend_load_reached") is False, "automatic_eviction_exercised": report.get("automatic_eviction_exercised")}, artifact="resource-policy-smoke.json")

    def _validate_l2_bundle(self) -> Mapping[str, Any]:
        summary = validate_hardware_bundle(self.output_dir)
        _atomic_write_json(self.output_dir / "l2-device-bundle-summary.json", summary)
        complete = summary.get("complete") is True
        self.summary["minimum_l2_complete"] = complete
        self._persist()
        if complete:
            status, reason = _PASS, "minimum L2 representative-device bundle is acceptance-ready"
        else:
            statuses = {self.summary["phases"].get(name, {}).get("status") for name in _MINIMUM_PHASES}
            start = self.summary["phases"].get("start_representative_server", {}).get("status")
            status = _FAIL if _FAIL in statuses or start == _FAIL else (_INCONCLUSIVE if _INCONCLUSIVE in statuses or _SKIPPED in statuses else _FAIL)
            reason = "minimum L2 bundle is incomplete because one or more prerequisites were inconclusive" if status == _INCONCLUSIVE else "minimum L2 bundle violates one or more acceptance contracts"
        return _phase(status, reason=reason, checks={"complete": complete, "gates": summary.get("gates"), "errors": summary.get("errors")}, artifact="l2-device-bundle-summary.json")

    def _rrg5(self) -> Mapping[str, Any]:
        request_bytes, reports = int(float(self.args.request_estimate_mib) * _MIB), []
        for suffix in ("a", "b"):
            try:
                report = execute_multi_model_device_evidence(MultiModelDeviceEvidenceOptions(model_a=self.args.model_a, model_b=self.args.model_b, model_a_path=self.args.model_a_path, model_b_path=self.args.model_b_path, backend=self.args.multi_model_backend, request_estimate_bytes=request_bytes, cycles=2, max_tokens=8, headroom_bytes=int(0.5 * _GIB), success_margin_bytes=int(0.5 * _GIB), host_safety_bytes=2 * _GIB, settle_seconds=2))
            except RuntimeError as exc:
                if _rrg5_refusal(exc):
                    return _phase(_INCONCLUSIVE, reason="RRG-5 preconditions were insufficient for safe attributable execution", checks={"precondition_refused": True})
                raise
            _atomic_write_json(self.output_dir / f"multimodel-{suffix}.json", report)
            if report.get("status") == "refused_host_safety":
                return _phase(_INCONCLUSIVE, reason="RRG-5 refused before backend construction because host-memory safety margin was unavailable", checks={"host_safety_refused": True, "report": suffix}, artifact=f"multimodel-{suffix}.json")
            reports.append(report)
        review = review_multi_model_evidence(reports, settings=MultiModelReviewSettings(min_reports=2, min_complete_cycles=4)).to_public_dict()
        _atomic_write_json(self.output_dir / "multimodel-review.json", review)
        complete = review.get("state") == MultiModelReviewState.SUFFICIENT_OBSERVATION_SET.value
        self.summary["rrg5_complete"] = complete
        self._persist()
        return _phase(_PASS if complete else _FAIL, reason="repeated two-model residency/concurrency/accounting/shutdown observation set is sufficient" if complete else "RRG-5 repeated observation contract was not satisfied", checks={key: review.get(key) for key in ("state", "complete_cycles", "identity_verified_cycles", "transient_overlap_cycles", "clean_accounting_cycles", "shutdown_complete_reports", "automatic_eviction_recommendation", "reclamation_safety_claim")}, artifact="multimodel-a.json,multimodel-b.json,multimodel-review.json")

    def _finalize(self) -> int:
        minimum = self.summary.get("minimum_l2_complete") is True
        rrg5 = self.args.scope == "minimum-l2" or self.summary.get("rrg5_complete") is True
        self.summary["complete"] = bool(minimum and rrg5)
        self.summary["completed_at"] = _utc_now()
        if platform.system().lower() == "darwin":
            try:
                self.summary["environment"]["memory_after"] = _snapshot(MacOSResourceObserver().snapshot())
            except Exception:  # noqa: BLE001 - final observation is non-blocking
                self.summary["environment"]["memory_after"] = None
        self._persist()
        self._print_summary()
        if self.summary["complete"]:
            return 0
        statuses = {item.get("status") for item in self.summary["phases"].values() if isinstance(item, Mapping)}
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
    parser = argparse.ArgumentParser(description="Run representative Apple Silicon evidence end-to-end with PASS/FAIL/INCONCLUSIVE phase verdicts.")
    parser.add_argument("--model-a", required=True)
    parser.add_argument("--model-a-path", default=None)
    parser.add_argument("--model-b", default=None)
    parser.add_argument("--model-b-path", default=None)
    parser.add_argument("--backend", choices=["llama_cpp", "mlx", "llama_server", "mlx_vlm_server"], default=None)
    parser.add_argument("--multi-model-backend", choices=["llama_cpp", "mlx", "llama_server", "mlx_vlm_server"], default=None)
    parser.add_argument("--request-estimate-mib", type=float, default=None)
    parser.add_argument("--scope", choices=["full", "minimum-l2"], default="full")
    parser.add_argument("--host", default="127.0.0.1", help="Only 127.0.0.1 is accepted by preflight.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--startup-timeout", type=float, default=300)
    parser.add_argument("--request-timeout", type=float, default=300)
    parser.add_argument("--evaluation-timeout", type=float, default=1800)
    parser.add_argument("--output-dir", default=None, help="Must resolve outside the repository checkout.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return DeviceEvidenceCampaign(args).run()
    except KeyboardInterrupt:
        print("Campaign interrupted; inspect campaign-summary.json for retained phase state.", file=sys.stderr)
        return 130
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Campaign failed: {_safe_exception_text(exc)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

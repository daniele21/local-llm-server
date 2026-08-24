from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

_GIB = 1024 ** 3
_EXPECTED_HEADROOM = int(0.5 * _GIB)
_EXPECTED_SUCCESS_MARGIN = int(0.5 * _GIB)
_EXPECTED_HOST_SAFETY = 2 * _GIB


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_object(path: Path) -> Mapping[str, Any] | None:
    try:
        payload = _load_json(path)
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, Mapping) else None


def _is_sha256(value: object) -> bool:
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    return len(lowered) == 64 and all(char in "0123456789abcdef" for char in lowered)


def _check(check_id: str, state: str, **evidence: object) -> dict[str, object]:
    return {"id": check_id, "state": state, "evidence": evidence}


def _check_manifest(evidence_dir: Path) -> tuple[dict[str, object], Mapping[str, Any] | None]:
    path = evidence_dir / "evidence-manifest.json"
    manifest = _load_object(path)
    if manifest is None:
        return _check("manifest_integrity", "blocked", reason="manifest_missing_or_invalid"), None
    if manifest.get("schema_version") != 1:
        return _check("manifest_integrity", "blocked", reason="unsupported_manifest_schema"), manifest

    files = manifest.get("files")
    if not isinstance(files, list):
        return _check("manifest_integrity", "blocked", reason="manifest_file_inventory_missing"), manifest

    invalid: list[str] = []
    verified = 0
    for item in files:
        if not isinstance(item, Mapping):
            invalid.append("invalid_inventory_entry")
            continue
        relative = item.get("path")
        expected = item.get("sha256")
        if not isinstance(relative, str) or not _is_sha256(expected):
            invalid.append(str(relative or "invalid_inventory_entry"))
            continue
        candidate_relative = Path(relative)
        if candidate_relative.is_absolute() or ".." in candidate_relative.parts:
            invalid.append(relative)
            continue
        candidate = evidence_dir / candidate_relative
        if not candidate.is_file() or _sha256(candidate) != str(expected).lower():
            invalid.append(relative)
            continue
        verified += 1

    state = "pass" if not invalid else "blocked"
    return (
        _check(
            "manifest_integrity",
            state,
            verified_files=verified,
            invalid_file_count=len(invalid),
            invalid_files=invalid,
            source_manifest_sha256=_sha256(path),
        ),
        manifest,
    )


def _step_map(manifest: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    if manifest is None:
        return {}
    steps = manifest.get("steps")
    if not isinstance(steps, list):
        return {}
    return {
        str(step.get("name")): step
        for step in steps
        if isinstance(step, Mapping) and isinstance(step.get("name"), str)
    }


def _check_runner_steps(manifest: Mapping[str, Any] | None) -> dict[str, object]:
    steps = _step_map(manifest)
    required = (
        "artifact-verification",
        "server",
        "runtime-identity",
        "status-before",
        "thinking-off-response",
        "thinking-on-hidden-response",
        "evaluation-off-a",
        "evaluation-off-b",
        "performance-lab-real-smoke",
        "status-after-pl",
        "server-shutdown",
        "reclamation-a",
        "reclamation-b",
        "reclamation-review",
        "resource-policy-smoke",
    )
    missing = [name for name in required if name not in steps]
    failed = [name for name in required if steps.get(name, {}).get("status") != "passed"]
    failed_steps = manifest.get("failed_steps") if manifest is not None else None
    if isinstance(failed_steps, list):
        failed.extend(str(item) for item in failed_steps if str(item) not in failed)
    state = "pass" if not missing and not failed else "blocked"
    return _check(
        "runner_steps",
        state,
        required_count=len(required),
        missing_steps=missing,
        nonpassing_steps=failed,
    )


def _select_runtime_identity(
    payload: Mapping[str, Any], expected_model: str | None
) -> tuple[str | None, Mapping[str, Any] | None]:
    models = payload.get("models")
    if not isinstance(models, Mapping):
        return None, None
    if expected_model and isinstance(models.get(expected_model), Mapping):
        return expected_model, models[expected_model]
    if len(models) == 1:
        key, value = next(iter(models.items()))
        return (str(key), value) if isinstance(value, Mapping) else (None, None)
    return None, None


def _check_runtime_identity(
    evidence_dir: Path, expected_model: str | None
) -> tuple[dict[str, object], str | None]:
    payload = _load_object(evidence_dir / "runtime-identity.json")
    if payload is None:
        return _check("runtime_identity", "blocked", reason="identity_missing_or_invalid"), None

    key, selected = _select_runtime_identity(payload, expected_model)
    if selected is None:
        return _check("runtime_identity", "blocked", reason="expected_runtime_not_resolved"), None

    model = selected.get("model") if isinstance(selected.get("model"), Mapping) else {}
    runtime = selected.get("runtime") if isinstance(selected.get("runtime"), Mapping) else {}
    hardware = selected.get("hardware") if isinstance(selected.get("hardware"), Mapping) else {}
    fingerprint = runtime.get("fingerprint")
    protocol_ok = payload.get("protocol_version") == "local-llm-identity-v1"
    verified = model.get("verification") == "verified" and runtime.get("evidence_grade") == "verified"
    fingerprint_ok = _is_sha256(fingerprint)
    state = "pass" if protocol_ok and verified and fingerprint_ok else "blocked"

    server = payload.get("server") if isinstance(payload.get("server"), Mapping) else {}
    return (
        _check(
            "runtime_identity",
            state,
            protocol_version=payload.get("protocol_version"),
            server_version=server.get("version"),
            runtime_key=key,
            model_id=model.get("id"),
            model_verification=model.get("verification"),
            backend=runtime.get("name"),
            backend_version=runtime.get("version"),
            runtime_evidence_grade=runtime.get("evidence_grade"),
            runtime_fingerprint=fingerprint if fingerprint_ok else None,
            hardware_system=hardware.get("system"),
            hardware_machine=hardware.get("machine"),
        ),
        str(fingerprint) if fingerprint_ok else None,
    )


def _response_message(payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], Mapping):
        return None
    message = choices[0].get("message")
    return message if isinstance(message, Mapping) else None


def _check_thinking_boundary(evidence_dir: Path) -> dict[str, object]:
    off = _load_object(evidence_dir / "thinking-off-response.json")
    on = _load_object(evidence_dir / "thinking-on-hidden-response.json")
    if off is None or on is None:
        return _check("thinking_boundary", "blocked", reason="thinking_response_missing_or_invalid")
    off_message = _response_message(off)
    on_message = _response_message(on)
    if off_message is None or on_message is None:
        return _check("thinking_boundary", "blocked", reason="openai_message_shape_missing")

    off_content = off_message.get("content")
    on_content = on_message.get("content")
    off_nonempty = isinstance(off_content, str) and bool(off_content.strip())
    on_nonempty = isinstance(on_content, str) and bool(on_content.strip())
    lowered = on_content.lower() if isinstance(on_content, str) else ""
    explicit_markup = "<think" in lowered or "</think>" in lowered
    reasoning_keys = ("reasoning", "reasoning_content", "thinking")
    exposed_reasoning_field = any(bool(on_message.get(key)) for key in reasoning_keys)
    state = (
        "pass"
        if off_nonempty and on_nonempty and not explicit_markup and not exposed_reasoning_field
        else "blocked"
    )
    return _check(
        "thinking_boundary",
        state,
        off_response_nonempty=off_nonempty,
        on_hidden_response_nonempty=on_nonempty,
        explicit_thinking_markup_exposed=explicit_markup,
        reasoning_field_exposed=exposed_reasoning_field,
    )


def _evaluation_payload(path: Path) -> Mapping[str, Any] | None:
    payload = _load_object(path)
    if payload is None:
        return None
    report = payload.get("report")
    return payload if isinstance(report, Mapping) else None


def _score_mean(results: list[object]) -> float | None:
    values: list[float] = []
    for result in results:
        if not isinstance(result, Mapping):
            continue
        scores = result.get("scores")
        if not isinstance(scores, list):
            continue
        for score in scores:
            if not isinstance(score, Mapping):
                continue
            value = score.get("value")
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                values.append(float(value))
    return sum(values) / len(values) if values else None


def _ev3_run_summary(payload: Mapping[str, Any]) -> tuple[bool, dict[str, object], tuple[object, ...]]:
    report = payload.get("report")
    if not isinstance(report, Mapping):
        return False, {}, ()
    manifest = report.get("manifest")
    results = report.get("results")
    if not isinstance(manifest, Mapping) or not isinstance(results, list):
        return False, {}, ()
    sample_ids = manifest.get("sample_ids")
    profile = manifest.get("reasoning_profile")
    if not isinstance(sample_ids, list) or not isinstance(profile, Mapping):
        return False, {}, ()

    explicit_results = True
    success_count = 0
    failure_count = 0
    result_ids: list[object] = []
    for result in results:
        if not isinstance(result, Mapping) or not isinstance(result.get("succeeded"), bool):
            explicit_results = False
            continue
        result_ids.append(result.get("sample_id"))
        if result.get("succeeded") is True:
            success_count += 1
        else:
            failure_count += 1
            if not isinstance(result.get("error_code"), str) or not str(result.get("error_code")).strip():
                explicit_results = False

    exact_contract = (
        payload.get("evidence_grade") is True
        and report.get("complete") is True
        and manifest.get("test_set_id") == "general-purpose"
        and manifest.get("test_set_version") == "1.0.0"
        and manifest.get("seed") == 0
        and len(sample_ids) == 10
        and len(set(map(str, sample_ids))) == 10
        and len(results) == 10
        and set(map(str, result_ids)) == set(map(str, sample_ids))
        and profile.get("requested") == "off"
        and profile.get("effective") == "off"
        and _is_sha256(manifest.get("test_set_identity"))
        and _is_sha256(manifest.get("runtime_fingerprint"))
        and explicit_results
    )
    selection_digest = hashlib.sha256(
        json.dumps(sample_ids, sort_keys=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    summary = {
        "run_id": manifest.get("run_id"),
        "model": manifest.get("model"),
        "test_set_id": manifest.get("test_set_id"),
        "test_set_version": manifest.get("test_set_version"),
        "test_set_identity": manifest.get("test_set_identity"),
        "sample_count": len(sample_ids),
        "sample_selection_digest": selection_digest,
        "seed": manifest.get("seed"),
        "reasoning_requested": profile.get("requested"),
        "reasoning_effective": profile.get("effective"),
        "runtime_fingerprint": manifest.get("runtime_fingerprint"),
        "complete": report.get("complete"),
        "success_count": success_count,
        "failure_count": failure_count,
        "objective_score_mean_descriptive": _score_mean(results),
    }
    compatibility_key = (
        manifest.get("test_set_identity"),
        tuple(map(str, sample_ids)),
        manifest.get("model"),
        manifest.get("seed"),
        manifest.get("runtime_fingerprint"),
        profile.get("requested"),
        profile.get("effective"),
    )
    return exact_contract, summary, compatibility_key


def _check_ev3(evidence_dir: Path, runtime_fingerprint: str | None) -> dict[str, object]:
    first = _evaluation_payload(evidence_dir / "evaluation-off-a.json")
    second = _evaluation_payload(evidence_dir / "evaluation-off-b.json")
    if first is None or second is None:
        return _check("ev3", "blocked", reason="evaluation_report_missing_or_invalid")
    first_ok, first_summary, first_key = _ev3_run_summary(first)
    second_ok, second_summary, second_key = _ev3_run_summary(second)
    comparable = first_key == second_key
    identity_matches = (
        runtime_fingerprint is not None
        and first_summary.get("runtime_fingerprint") == runtime_fingerprint
        and second_summary.get("runtime_fingerprint") == runtime_fingerprint
    )
    state = "pass" if first_ok and second_ok and comparable and identity_matches else "blocked"
    return _check(
        "ev3",
        state,
        run_a=first_summary,
        run_b=second_summary,
        comparable=comparable,
        runtime_identity_matches=identity_matches,
    )


def _check_performance_lab(evidence_dir: Path) -> dict[str, object]:
    stdout = evidence_dir / "performance-lab-real-smoke.stdout.txt"
    payload = _load_object(stdout)
    if payload is None:
        return _check("performance_lab_replacement", "blocked", reason="pl_smoke_output_missing_or_invalid")
    probe = payload.get("probe") if isinstance(payload.get("probe"), Mapping) else {}
    run = payload.get("run") if isinstance(payload.get("run"), Mapping) else {}
    pl_dir = evidence_dir / "performance-lab"
    bundles = sorted(path for path in pl_dir.rglob("*.plab.zip") if path.is_file()) if pl_dir.exists() else []
    stores = sorted(path for path in pl_dir.rglob("*.sqlite3") if path.is_file()) if pl_dir.exists() else []
    run_ok = (
        probe.get("healthy") is True
        and run.get("status") == "succeeded"
        and isinstance(run.get("run_id"), str)
        and bool(str(run.get("run_id")).strip())
        and isinstance(run.get("fingerprint_id"), str)
        and bool(str(run.get("fingerprint_id")).strip())
        and isinstance(run.get("sample_count"), int)
        and not isinstance(run.get("sample_count"), bool)
        and int(run.get("sample_count")) > 0
        and bool(bundles)
        and bool(stores)
    )
    return _check(
        "performance_lab_replacement",
        "pass" if run_ok else "blocked",
        probe_healthy=probe.get("healthy"),
        run_id=run.get("run_id"),
        run_status=run.get("status"),
        fingerprint_id=run.get("fingerprint_id"),
        sample_count=run.get("sample_count"),
        bundle_count=len(bundles),
        bundle_sha256=[_sha256(path) for path in bundles],
        sqlite_store_count=len(stores),
        sqlite_store_sha256=[_sha256(path) for path in stores],
    )


def _check_shutdown_and_status(evidence_dir: Path, manifest: Mapping[str, Any] | None) -> dict[str, object]:
    steps = _step_map(manifest)
    shutdown = steps.get("server-shutdown", {})
    before = _load_object(evidence_dir / "status-before.json")
    after = _load_object(evidence_dir / "status-after-pl.json")
    ok = (
        shutdown.get("status") == "passed"
        and shutdown.get("graceful") is True
        and before is not None
        and after is not None
    )
    return _check(
        "server_lifecycle",
        "pass" if ok else "blocked",
        graceful_shutdown=shutdown.get("graceful"),
        status_before_retained=before is not None,
        status_after_pl_retained=after is not None,
    )


def _check_he2(evidence_dir: Path) -> dict[str, object]:
    review = _load_object(evidence_dir / "reclamation-review.json")
    if review is None:
        return _check("he2", "blocked", reason="reclamation_review_missing_or_invalid")
    observations = review.get("observations") if isinstance(review.get("observations"), Mapping) else {}
    base_ok = (
        review.get("report_count") == 2
        and review.get("compatible_report_count") == 2
        and isinstance(review.get("complete_windows"), int)
        and int(review.get("complete_windows")) >= 6
        and review.get("error_cycles") == 0
        and observations.get("inconclusive") == 0
        and review.get("identity_grade") == "verified"
        and review.get("automatic_eviction_recommendation") == "not_provided"
        and review.get("production_safety_claim") is False
    )
    state_value = review.get("state")
    if not base_ok or state_value in {"insufficient", "incompatible", None}:
        state = "blocked"
    elif state_value == "mixed":
        state = "review_required"
    elif state_value in {"consistent_recovery_observed", "consistent_no_recovery_observed"}:
        state = "pass"
    else:
        state = "review_required"
    return _check(
        "he2",
        state,
        review_state=state_value,
        report_count=review.get("report_count"),
        compatible_report_count=review.get("compatible_report_count"),
        complete_windows=review.get("complete_windows"),
        error_cycles=review.get("error_cycles"),
        identity_grade=review.get("identity_grade"),
        observations={
            "recovery_observed": observations.get("recovery_observed"),
            "no_recovery_observed": observations.get("no_recovery_observed"),
            "inconclusive": observations.get("inconclusive"),
        },
        reasons=review.get("reasons"),
    )


def _check_res2(evidence_dir: Path) -> dict[str, object]:
    report = _load_object(evidence_dir / "resource-policy-smoke.json")
    if report is None:
        return _check("res2", "blocked", reason="resource_policy_report_missing_or_invalid")
    success = report.get("success") if isinstance(report.get("success"), Mapping) else {}
    rejection = report.get("rejection") if isinstance(report.get("rejection"), Mapping) else {}
    safety_margins_preserved = (
        report.get("headroom_bytes") == _EXPECTED_HEADROOM
        and report.get("success_margin_bytes") == _EXPECTED_SUCCESS_MARGIN
        and report.get("host_safety_bytes") == _EXPECTED_HOST_SAFETY
    )
    ok = (
        report.get("schema_version") == 1
        and report.get("procedure") == "bounded_resource_policy_smoke"
        and safety_margins_preserved
        and report.get("automatic_eviction_exercised") is False
        and success.get("admission") == "admit"
        and success.get("loaded") is True
        and success.get("inference_http_status") == 200
        and isinstance(success.get("committed_bytes"), int)
        and int(success.get("committed_bytes")) > 0
        and success.get("reserved_bytes_after_unload") == 0
        and success.get("committed_bytes_after_unload") == 0
        and success.get("reservation_count_after_unload") == 0
        and success.get("health_ok_after_unload") is True
        and success.get("health_state_after_unload") == "cold"
        and rejection.get("admission") == "reject"
        and rejection.get("resident_count_after_reject") == 0
        and rejection.get("reservation_count_after_reject") == 0
        and rejection.get("backend_load_reached") is False
    )
    return _check(
        "res2",
        "pass" if ok else "blocked",
        safety_margins_preserved=safety_margins_preserved,
        automatic_eviction_exercised=report.get("automatic_eviction_exercised"),
        success_admission=success.get("admission"),
        inference_http_status=success.get("inference_http_status"),
        committed_bytes=success.get("committed_bytes"),
        reserved_bytes_after_unload=success.get("reserved_bytes_after_unload"),
        committed_bytes_after_unload=success.get("committed_bytes_after_unload"),
        reservation_count_after_unload=success.get("reservation_count_after_unload"),
        health_state_after_unload=success.get("health_state_after_unload"),
        rejection_admission=rejection.get("admission"),
        resident_count_after_reject=rejection.get("resident_count_after_reject"),
        reservation_count_after_reject=rejection.get("reservation_count_after_reject"),
        backend_load_reached=rejection.get("backend_load_reached"),
    )


def review(evidence_dir: Path) -> dict[str, object]:
    evidence_dir = evidence_dir.expanduser().resolve()
    manifest_check, manifest = _check_manifest(evidence_dir)
    expected_model = str(manifest.get("model")) if manifest and manifest.get("model") is not None else None
    identity_check, fingerprint = _check_runtime_identity(evidence_dir, expected_model)
    checks = [
        manifest_check,
        _check_runner_steps(manifest),
        identity_check,
        _check_thinking_boundary(evidence_dir),
        _check_ev3(evidence_dir, fingerprint),
        _check_performance_lab(evidence_dir),
        _check_shutdown_and_status(evidence_dir, manifest),
        _check_he2(evidence_dir),
        _check_res2(evidence_dir),
    ]
    states = {str(item["state"]) for item in checks}
    if "blocked" in states:
        overall = "blocked"
    elif "review_required" in states:
        overall = "review_required"
    else:
        overall = "ready_for_mig003"
    return {
        "schema_version": 1,
        "procedure": "representative_evidence_review",
        "overall_state": overall,
        "model": expected_model,
        "checks": checks,
        "interpretation": (
            "This summary checks evidence completeness, identity/comparability and bounded procedure "
            "contracts. It is not a broad performance, thermal, memory-safety or production-safety claim."
        ),
        "privacy": (
            "The summary intentionally omits model paths, prompts, model outputs and raw private evidence paths."
        ),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Review one representative evidence directory and emit a public-safe gate summary."
    )
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    return parser


def main() -> int:
    args = _parser().parse_args()
    evidence_dir = args.evidence_dir.expanduser().resolve()
    result = review(evidence_dir)
    output = args.output.expanduser().resolve() if args.output else evidence_dir / "representative-review.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["overall_state"] == "ready_for_mig003":
        return 0
    if result["overall_state"] == "review_required":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

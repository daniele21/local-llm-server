"""Conservative review of repeated RRG-5 multi-model device reports.

The reviewer validates compatibility, repetition and ownership/accounting cleanup.
It intentionally does not turn memory deltas into an automatic-eviction or
production-safety recommendation; negative and inconclusive observations remain
visible for engineering judgment.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence


class MultiModelReviewState(str, Enum):
    INSUFFICIENT = "insufficient"
    INCOMPATIBLE = "incompatible"
    SUFFICIENT_OBSERVATION_SET = "sufficient_observation_set"


@dataclass(frozen=True, slots=True)
class MultiModelReviewSettings:
    min_reports: int = 2
    min_complete_cycles: int = 4

    def __post_init__(self) -> None:
        if self.min_reports < 2:
            raise ValueError("min_reports must be >= 2")
        if self.min_complete_cycles < 1:
            raise ValueError("min_complete_cycles must be >= 1")


@dataclass(frozen=True, slots=True)
class MultiModelEvidenceReview:
    state: MultiModelReviewState
    report_count: int
    compatible_report_count: int
    complete_cycles: int
    identity_verified_cycles: int
    transient_overlap_cycles: int
    clean_accounting_cycles: int
    shutdown_complete_reports: int
    rss_after_minus_before_bytes: tuple[int | float, ...]
    available_after_minus_before_bytes: tuple[int | float, ...]
    reasons: tuple[str, ...]

    def to_public_dict(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "report_count": self.report_count,
            "compatible_report_count": self.compatible_report_count,
            "complete_cycles": self.complete_cycles,
            "identity_verified_cycles": self.identity_verified_cycles,
            "transient_overlap_cycles": self.transient_overlap_cycles,
            "clean_accounting_cycles": self.clean_accounting_cycles,
            "shutdown_complete_reports": self.shutdown_complete_reports,
            "post_stop_observations": {
                "rss_after_minus_before_bytes": list(self.rss_after_minus_before_bytes),
                "available_after_minus_before_bytes": list(
                    self.available_after_minus_before_bytes
                ),
            },
            "reasons": list(self.reasons),
            "automatic_eviction_recommendation": "not_provided",
            "reclamation_safety_claim": False,
            "production_safety_claim": False,
            "interpretation": (
                "Sufficiency means the reports are compatible and repeatedly exercise "
                "the intended multi-model ownership/accounting paths. Memory deltas remain "
                "observational and require engineering review; this result does not enable "
                "automatic eviction."
            ),
        }


def review_multi_model_evidence(
    reports: Sequence[Mapping[str, Any]],
    *,
    settings: MultiModelReviewSettings | None = None,
) -> MultiModelEvidenceReview:
    cfg = settings or MultiModelReviewSettings()
    parsed = [_parse_report(report) for report in reports]
    valid = [item for item in parsed if item is not None]
    reasons: list[str] = []

    if len(valid) != len(reports):
        reasons.append("one_or_more_reports_have_invalid_schema")
    if not valid:
        return _result(
            state=MultiModelReviewState.INSUFFICIENT,
            reports=len(reports),
            compatible=(),
            reasons=tuple(reasons or ["no_valid_reports"]),
        )

    reference_key = valid[0]["compatibility_key"]
    compatible = [item for item in valid if item["compatibility_key"] == reference_key]
    if len(compatible) != len(valid):
        reasons.append("model_runtime_hardware_or_procedure_identity_differs")
        return _result(
            state=MultiModelReviewState.INCOMPATIBLE,
            reports=len(reports),
            compatible=compatible,
            reasons=tuple(reasons),
        )

    if len(compatible) < cfg.min_reports:
        reasons.append("insufficient_repeated_reports")

    totals = _totals(compatible)
    if totals["complete_cycles"] < cfg.min_complete_cycles:
        reasons.append("insufficient_complete_cycles")
    if totals["identity_verified_cycles"] != totals["complete_cycles"]:
        reasons.append("one_or_more_complete_cycles_lack_verified_runtime_identity")
    if totals["transient_overlap_cycles"] != totals["complete_cycles"]:
        reasons.append("one_or_more_complete_cycles_lack_transient_overlap")
    if totals["clean_accounting_cycles"] != totals["complete_cycles"]:
        reasons.append("one_or_more_cycles_left_configured_accounting")
    if totals["shutdown_complete_reports"] != len(compatible):
        reasons.append("one_or_more_shutdown_under_load_procedures_incomplete")
    if any(not bool(item["report_complete"]) for item in compatible):
        reasons.append("one_or_more_reports_incomplete")
    if any(bool(item["automatic_eviction_exercised"]) for item in compatible):
        reasons.append("automatic_eviction_must_not_be_exercised_in_rrg5")

    state = (
        MultiModelReviewState.INSUFFICIENT
        if reasons
        else MultiModelReviewState.SUFFICIENT_OBSERVATION_SET
    )
    return _result(
        state=state,
        reports=len(reports),
        compatible=compatible,
        reasons=tuple(reasons or ["compatible_repeated_observation_set"]),
    )


def _parse_report(report: Mapping[str, Any]) -> dict[str, Any] | None:
    if report.get("schema_version") != 1:
        return None
    procedure = report.get("procedure")
    models = report.get("models")
    budget = report.get("budget")
    host_before = report.get("host_before")
    cycles = report.get("cycles")
    shutdown = report.get("shutdown_under_load")
    if (
        not isinstance(procedure, Mapping)
        or procedure.get("name") != "multi_model_resource_governor_v1"
        or procedure.get("prompt_recorded") is not False
        or procedure.get("output_recorded") is not False
        or procedure.get("process_ids_recorded") is not False
        or procedure.get("automatic_eviction_enabled") is not False
        or not isinstance(models, list)
        or len(models) != 2
        or not all(isinstance(item, Mapping) for item in models)
        or not isinstance(budget, Mapping)
        or not isinstance(host_before, Mapping)
        or not isinstance(cycles, list)
        or not isinstance(shutdown, Mapping)
    ):
        return None

    request_estimate = procedure.get("request_estimate_bytes")
    if not _positive_int(request_estimate):
        return None
    if not _valid_models(models):
        return None

    parsed_cycles: list[dict[str, object]] = []
    identity_fingerprints: tuple[str, ...] | None = None
    cycle_auto_eviction = False
    for cycle in cycles:
        if not isinstance(cycle, Mapping):
            return None
        fingerprints = _identity_fingerprints(cycle.get("runtime_identities"))
        if fingerprints is not None:
            if identity_fingerprints is None:
                identity_fingerprints = fingerprints
            elif fingerprints != identity_fingerprints:
                return None

        identity_verified = (
            cycle.get("runtime_identities_verified") is True
            and fingerprints is not None
        )
        overlap = _transient_overlap_recomputed(cycle, int(request_estimate))
        clean_accounting = _accounting_clean(
            cycle.get("configured_accounting_after_unload")
        )
        responses_ok = _responses_ok(cycle.get("responses"), models)
        auto_eviction = cycle.get("automatic_eviction_exercised") is True
        cycle_auto_eviction = cycle_auto_eviction or auto_eviction
        recomputed_complete = (
            cycle.get("complete") is True
            and identity_verified
            and overlap
            and clean_accounting
            and responses_ok
            and not auto_eviction
        )
        post_stop = cycle.get("post_stop_observation")
        parsed_cycles.append(
            {
                "complete": recomputed_complete,
                "identity_verified": identity_verified,
                "transient_overlap": overlap,
                "clean_accounting": clean_accounting,
                "rss_delta": _optional_number(
                    post_stop.get("rss_after_minus_before_bytes")
                    if isinstance(post_stop, Mapping)
                    else None
                ),
                "available_delta": _optional_number(
                    post_stop.get("available_after_minus_before_bytes")
                    if isinstance(post_stop, Mapping)
                    else None
                ),
            }
        )

    shutdown_complete = _shutdown_contract_complete(shutdown)
    report_complete = (
        report.get("complete") is True
        and report.get("status") == "complete"
        and len(parsed_cycles) == procedure.get("cycles")
        and all(bool(cycle["complete"]) for cycle in parsed_cycles)
        and shutdown_complete
    )
    automatic_eviction_exercised = (
        report.get("automatic_eviction_exercised") is True
        or cycle_auto_eviction
        or shutdown.get("automatic_eviction_exercised") is True
    )

    compatibility_key = (
        _model_key(models),
        identity_fingerprints,
        _host_compatibility(host_before),
        procedure.get("cycles"),
        procedure.get("max_tokens"),
        request_estimate,
        procedure.get("global_max_running"),
        procedure.get("global_queue_capacity"),
        procedure.get("settle_after_unload_seconds"),
        procedure.get("shutdown_timeout_seconds"),
        procedure.get("sample_interval_seconds"),
        _budget_compatibility(budget),
    )
    return {
        "compatibility_key": compatibility_key,
        "cycles": parsed_cycles,
        "shutdown_complete": shutdown_complete,
        "report_complete": report_complete,
        "automatic_eviction_exercised": automatic_eviction_exercised,
    }


def _valid_models(models: Sequence[Mapping[str, Any]]) -> bool:
    seen_keys: set[str] = set()
    seen_ids: set[str] = set()
    for item in models:
        key = item.get("key")
        model_id = item.get("model_id")
        backend = item.get("backend")
        digest = item.get("artifact_sha256")
        estimate = item.get("estimate_bytes")
        if (
            not isinstance(key, str)
            or not key.strip()
            or not isinstance(model_id, str)
            or not model_id.strip()
            or not isinstance(backend, str)
            or not backend.strip()
            or not isinstance(digest, str)
            or not _is_sha256(digest)
            or not _positive_int(estimate)
            or key in seen_keys
            or model_id in seen_ids
        ):
            return False
        seen_keys.add(key)
        seen_ids.add(model_id)
    return True


def _model_key(models: Sequence[Mapping[str, Any]]) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (
            str(item["key"]),
            str(item["model_id"]),
            str(item["backend"]),
            str(item["artifact_sha256"]).lower(),
            int(item["estimate_bytes"]),
        )
        for item in models
    )


def _identity_fingerprints(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, list) or len(value) != 2:
        return None
    fingerprints: list[str] = []
    for identity in value:
        if not isinstance(identity, Mapping):
            return None
        fingerprint = identity.get("fingerprint")
        if not isinstance(fingerprint, str) or not _is_sha256(fingerprint):
            return None
        fingerprints.append(fingerprint.lower())
    return tuple(fingerprints)


def _responses_ok(
    value: object,
    models: Sequence[Mapping[str, Any]],
) -> bool:
    if not isinstance(value, list) or len(value) != 2:
        return False
    expected = {str(item["key"]) for item in models}
    observed: set[str] = set()
    for response in value:
        if not isinstance(response, Mapping):
            return False
        model = response.get("model")
        status = response.get("http_status")
        if not isinstance(model, str) or status != 200:
            return False
        observed.add(model)
    return observed == expected


def _transient_overlap_recomputed(
    cycle: Mapping[str, Any],
    request_estimate_bytes: int,
) -> bool:
    peak = cycle.get("configured_accounting_peak")
    if not isinstance(peak, Mapping):
        return False
    transient = peak.get("transient_committed_bytes")
    return (
        cycle.get("concurrent_transient_overlap_observed") is True
        and isinstance(transient, int)
        and not isinstance(transient, bool)
        and transient >= 2 * request_estimate_bytes
    )


def _accounting_clean(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    expected_zero = (
        "resident_committed_bytes",
        "resident_reserved_bytes",
        "transient_committed_bytes",
        "transient_reserved_bytes",
        "reservation_count",
    )
    return all(value.get(key) == 0 for key in expected_zero)


def _shutdown_contract_complete(shutdown: Mapping[str, Any]) -> bool:
    if shutdown.get("automatic_eviction_exercised") is True:
        return False
    remaining = shutdown.get("remaining_after_first_shutdown")
    retained_failed_owner = False
    if isinstance(remaining, list):
        retained_failed_owner = any(
            isinstance(item, Mapping)
            and item.get("state") == "failed"
            and isinstance(item.get("active_requests"), int)
            and not isinstance(item.get("active_requests"), bool)
            and int(item["active_requests"]) > 0
            for item in remaining
        )
    first_accounting = shutdown.get("configured_accounting_after_first_shutdown")
    retained_accounting = (
        isinstance(first_accounting, Mapping)
        and isinstance(first_accounting.get("resident_committed_bytes"), int)
        and not isinstance(first_accounting.get("resident_committed_bytes"), bool)
        and int(first_accounting["resident_committed_bytes"]) > 0
    )
    return (
        shutdown.get("complete") is True
        and shutdown.get("first_shutdown_reported_incomplete") is True
        and shutdown.get("active_owner_retained_after_timeout") is True
        and retained_failed_owner
        and retained_accounting
        and _accounting_clean(shutdown.get("configured_accounting_after_retry"))
    )


def _host_compatibility(host_before: Mapping[str, Any]) -> tuple[object, ...] | None:
    total = host_before.get("total_memory_bytes")
    if not isinstance(total, Mapping):
        return None
    value = total.get("value")
    source = total.get("source")
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value <= 0
        or source != "measured"
    ):
        return None
    platform_name = host_before.get("platform")
    if not isinstance(platform_name, str) or not platform_name.strip():
        return None
    return (platform_name, value, source)


def _budget_compatibility(budget: Mapping[str, Any]) -> tuple[object, ...]:
    keys = (
        "resident_estimate_bytes",
        "transient_capacity_bytes",
        "success_margin_bytes",
        "headroom_bytes",
        "host_safety_bytes",
        "usable_budget_bytes",
    )
    return tuple(budget.get(key) for key in keys)


def _totals(items: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    complete_cycles = 0
    identity_verified_cycles = 0
    transient_overlap_cycles = 0
    clean_accounting_cycles = 0
    shutdown_complete_reports = 0
    for item in items:
        for cycle in item["cycles"]:
            if cycle["complete"]:
                complete_cycles += 1
                identity_verified_cycles += int(bool(cycle["identity_verified"]))
                transient_overlap_cycles += int(bool(cycle["transient_overlap"]))
                clean_accounting_cycles += int(bool(cycle["clean_accounting"]))
        shutdown_complete_reports += int(bool(item["shutdown_complete"]))
    return {
        "complete_cycles": complete_cycles,
        "identity_verified_cycles": identity_verified_cycles,
        "transient_overlap_cycles": transient_overlap_cycles,
        "clean_accounting_cycles": clean_accounting_cycles,
        "shutdown_complete_reports": shutdown_complete_reports,
    }


def _result(
    *,
    state: MultiModelReviewState,
    reports: int,
    compatible: Sequence[Mapping[str, Any]],
    reasons: tuple[str, ...],
) -> MultiModelEvidenceReview:
    totals = _totals(compatible)
    rss: list[int | float] = []
    available: list[int | float] = []
    for item in compatible:
        for cycle in item["cycles"]:
            if cycle["rss_delta"] is not None:
                rss.append(cycle["rss_delta"])
            if cycle["available_delta"] is not None:
                available.append(cycle["available_delta"])
    return MultiModelEvidenceReview(
        state=state,
        report_count=reports,
        compatible_report_count=len(compatible),
        complete_cycles=totals["complete_cycles"],
        identity_verified_cycles=totals["identity_verified_cycles"],
        transient_overlap_cycles=totals["transient_overlap_cycles"],
        clean_accounting_cycles=totals["clean_accounting_cycles"],
        shutdown_complete_reports=totals["shutdown_complete_reports"],
        rss_after_minus_before_bytes=tuple(rss),
        available_after_minus_before_bytes=tuple(available),
        reasons=reasons,
    )


def _optional_number(value: object) -> int | float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return None


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(ch in "0123456789abcdef" for ch in value.lower())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Review compatible repeated RRG-5 multi-model evidence reports."
    )
    parser.add_argument("reports", nargs="+")
    parser.add_argument("--min-reports", type=int, default=2)
    parser.add_argument("--min-complete-cycles", type=int, default=4)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    reports = [json.loads(Path(path).read_text(encoding="utf-8")) for path in args.reports]
    review = review_multi_model_evidence(
        reports,
        settings=MultiModelReviewSettings(
            min_reports=args.min_reports,
            min_complete_cycles=args.min_complete_cycles,
        ),
    ).to_public_dict()
    rendered = json.dumps(review, indent=2, sort_keys=True) + "\n"
    if args.output:
        target = Path(args.output).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
        print(f"RRG-5 multi-model review written to {target.resolve()}")
    else:
        print(rendered, end="")

    if review["state"] != MultiModelReviewState.SUFFICIENT_OBSERVATION_SET.value:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

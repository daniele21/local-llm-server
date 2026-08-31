"""Order-sensitive diagnostic for the RRG-5 two-runtime load boundary.

The matrix reuses the bounded pair-load probe in both model orders. It is a
representative-device diagnostic only: it does not change runtime, admission,
or RRG-5 acceptance semantics.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Mapping

from .rrg5_load_probe import (
    RRG5PairLoadProbeOptions,
    run_rrg5_pair_load_probe,
)


def _projection(report: Mapping[str, object]) -> dict[str, object]:
    failure = report.get("failure")
    failure_mapping = failure if isinstance(failure, Mapping) else {}
    ports = report.get("private_ports")
    port_mapping = ports if isinstance(ports, Mapping) else {}
    return {
        "status": report.get("status"),
        "failed_phase": report.get("failed_phase"),
        "failure_category": failure_mapping.get("category"),
        "error_type": failure_mapping.get("error_type"),
        "startup_exit_code": failure_mapping.get("startup_exit_code"),
        "model_a_loaded": report.get("model_a_loaded"),
        "model_b_loaded": report.get("model_b_loaded"),
        "cleanup_complete": report.get("cleanup_complete"),
        "private_ports": dict(port_mapping),
    }


def classify_order_matrix(
    forward: Mapping[str, object],
    reverse: Mapping[str, object],
) -> str:
    """Classify whether the failure follows one model or the second-runtime slot."""
    if forward.get("status") == "refused_host_safety" or reverse.get("status") == "refused_host_safety":
        return "inconclusive_host_safety"

    forward_complete = forward.get("status") == "complete"
    reverse_complete = reverse.get("status") == "complete"
    forward_phase = forward.get("failed_phase")
    reverse_phase = reverse.get("failed_phase")

    if forward_complete and reverse_complete:
        return "both_orders_complete"
    if forward_phase == "load_model_b" and reverse_phase == "load_model_a":
        # In the reversed run, original model B occupies the first slot.
        return "original_model_b_standalone_failure"
    if forward_phase == "load_model_a" and reverse_phase == "load_model_b":
        # In the forward run, original model A occupies the first slot.
        return "original_model_a_standalone_failure"
    if forward_phase == "load_model_b" and reverse_phase == "load_model_b":
        return "second_runtime_failure_independent_of_model_order"
    if forward_phase == "load_model_b" and reverse_complete:
        return "original_model_b_fails_only_when_second"
    if forward_complete and reverse_phase == "load_model_b":
        return "original_model_a_fails_only_when_second"
    return "mixed_or_inconclusive_failure"


def run_rrg5_load_order_matrix(
    options: RRG5PairLoadProbeOptions,
) -> dict[str, object]:
    """Run pair-load diagnostics in A→B and B→A order with cleanup between runs."""
    forward = run_rrg5_pair_load_probe(options)
    reverse = run_rrg5_pair_load_probe(
        replace(
            options,
            model_a=options.model_b,
            model_a_path=options.model_b_path,
            model_b=options.model_a,
            model_b_path=options.model_a_path,
        )
    )
    classification = classify_order_matrix(forward, reverse)
    return {
        "schema_version": 1,
        "procedure": "rrg5_load_order_matrix_v1",
        "classification": classification,
        "forward_a_then_b": _projection(forward),
        "reverse_b_then_a": _projection(reverse),
        "runtime_or_acceptance_semantics_changed": False,
        "raw_backend_logs_retained": False,
    }

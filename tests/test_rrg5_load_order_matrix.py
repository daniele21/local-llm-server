from __future__ import annotations

from local_llm_server.rrg5_load_order_matrix import classify_order_matrix


def _report(status: str, failed_phase: str | None = None) -> dict[str, object]:
    return {"status": status, "failed_phase": failed_phase}


def test_classifies_both_orders_complete() -> None:
    assert classify_order_matrix(_report("complete"), _report("complete")) == "both_orders_complete"


def test_classifies_original_model_b_standalone_failure() -> None:
    assert (
        classify_order_matrix(
            _report("incomplete", "load_model_b"),
            _report("incomplete", "load_model_a"),
        )
        == "original_model_b_standalone_failure"
    )


def test_classifies_original_model_a_standalone_failure() -> None:
    assert (
        classify_order_matrix(
            _report("incomplete", "load_model_a"),
            _report("incomplete", "load_model_b"),
        )
        == "original_model_a_standalone_failure"
    )


def test_classifies_second_runtime_failure_independent_of_order() -> None:
    assert (
        classify_order_matrix(
            _report("incomplete", "load_model_b"),
            _report("incomplete", "load_model_b"),
        )
        == "second_runtime_failure_independent_of_model_order"
    )


def test_classifies_model_specific_second_slot_failure() -> None:
    assert (
        classify_order_matrix(
            _report("incomplete", "load_model_b"),
            _report("complete"),
        )
        == "original_model_b_fails_only_when_second"
    )
    assert (
        classify_order_matrix(
            _report("complete"),
            _report("incomplete", "load_model_b"),
        )
        == "original_model_a_fails_only_when_second"
    )


def test_classifies_host_safety_as_inconclusive() -> None:
    assert (
        classify_order_matrix(
            _report("refused_host_safety"),
            _report("complete"),
        )
        == "inconclusive_host_safety"
    )

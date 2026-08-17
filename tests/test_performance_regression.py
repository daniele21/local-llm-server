from __future__ import annotations

from scripts.run_performance_regression import load_policy, run_benchmark


def test_repository_performance_regression_policy_is_valid() -> None:
    policy = load_policy()
    assert policy["benchmark"] == "canonical_request_preparation"
    assert policy["max_median_ns_per_operation"] == 1_000_000


def test_benchmark_emits_identity_and_bounded_samples() -> None:
    policy = {
        "schema_version": 1,
        "benchmark": "canonical_request_preparation",
        "evidence_class": "hosted-linux-cpu-pure-python",
        "warmup_iterations": 2,
        "iterations_per_sample": 5,
        "samples": 3,
        "statistic": "median_ns_per_operation",
        "max_median_ns_per_operation": 100_000_000,
        "synthetic_input": True,
        "hardware_non_claims": [
            "model inference latency",
            "TTFT",
            "token throughput",
            "Apple Silicon performance",
        ],
    }
    result = run_benchmark(policy)
    assert result["passed"] is True
    assert len(result["sample_ns_per_operation"]) == 3
    assert result["synthetic_input"] is True
    identity = result["identity"]
    assert identity["evidence_kind"] == "ci_performance_regression"
    assert identity["comparison_key"]
    assert identity["evidence_id"]
    assert "prompt" not in str(result).lower()

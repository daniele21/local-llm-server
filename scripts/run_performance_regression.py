#!/usr/bin/env python3
"""Run one stable hosted-CI performance regression benchmark."""
from __future__ import annotations

import argparse
import json
import os
import platform
from pathlib import Path
from statistics import median
import subprocess
import sys
import time
from typing import Any, Mapping

from local_llm_server.evidence_identity import build_evidence_identity
from local_llm_server.request_pipeline import prepare_chat_request

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / ".engineering" / "performance-regression.json"

_SYNTHETIC_PAYLOAD = {
    "model": "benchmark-model",
    "messages": [{"role": "user", "content": "synthetic benchmark input"}],
    "max_output_tokens": 32,
    "temperature": 0.0,
    "stream": False,
}
_RUNTIME_CONFIG = {
    "model": "benchmark-model",
    "model_id": "benchmark/runtime",
    "modalities": ["text"],
    "thinking_mode": "none",
    "default_temperature": 0.0,
    "default_top_p": 0.95,
    "default_top_k": 40,
    "default_min_p": 0.0,
    "default_repeat_penalty": 1.0,
    "force_json": False,
}


def load_policy(path: Path = POLICY) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("performance regression policy schema_version must be 1")
    required_positive = (
        "warmup_iterations",
        "iterations_per_sample",
        "samples",
        "max_median_ns_per_operation",
    )
    for key in required_positive:
        item = value.get(key)
        if not isinstance(item, int) or isinstance(item, bool) or item <= 0:
            raise ValueError(f"{key} must be a positive integer")
    if value.get("statistic") != "median_ns_per_operation":
        raise ValueError("only median_ns_per_operation is supported")
    non_claims = value.get("hardware_non_claims")
    if not isinstance(non_claims, list) or len(non_claims) < 4:
        raise ValueError("hardware_non_claims must preserve the hosted-CI evidence boundary")
    return value


def _one_operation() -> None:
    prepared = prepare_chat_request(
        _SYNTHETIC_PAYLOAD,
        runtime_config=_RUNTIME_CONFIG,
        runtime_model_id="benchmark/runtime",
    )
    if prepared.backend.max_tokens != 32 or prepared.required_modalities != frozenset({"text"}):
        raise AssertionError("benchmark operation produced an unexpected request contract")


def _source_revision() -> str | None:
    from_env = os.getenv("GITHUB_SHA")
    if from_env:
        return from_env.strip() or None
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=2.0,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return completed.stdout.strip() or None


def run_benchmark(policy: Mapping[str, Any]) -> dict[str, object]:
    warmup = int(policy["warmup_iterations"])
    iterations = int(policy["iterations_per_sample"])
    samples = int(policy["samples"])
    threshold = int(policy["max_median_ns_per_operation"])

    for _ in range(warmup):
        _one_operation()

    timings: list[int] = []
    for _ in range(samples):
        started = time.perf_counter_ns()
        for _ in range(iterations):
            _one_operation()
        elapsed = time.perf_counter_ns() - started
        timings.append(max(0, elapsed // iterations))

    observed = int(median(timings))
    environment_class = "-".join(
        (
            "hosted" if os.getenv("CI") else "local",
            platform.system().lower() or "unknown",
            platform.machine().lower() or "unknown",
            f"python{platform.python_version_tuple()[0]}.{platform.python_version_tuple()[1]}",
        )
    )
    identity = build_evidence_identity(
        evidence_kind="ci_performance_regression",
        workload={
            "benchmark": str(policy["benchmark"]),
            "warmup_iterations": warmup,
            "iterations_per_sample": iterations,
            "samples": samples,
            "synthetic_input": True,
        },
        configuration={
            "statistic": "median_ns_per_operation",
            "threshold_ns_per_operation": threshold,
            "request_path": "prepare_chat_request",
        },
        environment_class=environment_class,
        source_revision=_source_revision(),
        runtime_identity={
            "python_implementation": platform.python_implementation().lower(),
            "python_version": platform.python_version(),
        },
    )
    return {
        "schema_version": 1,
        "identity": identity.to_dict(),
        "benchmark": str(policy["benchmark"]),
        "statistic": "median_ns_per_operation",
        "observed_ns_per_operation": observed,
        "threshold_ns_per_operation": threshold,
        "sample_ns_per_operation": timings,
        "passed": observed <= threshold,
        "synthetic_input": True,
        "hardware_non_claims": list(policy["hardware_non_claims"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        policy = load_policy()
        result = run_benchmark(policy)
    except (OSError, ValueError, AssertionError, json.JSONDecodeError) as exc:
        print(f"Performance regression: FAIL: {exc}")
        return 1
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    if not result["passed"]:
        print("RESULT: FAIL: median request-preparation time exceeded policy threshold", file=sys.stderr)
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

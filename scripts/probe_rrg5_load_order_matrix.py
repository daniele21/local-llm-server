#!/usr/bin/env python3
"""Run the bounded RRG-5 pair-load probe in both model orders."""
from __future__ import annotations

import argparse
import json

from local_llm_server.rrg5_load_order_matrix import run_rrg5_load_order_matrix
from local_llm_server.rrg5_load_probe import RRG5PairLoadProbeOptions

_MIB = 1024**2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run RRG-5 load A→B and B→A to classify model-vs-second-runtime failures."
    )
    parser.add_argument("--model-a", required=True)
    parser.add_argument("--model-a-path", default=None)
    parser.add_argument("--model-b", required=True)
    parser.add_argument("--model-b-path", default=None)
    parser.add_argument("--backend", default="llama_server")
    parser.add_argument("--request-estimate-mib", type=float, required=True)
    args = parser.parse_args()

    report = run_rrg5_load_order_matrix(
        RRG5PairLoadProbeOptions(
            model_a=args.model_a,
            model_a_path=args.model_a_path,
            model_b=args.model_b,
            model_b_path=args.model_b_path,
            backend=args.backend,
            request_estimate_bytes=int(args.request_estimate_mib * _MIB),
        )
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    classification = report.get("classification")
    if classification == "both_orders_complete":
        return 0
    if classification == "inconclusive_host_safety":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

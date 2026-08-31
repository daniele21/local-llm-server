#!/usr/bin/env python3
"""Run the bounded RRG-5 double-load diagnostic on a representative Mac."""
from __future__ import annotations

import argparse
import json

from local_llm_server.rrg5_load_probe import (
    RRG5PairLoadProbeOptions,
    run_rrg5_pair_load_probe,
)

_MIB = 1024**2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Load RRG-5 model A then B, classify bounded startup failure, and clean up."
    )
    parser.add_argument("--model-a", required=True)
    parser.add_argument("--model-a-path", default=None)
    parser.add_argument("--model-b", required=True)
    parser.add_argument("--model-b-path", default=None)
    parser.add_argument("--backend", default="llama_server")
    parser.add_argument("--request-estimate-mib", type=float, required=True)
    args = parser.parse_args()

    report = run_rrg5_pair_load_probe(
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
    if report.get("status") == "complete":
        return 0
    if report.get("status") == "refused_host_safety":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

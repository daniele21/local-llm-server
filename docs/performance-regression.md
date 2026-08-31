# Hosted performance regression gate

Status: active
Owner: runtime-and-platform
Canonical scope: current.performance-regression
Last reviewed: 2026-08-17

L2 blocks regressions only on a path whose measurement is stable enough for hosted CI: canonical chat request preparation before backend execution. `.engineering/performance-regression.json` owns warm-up, repetitions, statistic and threshold; `scripts/run_performance_regression.py` executes the benchmark.

The runner uses synthetic text, performs multiple timed samples after warm-up, gates on median nanoseconds per operation and emits a privacy-safe `EvidenceIdentity` envelope with source revision, environment class and workload/configuration fingerprints. Raw prompt/output data is not retained in evidence.

The gate does not measure model inference latency, TTFT, token throughput, backend startup, Apple Silicon performance or thermal behavior. Those remain representative-device evidence.

The integration slice wires this runner into a blocking L2 health job and retains only bounded identity-bearing JSON when useful for a failure investigation.

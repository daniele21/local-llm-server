# Deterministic resource regression contract

Status: active
Owner: runtime-and-platform
Canonical scope: current.resource-regression
Last reviewed: 2026-08-17

L2 hosted CI proves only Python-owned resource-ledger behavior that is stable without a model or accelerator. `.engineering/resource-regression.json` maps each claim to an exact test and preserves explicit non-claims.

The gate repeatedly exercises successful reserve/commit/release cycles, repeated rejected admission, and bounded retained Python heap after a warm-up using `tracemalloc`. Each completed lifecycle must leave the `ResourceManager` ledger empty.

This evidence does **not** prove native backend memory reclamation, Apple unified-memory or accelerator reclamation, RSS return-to-baseline, or automatic pressure-eviction safety. Those remain representative-device claims owned by the hardware evidence workstream.

Run `python3 scripts/verify_resource_regression.py` for contract integrity; normal pytest executes the behavioral and heap regression tests. Shared Repository Health integration remains L2-10.

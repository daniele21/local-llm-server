# Performance and resource budgets

Status: active
Owner: runtime-and-platform
Canonical source: `.engineering/performance-budgets.json`
Read when: changing runtime limits, release performance claims or representative-device evidence
Last reviewed: 2026-08-17

## Principle

A budget is a configured limit or target with an owner and unit. An observation is a measured fact. Local LLM Server never converts an unavailable observation into zero and never treats a configured limit as proof that the runtime achieved it.

## Repository-enforceable budgets

The machine-readable contract owns deterministic operational/resource limits already present in the product and engineering lifecycle: managed-backend startup timeout, inference timeout, default per-runtime concurrency, default context capacity, local successful-build retention and Playwright failure-evidence retention.

`python3 scripts/verify_performance_budgets.py` rejects missing owners/units/sources, duplicate IDs, non-positive maxima or repository entries that are not explicitly CI-enforceable. L1 integration wires this validator into Repository Health.

## Representative-device budgets

TTFT, decode throughput, peak/post-unload memory and real shutdown time depend materially on model, backend, device and configuration. They therefore require an explicit evidence campaign identity rather than one universal cross-hardware threshold.

Every representative performance claim must record at least:

- model/artifact fingerprint;
- backend/runtime version;
- resolved runtime configuration;
- hardware/OS identity;
- startup time;
- TTFT;
- decode tokens/second;
- peak memory;
- post-unload memory;
- shutdown time;
- campaign-specific target/threshold and rationale when a pass/fail claim is made.

The evidence procedure remains owned by `device-evidence-runbook.md`. A missing campaign threshold means the run is descriptive evidence, not a product pass/fail performance certification.

## Changing a budget

A change to a repository hard/default budget must update its actual product/config owner and this contract together. A change to a representative-device target must be tied to a named hardware/model/backend profile and retained evidence. Do not loosen a threshold merely to make a failing run green without documenting the reason and expected product impact.

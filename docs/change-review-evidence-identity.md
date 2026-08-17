# Complexity review and evidence identity

Status: active
Owner: repository engineering
Canonical scope: engineering.reference-grade-governance
Last reviewed: 2026-08-17

L2 treats new complexity and decision-bearing evidence as explicit engineering surfaces.

## Complexity review

`.engineering/change-review-policy.json` owns the scopes and five questions required when a change adds a dependency/toolchain, changes an architecture or ownership boundary, changes a persisted/public contract, adds concurrency/resource lifecycle, broadens a network/trust boundary, or materially changes build/release/evidence machinery.

The pull-request template contains one machine-checked marker for each question. Meaningful changes answer them concretely; non-applicable changes state `N/A` with the reason. `scripts/verify_change_review.py` prevents the template and policy from silently drifting apart.

## Evidence identity

`local_llm_server.evidence_identity` provides a common privacy-safe identity envelope for benchmark/evidence runs that influence engineering decisions. It stores fingerprints rather than raw workload/configuration payloads and records:

- evidence kind and unique run identity;
- source revision when available;
- environment class;
- workload/configuration fingerprints;
- optional runtime-identity fingerprint;
- a stable comparison key for repeated compatible setups;
- a unique evidence ID for the concrete run.

Raw prompt/output and private host/path/user keys are rejected from identity inputs. Domain-specific evidence keeps its own result schema; this envelope standardizes reproducibility/attribution, not metrics.

The deterministic L2 performance lane reuses this envelope. Representative-device evidence remains responsible for truthful hardware/runtime identity and does not invent unavailable fields.

# Current State

Status: active
Last reviewed: 2026-08-17

Local LLM Server is a local-first, privacy-preserving multi-backend inference server with deterministic hosted-CI boundaries and representative-device evidence for hardware-dependent claims.

## Engineering baseline

- Standard: `daniele21/repo-template-sw` `0.3.0`, pinned to revision `41ba67a124b0daa33db2a02055d76897391d7092`.
- **L2 repository-side engineering is complete** at acceptance revision `d528b6c5b676e705e7ccf24800929da6d5534203`.
- Full L2 remains **hardware-gate pending**; representative Apple Silicon/model/backend claims are not inferred from hosted CI.
- L1 acceptance revision: `d068a76d07bf204ca58ee2dfc29890bf3f1177cb`.
- Canonical branch protection remains intentionally deferred by the owner.
- Profiles: Python, local-AI, TypeScript and macOS.

## L2 repository capabilities

The accepted repository baseline includes:

- AST-backed architecture ownership/dependency fitness rules;
- deterministic resource-ledger and retained-Python-heap regression evidence with native/unified-memory non-claims;
- reproducible synthetic request-preparation performance regression with warm-up, repeated samples, 100 µs/op median ceiling and identity-bearing evidence;
- critical fault-injection/recovery coverage across resource, worker, persistence, pressure and request lifecycles;
- explicit repeatability/cleanliness evidence for development, test, E2E, build, smoke and runtime lifecycles;
- fresh-installed-wheel HTTP failure → retry → recovery using real localhost Uvicorn and bounded shutdown;
- five-question complexity/dependency review plus privacy-safe reproducible evidence identity;
- documentation/repository drift detection for freshness, canonical scope, duplicate bodies, workstream consistency and completed-workstream cleanup.

Repository Health permanently runs all L1/L2 structural fitness functions. `L2 Performance Regression` is a separate blocking timed gate; Artifact Lifecycle, Security Audit, Package Install Smoke, Python 3.10/3.11/3.12, lint, Playwright and zero-residue remain part of the accepted validation surface.

## Remaining L2 gate

Only `L2-11` remains blocked. Full L2 requires compatible retained physical evidence from `docs/workstreams/runtime-correctness-evidence-hardening.md`, including the outstanding target-Mac/model/backend correctness, evaluation, reclamation and resource-policy runs relevant to hardware-dependent claims.

Hosted CI does not prove Apple unified/native/accelerator memory reclamation, backend/model TTFT or throughput, thermal behavior, backend-specific thinking behavior, or representative-hardware pressure-eviction safety.

## Active workstreams

- `docs/workstreams/l2-reference-grade.md` — full-L2 hardware evidence gate and final state transfer.
- `docs/workstreams/runtime-correctness-evidence-hardening.md` — representative-device runtime correctness and evidence.

## Durable operational references

- `docs/architecture.md`
- `docs/architecture-fitness.md`
- `docs/resource-regression-contract.md`
- `docs/performance-regression.md`
- `docs/fault-injection-contract.md`
- `docs/repeatability-contract.md`
- `docs/built-surface-e2e.md`
- `docs/change-review-evidence-identity.md`
- `docs/device-evidence-runbook.md`

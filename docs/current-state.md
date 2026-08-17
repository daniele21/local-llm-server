# Current State

Status: active
Last reviewed: 2026-08-17

Local LLM Server is a local-first, privacy-preserving multi-backend inference server with deterministic hosted-CI boundaries and representative-device evidence for hardware-dependent claims.

## Engineering baseline

- Standard: `daniele21/repo-template-sw` `0.3.0`, pinned to revision `41ba67a124b0daa33db2a02055d76897391d7092`.
- Repository-side target: **L2 integration validation**; upstream 0.4.0 is intentionally out of scope.
- L1 acceptance revision: `d068a76d07bf204ca58ee2dfc29890bf3f1177cb`.
- Canonical branch protection remains intentionally deferred by the owner.
- Profiles: Python, local-AI, TypeScript and macOS.

## L2 repository capabilities

Converged on the L2-10 integration branch:

- AST-backed architecture ownership/dependency fitness rules;
- deterministic resource-ledger and retained-Python-heap regression evidence with native/unified-memory non-claims;
- reproducible synthetic request-preparation performance regression using warm-up, repeated samples, median gating and evidence identity;
- critical fault-injection/recovery matrix across resource, worker, persistence, pressure and request lifecycles;
- explicit repeatability/cleanliness evidence for development, test, E2E, build, smoke and runtime lifecycles;
- fresh-installed-wheel HTTP failure → retry → recovery journey using real localhost Uvicorn and bounded shutdown;
- five-question complexity/dependency review plus privacy-safe reproducible evidence identity;
- stronger docs/repository drift detection: freshness, canonical scope, duplicate body, active-workstream consistency and completed-workstream cleanup.

For L2, Repository Health runs all L1 specialists plus the new architecture/resource/fault/repeatability/change-review/built-surface validators. A separate blocking `L2 Performance Regression` job runs the timed benchmark in the locked environment and retains bounded JSON evidence for seven days.

## Acceptance boundary

`L2-10` is active until one exact combined head passes CI, Repository Health, Artifact Lifecycle, Security Audit, Package Install Smoke and L2 Performance Regression.

Full L2 additionally requires representative Apple Silicon/model/backend evidence for hardware-dependent claims. That remains owned by `docs/workstreams/runtime-correctness-evidence-hardening.md`; hosted CI does not manufacture those observations. Until that evidence is complete, final L2 status remains hardware-gate pending even after repository-side acceptance.

## Active workstreams

- `docs/workstreams/l2-reference-grade.md` — repository-side integration acceptance and final hardware gate.
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

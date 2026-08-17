# Current State

Status: active
Last reviewed: 2026-08-17

Local LLM Server is a local-first, privacy-preserving multi-backend inference server with deterministic hosted-CI boundaries and representative-device evidence for hardware-dependent claims.

## Engineering baseline

- Standard: `daniele21/repo-template-sw` `0.3.0`.
- Target: **L1**, with canonical branch protection intentionally deferred by the owner.
- Profiles: Python, local-AI, TypeScript and macOS.
- Canonical setup/check/test/build/clean contracts are declared under `.engineering/commands.json`.
- Repository Health validates structure, operating contract, docs/context budgets and, at L1, specialist performance-budget, lifecycle-contract and security-exception fitness functions.

## L1 production readiness

Implemented and independently validated:

- locked Python/npm dependency resolution plus blocking Python/Node vulnerability audits;
- time-bounded machine-readable vulnerability exceptions;
- bounded schema-aware export/restore for server-owned evaluation/test-set/verification JSON state;
- machine-readable critical lifecycle failure/cancellation/shutdown contracts linked to concrete pytest evidence;
- machine-readable deterministic performance/resource budgets separated from representative-hardware measurements;
- immutable release/rollback semantics and fresh-environment wheel/CLI install smoke;
- identity-bearing, allow-listed, privacy-safe E2E failure evidence with zero-residue lifecycle verification.

`L1-08` is validating the combined exact head with CI, Repository Health, Security Audit, Artifact Lifecycle, Package Install Smoke and Playwright E2E. After that, `L1-09` transfers durable truth and removes the completed L1 workstream.

## Runtime evidence boundary

Real-runtime/model execution, Apple Silicon memory/reclamation, backend-specific performance, thinking behavior and other hardware-dependent claims remain owned by `docs/workstreams/runtime-correctness-evidence-hardening.md`. Hosted CI does not manufacture those observations.

## Active workstreams

- `docs/workstreams/l1-production-readiness.md` — integration acceptance/finalization.
- `docs/workstreams/runtime-correctness-evidence-hardening.md` — representative-device runtime correctness and evidence.

## Durable operational references

- `docs/architecture.md`
- `docs/configuration-reference.md`
- `docs/state-recovery.md`
- `docs/lifecycle-failure-contracts.md`
- `docs/security-dependency-policy.md`
- `docs/release-rollback-runbook.md`
- `docs/performance-budget-contract.md`
- `docs/device-evidence-runbook.md`

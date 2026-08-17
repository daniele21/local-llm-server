# Current State

Status: active
Last reviewed: 2026-08-17

Local LLM Server is a local-first, privacy-preserving multi-backend inference server with deterministic hosted-CI boundaries and representative-device evidence for hardware-dependent claims.

## Engineering baseline

- Standard: `daniele21/repo-template-sw` `0.3.0`.
- Repository-side target: **L1 complete**, with canonical branch protection intentionally deferred by the owner.
- L1 acceptance revision: `d068a76d07bf204ca58ee2dfc29890bf3f1177cb`.
- Profiles: Python, local-AI, TypeScript and macOS.
- Canonical setup/check/test/build/clean contracts are declared under `.engineering/commands.json`.
- Repository Health validates structure, operating contract, docs/context budgets and, at L1, specialist performance-budget, lifecycle-contract and security-exception fitness functions.

## L1 production-ready repository capabilities

- locked Python/npm dependency resolution with blocking Python/Node vulnerability audits and time-bounded exceptions;
- bounded schema-aware export/restore for server-owned evaluation/test-set/verification JSON state;
- critical lifecycle failure/cancellation/shutdown claims mapped to concrete pytest evidence;
- deterministic performance/resource budgets separated from representative-hardware measurements;
- immutable artifact/release identity, rollback semantics and fresh-environment wheel/CLI install smoke;
- identity-bearing, allow-listed, privacy-safe E2E failure evidence with blocking zero-residue verification;
- permanent CI fitness functions for performance budgets, lifecycle contracts and vulnerability-exception expiry.

The L1 acceptance revision passed normal CI, Repository Health, Artifact Lifecycle, Security Audit and Package Install Smoke on `dev`, including Python 3.10/3.11/3.12, Playwright E2E and zero-residue verification.

## Runtime evidence boundary

Real-runtime/model execution, Apple Silicon memory/reclamation, backend-specific performance, thinking behavior and other hardware-dependent claims remain owned by `docs/workstreams/runtime-correctness-evidence-hardening.md`. Hosted CI does not manufacture those observations.

## Active workstreams

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

# Current State

Status: active
Last reviewed: 2026-08-17

Local LLM Server is a local-first, privacy-preserving multi-backend inference server with deterministic hosted-CI boundaries and representative-device evidence for hardware-dependent claims.

## Engineering baseline

- Standard: `daniele21/repo-template-sw` `0.3.0`, pinned to revision `41ba67a124b0daa33db2a02055d76897391d7092`.
- Repository-side target: **L2 active**; the upstream standard has moved to 0.4.0 but that upgrade is intentionally out of this workstream.
- L1 acceptance revision: `d068a76d07bf204ca58ee2dfc29890bf3f1177cb`.
- Canonical branch protection remains intentionally deferred by the owner.
- Profiles: Python, local-AI, TypeScript and macOS.
- Canonical setup/check/test/build/clean contracts are declared under `.engineering/commands.json`.
- Repository Health already validates structure, operating contract, docs/context budgets, performance budgets, lifecycle contracts and security-exception expiry.

## L1 production-ready repository capabilities

- locked Python/npm dependency resolution with blocking Python/Node vulnerability audits and time-bounded exceptions;
- bounded schema-aware export/restore for server-owned evaluation/test-set/verification JSON state;
- critical lifecycle failure/cancellation/shutdown claims mapped to concrete pytest evidence;
- deterministic performance/resource budgets separated from representative-hardware measurements;
- immutable artifact/release identity, rollback semantics and fresh-environment wheel/CLI install smoke;
- identity-bearing, allow-listed, privacy-safe E2E failure evidence with blocking zero-residue verification;
- permanent CI fitness functions for performance budgets, lifecycle contracts and vulnerability-exception expiry.

## L2 reference-grade work

`docs/workstreams/l2-reference-grade.md` owns the L2 repository work. Independent lanes cover architecture fitness, deterministic memory/resource and performance regression, fault injection, lifecycle repeatability, built-surface E2E recovery, complexity/evidence identity and stronger repository/document drift policy. Shared CI/Repository Health wiring is deferred to the integration slice so lanes remain independently mergeable.

Full L2 additionally requires representative hardware evidence when Apple Silicon/model/backend behavior materially affects the claim. That evidence is not reproducible in hosted CI and remains a hard dependency on the runtime-evidence workstream.

## Runtime evidence boundary

Real-runtime/model execution, Apple Silicon memory/reclamation, backend-specific performance, thinking behavior and other hardware-dependent claims remain owned by `docs/workstreams/runtime-correctness-evidence-hardening.md`. Hosted CI does not manufacture those observations.

## Active workstreams

- `docs/workstreams/l2-reference-grade.md` — repository-side reference-grade engineering and final L2 evidence gate.
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

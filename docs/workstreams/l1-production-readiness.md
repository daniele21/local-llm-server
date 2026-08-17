# L1 production readiness

Status: active
Owner: repository engineering
Read when: coordinating `repo-template-sw 0.3.0` L1 adoption
Last reviewed: 2026-08-17

## Goal

Raise Local LLM Server from the repository-side L0 baseline to a truthful L1 production-ready engineering baseline without weakening local-first, privacy, resource, evidence or artifact invariants.

Branch protection is an owner-deferred exception and is not part of this workstream. Hardware-dependent claims remain owned by `runtime-correctness-evidence-hardening.md` and must not be fabricated in hosted CI.

## L1 gap assessment

Already strong enough to KEEP:

- integration/contract coverage across runtime, API, evaluation, resource, identity and artifact boundaries;
- automated Playwright critical journeys with owned zero-residue cleanup;
- immutable build identity, manifest, SHA-256, build delta, bounded retention and GitHub Release storage;
- explicit runtime/resource lifecycle rules, timeout/shutdown handling and representative-device evidence runbook;
- path-free identity and privacy-safe default telemetry semantics.

Gaps to ADAPT:

- dependency/supply-chain vulnerability scanning is not a blocking repository gate;
- persisted evaluation reports and verification receipts lack an explicit schema/migration/export/restore contract;
- critical failure/recovery coverage is distributed rather than enforced through a compact L1 contract matrix;
- performance/resource budgets are described semantically but not owned as machine-readable thresholds/claims;
- release creation is automated but operator rollback/recovery and fresh-install smoke are not first-class gates;
- Playwright failure artifacts are bounded but not yet explicitly identity-bearing/privacy-validated.

## Work graph

| ID | Work | Depends on | State | Primary write boundary |
| --- | --- | --- | --- | --- |
| L1-01 | target L1 + gap map + parallel plan | — | ACTIVE | baseline/workstream/current-state only |
| L1-02 | supply-chain security and dependency audit gate | L1-01 | READY | security workflow, dependency policy, lock/tooling |
| L1-03 | persisted-state schema, compatibility, export/restore/recovery | L1-01 | READY | evaluation/artifact state modules + CLI/tests |
| L1-04 | critical failure/cancellation/shutdown/recovery contract matrix | L1-01 | READY | lifecycle integration tests + narrowly owned fixes |
| L1-05 | performance/resource budget contract and validation | L1-01 | READY | performance budget config/docs/tests |
| L1-06 | release/rollback/recovery runbook + fresh-install artifact smoke | L1-01 | READY | release workflow/scripts/runbook |
| L1-07 | identity-bearing privacy-safe E2E failure evidence | L1-01 | READY | E2E evidence helper + CI/test docs |
| L1-08 | shared integration, repository-health convergence and L1 acceptance | L1-02..L1-07 | BLOCKED | shared workflows/baseline/current-state |
| L1-09 | transfer durable truth and delete completed workstream | L1-08 | BLOCKED | docs lifecycle only |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

## Parallel execution rules

After L1-01 merges, L1-02 through L1-07 may run in parallel from the same `dev` head. Lanes must not edit `.engineering/baseline.json`, `docs/current-state.md` or this workstream; those are reserved for L1-08 integration.

Only L1-02 may own `pyproject.toml` / `uv.lock` dependency-audit tooling. Only L1-06 may own `release.yml`. Only L1-07 may own Playwright failure-evidence wiring in `ci.yml`. If another lane needs a shared workflow change, record it for L1-08 rather than creating cross-lane drift.

## Acceptance by lane

### L1-02 — supply-chain security

- current Python and Node dependency graphs are audited with explicit severity/failure policy;
- security tooling/version is pinned or otherwise deterministically identified;
- dependency audit runs on PR/push and can also run manually/periodically;
- known exceptions, if any, are explicit, bounded and reviewed rather than silently ignored.

### L1-03 — persisted state

- every server-owned persisted JSON category has a versioned envelope or explicit compatible legacy reader;
- unknown future schema fails safely without destructive rewrite;
- export/restore covers server-owned small state without model weights/caches or arbitrary paths;
- restore validates content before promotion and does not overwrite unrelated state silently;
- migration/backward-compatibility and recovery behavior have deterministic tests.

### L1-04 — lifecycle failure contracts

- one compact test matrix proves applicable startup failure, dependency/backend failure, timeout, cancellation and shutdown cleanup at critical owners;
- no test relabels unsupported worker cancellation/streaming as supported;
- recovery leaves reservations, leases, listeners/processes and temporary owned state consistent.

### L1-05 — budgets

- important deterministic budgets have one machine-readable owner with units and applicability;
- hardware-dependent performance targets are separated from CI-enforceable structural/resource limits;
- validators reject malformed/unbounded budget entries;
- observed metrics remain distinct from configured budgets.

### L1-06 — release operations

- release runbook defines preflight, publish, verification, rollback and recovery semantics;
- rollback creates a new corrective release or points consumers to a prior immutable release; tags/assets are never rewritten;
- CI installs the produced wheel into a fresh environment and performs a bounded package/CLI smoke before publication;
- release failure cannot promote incomplete assets.

### L1-07 — E2E evidence

- failure evidence carries run/attempt/source identity without private paths or sensitive payloads;
- artifact name is collision-safe and traceable;
- retained files are explicitly allow-listed and privacy checked;
- retention remains bounded.

## L1 integration acceptance

L1-08 may move to DONE when the combined exact head passes normal CI, Repository Health, dependency/security audit, artifact lifecycle, package install smoke and E2E zero-residue/evidence checks. Real runtime/hardware observations that cannot be truthfully established in hosted CI remain linked to the existing representative-device workstream and constrain only the corresponding runtime/performance claims.

## Stop conditions

- a lane introduces cloud fallback or expands network trust implicitly;
- persisted-state recovery can delete model caches or arbitrary user data;
- a security gate downloads mutable `latest` tooling without identity;
- a performance budget encodes hardware claims that hosted CI cannot establish;
- rollback mutates an existing tag/release;
- failure evidence contains prompt/output/media/private-path content by default.

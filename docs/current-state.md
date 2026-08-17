# Current repository state

Status: active
Owner: repository
Read when: understanding what is integrated, blocked or executable next
Last reviewed: 2026-08-17

Keep this file operational and small. Detailed planning belongs in `docs/workstreams/`; durable behavior belongs in owning docs/tests.

## Current milestone

Repository-side L0 engineering work is complete. Branch protection is an owner-deferred exception. The repository engineering target is now **L1 production readiness** while representative-device runtime evidence continues separately.

## Active workstreams

| Workstream | Executable now | State | Main dependency |
| --- | --- | --- | --- |
| [`l1-production-readiness`](workstreams/l1-production-readiness.md) | `L1-02`..`L1-07` after planning merge | ACTIVE — production readiness | independent security/state/lifecycle/budget/release/E2E lanes |
| [`runtime-correctness-evidence-hardening`](workstreams/runtime-correctness-evidence-hardening.md) | `TH-E1`, `EV-3`, `HE-2`, `RES-2` | ACTIVE — device evidence | physical target-Mac execution |

## Integrated repository baseline

`dev` already has lock-backed CI, Repository Health, owned Playwright zero-residue cleanup, immutable identified wheel/sdist builds with manifest/SHA-256/delta/retention, release storage, security/data policy, architecture/ADR routing and canonical lifecycle commands.

L1 reuses those strengths rather than rebuilding them.

## L1 gaps

The remaining repository-side production-readiness gaps are:

- blocking dependency/supply-chain vulnerability audit;
- explicit schema/backward-compatibility plus export/restore/recovery for server-owned persisted JSON state;
- compact critical failure/cancellation/shutdown/recovery integration matrix;
- machine-owned performance/resource budget contract separating CI-safe limits from hardware claims;
- release/rollback/recovery runbook plus fresh-install artifact smoke;
- identity-bearing, allow-listed and privacy-checked Playwright failure evidence.

These six lanes are intentionally parallel after `L1-01` lands. Shared baseline/current-state/workstream files are reserved for the final integration slice.

## Runtime evidence still pending

Real Nemotron thinking smoke, comparable evaluation runs, verified Apple Silicon reclamation/resource reports and final runtime-dependent release claims remain owned by the runtime-correctness workstream. Hosted CI must not substitute for them.

## Next

Merge the L1 planning slice, then execute `L1-02` through `L1-07` in parallel from one exact `dev` head. Integrate only after each lane independently passes its relevant gate.

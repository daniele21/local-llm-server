# repo-template-sw baseline adoption

Status: active
Owner: repository engineering
Read when: implementing or coordinating alignment with `daniele21/repo-template-sw` baseline `0.3.0`
Last reviewed: 2026-08-17

## Goal

Make Local LLM Server self-contained and truthfully compliant with the applicable L0 requirements of `repo-template-sw` baseline `0.3.0`, while preserving stronger local-AI, testing, browser E2E, runtime-lifecycle and hardware-evidence practices.

The adopted repository must expose canonical operations, repository-health checks, identifiable immutable builds, bounded E2E evidence, explicit trust/data boundaries and low-cost agent routing without overstating unvalidated maturity.

## Invariants

- Native tooling remains behind `setup -> doctor -> dev -> check -> test -> e2e -> build -> smoke -> package -> stop -> clean`.
- Public runtime, identity, evidence and privacy contracts remain compatible unless explicitly versioned.
- Product version, unique build identity and source identity remain distinct.
- Successful artifacts are immutable; build/release operations use explicit ownership and bounded retention.
- Project-owned processes, listeners, temporary files and evidence are cleaned on every applicable exit path.
- Hardware/performance/memory claims require representative hardware evidence; hosted CI never substitutes for it.
- Existing stronger practices are `KEEP`/`ADAPT`, not overwritten for template uniformity.
- Shared command/workflow/state files have one integration owner at a time.

## Applicable baseline

- Standard: `daniele21/repo-template-sw` `0.3.0`.
- Target: truthful `L0`.
- Profiles: `python`, `local-ai`, `typescript`/JavaScript and runtime-relevant `macos`.
- Native `.app`/`.dmg`, signing and notarization: `N/A` for the wheel/sdist product.

## Work graph

| ID | Work | Depends on | State |
| --- | --- | --- | --- |
| STD-01 | baseline metadata + canonical operating contract | — | DONE |
| STD-02 | agent routing, core Skills, validators, contribution/PR governance | STD-01 | DONE |
| STD-03 | reproducible setup/check/test and lock-backed CI | STD-01 | DONE |
| STD-04 | unique build identity + immutable artifact/release lifecycle | STD-01 | DONE |
| STD-05 | E2E run ownership, zero-residue and bounded failure evidence | STD-01 | DONE |
| STD-06 | security/data lifecycle + MIT license | STD-01 | DONE |
| STD-07 | current architecture + ADR/feature/document topology | STD-06 | DONE |
| STD-08 | shared workflow/command integration + external branch-policy evidence | STD-02..STD-07 | ACTIVE |
| STD-09 | full applicable operating lifecycle + repository-health validation | STD-08 | BLOCKED |
| STD-10 | transfer final durable truth and remove this workstream | STD-09 | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

## Integrated lane evidence

- `STD-01`: PR #116, merge `1a66e185f7fac59659f4725f7e97c78a50b42a73`.
- `STD-02/03`: PR #118, merge `3eab70c34975d4bf2d951eb13a7de6519fa3271c`; lock-backed CI passed lint, Python 3.10/3.11/3.12 and Playwright.
- `STD-04`: PR #119, merge `b2a82f6758900b3b7716c2bc4b7918b451ec7b2f`; immutable artifact helper tests and normal CI passed after rebasing onto the lock-backed tree.
- `STD-05`: PR #120, merge `a90bdd913d32d328ccefcb6b682f02f3a25d9a5d`; lifecycle tests and Playwright passed after rebasing onto the lock-backed tree.
- `STD-06`: PR #117, merge `f6733fb8318cf7a0e990a4ac5579cebd1d78ceec`.
- `STD-07`: PR #121, merge `9827e9771ae4094374ae5bfd01291bd44fc120ae`; current architecture/ADR/features routing integrated and the completed E2E workstream was transferred/deleted.

The parallel phase is complete. No further adoption lane may bypass `STD-08` shared integration.

## Current executable slice — STD-08

### Integration changes

- install `.github/workflows/repository-health.yml` as a blocking zero-dependency structural/operations/docs/context gate;
- wire `tests/e2e/verify_residue.py` as an always-run post-Playwright CI step;
- bound Playwright failure evidence to seven days;
- mark the installed core Skills as project-customized in `.engineering/baseline.json`;
- reconcile `.engineering/commands.json` with lock-backed setup/check/test, owned E2E cleanup, real-runtime smoke and implemented build/artifact behavior;
- update only this workstream's repository-level current-state routing.

### External branch-policy evidence

Authenticated GitHub branch state was inspected on 2026-08-17. `dev` currently reports:

```text
protected = false
required status checks = off
```

This is an explicit external configuration gap. The repository now defines CI/health gates, but adoption work must not claim that GitHub enforces those checks on `dev` until branch protection/rulesets are configured and re-verified. No branch-protection write tool is available in the current GitHub connector, so the gap remains pending rather than being silently assumed.

### Acceptance

`STD-08` can move to `DONE` when:

1. Repository Health passes on the combined integration head.
2. Normal CI passes lint + Python 3.10/3.11/3.12 + Playwright on the same head.
3. The Playwright job always performs independent residue verification.
4. Failure artifacts have explicit seven-day retention.
5. Canonical command/baseline metadata agrees with executable behavior.
6. The external `dev` branch-policy gap is recorded as pending rather than claimed as enforced.

## STD-09 lifecycle validation

After `STD-08` merges, execute the applicable lifecycle on one exact integrated revision:

```text
repository health
check
test
e2e + residue verification
build #1
build #2 from the same source revision
inspect manifest / SHA256SUMS / BUILD_CHANGELOG / lineage retention
real-runtime smoke when a suitable already-running target runtime is available
clean
```

Also verify failed/partial staging does not appear as successful output and local retention leaves two successful comparable builds per lineage.

Unavailable representative hardware or runtime-dependent observations remain `PENDING`; do not manufacture them in hosted CI.

## Slice acceptance summary

| Slice | Durable acceptance |
| --- | --- |
| STD-02 | bounded project-specific AGENTS/Skills/validators/PR guidance |
| STD-03 | committed Python/Node lock state; deliberate Python 3.10/3.11/3.12 CI; no manual dependency list as source of truth |
| STD-04 | unique build identity, staging/promote, manifest, SHA-256, build delta, retention=2, immutable tags/releases |
| STD-05 | owned E2E root/shutdown, bounded readiness/shutdown, independent listener/temp residue check, bounded failure evidence |
| STD-06 | vulnerability reporting, supported versions, local trust/data defaults and MIT license |
| STD-07 | current architecture owner, ADR/features routing, completed workstreams deleted by default |
| STD-08 | combined repository-health/CI/command integration and explicit external branch-policy evidence |
| STD-09 | repeatable applicable lifecycle with residue/artifact inspection |

## Stop conditions

- A wrapper would create a second source of truth instead of routing to native commands.
- A lane/integration would weaken runtime, privacy, evidence or artifact invariants.
- Build identity would expose secrets/private paths or collapse product version and build ID.
- Cleanup cannot prove ownership before deletion.
- GitHub/external/hardware behavior cannot be verified: record it as pending instead of claiming success.

## Durable destinations

- `.engineering/`: adopted baseline, command mapping and lifecycle contract.
- `AGENTS.md` + `skills/`: bounded agent routing/skills.
- `docs/architecture.md`, `docs/adr/`, `docs/features/`: current architecture, durable decisions and feature behavior.
- `SECURITY.md`: trust/data/disclosure policy.
- tests/validators/workflows: executable repository and operating invariants.
- `docs/current-state.md`: compact operational routing only.

## Completion

This workstream completes only after `STD-09` establishes all applicable lifecycle claims, external gaps remain explicit, and durable docs agree with executable behavior. `STD-10` then updates final baseline/current state, removes the workstream index entry and deletes this file by default; Git history remains the adoption record.

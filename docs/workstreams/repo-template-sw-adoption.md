# repo-template-sw baseline adoption

Status: active
Owner: repository engineering
Read when: implementing or coordinating alignment with `daniele21/repo-template-sw` baseline `0.3.0`
Last reviewed: 2026-08-17

## Goal

Make Local LLM Server self-contained and truthfully compliant with the applicable L0 requirements of `repo-template-sw` baseline `0.3.0`, while preserving the repository's stronger local-AI, testing, browser E2E, runtime-lifecycle and hardware-evidence practices.

The result must include canonical commands, repository-health checks, identifiable immutable builds, bounded E2E evidence, explicit trust/data boundaries and low-cost agent routing. Record stronger evidence without claiming unvalidated maturity.

## Non-goals

- Replacing native tooling, copying placeholders or forcing cosmetic layouts.
- Changing local-AI, scheduling, residency, reasoning or evaluation semantics.
- Reclassifying pending device evidence or broadening release claims.
- Deleting or committing the current untracked `evidence/` tree before its durable storage and privacy policy is decided.
- Adding Docker, Make, a new E2E framework or native macOS packaging without a product need.

## Invariants

- Native commands remain the implementation behind the common `setup -> doctor -> dev -> check -> test -> e2e -> build -> smoke -> package -> stop -> clean` vocabulary.
- Public runtime, identity, evidence and privacy contracts remain compatible unless explicitly versioned.
- Build version, build identity and source identity remain distinct; successful artifacts are immutable and never replaced in place.
- Operations own and clean processes, listeners, temporary files and evidence on every exit path.
- Hardware claims require hardware evidence; the runtime-correctness workstream owns device observations and release claims.
- Shared state, package, command-contract and workflow files have one integration owner at a time.
- Existing stronger project practices are classified `KEEP` or `ADAPT`, not overwritten for template uniformity.

## Applicable baseline

- Source/version: `daniele21/repo-template-sw` / `0.3.0`; initial target: truthful L0 compliance.
- Profiles: `python`, `local-ai`, `typescript`/JavaScript and runtime-relevant `macos`.
- Native `.app`/`.dmg` packaging, signing and notarization are `N/A` for the wheel/sdist product.

## Work graph

| ID | Work | Owns/writes | Depends on | Parallel | State |
| --- | --- | --- | --- | --- | --- |
| STD-01 | Establish baseline metadata and canonical operating-command contract | `.engineering/baseline.json`, `.engineering/commands.json`, `.engineering/documentation-policy.json` | — | no; foundation | READY |
| STD-02 | Install and specialize agent routing, core Skills and repository validators | `AGENTS.md`, `skills/**`, `scripts/verify_*.py`, `.editorconfig`, `CONTRIBUTING.md`, `.github/pull_request_template.md` | STD-01 | lane A | BLOCKED |
| STD-03 | Make setup/check/test and CI dependency resolution reproducible | `.github/workflows/ci.yml`, setup/check/test command implementation, lockfile usage | STD-01 | lane A | BLOCKED |
| STD-04 | Implement unique build identity and immutable artifact lifecycle | `deploy.sh`, `release.sh`, `.github/workflows/release.yml`, build/artifact scripts and tests | STD-01 | lane B | BLOCKED |
| STD-05 | Enforce E2E/runtime zero-residue and bounded failure evidence | `tests/e2e/**`, `playwright.config.js`, E2E lifecycle tests; CI handoff notes only | STD-01 | lane C | BLOCKED |
| STD-06 | Add security, data-lifecycle, contribution and license baseline | `SECURITY.md`, `LICENSE`, security/data sections not owned by active evidence docs | STD-01 | lane D | BLOCKED |
| STD-07 | Normalize architecture and documentation topology without losing durable content | `docs/architecture.md`, `docs/adr/**`, `docs/features/**`, documentation routing/policy | STD-01 | lane D | BLOCKED |
| STD-08 | Integrate shared workflows, health CI, PR gates and branch-policy evidence | `.github/workflows/**`, `README.md`, `.engineering/commands.json`, shared integration fixes | STD-02, STD-03, STD-04, STD-05, STD-06, STD-07 | no; integration | BLOCKED |
| STD-09 | Run full operating-lifecycle and repository-health validation | validation evidence only; fixes return to owning slice | STD-08 | no | BLOCKED |
| STD-10 | Transfer durable truth, record baseline and delete this workstream | `docs/current-state.md`, `docs/workstreams/README.md`, final baseline metadata | STD-09 | no | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

Parallel work is allowed only inside the declared path boundaries. A lane that discovers a required change in a shared integration file records the handoff under its slice and leaves the actual shared-file edit to STD-08.

## Parallel execution model

After STD-01 is merged into `dev`, use four non-conflicting lanes:

| Lane | Slices | Primary concern | Must not edit concurrently |
| --- | --- | --- | --- |
| A — governance/reproducibility | STD-02, STD-03 | agent routing, validators, locked setup/check/test | release/build scripts; product/evidence docs |
| B — build/release | STD-04 | build ID, staging/promote, manifest, checksum, delta, retention, immutable tags | CI workflow and docs owned by other lanes |
| C — E2E lifecycle | STD-05 | fixture cleanup, listener/process/temp verification, evidence retention contract | `.github/workflows/ci.yml`; hand off retention edits to STD-08 |
| D — trust/docs | STD-06, then STD-07 | security/data policy, license, current architecture, ADR/feature topology | evidence results, release claims and active runtime workstream content |

Within lane A, STD-02 and STD-03 may run concurrently after STD-01 if STD-02 does not edit `.github/workflows/ci.yml`. Within lane D, run STD-06 before STD-07 because trust/data ownership feeds the architecture document.

Use one focused branch/PR per lane from current `dev`; update it before STD-08. Never resolve conflicts by dropping another lane's invariant.

## Current executable slice

`STD-01`

Acceptance:

- `.engineering/baseline.json` records standard `0.3.0`, the selected profiles, truthful target level and local Skill customization state.
- `.engineering/commands.json` maps every canonical intent to a real native command or a justified `n/a`.
- `setup`, `check`, `test`, `build` and `clean` are not `n/a`.
- `e2e` maps to the existing Playwright suite; it is not conflated with smoke.
- local runtime, build identity, artifact lifecycle and ephemeral-resource sections describe the intended enforceable contract rather than current wishful behavior.
- unresolved implementation gaps are represented by this workstream, not hidden behind placeholder commands.

Validation:

- `python3 scripts/verify_operations.py` once the validator is installed by STD-02; until then validate JSON syntax and command existence directly.
- Review each command against `README.md`, `docs/getting-started.md`, CI, `deploy.sh`, `release.sh`, `package.json` and the actual CLI entrypoints.

## Slice acceptance and validation

| Slice | Acceptance | Validation |
| --- | --- | --- |
| STD-02 | Bounded project-specific `AGENTS.md`; versioned core Skills; zero-dependency repository/operations/docs/context validators; PR guidance distinguishes test, E2E, smoke and device evidence. | Run all `scripts/verify_*.py` checks. |
| STD-03 | CI consumes committed Python/Node lock state; Python 3.10/3.11/3.12 support remains deliberate; Ruff, pytest and browser setup have one canonical path; current gates remain blocking. | Run canonical `check` and `test` from a clean environment; verify workflow/lock synchronization. |
| STD-04 | Each build carries product version, unique build ID, revision and dirty state; staging/promote prevents partial success; artifacts include manifest, SHA-256 and delta; two builds retained per lineage; tags are immutable. | Build twice from one revision without overwrite; test failed staging, manifest/checksum/delta and retention. |
| STD-05 | Playwright fixture cleans its evaluation root and owns shutdown; loopback startup/readiness is bounded; no process/listener/temp residue; privacy-safe failure evidence has explicit retention. | Run successful and controlled-failure E2E; verify processes, port and run-owned temp state are gone after both. |
| STD-06 | `SECURITY.md` defines reporting, supported versions, trust and sensitive-data defaults; MIT `LICENSE` matches package metadata. | Repository validator plus policy review against actual runtime/data behavior. |
| STD-07 | `docs/architecture.md` owns current boundaries/resources/trust flows; ADR/feature routing is explicit; progress remains only in current state and active workstreams. | Documentation/context validators and link/canonical-owner review. |
| STD-08 | Health checks and bounded E2E artifacts are integrated without duplicate setup; branch rules/checks are verified or explicitly pending. | Inspect shared workflow diff and authenticated GitHub state when available. |
| STD-09 | Applicable canonical lifecycle is repeatable and leaves no owned residue; unavailable hardware/external evidence remains pending. | Run health checks plus `check`, `test`, `e2e`, `build`, `smoke`, `stop`, `clean`; compare state before/after. |

## Integration points

- STD-01 freezes command names and operating semantics before parallel implementation begins.
- STD-03 hands CI dependency/setup requirements to STD-08; STD-05 hands E2E retention/upload requirements to STD-08.
- STD-04 owns build/release scripts and workflow until integration.
- STD-06 supplies trust/data ownership to STD-07's architecture map.
- The runtime-correctness workstream owns the device runbook, observations, roadmap evidence and release claims.
- Edits to `docs/current-state.md` are serialized: this workstream adds/removes only its own row; evidence status remains owned by the runtime-correctness workstream.
- Current untracked `evidence/` files are neither deleted nor committed by adoption work. STD-06/STD-08 must decide and document their durable storage/retention boundary first.

## Stop conditions

- A wrapper would create a second command source of truth, or a lane must weaken an existing invariant.
- Build identity would expose secrets/private paths or collapse product version and build ID.
- Cleanup cannot prove ownership, or a documentation move would discard durable truth.
- GitHub branch protection or other external configuration cannot be verified: record it as pending instead of claiming completion.

## Durable documentation destinations

- `.engineering/`: adopted baseline, profiles, command mapping and lifecycle contract.
- `AGENTS.md`: bounded routing, ownership and invariants.
- `docs/architecture.md`: current boundaries, resources, trust/data flow and composition roots.
- `docs/adr/` and `docs/features/`: durable decisions/behavior lacking a better canonical owner.
- `SECURITY.md`: disclosure process, supported versions and security/trust expectations.
- tests, validators and CI: executable truth for repository and operating invariants.

## Completion

This workstream is complete only when all slices are `DONE`, applicable operating commands and health checks pass, builds and E2E demonstrate their promised lifecycle behavior, external configuration gaps are explicit, and durable docs agree with executable behavior.

At completion, update `.engineering/baseline.json` and `docs/current-state.md`, remove this entry from `docs/workstreams/README.md`, then delete this file by default. Git history remains the adoption history.

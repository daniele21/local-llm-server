# repo-template-sw baseline adoption

Status: active
Owner: repository engineering
Read when: completing or verifying alignment with `daniele21/repo-template-sw` baseline `0.3.0`
Last reviewed: 2026-08-17

## Goal

Make Local LLM Server truthfully compliant with the applicable L0 requirements of `repo-template-sw` `0.3.0`, preserving stronger local-AI, testing, E2E, lifecycle and hardware-evidence practices.

## Applicable baseline

- Standard: `daniele21/repo-template-sw` `0.3.0`.
- Target: `L0`.
- Profiles: `python`, `local-ai`, `typescript`, runtime-relevant `macos`.
- Native `.app`/`.dmg`, signing/notarization: `N/A` for the wheel/sdist product.

## Work graph

| ID | Work | State |
| --- | --- | --- |
| STD-01 | baseline metadata + canonical operating contract | DONE |
| STD-02 | agent routing, Skills, validators, contribution/PR governance | DONE |
| STD-03 | lock-backed reproducible setup/check/test/CI | DONE |
| STD-04 | unique build identity + immutable artifact/release lifecycle | DONE |
| STD-05 | E2E run ownership, zero-residue + bounded failure evidence | DONE |
| STD-06 | security/data lifecycle + MIT license | DONE |
| STD-07 | current architecture + ADR/feature/document topology | DONE |
| STD-08 | shared workflow/command integration | DONE |
| STD-09 | canonical operating/artifact lifecycle validation | DONE |
| STD-10 | final L0 transfer + delete workstream | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

## Repository-side implementation — complete

Integrated through PRs #116–#123. The repository now has:

- `.engineering` baseline, documentation policy and canonical command contract;
- bounded root agent routing, five project-customized core Skills and zero-dependency repository/operations/docs/context validators;
- committed Python/Node lock state and Python 3.10/3.11/3.12 deterministic CI;
- mandatory Playwright product acceptance with process-level fixture ownership, bounded graceful shutdown, independent zero-residue verification and seven-day failure-evidence retention;
- MIT license, security/trust/data-lifecycle policy, current architecture, ADR/feature routing and delete-by-default completed-workstream lifecycle;
- unique build/source identity, staging/promote, manifest, SHA-256 inventory, build delta, retention=2 and immutable tag/release behavior;
- packaging toolchain in the committed lock; canonical `./deploy.sh` uses the synchronized environment with no hidden sync/resolution;
- release-style version bump updates `pyproject.toml`, `VERSION` and only the local editable project version in `uv.lock`, then verifies the lock without dependency re-resolution.

## STD-08 evidence

PR #122 merged as `dde269c0e489677de3cf78f9656880914ed27673` after the same exact feature head passed:

- repository/operations/docs/agent-context health checks;
- artifact lifecycle with real wheel/sdist builds;
- lint and Python 3.10/3.11/3.12 tests;
- Playwright product acceptance and independent zero-residue verification.

The E2E integration uncovered and fixed a real lifecycle defect: Playwright originally outlived the temp-state cleanup boundary. The final design makes `fixture_runner.py` the explicit process/root owner and validates zero residue after shutdown.

## STD-09 evidence

PR #123 merged as `d302075fe54aa2e6499bd53d3811823d81db3ba3`. On its exact feature head `530d68af63ce54838eb6f7c1c5c69b6819b6c168`, both `CI` and `Repository Health` completed successfully.

The permanent artifact lifecycle gate now executes the real canonical `./deploy.sh --skip-tests` repeatedly and validates:

- three successful builds from the same source revision with unique build IDs;
- manifest, wheel, sdist, identified bundle and SHA-256 inventory;
- build delta against the previous comparable build;
- retention of only the latest two successful comparable builds;
- controlled package-verification failure is not promoted and leaves no staging residue;
- release-style `0.4.0 -> 0.4.1` bump keeps `pyproject.toml`, `VERSION` and `uv.lock` consistent and passes `uv lock --check`;
- canonical clean removes project-owned build output.

A real-runtime smoke remains `PENDING` until a suitable already-running target runtime exists. It is not substituted by hosted CI. Representative hardware/performance/resource claims remain owned by `runtime-correctness-evidence-hardening`.

## STD-10 blocker — canonical branch protection

`repo-template-sw` L0 explicitly requires CI on pull requests **and protected canonical branches**.

Authenticated GitHub state on 2026-08-17 shows both repository canonical branches are currently unprotected:

```text
main: protected=false; required status checks=off
dev:  protected=false; required status checks=off
```

The repository defines and passes the required CI/health workflows, but GitHub does not currently enforce them before canonical-branch updates. Therefore full L0 compliance must remain **blocked**, not claimed.

The connected GitHub capability has no branch-protection/ruleset write action, and no installable integration exposing that operation was found. This is an external configuration blocker rather than remaining repository implementation work.

### To unblock STD-10

Configure branch protection/rulesets for the canonical branches (at minimum the actively used `dev`, and `main` for release integration) so changes require pull requests and the repository's blocking CI/health checks. Re-read authenticated branch state afterward.

When enforcement is verified:

1. mark `.engineering/baseline.json` L0 adoption complete;
2. remove this workstream from `docs/workstreams/README.md`;
3. delete this file by default;
4. retain the external/runtime evidence caveats only in their durable owners.

## Durable owners

- `.engineering/`: adopted baseline, commands and lifecycle contract.
- `AGENTS.md` + `skills/`: agent routing and reusable change workflow.
- `docs/architecture.md`, `docs/adr/`, `docs/features/`: architecture/decisions/features.
- `SECURITY.md`: trust/data/disclosure policy.
- tests/validators/workflows: executable repository and lifecycle invariants.
- `docs/current-state.md`: compact operational state.
- runtime-correctness workstream/runbook: representative device and hardware-dependent evidence.

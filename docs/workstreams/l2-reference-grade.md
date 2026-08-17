# L2 reference-grade engineering

Status: active
Owner: repository engineering
Read when: coordinating `repo-template-sw 0.3.0` L2 adoption
Last reviewed: 2026-08-17

## Goal

Raise Local LLM Server from the completed repository-side L1 baseline to a truthful L2 reference-grade engineering baseline. L2 must increase the strength of executable invariants and evidence, not merely add documentation or CI volume.

The adopted standard is pinned to `repo-template-sw` `0.3.0` at revision `41ba67a124b0daa33db2a02055d76897391d7092`. The upstream repository has since moved to 0.4.0; upgrading the standard is out of scope for this workstream.

Canonical branch protection remains an owner-deferred exception. Hardware-dependent L2 evidence is an explicit dependency on `runtime-correctness-evidence-hardening.md`; hosted CI must not manufacture Apple Silicon behavior.

## Work graph

| ID | Work | Depends on | State |
| --- | --- | --- | --- |
| L2-01 | pin L2 target, exact standard revision and gap/parallel plan | — | DONE |
| L2-02 | architecture ownership/dependency fitness functions | L2-01 | DONE |
| L2-03 | deterministic resource + memory regression contracts | L2-01 | DONE |
| L2-04 | stable CI performance regression gates | L2-01 | DONE |
| L2-05 | pressure/fault-injection lifecycle coverage | L2-01 | DONE |
| L2-06 | repeatability + cleanliness evidence across operating lifecycles | L2-01 | DONE |
| L2-07 | E2E failure/retry/recovery + installed/built surface | L2-01 | DONE |
| L2-08 | complexity/dependency review + reproducible evidence identity | L2-01 | DONE |
| L2-09 | repository policy + stale/duplicate/completed-doc drift detection | L2-01 | DONE |
| L2-10 | shared integration and repository-side L2 acceptance | L2-02..L2-09 | ACTIVE |
| L2-11 | representative hardware gate + durable state transfer/finalization | L2-10, runtime evidence | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

## Implemented reference-grade capabilities

### Architecture fitness

`.engineering/architecture-policy.json` and `scripts/verify_architecture.py` protect backend-neutral core contracts, transport-neutral scheduling/resource policy, the intentional HTTP scheduler adapter boundary and forbidden product-composition backedges by parsing real Python imports.

### Resource and memory regression

Hosted CI repeats successful and rejected resource lifecycles and bounds retained Python heap growth after warm-up. It proves the owned resource ledger returns to baseline; it does not claim RSS, native backend or Apple unified-memory reclamation.

### Performance regression

The canonical request-preparation path uses synthetic input, warm-up, seven repeated samples and a median gate. Evidence includes source/environment/workload/configuration identity. Model latency, TTFT, throughput, backend startup, thermals and Apple Silicon performance remain representative-device claims.

### Fault injection

The fault matrix requires concrete recovery evidence across resource admission, worker lifecycle, persistence integrity, pressure policy, request admission and request lifecycle. Existing high-value behavioral tests are referenced rather than duplicated.

### Repeatability

Development, test, E2E, build, smoke and runtime lifecycles have explicit cleanliness/repeatability evidence, including repeated owned E2E roots, three canonical builds, zero-residue browser cleanup, fresh-install cleanup and multi-cycle worker evidence.

### Built-surface recovery

Package Install Smoke installs the produced wheel into a fresh locked environment and launches a real localhost Uvicorn HTTP journey using the installed package. It proves health → expected not-resident failure → valid retry → healthy recovery with deterministic local engine, bounded shutdown and no model download.

### Complexity and evidence identity

Meaningful changes expose the standard's five complexity questions in the PR template. Decision-bearing evidence can use a privacy-safe identity envelope with stable workload/config/runtime fingerprints, comparison key, run identity and source revision without retaining raw prompts/outputs/private paths.

### Repository/docs drift

Documentation health now enforces review freshness, active workstream index consistency, unique declared canonical scope, completed-workstream cleanup, exact normalized duplicate detection above threshold and existing context/token budgets.

## L2-10 integration acceptance

The implementation lanes are converged on one branch. For `target_level=L2`, `scripts/verify_repository.py` now runs all L1 specialists plus architecture, resource regression, fault injection, repeatability, complexity-review and built-surface wiring validators.

Performance is intentionally a separate blocking `L2 Performance Regression` job because it executes a timed benchmark rather than validating static contracts. The job uses the locked environment and retains only bounded identity-bearing JSON for seven days.

L2-10 is DONE only when one exact head passes:

- Repository Health including all L1/L2 specialist validators and documentation drift checks;
- L2 Performance Regression;
- Artifact Lifecycle;
- Security Audit;
- fresh-installed-wheel Package Install Smoke including HTTP failure/retry/recovery;
- normal CI: lint, Python 3.10/3.11/3.12, Playwright E2E and zero residue.

## Hardware/full-L2 boundary

Full L2 is not complete until `runtime-correctness-evidence-hardening.md` provides representative hardware evidence for behavior materially affected by Apple Silicon/model/backend execution. After repository-side acceptance, this workstream may reach `repository-side-complete-hardware-gate-pending`, but L2-11 remains BLOCKED until the retained evidence is compatible and durable docs are reconciled.

## Stop conditions

Stop and surface the result rather than weakening gates if:

- a proposed CI timing gate is noisy or hardware-sensitive;
- a memory test implies native/unified-memory reclamation it does not observe;
- fault injection can damage user/model/cache state outside a run-owned fixture;
- architecture rules encode accidental current imports rather than intended ownership;
- E2E requires retaining prompt/output/private-path content by default;
- a complexity exception becomes a permanent undocumented bypass;
- representative hardware evidence is missing, incompatible or inconclusive.

## Finalization

After L2-10 and the hardware dependency are satisfied, record the exact accepted revision, transfer durable truth into owning docs/contracts, remove this workstream from the active index and delete it by default. Git history remains implementation history.

# L2 reference-grade engineering

Status: active
Owner: repository engineering
Read when: coordinating `repo-template-sw 0.3.0` L2 adoption
Last reviewed: 2026-08-17

## Goal

Raise Local LLM Server from the completed repository-side L1 baseline to a truthful L2 reference-grade engineering baseline. L2 must increase the strength of executable invariants and evidence, not merely add documentation or CI volume.

The adopted standard is pinned to `repo-template-sw` `0.3.0` at revision `41ba67a124b0daa33db2a02055d76897391d7092`. The upstream repository has since moved to 0.4.0; upgrading the standard is out of scope for this workstream.

Canonical branch protection remains an owner-deferred exception. Hardware-dependent L2 evidence is an explicit dependency on `runtime-correctness-evidence-hardening.md`; hosted CI must not manufacture Apple Silicon behavior.

## Gap map

Already strong enough to reuse:

- machine-enforced repository/documentation/agent-context/operating-contract checks;
- locked dependency graph, vulnerability scanning and bounded exceptions;
- deterministic lifecycle failure contracts and zero-residue E2E ownership;
- immutable artifact identity, build staging/checksums/deltas and fresh-install package smoke;
- machine-readable deterministic resource/performance budgets;
- representative-device evidence runbook and active hardware-evidence workstream.

L2 gaps to close:

- architecture dependency/ownership fitness functions;
- deterministic memory/resource regression evidence;
- stable performance regression gates for CI-safe paths;
- pressure/fault injection at important lifecycle boundaries;
- repeatability/cleanliness evidence across important operating lifecycles;
- representative failure/retry/recovery E2E journeys;
- E2E against the built/installed surface where practical;
- explicit complexity/dependency review for meaningful additions;
- reproducible benchmark/evidence identity for decision-bearing results;
- stronger repository policy and stale/duplicate/completed-document drift detection;
- representative hardware evidence before claiming full L2.

## Work graph

| ID | Work | Depends on | State |
| --- | --- | --- | --- |
| L2-01 | pin L2 target, exact standard revision and gap/parallel plan | — | ACTIVE |
| L2-02 | architecture ownership/dependency fitness functions | L2-01 | READY |
| L2-03 | deterministic resource + memory regression contracts | L2-01 | READY |
| L2-04 | stable CI performance regression gates | L2-01 | READY |
| L2-05 | pressure/fault-injection lifecycle coverage | L2-01 | READY |
| L2-06 | repeatability + cleanliness evidence across operating lifecycles | L2-01 | READY |
| L2-07 | E2E failure/retry/recovery + installed/built surface | L2-01 | READY |
| L2-08 | complexity/dependency review + reproducible evidence identity | L2-01 | READY |
| L2-09 | repository policy + stale/duplicate/completed-doc drift detection | L2-01 | READY |
| L2-10 | shared integration and repository-side L2 acceptance | L2-02..L2-09 | BLOCKED |
| L2-11 | representative hardware gate + durable state transfer/finalization | L2-10, runtime evidence | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

## Parallel ownership

To minimize merge conflicts, independent slices own distinct files until L2-10:

- L2-02: `.engineering/architecture-policy.json`, `scripts/verify_architecture.py`, architecture-fitness tests/docs.
- L2-03: resource/memory regression fixtures/tests and their machine-readable contract.
- L2-04: deterministic benchmark runner/baseline/gate for stable non-hardware-sensitive paths.
- L2-05: fault-injection helpers/tests and lifecycle contract extensions owned by that slice only.
- L2-06: repeatability runner/contract/tests; no shared workflow edits.
- L2-07: E2E fixture/journey/package-surface files; shared CI wiring deferred to L2-10.
- L2-08: complexity-review and evidence-identity policy/validators/template changes.
- L2-09: docs/repository-policy drift validator and tests.
- L2-10 alone owns shared Repository Health/CI wiring and baseline/current-state convergence.

## Acceptance principles

### Architecture

Fitness functions must check real imports/owners and fail on forbidden dependency direction. They must encode a small set of high-value boundaries from `docs/architecture.md`, not attempt to formalize every module relationship.

### Memory/resource regression

Hosted CI may test deterministic object/resource ownership, bounded cardinality, accounting return-to-baseline and Python heap growth where stable. It must not claim unified-memory or backend-native reclamation.

### Performance regression

Only paths with stable hosted measurement may block on timing. Hardware/backend/model throughput, TTFT and thermal behavior remain representative-device evidence. CI benchmarks must include exact source/config/tool/runtime identity and enough repetitions to avoid one-shot timing claims.

### Fault injection

Inject at owned boundaries: failed allocation/load, corrupt input, interrupted/failed writes, dependency failure, timeout/cancellation, stale owned state and failed staging where applicable. Tests must prove cleanup/recovery rather than only error classification.

### Repeatability

Important lifecycle evidence must prove repeated runs do not accumulate project-owned processes/listeners/temp roots/build staging/state. Existing build and E2E repeatability is reused and extended rather than duplicated.

### E2E

Keep critical journeys small. Add representative failure/retry/recovery only where the assembled system outcome matters. When technically practical, validate the installed wheel/built static assets rather than source checkout alone.

### Complexity and evidence identity

Meaningful dependency/architecture additions must answer the standard's five complexity questions. Decision-bearing benchmark/evidence artifacts require schema/version, source revision, run identity, configuration/workload identity and environment class; unavailable hardware facts remain unavailable.

### Repository policy/docs

Detect duplicated canonical-scope ownership, completed workstreams left active, stale `Last reviewed` policy violations where configured, invalid links/routing and policy files that no longer have validators. Avoid subjective prose linting.

## Hardware/full-L2 boundary

Full L2 is not complete until the active runtime-evidence workstream provides the representative hardware evidence required for behavior materially affected by Apple Silicon/model/backend execution. Repository-side L2 can reach `implemented-and-validated-hardware-gate-pending`, but L2-11 must remain blocked until that evidence is retained and durable docs are reconciled.

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

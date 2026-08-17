# L2 reference-grade engineering

Status: active
Owner: repository engineering
Read when: coordinating `repo-template-sw 0.3.0` L2 adoption
Last reviewed: 2026-08-17

## Goal

Raise Local LLM Server from L1 to a truthful L2 reference-grade baseline. The adopted standard is pinned to `repo-template-sw` `0.3.0` revision `41ba67a124b0daa33db2a02055d76897391d7092`; upstream 0.4.0 is intentionally a separate future adoption decision.

Canonical branch protection remains an owner-deferred exception. Hardware-dependent claims require retained representative-device evidence and are never inferred from hosted CI.

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
| L2-10 | shared integration and repository-side L2 acceptance | L2-02..L2-09 | DONE |
| L2-11 | representative hardware gate + durable state transfer/finalization | L2-10, runtime evidence | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

## Repository-side acceptance

Repository-side L2 acceptance revision: `d528b6c5b676e705e7ccf24800929da6d5534203`.

That exact integrated `dev` revision passed:

- Repository Health with all L1/L2 specialist validators and documentation drift checks;
- `L2 Performance Regression` with a 100 µs/op median ceiling for synthetic canonical request preparation;
- Artifact Lifecycle through three canonical builds, retention, failed-stage cleanup and release-style lock identity;
- Security Audit;
- fresh-installed-wheel Package Install Smoke including real localhost Uvicorn failure → retry → recovery;
- lint, Python 3.10/3.11/3.12, Playwright E2E and post-run zero residue.

Durable L2 contracts now cover:

- architecture ownership/dependency direction;
- deterministic resource-ledger and Python-heap regression with native/unified-memory non-claims;
- reproducible hosted performance regression with privacy-safe evidence identity;
- critical fault injection and recovery invariants;
- repeatability/cleanliness across development, test, E2E, build, smoke and runtime lifecycles;
- built/installed-surface failure/retry/recovery;
- complexity/dependency review;
- documentation freshness, canonical-scope ownership, duplicate detection and workstream lifecycle consistency.

## L2-11 hardware gate

Full L2 remains **BLOCKED** on `docs/workstreams/runtime-correctness-evidence-hardening.md`. Current representative-device evidence still required includes the target-Mac thinking comparison, comparable evaluation runs, compatible Apple Silicon reclamation cycles and bounded resource-policy smoke. Release/reconciliation evidence that depends on those runs cannot be finalized first.

Hosted CI evidence is intentionally insufficient to prove:

- Apple unified/native/accelerator memory reclamation;
- model/backend TTFT or token throughput;
- thermal or sustained-device behavior;
- backend-specific thinking behavior;
- automatic pressure eviction safety on representative hardware.

## Unblock condition

L2-11 may move to DONE only when the runtime workstream retains compatible evidence identities for the required physical runs and durable docs reconcile those observations without contradiction. Then:

1. record the full L2 evidence/acceptance revision;
2. update `.engineering/baseline.json` from hardware-gate-pending to complete;
3. transfer any remaining durable hardware truth into owning docs;
4. remove this workstream from `docs/workstreams/README.md`;
5. delete this completed workstream by default;
6. run the complete repository validation after deletion.

## Stop conditions

Do not weaken a hosted gate to obtain L2, convert deterministic heap evidence into native-memory claims, retain prompt/output/private paths for convenience, or mark representative hardware evidence complete when a required physical run is missing/incompatible/inconclusive.

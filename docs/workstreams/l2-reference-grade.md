# L2 reference-grade engineering

Status: active — representative evidence pending
Owner: repository engineering
Read when: coordinating `repo-template-sw 0.4.0` L2 completion
Last reviewed: 2026-08-18

## Goal

Complete a truthful L2 reference-grade baseline on `repo-template-sw` **0.4.0** revision `60e0f498a459e2de114ccb23f6cd50994c19513f`, including the adopted `product-ui` profile, without promoting hosted-CI or one-device observations into broader hardware/product claims.

Canonical branch protection remains an owner-deferred exception. Repository-side engineering and product-ui guardrails are accepted; full L2 still requires real representative-device evidence and the two human product-experience evidence tasks.

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
| L2-PX | 0.4.0 product-ui deterministic guardrails | L2-10 | DONE |
| L2-BRIDGE | deterministic bridge from real device/human evidence to bounded summaries | L2-10, L2-PX | ACTIVE |
| L2-11 | representative hardware + human evidence gate and durable finalization | L2-BRIDGE, runtime/product evidence | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

## Accepted repository baseline

Engineering repository-side L2 acceptance revision remains `d528b6c5b676e705e7ccf24800929da6d5534203`. The 0.4.0/product-ui repository guardrail acceptance revision is `89d360698234016ddfe1f3fff0bacbc4f9bb7852`, integrated to `dev` through PR #145.

The accepted deterministic surface covers:

- architecture ownership/dependency direction;
- deterministic resource-ledger/Python-heap regression with native/unified-memory non-claims;
- reproducible hosted performance regression;
- critical fault injection and recovery invariants;
- repeatability/cleanliness across development, test, E2E, build, smoke and runtime lifecycles;
- built/installed-surface failure/retry/recovery;
- complexity/dependency review and privacy-safe evidence identity;
- documentation freshness/canonical-scope/workstream lifecycle drift;
- product-ui task/brand/design-system/accessibility/adaptive/journey/review/privacy contracts.

Repository Health, L2 Performance Regression, Artifact Lifecycle, Security Audit, Package Install Smoke, lint, Python 3.10/3.11/3.12, Playwright and zero-residue remain the deterministic acceptance surface.

## L2 evidence bridge

The evidence bridge is repository code, not evidence itself. Its purpose is to make the final physical/human campaigns reviewable without manual claim assembly or accidental retention of private content.

The target implementation provides:

- `python -m local_llm_server.l2_evidence_bridge capture-thinking` for explicit ON/OFF-hidden exercise without retaining prompt/output;
- `validate-hardware-bundle` for TH-E1 + EV-3 + HE-2 + RES-2 compatibility/completeness review;
- `validate-product-ui` for bounded manual accessibility/usability evidence;
- `.engineering/l2-evidence-bridge.json` as the machine-readable bridge contract;
- `scripts/verify_l2_evidence_bridge.py` as a Repository Health fitness function;
- non-evidence templates that are rejected as real completion evidence.

The bridge never mutates `.engineering/baseline.json`, never authorizes automatic eviction and cannot replace the physical/human execution.

## L2-11 remaining evidence

Full engineering L2 remains blocked on `docs/workstreams/runtime-correctness-evidence-hardening.md`. Required representative Mac evidence is:

- TH-E1 explicit thinking OFF/ON-hidden campaign;
- EV-3 two attribution-safe `general-purpose v1.0.0`, 10-sample, seed-0 OFF runs;
- HE-2 two compatible verified 3-cycle Apple Silicon reclamation reports plus conservative review;
- RES-2 bounded admit/account/release/reject resource-policy smoke.

Full `product-ui` L2 additionally requires the real manual accessibility review and representative-user usability session owned by `docs/workstreams/v040-product-ui-l2.md`.

Hosted CI cannot prove Apple unified/native/accelerator memory reclamation, representative model/backend TTFT or throughput, thermal/sustained behavior, backend-specific real-model thinking behavior, pressure-eviction safety or human usability/accessibility outcomes.

## Unblock condition

L2-11 may move to DONE only when:

1. the representative hardware bundle is produced by real physical runs and the bounded validator reports complete;
2. the two product-ui human evidence sets exist and their validator reports acceptance-ready after any justified remediation/review;
3. durable docs reconcile the observed results without embedding private paths/content;
4. no negative/inconclusive observation is hidden or rerun merely to manufacture a pass;
5. the final deterministic repository gate is green after evidence-ledger/doc changes.

Then record the full L2 evidence/acceptance revision, transfer durable truth into owning docs, remove completed workstreams from the active index and delete completed workstream files by default.

## Stop conditions

Do not weaken hosted gates, convert Python-heap evidence into native-memory claims, retain prompt/output/private paths for convenience, alter evidence merely to obtain a favorable result, or mark representative hardware/human evidence complete when a required real run/session is missing, incompatible or unresolved.

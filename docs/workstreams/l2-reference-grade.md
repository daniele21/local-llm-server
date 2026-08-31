# L2 reference-grade engineering

Status: active — human product evidence pending
Owner: repository engineering
Read when: coordinating final `repo-template-sw 0.8.0` L2 completion
Last reviewed: 2026-08-31

## Goal

Complete a truthful L2 reference-grade baseline on `repo-template-sw` **0.8.0** revision `6677c5349d64ea6d935f1b460d03a47c236821bc`, including the adopted `product-ui` profile, without promoting one-device observations into broader hardware/product claims.

Canonical branch protection remains an owner-deferred exception. Repository-side engineering guardrails and the required representative Apple Silicon runtime evidence are accepted. Full L2 now requires only the two real-human product-experience evidence tasks plus final durable reconciliation and deterministic acceptance.

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
| L2-PX | product-ui deterministic guardrails | L2-10 | DONE |
| L2-BRIDGE | deterministic bridge from real device/human evidence to bounded summaries | L2-10, L2-PX | DONE |
| L2-HW | representative Apple Silicon runtime evidence | L2-BRIDGE | DONE |
| L2-11 | human product evidence + durable finalization | L2-PX, L2-HW | ACTIVE |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

## Accepted repository baseline

Repository-side L2 acceptance revision remains `d528b6c5b676e705e7ccf24800929da6d5534203`. The product-ui repository guardrail acceptance revision is `89d360698234016ddfe1f3fff0bacbc4f9bb7852`; the deterministic L2 evidence bridge is accepted on `de899cc945e1d1c735a2ded91c5da717ce0fe2b0`.

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

## Accepted representative hardware evidence

The 2026-08-31 representative Mac campaign produced an acceptance-ready minimum L2 hardware bundle:

- TH-E1 explicit thinking OFF and ON-hidden;
- EV-3 two attribution-safe `general-purpose v1.0.0`, 10-sample, seed-0 reasoning-OFF runs;
- HE-2 two compatible verified 3-cycle Apple Silicon reclamation reports plus conservative review;
- RES-2 bounded admit/account/release/reject resource-policy smoke;
- bounded bundle validation PASS.

The separate RRG-5 multi-model governor campaign also reached `sufficient_observation_set`: 2 compatible reports, 4 complete cycles, 4 verified-identity cycles, 4 transient-overlap cycles, 4 clean-accounting cycles and 2 complete shutdown-under-load procedures.

These results prove the exercised representative-device contracts only. Memory deltas remain observational; automatic eviction is not recommended, reclamation safety is not claimed and production safety is not claimed. Automatic pressure eviction remains disabled.

## L2 evidence bridge

The evidence bridge is repository code, not evidence itself. It provides:

- `python -m local_llm_server.l2_evidence_bridge capture-thinking` for explicit ON/OFF-hidden exercise without retaining prompt/output;
- `validate-hardware-bundle` for TH-E1 + EV-3 + HE-2 + RES-2 compatibility/completeness review;
- `validate-product-ui` for bounded manual accessibility/usability evidence;
- `.engineering/l2-evidence-bridge.json` as the machine-readable bridge contract;
- `scripts/verify_l2_evidence_bridge.py` as a Repository Health fitness function;
- non-evidence templates that are rejected as real completion evidence.

The bridge never authorizes automatic eviction and cannot replace the physical/human execution.

## L2-11 remaining evidence

Full L2 now remains gated by `docs/workstreams/v040-product-ui-l2.md`:

- PX4-09 — real manual accessibility review of the primary journeys;
- PX4-10 — representative-user usability session with bounded non-sensitive evidence.

Hosted CI cannot replace human accessibility/usability judgment. The accepted representative Mac run also does not prove cross-device memory behavior, representative throughput, thermals, sustained-load safety or a future pressure-eviction policy.

## Completion condition

L2-11 may move to DONE only when:

1. the two product-ui human evidence sets exist and their validator reports acceptance-ready after any justified remediation/review;
2. durable docs reconcile those observed results without embedding private content;
3. no negative/inconclusive observation is hidden or rerun merely to manufacture a pass;
4. the final deterministic repository gate is green on the exact final head.

Then record the full L2 acceptance revision, transfer durable truth into owning docs, remove completed workstreams from the active index and delete completed workstream files by default.

## Stop conditions

Do not weaken hosted gates, convert one-Mac observations into cross-device/native-memory safety claims, retain prompt/output/private paths for convenience, alter evidence merely to obtain a favorable result, or mark human evidence complete when a required real review/session is missing, incompatible or unresolved.

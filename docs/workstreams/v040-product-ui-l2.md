# repo-template-sw 0.4.0 product-ui L2 migration

Status: active
Owner: repository engineering + web product
Read when: coordinating the 0.3.0 -> 0.4.0 migration and product-ui L2 evidence
Last reviewed: 2026-08-18

## Goal

Migrate the already accepted `repo-template-sw 0.3.0` L2 repository baseline to `0.4.0` revision `60e0f498a459e2de114ccb23f6cd50994c19513f`, adopt the `product-ui` profile for the bundled Local LLM Studio/control-plane UI, and turn existing UX/accessibility/design-system strengths into explicit reference-grade contracts without replacing the current code-first design system or introducing a new UI framework.

The existing full-L2 representative-hardware gate remains owned by `l2-reference-grade.md` + `runtime-correctness-evidence-hardening.md`. This migration must not relabel hosted UI evidence as physical runtime evidence.

## Delta classification

| 0.4.0 delta | Classification | Local mapping |
| --- | --- | --- |
| `product-ui` applicability | APPLY | bundled Local LLM Studio is a material browser UI |
| design source of truth | MERGE | keep code-first `src/local_llm_server/static/` + `docs/brand-guidelines.md` |
| brand/tokens/components | MERGE | keep `design-system.css`; add machine-readable routing, no second system |
| task model / progressive disclosure | KEEP + FORMALIZE | existing control-plane IA and advanced chat controls; declare in UX contract |
| critical states / recovery | KEEP + FORMALIZE | existing source-backed status/error/loading behavior + E2E; map evidence |
| accessibility | KEEP + HARDEN | existing keyboard/focus/reduced-motion tests; declare WCAG 2.2 AA target |
| adaptive layout | KEEP + HARDEN | existing 1100/720/420px layout classes; make them contractual |
| critical journeys / E2E | MERGE | reuse existing Playwright product/studio suites and zero-residue evidence |
| visual regression | DEFER | no pixel baseline until a stable high-risk surface justifies maintenance cost; semantic visual contracts remain blocking |
| design-system drift | APPLY | namespace/token/component duplicate guard |
| privacy-safe telemetry/research | APPLY | telemetry remains off by default; define bounded usability evidence contract |
| representative-user usability | DEFERRED EVIDENCE | protocol is repository-owned; no session result is fabricated |
| UX change review | APPLY | PR template questions for hierarchy/cognitive load/recovery/accessibility |

## Work graph

| ID | Work | Depends on | State |
| --- | --- | --- | --- |
| PX4-01 | pin 0.4.0 revision, add `product-ui`, record semantic delta | — | ACTIVE |
| PX4-02 | specialized UX + brand contracts and upstream validator | PX4-01 | ACTIVE |
| PX4-03 | map accessibility, adaptive layouts and critical journeys to existing evidence | PX4-02 | ACTIVE |
| PX4-04 | design-system token/component drift and duplication fitness function | PX4-02 | ACTIVE |
| PX4-05 | privacy-safe research/usability evidence contract and manual protocol | PX4-02 | ACTIVE |
| PX4-06 | significant UX change review contract + PR/Skill integration | PX4-02 | ACTIVE |
| PX4-07 | Repository Health integration and exact-head acceptance | PX4-03..PX4-06 | BLOCKED |
| PX4-08 | durable state transfer/finalize migration; keep any real manual gate explicit | PX4-07 | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

## Acceptance boundary

Repository-side 0.4.0 product-ui acceptance requires the same exact head to pass:

- upstream-compatible product experience validator;
- Local L2 product-ui drift/evidence validator;
- all existing L1/L2 repository fitness functions;
- documentation lifecycle and context budgets;
- accessibility source tests;
- Playwright E2E and zero residue;
- Artifact Lifecycle, Security Audit, Package Install Smoke and L2 Performance Regression.

Full product-ui L2 must not claim representative-user usability evidence until a real session is retained under the bounded protocol. Full engineering L2 additionally remains blocked on the separate representative-hardware evidence gate.

## Stop conditions

- do not add a second CSS/UI framework merely for compliance;
- do not copy concept mockups into production truth;
- do not collect prompts, outputs, local paths or machine identity as usability telemetry;
- do not treat source-level accessibility checks as a substitute for all manual assistive-technology validation;
- do not create pixel snapshots for unstable/incidental surfaces just to satisfy a checkbox;
- do not mark manual usability or physical-device evidence complete unless actually executed.

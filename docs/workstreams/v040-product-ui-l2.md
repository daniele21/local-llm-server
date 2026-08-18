# repo-template-sw 0.4.0 product-ui L2 migration

Status: active — integration validation
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
| PX4-01 | pin 0.4.0 revision, add `product-ui`, record semantic delta | — | DONE |
| PX4-02 | specialized UX + brand contracts and upstream validator | PX4-01 | DONE |
| PX4-03 | map accessibility, adaptive layouts and critical journeys to existing evidence | PX4-02 | DONE |
| PX4-04 | design-system token/component drift and duplication fitness function | PX4-02 | DONE |
| PX4-05 | privacy-safe research/usability evidence contract and manual protocol | PX4-02 | DONE |
| PX4-06 | significant UX change review contract + PR/Skill integration | PX4-02 | DONE |
| PX4-07 | Repository Health integration and exact-head acceptance | PX4-03..PX4-06 | ACTIVE |
| PX4-08 | durable state transfer/finalize migration; keep any real manual gate explicit | PX4-07 | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

## Implemented repository guardrails

- `design/ux-contract.json` declares task hierarchy, states, WCAG target, adaptive contexts, critical journeys and existing evidence owners.
- `design/brand-kit.json` routes semantic brand tokens to the existing `--ds-*` design system and existing logo/favicon rather than duplicating assets.
- `scripts/verify_product_experience.py` carries the upstream 0.4.0 structural contract.
- `.engineering/product-ui-l2.json` + `scripts/verify_product_ui_l2.py` enforce local L2 ownership for semantic tokens/components, adaptive breakpoints, journey evidence, privacy-safe usability fields and UX review markers.
- `docs/product-experience-validation.md` owns the manual accessibility/usability protocol and explicitly forbids raw prompt/output/path/machine identity retention.
- the PR template and three customized review/change Skills now require user-task/hierarchy/cognitive-load/recovery/accessibility/adaptive/design-system/evidence review for meaningful UI changes.
- `scripts/verify_repository.py` invokes both upstream and project-specific product-ui checks for the L2 target.

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

## PX4-08 finalization rule

After PX4-07 passes on one exact integrated revision:

1. record the exact 0.4.0 product-ui repository acceptance revision in `.engineering/baseline.json`;
2. mark deterministic product-ui capabilities accepted while retaining manual accessibility/usability as explicit pending evidence;
3. move durable migration truth into `docs/current-state.md` and owning design docs;
4. keep this workstream active if a manual product-ui L2 gate remains pending rather than deleting evidence debt;
5. never conflate the product-ui manual gate with the separate Apple Silicon/model/backend hardware gate.

## Stop conditions

- do not add a second CSS/UI framework merely for compliance;
- do not copy concept mockups into production truth;
- do not collect prompts, outputs, local paths or machine identity as usability telemetry;
- do not treat source-level accessibility checks as a substitute for all manual assistive-technology validation;
- do not create pixel snapshots for unstable/incidental surfaces just to satisfy a checkbox;
- do not mark manual usability or physical-device evidence complete unless actually executed.

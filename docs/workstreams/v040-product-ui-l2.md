# repo-template-sw 0.4.0 product-ui L2 migration

Status: active — manual product-experience evidence pending
Owner: repository engineering + web product
Read when: coordinating the 0.4.0 `product-ui` L2 evidence boundary
Last reviewed: 2026-08-18

## Goal

Adopt `repo-template-sw 0.4.0` revision `60e0f498a459e2de114ccb23f6cd50994c19513f` and the `product-ui` profile for the bundled Local LLM Studio/control-plane UI without replacing the existing code-first design system or fabricating human/device evidence.

The deterministic repository migration has passed acceptance. This workstream now owns only the two real-human evidence tasks required before a full `product-ui` L2 claim. The separate full-engineering-L2 representative-hardware gate remains owned by `l2-reference-grade.md` + `runtime-correctness-evidence-hardening.md`.

## Delta classification

| 0.4.0 delta | Classification | Local mapping |
| --- | --- | --- |
| `product-ui` applicability | APPLY | bundled Local LLM Studio is a material browser UI |
| design source of truth | MERGE | keep code-first `src/local_llm_server/static/` + `docs/brand-guidelines.md` |
| brand/tokens/components | MERGE | keep `design-system.css`; add machine-readable routing, no second system |
| task model / progressive disclosure | KEEP + FORMALIZE | existing control-plane IA and advanced chat controls; declared in UX contract |
| critical states / recovery | KEEP + FORMALIZE | existing source-backed status/error/loading behavior + E2E; mapped evidence |
| accessibility | KEEP + HARDEN | existing keyboard/focus/reduced-motion tests; WCAG 2.2 AA target declared |
| adaptive layout | KEEP + HARDEN | existing 1100/720/420px layout classes are contractual |
| critical journeys / E2E | MERGE | existing Playwright product/studio suites and zero-residue evidence |
| visual regression | DEFER | no pixel baseline until a stable high-risk surface justifies maintenance cost |
| design-system drift | APPLY | namespace/token/component duplicate guard is blocking |
| privacy-safe telemetry/research | APPLY | telemetry remains off by default; bounded usability evidence only |
| representative-user usability | MANUAL EVIDENCE | protocol exists; no result is fabricated |
| UX change review | APPLY | PR template covers hierarchy/cognitive load/recovery/accessibility |

## Work graph

| ID | Work | Depends on | State |
| --- | --- | --- | --- |
| PX4-01 | pin 0.4.0 revision, add `product-ui`, record semantic delta | — | DONE |
| PX4-02 | specialized UX + brand contracts and upstream validator | PX4-01 | DONE |
| PX4-03 | map accessibility, adaptive layouts and critical journeys to existing evidence | PX4-02 | DONE |
| PX4-04 | design-system token/component drift and duplication fitness function | PX4-02 | DONE |
| PX4-05 | privacy-safe research/usability evidence contract and manual protocol | PX4-02 | DONE |
| PX4-06 | significant UX change review contract + PR/Skill integration | PX4-02 | DONE |
| PX4-07 | Repository Health integration and exact-head acceptance | PX4-03..PX4-06 | DONE |
| PX4-08 | durable state transfer and repository migration acceptance | PX4-07 | DONE |
| PX4-09 | execute and retain bounded manual accessibility review | PX4-08 | READY |
| PX4-10 | execute and retain bounded representative-user usability session | PX4-08 | READY |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

PX4-09 and PX4-10 are independent and may proceed in parallel. They require actual human interaction with a built product surface and cannot be satisfied by hosted CI.

## Accepted repository guardrails

Exact implementation head `89d360698234016ddfe1f3fff0bacbc4f9bb7852` passed the combined repository acceptance set:

- upstream Product Experience Contract validator;
- Local product-ui L2 drift/evidence validator;
- all existing L1/L2 specialist fitness functions;
- documentation lifecycle/context budget;
- L2 Performance Regression;
- Artifact Lifecycle;
- Security Audit;
- Package Install Smoke;
- lint and Python 3.10/3.11/3.12;
- Playwright critical journeys and zero E2E residue.

The accepted implementation provides:

- `design/ux-contract.json` for task hierarchy, states, accessibility, adaptive contexts and critical journeys;
- `design/brand-kit.json` routing semantic brand roles to the existing `--ds-*` design system and shipped assets;
- upstream-compatible `scripts/verify_product_experience.py`;
- `.engineering/product-ui-l2.json` + `scripts/verify_product_ui_l2.py` for design ownership, breakpoint, evidence, privacy and review drift;
- `docs/product-experience-validation.md` for manual accessibility/usability protocol and forbidden sensitive evidence;
- PR/Skill review requirements for user-task/hierarchy/cognitive-load/recovery/accessibility/adaptive/design-system/evidence changes.

## Remaining manual evidence

### PX4-09 — manual accessibility

Use `docs/product-experience-validation.md#manual-accessibility-review` against a built product surface. Retain only bounded findings. A negative or inconclusive result remains evidence and must not be repeated merely to manufacture a pass.

Completion changes `.engineering/product-ui-l2.json` `manual_accessibility_status` from `pending` only when the retained evidence exists.

### PX4-10 — representative-user usability

Use `docs/product-experience-validation.md#representative-user-usability` with non-sensitive demo/test data. Retain only the allow-listed task/outcome fields; do not retain raw prompts, outputs, media, private paths or machine identity.

Completion changes `.engineering/product-ui-l2.json` `representative_user_usability_status` from `pending` only when the retained evidence exists.

## Completion boundary

Repository-side **0.4.0 product-ui guardrails are accepted**. Full `product-ui` L2 is not evidence-complete while PX4-09 or PX4-10 remains open.

This boundary is independent from full engineering L2, which additionally requires the separate representative Apple Silicon/model/backend campaigns.

## Stop conditions

- do not add a second CSS/UI framework merely for compliance;
- do not copy concept mockups into production truth;
- do not collect prompts, outputs, local paths or machine identity as usability telemetry;
- do not treat source-level accessibility checks as a substitute for manual assistive-technology validation;
- do not create pixel snapshots for unstable/incidental surfaces just to satisfy a checkbox;
- do not mark manual usability or physical-device evidence complete unless actually executed.

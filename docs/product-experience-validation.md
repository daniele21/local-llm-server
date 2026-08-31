# Product experience validation

Status: active
Document type: validation-contract
Owner: web-product-and-docs
Canonical scope: design.product-experience-validation
Read when: changing critical UI journeys, accessibility, adaptive behavior, design-system ownership or product research evidence
Last reviewed: 2026-08-31

## Purpose

Local LLM Studio treats product experience as a correctness surface. Automated evidence protects deterministic interaction contracts; manual evidence is retained only when a human judgment is necessary. Neither class of evidence is allowed to weaken the local-first privacy boundary.

This document specializes the `repo-template-sw 0.8.0` `product-ui` contract for this repository. Canonical visual/component implementation remains in `src/local_llm_server/static/design-system.css` and the source-backed control-plane renderers, with durable brand intent in the repository design documentation.

## Automated evidence

### Accessibility

`tests/test_accessibility_ui_assets.py` provides deterministic source-level coverage for native route semantics, keyboard relationships, skip navigation, visible focus, non-color-only status meaning, reduced motion, adaptive layouts and canonical semantic-component ownership. Playwright covers complete browser journeys where source inspection cannot prove the user outcome.

Automated checks are necessary but are not represented as a complete substitute for manual keyboard or assistive-technology review.

### Critical journeys

The canonical critical journeys are declared in `design/ux-contract.json` and mapped to concrete evidence in `.engineering/product-ui-l2.json`.

Required journeys include:

1. open the control plane, understand server/runtime state and navigate the core surfaces;
2. configure and submit a chat inference, observe progress/failure and recover for the next action.

Model/runtime management and evaluation review are also named journeys so their evidence ownership cannot disappear silently as the UI evolves.

### Adaptive layout

The supported browser layout classes are:

- wide desktop: at least 1101 px;
- compact desktop/tablet: 721–1100 px;
- narrow: 421–720 px;
- small viewport: at most 420 px.

The L2 product-ui validator checks the corresponding media-query boundaries in the canonical shell CSS. A change to those boundaries must update behavior and contract intentionally.

### Design-system drift

The `--ds-*` token namespace and canonical `.ds-*` semantic component roots are owned by `src/local_llm_server/static/design-system.css`.

Repository Health rejects removal of required semantic tokens/components, reserved `--ds-*` definitions in another owner, duplicate canonical semantic component roots, missing critical-journey evidence and privacy/review-policy drift.

## Visual regression policy

Repository-wide pixel-perfect visual regression is not a blocking mechanism. Targeted visual contracts are allowed only for stable high-risk surfaces with deterministic fixture state, viewport, theme and motion preference; synthetic-only evidence; independent semantic assertions; tolerance for insignificant rasterization differences; and explicit review of meaningful fingerprint changes.

The current blocking targeted set is intentionally small:

- `Overview` at the deterministic 1440×1000 dark/reduced-motion fixture;
- `Benchmark & Evaluation` setup at the same fixture.

`tests/e2e/product_experience_p2.spec.js` derives a bounded perceptual geometry/hierarchy fingerprint and does not retain the screenshot PNG in the normal gate. These fingerprints do not claim coverage for light mode, responsive widths, every state, real runtime data or representative hardware.

## Manual accessibility review

Current status: **complete for source revision `a29e77c1ce4e65294440cfe4fc47e33c92173096`**.

The accepted 2026-08-31 bounded review covers all six required checks:

1. keyboard-only primary shell and critical actions;
2. logical and visible focus order;
3. accessibility tree or screen-reader inspection for primary status/navigation/chat;
4. zoom and text scaling preserving primary actions/recovery;
5. reduced-motion behavior preserving essential feedback;
6. representative error/loading/empty/disabled states and recovery guidance.

The retained evidence is `docs/evidence/manual-accessibility-2026-08-31.json`. It reports no blocking finding for the exercised product surface. The evidence is scoped to the exact tested revision and does not create a permanent claim for future materially changed UI.

Negative or inconclusive findings in future reviews remain evidence and must not be rerun merely until they become favorable. A rerun is justified after a concrete product fix or material tested-surface change.

The canonical non-evidence template remains `docs/evidence-templates/manual-accessibility.example.json`. Future evidence must replace the example identifier, bind to an exact 40-character source revision and record one bounded result for every required check.

## Representative-user usability

Current status: **complete for source revision `a29e77c1ce4e65294440cfe4fc47e33c92173096`**.

The accepted 2026-08-31 representative review covers the minimum retained journey set:

- `control-plane-status-and-navigation`;
- `chat-inference-and-recovery`;
- `advanced-control-discovery`;
- `evidence-interpretation`.

The retained evidence is `docs/evidence/representative-usability-2026-08-31.json`. All four required journeys are recorded as completed with no high/critical finding. Duration was not measured, and no raw prompt/output/private machine content is retained.

The purpose remains to answer bounded experience questions: whether users can understand server/runtime state, complete primary inference without backend-architecture knowledge, recover from failures, find advanced controls without normal-flow overload and distinguish measured/estimated/unavailable evidence.

### Allowed retained fields

Only these bounded fields may be retained per usability record by default:

- `study_id`;
- `journey_id`;
- `task_completed`;
- `needed_recovery`;
- `assistance_required`;
- `duration_bucket`;
- `severity`;
- `sanitized_observation`.

`sanitized_observation` describes interaction behavior rather than product content.

### Forbidden retained data

Do not retain by default raw prompts/model outputs, uploaded media/document content, local paths, hostnames/usernames/machine identifiers, credentials/secrets, private screen recordings or conversation content merely because it appeared during a session.

Product telemetry remains off by default. This protocol does not authorize background analytics.

## Validate real human evidence

Use the packaged validator against bounded JSON files:

```bash
python -m local_llm_server.l2_evidence_bridge validate-product-ui \
  --accessibility /path/to/manual-accessibility.json \
  --usability /path/to/representative-usability.json \
  --output /path/to/product-ui-evidence-summary.json
```

The validator rejects example identifiers, requires the exact accessibility check and usability journey sets, enforces the usability allow-list, rejects private-path/email/secret-like observations, preserves negative/inconclusive findings and reports evidence presence, blocking findings and acceptance readiness separately. It never silently mutates `.engineering/product-ui-l2.json` or `.engineering/baseline.json`.

For manual accessibility, a failed or inconclusive required check is blocking until resolved and justifiably re-reviewed. For usability, `high` or `critical` findings are blocking; lower-severity findings remain evidence requiring product judgment.

The accepted bounded summary for the current candidate is `docs/evidence/product-ui-evidence-summary-2026-08-31.json`.

## Significant UX change review

A meaningful UI change must evaluate, where applicable, user task model, information/action hierarchy, cognitive load/progressive disclosure, failure prevention/recovery, accessibility, adaptive behavior, canonical design-system reuse and regression/evidence impact. The pull-request template contains machine-checked markers for these questions.

## Evidence identity and cleanup

UI/E2E evidence follows the repository evidence contract: associate retained evidence with source/run identity, keep CI retention bounded, keep raw user/model content out of retained evidence, close owned browser/server/process/listener/temp state after runs and preserve the zero-residue gate independently from browser assertions.

Human-evidence summaries must use the exact tested source revision. Only bounded summary/observations required for the claim are retained; raw recordings or local product content are not implied by this contract.

## Completion semantics

Repository-side `repo-template-sw 0.8.0` product-ui guardrails are accepted when deterministic contracts/workflows are green on the same integrated revision.

For the current candidate, manual accessibility and representative-user usability evidence are both accepted and `.engineering/product-ui-l2.json` records both statuses as `complete`. Full product-ui L2 may therefore be claimed for the exact accepted scope once the final publication head passes the required deterministic preflight.

Any materially changed future UX invalidates only the evidence affected by that change; it must not inherit manual acceptance automatically. A status may become `not-justified` only through an explicit documented product-risk decision, never as a shortcut around evidence collection.

# Product experience validation

Status: active
Document type: validation-contract
Owner: web-product-and-docs
Canonical scope: design.product-experience-validation
Read when: changing critical UI journeys, accessibility, adaptive behavior, design-system ownership or product research evidence
Last reviewed: 2026-08-18

## Purpose

Local LLM Studio treats product experience as a correctness surface. Automated evidence protects deterministic interaction contracts; manual evidence is retained only when a human judgment is necessary. Neither class of evidence is allowed to weaken the local-first privacy boundary.

This document specializes the `repo-template-sw 0.4.0` `product-ui` contract for this repository. It does not introduce a second design system: canonical visual/component implementation remains in `src/local_llm_server/static/design-system.css` and the source-backed control-plane renderers, with durable brand intent in `docs/brand-guidelines.md`.

## Automated evidence

### Accessibility

`tests/test_accessibility_ui_assets.py` provides deterministic source-level coverage for:

- keyboard-operable tab navigation and roving focus;
- semantic tab/tablist/tabpanel relationships;
- skip navigation;
- visible focus styles;
- status meaning that is not color-only;
- reduced-motion behavior;
- adaptive layouts and horizontally accessible dense tables.

Playwright covers complete browser journeys where source inspection cannot prove the user outcome. Automated checks are necessary but are not represented as a complete substitute for manual keyboard or assistive-technology review.

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

The L2 product-ui validator checks the corresponding media-query boundaries in the canonical shell CSS. A change to those boundaries must update both behavior and the contract intentionally.

### Design-system drift

The `--ds-*` token namespace and canonical `.ds-*` semantic component roots are owned by `src/local_llm_server/static/design-system.css`.

Repository Health rejects:

- removal of required semantic tokens/components;
- reserved `--ds-*` token declarations in another CSS owner;
- duplicate definitions of canonical semantic component roots outside the design-system owner;
- missing critical-journey evidence files;
- privacy-policy or PR-review drift.

Legacy/local styles may reference canonical tokens or retain non-`ds` names while they are incrementally converged. The guardrail prevents creation of a second canonical design system without forcing a risky whole-UI rewrite.

## Visual regression policy

Pixel-level visual regression is currently not a blocking repository-wide mechanism. The UI is still converging and freezing incidental pixels would add maintenance cost without a corresponding correctness claim.

A visual snapshot should be introduced only for a stable, high-risk surface where geometry or visual state is itself part of the user contract. Until then, semantic component/state tests, accessibility assertions and complete Playwright journeys are the blocking regression surface.

This is an explicit scope decision, not evidence that visual regressions are impossible.

## Manual accessibility review

Current status: **pending**.

A representative manual review should use the built product surface and record only bounded results. At minimum:

1. navigate the primary shell and critical actions using keyboard only;
2. verify focus order remains logical and visible through navigation, forms and recovery states;
3. use a browser/OS accessibility tree or screen reader for the primary status/navigation and chat journey;
4. verify zoom/text scaling does not hide the primary action or recovery path in supported layout classes;
5. verify reduced-motion preference removes non-essential transitions/animation without removing feedback;
6. inspect representative error/loading/empty/disabled states for understandable announcements and next actions.

Negative or inconclusive findings are evidence and must be retained as such. Do not repeat a session merely until it produces a favorable result. A rerun is justified after a concrete product fix or a material change in the tested surface.

The canonical non-evidence template is `docs/evidence-templates/manual-accessibility.example.json`. Copy it outside the repository evidence templates, replace the `example-*` identifier, bind it to the exact 40-character source revision and record one bounded result for every required check.

## Representative-user usability

Current status: **pending**.

The purpose is to answer bounded experience questions for important/high-risk flows, not to build analytics surveillance. A session should use non-sensitive demo/test data and focus on these questions:

- Can the user tell whether the server is available and whether a model is cold, resident or the default route?
- Can the user complete the primary chat/inference journey without first understanding backend architecture?
- When an operation fails, can the user identify what happened and the next recovery action?
- Can the user find advanced controls when needed without those controls dominating normal use?
- Can the user distinguish measured/available evidence from unavailable or estimated information?

The minimum retained journey set is:

- `control-plane-status-and-navigation`;
- `chat-inference-and-recovery`;
- `advanced-control-discovery`;
- `evidence-interpretation`.

The canonical non-evidence template is `docs/evidence-templates/representative-usability.example.json`.

### Allowed retained fields

Only the following bounded fields may be retained per usability record by default:

- `study_id`;
- `journey_id`;
- `task_completed`;
- `needed_recovery`;
- `assistance_required`;
- `duration_bucket`;
- `severity`;
- `sanitized_observation`.

`sanitized_observation` must describe interaction behavior rather than reproduce product content.

### Forbidden retained data

Do not retain by default:

- raw prompts or model outputs;
- uploaded media or document content;
- local file paths;
- hostnames, usernames or machine identifiers;
- access tokens, secrets or API credentials;
- full screen recordings containing private local information;
- model conversation content merely because it appeared during a usability session.

Product telemetry remains **off by default**. A future telemetry mechanism requires a separate explicit privacy/product decision; this protocol is not authorization to add background analytics.

## Validate real human evidence

After a real manual accessibility review and/or representative-user session has been recorded, run the packaged validator against the bounded JSON files:

```bash
python -m local_llm_server.l2_evidence_bridge validate-product-ui \
  --accessibility /path/to/manual-accessibility.json \
  --usability /path/to/representative-usability.json \
  --output /path/to/product-ui-evidence-summary.json
```

The validator:

- rejects the example template identifiers as completion evidence;
- requires the exact accessibility check set and usability journey set;
- enforces the usability allow-list from `.engineering/product-ui-l2.json`;
- rejects observations that appear to contain private paths, email addresses or secret-like values;
- preserves negative/inconclusive findings instead of rewriting them;
- reports evidence presence, blocking findings and acceptance readiness separately;
- emits a bounded summary and **never mutates** `.engineering/product-ui-l2.json` or `.engineering/baseline.json`.

For manual accessibility, a failed or inconclusive required check is blocking until the underlying issue is resolved and a justified follow-up review is performed. For representative-user usability, `high` or `critical` findings are surfaced as blocking; lower-severity findings remain evidence and still require product judgment rather than silent dismissal.

A validator exit code of `2` means the evidence is validly incomplete/not acceptance-ready. It is not permission to edit observations or thresholds merely to obtain a green result.

## Significant UX change review

A meaningful UI change must evaluate, where applicable:

- user task model;
- information/action hierarchy;
- cognitive load and progressive disclosure;
- failure prevention and recovery;
- accessibility;
- adaptive behavior;
- reuse of the canonical design system;
- regression/evidence impact.

The pull-request template contains machine-checked markers for these questions. `N/A` is acceptable only with a concrete reason; silence is not.

## Evidence identity and cleanup

UI/E2E evidence follows the repository's existing evidence contract:

- associate retained evidence with source/run identity;
- keep CI retention bounded;
- keep raw user/model content out of default retained failure evidence;
- close owned browser/server/process/listener/temp state after runs;
- preserve the existing zero-residue gate independently from the success of browser assertions.

Human-evidence summaries must use the exact tested source revision. The repository may retain only the bounded summary/observations required for the claim; source recordings or raw local content are not implied by this contract.

## Completion semantics

Repository-side `repo-template-sw 0.4.0` product-ui guardrails are already accepted when deterministic contracts and workflows are green on the same integrated revision.

**Full product-ui L2 is not complete while manual accessibility and representative-user usability statuses remain `pending`.** A status may become `not-justified` only through an explicit documented product-risk decision; it must not be used simply to bypass evidence collection.

The bridge validator provides evidence readiness; status promotion remains an explicit repository change reviewed against the retained bounded evidence. This product-ui completion boundary is independent from the separate full-engineering-L2 Apple Silicon/model/backend evidence gate.

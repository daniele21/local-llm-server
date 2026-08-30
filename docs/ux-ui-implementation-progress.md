# Local LLM Server UX/UI progress

Status: active
Document type: workstream-state
Owner: web-product
Canonical scope: state.web-ux
Read when: determining the remaining UX/UI redesign work and its data-contract blockers
Last reviewed: 2026-08-30

Canonical target specification: [`ux-ui-implementation-plan.md`](ux-ui-implementation-plan.md)
Canonical experience contract: [`../design/ux-contract.json`](../design/ux-contract.json)

## Status legend

`PARTIAL` connected behavior/incomplete acceptance · `BLOCKED` upstream source missing · `PENDING` not started · `EVIDENCE` implementation complete/UX or hardware evidence pending · `DONE` complete.

## Workstreams

| Workstream | Status | Integrated boundary | Remaining gate |
| --- | --- | --- | --- |
| Existing Studio workflows | PARTIAL | real Chat and Logs preserved while Models lifecycle is owned directly by the control-plane surface | legacy internal markup cleanup without regression |
| Design system | EVIDENCE | tokens/primitives + canonical EvidenceValue, ResourceBudget, ActionFeedback and disclosure semantics + native/control focus + reduced-motion/light-dark semantics | manual light/dark contrast and semantic-component acceptance |
| Shell/navigation | EVIDENCE | seven canonical URL destinations, refresh/back/forward behavior, opaque model/evaluation detail links, skip link and `aria-current` navigation | real keyboard/zoom/screen-reader traversal |
| Overview | EVIDENCE | readiness/residency/budget/workload/capacity first scan with advanced evidence/provenance disclosure + targeted deterministic visual contract | representative runtime/hardware + manual usability evidence |
| Models & Runtimes | PARTIAL | integrated load/unload/default-route/pin actions + semantic ResourceBudget/ActionFeedback + resource accounting + per-runtime estimate + refresh-stable contextual detail + load-feasibility recovery | route-preserving reload contract, destructive-action acceptance, manual accessibility and hardware evidence |
| Resource budget/pressure | PARTIAL | configured accounting envelope + deterministic pressure-policy contracts + explicit load-capacity decision support and semantic ResourceBudget presentation | representative pressure/hardware evidence before automation |
| Capability UX | PARTIAL | server descriptors drive Endpoints and a task-first Playground model | broader backend/task evidence + manual acceptance |
| Pin/auto-evict | PARTIAL | pin/unpin + evictable + LRU/TTL + hysteretic dry policy | hardware review before any automatic unload |
| Runtime fingerprint | PARTIAL | verified auto-capture + broader backend-version evidence + contextual/progressive-disclosure UI presentation | specialist artifact/backend coverage |
| Endpoints | PARTIAL | task/model compatibility matrix from real capability sources + Try in Playground action | copyable language examples + visual/manual regression evidence |
| Playground text | PARTIAL | task-first Chat mode over the real composer and explicit resident-model selection | legacy-internal cleanup + manual acceptance |
| Playground structured | PARTIAL | first-class task choice owns JSON mode and compatible runtime filtering | schema-oriented UX + broader backend evidence |
| Playground vision | PARTIAL | first-class task choice + real multimodal path + capability-driven image control + fail-closed remote media | regression/hardware evidence |
| Playground transcription | PARTIAL | first-class task choice + multipart local transcription workflow | compatible backend/hardware evidence |
| Benchmark & Evaluation | EVIDENCE | primary Model/Test set/Samples/Run hierarchy + progressive seed/retention/dataset/evidence/identity disclosure + results/history/comparison + deep links + targeted deterministic visual contract | richer experiment dimensions + manual usability/accessibility evidence |
| System/Diagnostics | PARTIAL | canonical runtime/resource/scheduler/identity summary above real logs | visual/hardware evidence |
| Settings/privacy | PARTIAL | read-only effective policy/resource/residency/scheduler state | manual acceptance + mutation semantics only if product requires them |
| Responsive | EVIDENCE | min-width guards, single-column breakpoints, action stacking and horizontal table access | real phone/tablet/desktop + 200% zoom verification |
| Accessibility | EVIDENCE | route navigation semantics, local task-tab semantics, native details disclosures, visible evidence-kind text, focus expansion, non-color state text and reduced motion | contrast + full workflow/manual audit |
| Visual regression | PARTIAL | blocking SHA-256 pixel contracts for deterministic Overview and Evaluation setup fixtures at 1440×1000 dark/reduced-motion | stable responsive/state coverage only as additional high-risk surfaces justify it |
| Hardware UX evidence | PARTIAL | repeatable worker reclamation CLI/report schema exists | representative device reports + real runtime screenshots |

## Current UX v2 structural state

### Navigation and deep links

Primary control-plane navigation now follows the route contract instead of presenting the whole application as one ARIA tabset:

- `/overview`;
- `/models` and `/models/{opaque-model-id}`;
- `/endpoints`;
- `/playground`;
- `/evaluations` and `/evaluations/{opaque-run-id}`;
- `/system`;
- `/settings`.

The server owns these routes and serves the same Studio surface on direct refresh. Sidebar destinations are links with `aria-current="page"`; ARIA tab semantics remain reserved for local subsection controls such as the task selector. The legacy `/` entry point remains compatible and canonicalizes to `/overview` in the browser.

Model and evaluation detail URLs use opaque, URL-safe identifiers derived from already-public UI identities. Direct detail refresh waits for the owning async surface and then restores the existing canonical detail renderer. Missing/invalid detail state fails into an explicit recovery notice instead of guessing.

### Overview

Overview consumes real `/health`, `/status`, `/v1/models`, `/api/v1/resources`, `/api/v1/evidence` and `/api/v1/scheduler`. Missing values remain **Unavailable**.

The first scan is intentionally bounded to five questions:

- is local AI ready;
- how many runtimes are resident and which route is default;
- how much of the configured AI accounting budget is used and what headroom remains;
- how much work is active/queued;
- whether the accounting envelope currently has headroom for another load decision.

Fine-grained timing, fingerprint, admission and provenance remain available under **Runtime evidence & provenance** rather than competing above the fold. Advanced metrics now reuse the canonical `EvidenceValue` presentation and expose evidence kind as visible text. Resource language remains deliberately framed as configured/accounted capacity: low or exhausted headroom is **not** presented as observed physical-memory pressure.

When accounting headroom is constrained, Overview sends the user to the existing Models & Runtimes feasibility/recovery flow instead of introducing a second eviction mechanism.

The deterministic 1440×1000 dark/reduced-motion Overview fixture now has a blocking in-memory screenshot SHA-256 contract. It protects the stable decision hierarchy only; it is not representative-hardware evidence and does not replace responsive/manual review.

### Models & Runtimes

Models & Runtimes remains the canonical lifecycle surface. It directly uses the existing server-owned lifecycle contracts:

- `POST /api/v1/models/load`;
- `POST /api/v1/models/activate` for default-route changes;
- `DELETE /api/v1/models/{model}` for explicit unload;
- `POST /api/v1/residency/pin` for explicit pin/unpin.

Artifact, runtime, route and policy remain separate columns/states. The view does not invent `Verified` artifact evidence when the catalog only proves local availability.

Resource UX separates configured usable budget, accounted committed bytes, accounted reservations, derived remaining capacity and per-runtime load `estimate_bytes` when exposed. A per-runtime estimate is labeled **Estimate**, not observed physical memory; unavailable observed runtime memory remains **Unavailable**. The existing budget/accounting owner now uses the canonical `ResourceBudget` visual semantics and lifecycle messages use `ActionFeedback` without changing server admission authority.

Cold-model Load opens a feasibility surface showing estimated requirement, available capacity and deficit. When an idle non-default runtime is policy-evictable and has sufficient estimated capacity, the UI can offer explicit `Unload <runtime> & continue`. This is an intentional user action; hidden unload/automatic eviction remains forbidden.

Model detail remains contextual beside the inventory but is now reachable through `/models/{opaque-model-id}` and survives refresh. Reload remains deliberately unavailable because the server does not expose a route-preserving reload contract.

### Endpoints and Playground

Capability truth remains server-owned and model-name heuristics remain forbidden. Playground starts with four peer task surfaces: Chat, Structured output, Vision-language and Transcription. The user chooses task before model; compatible resident runtimes execute immediately and compatible cold runtimes expose explicit **Load & use**.

Chat, Structured output and Vision-language reuse the proven composer execution path. Unsupported task/model combinations remain disabled/fail closed. Transcription remains a first-class task over `/v1/audio/transcriptions`. If capability sources disappear, the capability layer restores legacy controls instead of leaving stale inferred state.

### Benchmark & Evaluation

Evaluation keeps the existing server-owned run, test-set, scorer, history and comparison contracts. The first scan is now explicitly bounded to **Model → Test set → Samples → Run evaluation**.

Reproducibility and management controls remain available without dominating that path:

- seed, retained-content policy and scorer note live under **Advanced run settings**;
- custom dataset import/library is a separate closed disclosure;
- evidence-grade/exploratory definitions are a separate closed disclosure;
- full fingerprint/config/test-set identity appears under **Run identity & reproducibility** after a result or history selection.

Result quality/success/time/token metrics reuse canonical `EvidenceValue` semantics with visible evidence-kind text. Persisted history, comparison, per-sample detail and `/evaluations/{opaque-run-id}` deep links remain unchanged in ownership and behavior.

The deterministic 1440×1000 dark/reduced-motion Evaluation setup fixture now has a blocking in-memory screenshot SHA-256 contract. The PNG is not retained by the normal gate. Richer experiment controls such as explicit warm/cold mode or user-configurable quality/performance weighting remain out of scope until a real server-owned contract exists.

### System / Diagnostics

Diagnostics prepends source-backed operational evidence to real live logs: resident/active state, identity coverage, scheduler inflight/queue, remaining resource budget and canonical queue-wait/TTFT/decode-throughput values only when sourced. Prompt/generated content is not copied into the evidence layer.

### Settings

Settings remains source-backed/read-only. It shows canonical request policy, remote-media/remote-code flags, resource budget, residency/pinning and scheduler state without inventing configuration mutations that lack a server-owned contract.

## Integrated deterministic accessibility/responsive foundation

The product surface provides:

- native route links for the seven primary destinations with `aria-current` on the current page;
- refresh/back/forward-stable primary navigation and opaque detail routes;
- a keyboard skip link to the main workspace;
- inactive legacy-backed panels hidden from the accessibility tree;
- decorative navigation icons hidden from assistive technology;
- visible focus outlines for design-system and retained native/legacy controls;
- status and evidence-kind text in addition to color/style;
- native keyboard-operable details/summary for advanced Evaluation disclosure;
- reduced-motion handling;
- `min-width: 0`, content wrapping and one-column responsive breakpoints;
- preserved horizontal table access instead of clipped columns;
- a local task selector with tab semantics and Arrow/Home/End navigation;
- resource and runtime states expressed in text, not only through color.

These deterministic contracts are not the final manual accessibility certification.

## Immediate UX validation wave

### H1b — Manual accessibility acceptance

Verify on the real integrated UI:

- keyboard-only traversal across route navigation, task selector, model inventory/detail, Evaluation disclosures, forms, upload controls and lifecycle actions;
- sensible focus order after page navigation, disclosure changes, async source refreshes and action completion;
- semantic names for remaining icon-only controls;
- light/dark contrast for text, focus, status badges, evidence kinds and disabled states;
- no critical action/data loss at 200% browser zoom;
- screen-reader spot checks for current-route state, task selection and dynamic status feedback.

### H2b — Responsive and visual regression

The first targeted visual contracts are now integrated for stable Overview and Evaluation setup fixture surfaces. Extend visual coverage only when a state is stable and high-risk enough to justify a strict pixel contract. Candidate future states remain loading, empty/cold, unavailable source, warning/accounting constraint, error/action failure, success/resident/evidence-grade and insufficient-capacity/load-feasibility across representative widths.

Real runtime screenshots remain separate from deterministic fixture visual evidence and must not be promoted from hosted CI.

### H3 — Representative runtime evidence

Use the canonical representative-device evidence workflow plus compatible text/vision/transcription runtimes to collect real hardware states. Real runtime screenshots and hardware-dependent memory/performance claims remain blocked until these runs exist.

### H4 — Remaining structural cleanup

After the P2 surface acceptance stabilizes:

- remove legacy model lifecycle markup that is no longer a product entrypoint;
- keep the proven Chat execution implementation until the task-first wrapper has complete parity evidence;
- fold the product-semantic presentation adapter into owning renderers when legacy/static convergence makes that lower-complexity than the adapter;
- align README/API examples with current product entrypoints;
- update public screenshots only from implemented real states.

## Evidence UX rules

- `0` is valid only when a source measured or accounted zero; missing data is `Unavailable`.
- resource estimate and observed footprint remain distinguishable.
- global resource-policy accounting is not relabeled as physical runtime RSS or memory pressure.
- child RSS is shown only while the child PID is actually observable; after stop it is not fabricated as measured zero.
- chunk throughput is never token throughput.
- exploratory benchmark runs may execute but are not presented as evidence-grade comparisons.
- memory/resource admission remains a server-owned decision even when the UI can preview current estimates.
- capability truth is server-owned; JavaScript presents/filters it but does not invent support.
- custom test-set files are data, not executable scorer/plugin definitions.
- explicit eviction/unload success is not presented as a host-memory reclamation guarantee.
- deterministic accessibility/pixel-fixture tests are not a substitute for manual contrast/zoom or real hardware evidence.
- a changed visual digest requires intentional review of the rendered fixture; it must not be mechanically updated just to make CI green.

## Acceptance still pending

Before primary UX surfaces can be marked DONE:

- complete keyboard/focus/semantic-label workflow audit;
- contrast verification in supported light/dark modes;
- real 200% zoom and representative width usability;
- extend visual contracts to additional stable high-risk states/widths where justified;
- action confirmation/feedback review for destructive lifecycle operations;
- screen-reader spot checks for route/task/disclosure/dynamic-state semantics;
- real runtime screenshots for public documentation;
- representative hardware evidence for resource/performance claims.

## Update rule

Update this file in the same integration cycle whenever a UX workstream status or blocker changes. Keep detailed acceptance criteria in the target specification and durable behavior in `design/ux-contract.json`.

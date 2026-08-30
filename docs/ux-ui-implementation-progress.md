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
| Existing Studio workflows | PARTIAL | real Chat and Logs preserved while Models lifecycle is now owned directly by the control-plane surface | legacy internal markup cleanup without regression |
| Design system | EVIDENCE | tokens/primitives + expanded native/control focus + reduced-motion/light-dark semantics | manual light/dark contrast evidence |
| Shell/navigation | EVIDENCE | seven destinations + dedicated ARIA tablist/tabpanel + roving keyboard focus + skip link | route/deep-link migration + real end-to-end keyboard/zoom traversal |
| Overview | PARTIAL | health/status/models + resource/evidence/scheduler sources | hierarchy simplification + representative runtime/hardware evidence |
| Models & Runtimes | PARTIAL | integrated load/unload/default-route/pin actions + resource accounting + per-runtime estimate + contextual detail + load-feasibility recovery | route-preserving reload contract, manual accessibility and hardware evidence |
| Resource budget/pressure | PARTIAL | configured accounting envelope + deterministic pressure-policy contracts + explicit load-capacity decision support | representative pressure/hardware evidence before automation |
| Capability UX | PARTIAL | server descriptors drive Endpoints and a task-first Playground model | broader backend/task evidence + manual acceptance |
| Pin/auto-evict | PARTIAL | pin/unpin + evictable + LRU/TTL + hysteretic dry policy | hardware review before any automatic unload |
| Runtime fingerprint | PARTIAL | verified auto-capture + broader backend-version evidence + contextual UI presentation | specialist artifact/backend coverage |
| Endpoints | PARTIAL | task/model compatibility matrix from real capability sources + Try in Playground action | copyable language examples + visual/manual regression evidence |
| Playground text | PARTIAL | task-first Chat mode over the real composer and explicit resident-model selection | legacy-internal cleanup + manual acceptance |
| Playground structured | PARTIAL | first-class task choice owns JSON mode and compatible runtime filtering | schema-oriented UX + broader backend evidence |
| Playground vision | PARTIAL | first-class task choice + real multimodal path + capability-driven image control + fail-closed remote media | regression/hardware evidence |
| Playground transcription | PARTIAL | first-class task choice + multipart local transcription workflow | compatible backend/hardware evidence |
| Benchmark & Evaluation | PARTIAL | run/results/history/comparison + custom JSON import/version selection | hierarchy simplification + richer experiments + visual/manual evidence |
| System/Diagnostics | PARTIAL | canonical runtime/resource/scheduler/identity summary above real logs | visual/hardware evidence |
| Settings/privacy | PARTIAL | read-only effective policy/resource/residency/scheduler state | manual acceptance + mutation semantics only if product requires them |
| Responsive | EVIDENCE | min-width guards, single-column breakpoints, action stacking and horizontal table access | real phone/tablet/desktop + 200% zoom verification |
| Accessibility | EVIDENCE | shell semantics, task-selector keyboard semantics, focus expansion, non-color state text and reduced motion | contrast + full workflow/manual audit |
| Visual regression | PENDING | no stable screenshot suite yet | deterministic source-state fixtures + screenshot gate |
| Hardware UX evidence | PARTIAL | repeatable worker reclamation CLI/report schema exists | representative device reports + real runtime screenshots |

## Current UX v2 structural state

### Overview

Overview consumes real `/health`, `/status`, `/v1/models`, `/api/v1/resources`, `/api/v1/evidence` and `/api/v1/scheduler`. It distinguishes configured default identity from resident default route, cold state from failure, resource policy state, queue wait and verified/exploratory identity. Missing values remain **Unavailable**.

The next structural pass should reduce dashboard density further so readiness, resident runtimes, AI budget/headroom, active/queued work and pressure dominate the first scan.

### Models & Runtimes

Models & Runtimes is now the canonical lifecycle surface instead of a summary that sends the user back to legacy controls.

It directly uses the existing server-owned lifecycle contracts:

- `POST /api/v1/models/load`;
- `POST /api/v1/models/activate` for default-route changes;
- `DELETE /api/v1/models/{model}` for explicit unload;
- `POST /api/v1/residency/pin` for explicit pin/unpin.

Artifact, runtime, route and policy remain separate columns/states. The view does not invent `Verified` artifact evidence when the catalog only proves local availability.

Resource UX separates:

- configured usable budget;
- accounted committed bytes;
- accounted reservations;
- derived remaining capacity;
- per-runtime load `estimate_bytes` when current evidence exposes an estimate.

A per-runtime estimate is labeled **Estimate**, not observed physical memory. If an observed runtime-memory source is unavailable, the UI says **Unavailable** rather than deriving one from model size.

Cold-model Load opens a feasibility surface that shows estimated requirement, available capacity and deficit. When an idle non-default runtime is policy-evictable and has sufficient estimated capacity, the UI can offer an explicit `Unload <runtime> & continue` action. This is an intentional user action and the estimated capacity is not presented as physical-memory observation. Hidden unload/automatic eviction remains forbidden.

Model detail stays in context beside the inventory and progressively discloses runtime identity/diagnostics. Reload is deliberately shown as unavailable because the server does not currently expose a route-preserving reload contract; the UI does not emulate reload through default-route activation.

### Endpoints and Playground

Capability truth remains server-owned and model-name heuristics remain forbidden.

The Playground now starts with four peer task surfaces:

- Chat;
- Structured output;
- Vision-language;
- Transcription.

The user chooses the task before choosing the model. The surface then separates compatible resident runtimes from compatible cold runtimes. Resident runtimes can be selected immediately; cold runtimes expose explicit **Load & use** through the existing load API.

Chat, Structured output and Vision-language reuse the proven legacy composer execution path rather than introducing a second request implementation:

- Chat enables the text composer for a compatible resident runtime;
- Structured output makes the task choice own JSON mode;
- Vision-language enables local image controls only for a runtime declaring `vision_language` plus image input;
- unsupported task/model combinations remain disabled/fail closed.

Transcription is no longer a nested capability panel for whichever chat model happens to be selected. It is a first-class task surface over `/v1/audio/transcriptions` with an explicit compatible model.

If capability sources disappear, the capability layer restores legacy controls instead of leaving stale task-based disabled state.

### Benchmark & Evaluation

The evaluation screen supports resident-model selection, versioned built-in/custom test sets, deterministic seed/sample counts, validated JSON import, explicit test-set version propagation, duplicate-conflict feedback, expandable per-sample prompt/expected/output/check/metric details, persisted history and compatibility-aware comparison. Private local history keeps generated output by default with a per-run opt-out; prompt and expected value stay available through the matching immutable test set. Legacy runs are enriched only after dataset-identity verification. Open run/sample inspectors, focus and scroll orientation survive the ten-second history refresh. It does not auto-declare a better/worse model.

The next structural pass should move seed/preset/weighting and full identity evidence behind progressive disclosure while preserving reproducibility.

### System / Diagnostics

Diagnostics prepends source-backed operational evidence to real live logs: resident/active state, identity coverage, scheduler inflight/queue, remaining resource budget and canonical queue-wait/TTFT/decode-throughput values only when sourced. Prompt/generated content is not copied into the evidence layer.

### Settings

Settings remains source-backed/read-only. It shows canonical request policy, remote-media/remote-code flags, resource budget, residency/pinning and scheduler state without inventing configuration mutations that lack a server-owned contract.

## Integrated deterministic accessibility/responsive foundation

The product surface provides:

- a dedicated ARIA `tablist` containing only the seven current control-plane destinations;
- `tab`/`tabpanel` relationships and roving Arrow/Home/End keyboard behavior;
- inactive panels hidden from the accessibility tree;
- a keyboard skip link to the main workspace;
- decorative navigation icons hidden from assistive technology;
- visible focus outlines for design-system and retained native/legacy controls;
- status text in addition to color;
- reduced-motion handling;
- `min-width: 0`, content wrapping and one-column responsive breakpoints;
- preserved horizontal table access instead of clipped columns;
- a task selector with tab semantics and Arrow/Home/End navigation;
- resource and runtime states expressed in text, not only through color.

These deterministic contracts are not the final manual accessibility certification.

## Immediate UX validation wave

### H1b — Manual accessibility acceptance

Verify on the real integrated UI:

- keyboard-only traversal across shell, task selector, model inventory/detail, forms, upload controls and lifecycle actions;
- sensible focus order after async source refreshes and action completion;
- semantic names for remaining icon-only controls;
- light/dark contrast for text, focus, status badges and disabled states;
- no critical action/data loss at 200% browser zoom;
- screen-reader spot checks for task/panel selection and dynamic status feedback.

### H2b — Responsive and visual regression

Create deterministic source-state fixtures for:

- loading;
- empty/cold;
- unavailable source;
- warning/pressure/exploratory;
- error/action failure;
- success/resident/evidence-grade;
- insufficient-capacity/load-feasibility.

Capture stable phone/tablet/desktop reference widths and separate fixture screenshots from real runtime screenshots. Visual regression should detect layout/state regressions without presenting synthetic fixtures as product performance evidence.

### H3 — Representative runtime evidence

Use the canonical representative-device evidence workflow plus compatible text/vision/transcription runtimes to collect real hardware states. Real runtime screenshots and hardware-dependent memory/performance claims remain blocked until these runs exist.

### H4 — Remaining structural cleanup

After the P0 surface acceptance stabilizes:

- remove legacy model lifecycle markup that is no longer a product entrypoint;
- keep the proven Chat execution implementation until the task-first wrapper has complete parity evidence;
- migrate app-wide navigation from global tab semantics to refresh-stable routes/deep links as required by UX contract 0.6;
- simplify Overview and Evaluation hierarchy/progressive disclosure;
- align README/API examples with current product entrypoints;
- update public screenshots only from implemented real states.

## Evidence UX rules

- `0` is valid only when a source measured or accounted zero; missing data is `Unavailable`.
- resource estimate and observed footprint remain distinguishable.
- global resource-policy accounting is not relabeled as physical runtime RSS.
- child RSS is shown only while the child PID is actually observable; after stop it is not fabricated as measured zero.
- chunk throughput is never token throughput.
- exploratory benchmark runs may execute but are not presented as evidence-grade comparisons.
- memory/resource admission remains a server-owned decision even when the UI can preview current estimates.
- capability truth is server-owned; JavaScript presents/filters it but does not invent support.
- custom test-set files are data, not executable scorer/plugin definitions.
- explicit eviction/unload success is not presented as a host-memory reclamation guarantee.
- deterministic accessibility/fixture tests are not a substitute for manual contrast/zoom or real hardware evidence.

## Acceptance still pending

Before primary UX surfaces can be marked DONE:

- complete keyboard/focus/semantic-label workflow audit;
- contrast verification in supported light/dark modes;
- real 200% zoom and representative width usability;
- stable source-state visual regression suite;
- action confirmation/feedback review for destructive lifecycle operations;
- screen-reader spot checks for task/dynamic-state semantics;
- route/deep-link migration for app-wide navigation;
- real runtime screenshots for public documentation;
- representative hardware evidence for resource/performance claims.

## Update rule

Update this file in the same integration cycle whenever a UX workstream status or blocker changes. Keep detailed acceptance criteria in the target specification and durable behavior in `design/ux-contract.json`.

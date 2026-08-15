# Local LLM Server UX/UI progress

Status: active
Document type: workstream-state
Owner: web-product
Canonical scope: state.web-ux
Read when: determining the remaining UX/UI redesign work and its data-contract blockers
Last reviewed: 2026-08-15

Canonical target specification: [`ux-ui-implementation-plan.md`](ux-ui-implementation-plan.md)

## Status legend

`PARTIAL` connected behavior/incomplete acceptance · `BLOCKED` upstream source missing · `PENDING` not started · `EVIDENCE` implementation complete/UX or hardware evidence pending · `DONE` complete.

## Workstreams

| Workstream | Status | Integrated boundary | Remaining gate |
| --- | --- | --- | --- |
| Existing Studio workflows | PARTIAL | real Chat, Models lifecycle, Logs, examples and Swagger preserved during migration | legacy-internal cleanup without regression |
| Design system | EVIDENCE | tokens/primitives + expanded native/control focus + reduced-motion/light-dark semantics | manual light/dark contrast evidence |
| Shell/navigation | EVIDENCE | seven destinations + dedicated ARIA tablist/tabpanel + roving keyboard focus + skip link | real end-to-end keyboard/zoom traversal |
| Overview | PARTIAL | health/status/models + resource/evidence/scheduler sources | representative runtime/hardware evidence |
| Models & Runtimes | PARTIAL | catalog/resident/capability/resource/identity/residency sources + pin UX | lifecycle/manual-accessibility/hardware evidence |
| Resource budget/pressure | PARTIAL | configured product policy + deterministic pressure-policy contracts | representative pressure/hardware evidence before automation |
| Capability UX | PARTIAL | server descriptors drive Endpoints and Playground controls | broader backend/task evidence + manual acceptance |
| Pin/auto-evict | PARTIAL | pin/unpin + evictable + LRU/TTL + hysteretic dry policy | hardware review before any automatic unload |
| Runtime fingerprint | PARTIAL | verified auto-capture + broader backend-version evidence + UI presentation | specialist artifact/backend coverage |
| Endpoints | PARTIAL | task/model compatibility matrix from real capability sources | visual/manual regression evidence |
| Playground text | PARTIAL | real chat + canonical capability-driven controls | legacy-internal cleanup + manual acceptance |
| Playground vision | PARTIAL | real multimodal path + capability-driven image control + fail-closed remote media | regression/hardware evidence |
| Playground transcription | PARTIAL | first-class multipart transcription API + capability-driven mini-playground | compatible backend/hardware evidence |
| Benchmark & Evaluation | PARTIAL | run/results/history/comparison + custom JSON import/version selection | richer experiments + visual/manual evidence |
| System/Diagnostics | PARTIAL | canonical runtime/resource/scheduler/identity summary above real logs | visual/hardware evidence |
| Settings/privacy | PARTIAL | read-only effective policy/resource/residency/scheduler state | manual acceptance + mutation semantics only if product requires them |
| Responsive | EVIDENCE | min-width guards, single-column breakpoints, action stacking and horizontal table access | real phone/tablet/desktop + 200% zoom verification |
| Accessibility | EVIDENCE | tab semantics, Arrow/Home/End navigation, skip link, focus expansion, decorative-icon hiding, text status | contrast + full workflow/manual audit |
| Visual regression | PENDING | no stable screenshot suite yet | deterministic source-state fixtures + screenshot gate |
| Hardware UX evidence | PARTIAL | repeatable worker reclamation CLI/report schema exists | representative device reports + real runtime screenshots |

## Source-backed product state now available

### Overview

The Overview consumes real `/health`, `/status`, `/v1/models`, `/api/v1/resources`, `/api/v1/evidence` and `/api/v1/scheduler`. It distinguishes configured default identity from resident default route, cold state from failure, resource policy state, queue wait and verified/exploratory identity. Missing values remain **Unavailable**.

### Models & Runtimes

The Models view combines resident identity, status/default routing, configured catalog/capabilities, resource admission, verified runtime identity and residency/pinning evidence. Pin/unpin is a real admin action. `Evictable` means current policy eligibility only and is never displayed as proof of memory reclamation.

### Endpoints and Playground

The capability layer consumes server-owned descriptors rather than named-model heuristics. Chat, vision-language, structured-generation and transcription availability follow declared tasks/modalities/features; only resident runtimes are presented as immediately executable. Transcription remains a distinct audio -> text workflow over `/v1/audio/transcriptions`. Capability-source loss restores the legacy controls instead of leaving stale disabled UI.

### Benchmark & Evaluation

The evaluation screen supports resident-model selection, versioned built-in/custom test sets, deterministic seed/sample counts, validated JSON import, explicit test-set version propagation, duplicate-conflict feedback, per-sample result/error/evidence state, persisted history and compatibility-aware comparison. It does not auto-declare a better/worse model.

### System / Diagnostics

Diagnostics prepends source-backed operational evidence to real live logs: resident/active state, identity coverage, scheduler inflight/queue, remaining resource budget and canonical queue-wait/TTFT/decode-throughput values only when sourced. Prompt/generated content is not copied into the evidence layer.

### Settings

Settings remains source-backed/read-only. It shows canonical request policy, remote-media/remote-code flags, resource budget, residency/pinning and scheduler state without inventing configuration mutations that lack a server-owned contract.

## Integrated deterministic accessibility/responsive foundation

The shell now provides:

- a dedicated ARIA `tablist` containing only the seven control-plane destinations; auxiliary controls such as the guided tour remain outside tab semantics;
- `tab`/`tabpanel` relationships through `aria-controls`, `aria-labelledby` and `aria-selected`;
- roving tabindex and ArrowUp/Down/Left/Right plus Home/End navigation;
- inactive panels hidden from the accessibility tree;
- a keyboard skip link to the main workspace;
- decorative navigation icons marked assistive-technology hidden/non-focusable;
- visible focus outlines for design-system and retained native/legacy buttons, links, inputs, selects and textareas;
- status text in addition to the color indicator;
- broader reduced-motion handling;
- `min-width: 0`, content wrapping and one-column responsive breakpoints for high-zoom/narrow effective viewports;
- preserved horizontal table access instead of clipping columns.

These contracts pass deterministic CI and Node syntax checks. They are **not** the final manual accessibility certification.

## Immediate UX validation wave

### H1b — Manual accessibility acceptance

Verify on the real integrated UI:

- keyboard-only traversal across shell, forms, tables, upload controls and lifecycle actions;
- sensible focus order after async source refreshes and action completion;
- semantic names for remaining icon-only controls outside the control-plane shell;
- light/dark contrast for text, focus, status badges and disabled states;
- no critical action/data loss at 200% browser zoom;
- screen-reader spot checks for tab/panel selection and dynamic status feedback.

### H2b — Responsive and visual regression

Create deterministic source-state fixtures for:

- loading;
- empty/cold;
- unavailable source;
- warning/pressure/exploratory;
- error/action failure;
- success/resident/evidence-grade.

Capture stable phone/tablet/desktop reference widths and separate fixture screenshots from real runtime screenshots. Visual regression should detect layout/state regressions without presenting synthetic fixtures as product performance evidence.

### H3 — Representative runtime evidence

Use `local-llm evidence-reclamation` plus compatible text/vision/transcription runtimes to collect real hardware states. The worker runner can record live child RSS during READY/PEAK and host memory before/after stop while keeping prompt/output/path data out of the JSON report. Real runtime screenshots and hardware-dependent claims remain blocked until these runs exist.

### H4 — Legacy/internal and release cleanup

After acceptance coverage stabilizes:

- remove obsolete internal/placeholder markup superseded by source-backed overlays;
- retain real Chat, Logs and lifecycle behavior until modular replacements prove parity;
- align README/API examples with the current product entrypoints and hardware evidence workflow;
- update public screenshots only from implemented real states.

## Evidence UX rules

- `0` is valid only when a source measured zero; missing data is `Unavailable`.
- resource estimate and observed footprint remain distinguishable.
- child RSS is shown only while the child PID is actually observable; after stop it is not fabricated as measured zero.
- chunk throughput is never token throughput.
- exploratory benchmark runs may execute but are not presented as evidence-grade comparisons.
- reclamation evidence is not PASS merely because a subprocess exits or one memory delta is positive.
- capability truth is server-owned; JavaScript presents/filters it but does not invent support.
- custom test-set files are data, not executable scorer/plugin definitions.
- explicit eviction success is not presented as a host-memory reclamation guarantee.
- deterministic accessibility/fixture tests are not a substitute for manual contrast/zoom or real hardware evidence.

## Acceptance still pending

Before primary UX surfaces can be marked DONE:

- complete keyboard/focus/semantic-label workflow audit;
- contrast verification in supported light/dark modes;
- real 200% zoom and representative width usability;
- stable source-state visual regression suite;
- action confirmation/feedback review for destructive lifecycle operations;
- screen-reader spot checks for tab/dynamic-state semantics;
- real runtime screenshots for public documentation;
- representative hardware evidence for resource/performance claims.

## Update rule

Update this file in the same integration cycle whenever a UX workstream status or blocker changes. Keep detailed acceptance criteria in the target specification.

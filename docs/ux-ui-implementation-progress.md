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
| Design system | PARTIAL | tokens/primitives/focus/reduced-motion/light-dark | full accessibility/contrast evidence |
| Shell/navigation | PARTIAL | seven control-plane destinations navigable with truthful neutral fallbacks | keyboard/responsive evidence |
| Overview | PARTIAL | health/status/models + resource/evidence/scheduler sources | representative runtime/hardware evidence |
| Models & Runtimes | PARTIAL | catalog/resident/capability/resource/identity/residency sources + pin UX | lifecycle/accessibility/hardware evidence |
| Resource budget/pressure | PARTIAL | configured product policy and `/api/v1/resources` | measured reconciliation + hardware evidence |
| Capability UX | PARTIAL | server descriptors drive Endpoints and Playground controls | broader backend/task evidence + accessibility |
| Pin/auto-evict | PARTIAL | pin/unpin + explicit evictable state + deterministic LRU/TTL preview/execution | pressure-trigger validation + hardware evidence before automation |
| Runtime fingerprint | PARTIAL | verified auto-capture + Overview/Models/Diagnostics presentation | broader artifact/backend coverage |
| Endpoints | PARTIAL | task/model compatibility matrix from real capability sources | accessibility/regression evidence |
| Playground text | PARTIAL | real chat + canonical capability-driven controls | legacy-internal cleanup + accessibility/evidence |
| Playground vision | PARTIAL | real multimodal path + capability-driven image control + fail-closed remote media | regression/hardware evidence |
| Playground transcription | PARTIAL | first-class multipart transcription API + capability-driven mini-playground | compatible backend/hardware evidence |
| Benchmark & Evaluation | PARTIAL | run/results/history/comparison + custom JSON import/version selection | richer experiments + accessibility/visual evidence |
| System/Diagnostics | PARTIAL | canonical runtime/resource/scheduler/identity summary above real live logs | accessibility/visual/hardware evidence |
| Settings/privacy | PARTIAL | read-only effective policy/resource/residency/scheduler state | accessibility + future mutation semantics only if product requires them |
| Responsive | PARTIAL | primary control-plane grids include responsive collapse rules | reference-width + 200% zoom verification |
| Accessibility | PARTIAL | primitive-level focus/status/reduced motion | full keyboard/focus/contrast/zoom matrix |
| Visual regression | PENDING | no stable screenshot suite yet | deterministic source-state fixtures + screenshot gate |
| Hardware UX evidence | PENDING | deterministic lifecycle experiment harness exists | representative reclamation/performance runs |

## Source-backed product state now available

### Overview

The Overview consumes real `/health`, `/status`, `/v1/models`, `/api/v1/resources`, `/api/v1/evidence` and `/api/v1/scheduler` sources where available. It distinguishes configured default identity from resident default route, cold state from failure, resource policy state, queue wait and verified/exploratory identity. Missing values remain **Unavailable**.

### Models & Runtimes

The Models view now combines:

- `/v1/models` for resident identity;
- `/status` for route/lifecycle/active-request state;
- `/api/v1/models/registry` for configured catalog and capability descriptors;
- `/api/v1/resources` for global resource admission state;
- `/api/v1/evidence` for verified runtime identity;
- `/api/v1/residency` for pin/evictability/last-used state.

Pin/unpin is a real admin action. `Evictable` means policy eligibility only; it is not presented as proof of resource reclamation.

### Endpoints and Playground

The capability layer consumes server-owned descriptors rather than named-model heuristics:

- chat, vision-language, structured-generation and transcription availability are derived from declared tasks;
- text/image controls follow declared input modalities;
- structured-output/thinking controls follow declared features;
- only resident runtimes are presented as immediately executable;
- transcription is a distinct audio -> text flow over `/v1/audio/transcriptions`;
- when capability metadata is unavailable, legacy controls are restored instead of being left stale/disabled.

### Benchmark & Evaluation

The evaluation screen supports:

- resident model selection;
- versioned built-in/custom test sets;
- valid sample multiples of 10 and deterministic seed;
- validated JSON custom test-set import;
- explicit id + version propagation into runs;
- duplicate conflict without silent replace;
- objective quality, execution success, per-sample result/error and sourced timing/token evidence;
- evidence-grade vs exploratory run state based on runtime fingerprint;
- persisted history inspection and compatibility-aware baseline/candidate comparison;
- no automatic better/worse verdict.

### System / Diagnostics

Diagnostics now prepends source-backed operational evidence to the existing real log workflow:

- resident runtime/active-request state;
- verified identity coverage;
- scheduler inflight/queue state;
- remaining configured resource budget;
- canonical queue-wait/TTFT/decode-throughput values from `durations_ms` and `throughput` only when sourced.

Prompt/generated content is not copied into the diagnostics evidence layer.

### Settings

Settings is intentionally read-only and source-backed. It shows:

- whether canonical request policy is installed;
- remote-media and remote-code defaults/effective runtime flags;
- resource budget state;
- residency/pinning state;
- scheduler policy state.

The UI does not invent mutation controls for policy settings that lack a defined server-owned mutation contract.

## Immediate UX hardening wave

### H1 — Accessibility acceptance

Implement/verify:

- keyboard-only navigation through shell, forms, tables and lifecycle controls;
- visible focus for all interactive elements;
- semantic names for icon-only controls;
- status text in addition to color;
- light/dark contrast checks;
- 200% zoom without clipped critical actions/data.

### H2 — Responsive and visual regression

Create deterministic source-state fixtures for:

- loading;
- empty/cold;
- unavailable source;
- warning/pressure/exploratory;
- error/action failure;
- success/resident/evidence-grade.

Capture stable reference widths for phone/tablet/desktop and prevent regression without presenting fixture screenshots as real runtime evidence.

### H3 — Representative runtime evidence

Use the repeated lifecycle/reclamation harness and compatible task runtimes to capture real states used by public screenshots and product claims. Hardware evidence remains separate from deterministic UI fixtures.

### H4 — Legacy-internal cleanup

Once acceptance coverage is stable:

- remove obsolete duplicate placeholder/internal markup that overlays have superseded;
- retain real Chat, Logs and lifecycle behavior until modular replacements prove parity;
- keep supported product entrypoints aligned with UI documentation.

## Evidence UX rules

- `0` is valid only when a source measured zero; missing data is `Unavailable`.
- resource estimate and observed footprint remain distinguishable.
- chunk throughput is never token throughput.
- exploratory benchmark runs may execute but are not presented as evidence-grade comparisons.
- reclamation evidence is not PASS merely because a subprocess exits or one memory delta is positive.
- capability truth is server-owned; JavaScript presents/filters it but does not invent support.
- custom test-set files are data, not executable scorer/plugin definitions.
- explicit eviction success is not presented as a host-memory reclamation guarantee.

## Acceptance still pending

Before primary UX surfaces can be marked DONE:

- keyboard/focus/semantic-label audit;
- contrast verification in supported light/dark modes;
- 200% zoom and representative width usability;
- stable source-state visual regression suite;
- action confirmation/feedback review for destructive lifecycle operations;
- real runtime screenshots for public documentation;
- representative hardware evidence for resource/performance claims.

## Update rule

Update this file in the same integration cycle whenever a UX workstream status or blocker changes. Keep detailed acceptance criteria in the target specification.

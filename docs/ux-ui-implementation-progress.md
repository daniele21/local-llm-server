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
| Existing Studio workflows | PARTIAL | real Chat, Models, Logs, examples and Swagger preserved | modular migration without regression |
| Design system | PARTIAL | tokens/primitives/focus/reduced-motion/light-dark | full screen adoption + accessibility evidence |
| Shell/navigation | PARTIAL | seven control-plane destinations navigable | screen-level responsive/keyboard evidence |
| Overview | PARTIAL | health/status/models + resource/evidence/scheduler sources | representative hardware evidence + final diagnostics composition |
| Models & Runtimes | PARTIAL | resident/catalog/capability/cold/default source-backed view | pin/eviction controls + lifecycle UX evidence |
| Resource budget/pressure | PARTIAL | configured product policy and `/api/v1/resources` | measured reconciliation + hardware evidence |
| Capability UX | PARTIAL | descriptors public and rendered in Models | capability-driven Playground/Endpoints |
| Pin/auto-evict | PENDING | no B6 policy yet | B6a pin metadata then lease-safe LRU/TTL |
| Runtime fingerprint | PARTIAL | verified auto-capture + `/api/v1/evidence` + Overview | broader artifact/backend coverage |
| Endpoints | PARTIAL | real Swagger/examples + public capability metadata | task/model compatibility composition |
| Playground text | PARTIAL | real chat + canonical policy/capability enforcement | modular capability-driven controls + live evidence presentation |
| Playground vision | PARTIAL | real multimodal path + fail-closed remote media | capability-driven model/controls + regression evidence |
| Playground transcription | PARTIAL | first-class `/v1/audio/transcriptions` backend/API | dedicated UI workflow + compatible runtime evidence |
| Benchmark & Evaluation | PARTIAL | real run/results/history/comparison + custom dataset backend | custom upload/version-selection UI |
| System/Diagnostics | PARTIAL | real logs/status preserved; evidence sources exist | modular source-backed diagnostics screen |
| Settings/privacy | PARTIAL | supported entrypoints enforce remote-media policy | source-backed policy state/configuration presentation |
| Responsive | PARTIAL | major control-plane grids collapse responsively | full screen/reference-width verification |
| Accessibility | PARTIAL | primitive-level focus/status/reduced motion | keyboard/focus/contrast/zoom matrix |
| Visual regression | PENDING | no stable screenshot suite | stable source-backed states + fixture strategy |
| Hardware UX evidence | PENDING | no representative reclamation/performance matrix | B3d/H3 representative hardware runs |

## Source-backed product state now available

### Overview

The Overview consumes real `/health`, `/status`, `/v1/models`, `/api/v1/resources`, `/api/v1/evidence` and `/api/v1/scheduler` sources where available. It distinguishes:

- configured default identity from resident default route;
- cold/zero-resident state from failure;
- configured/disabled/unavailable resource policy;
- measured values from unavailable values;
- queue wait from runtime execution timing;
- verified runtime fingerprint from exploratory/no-fingerprint state.

`null`/missing values remain **Unavailable**; the UI does not coerce them to zero.

### Models & Runtimes

The control-plane Models view combines:

- `/v1/models` for resident identity;
- `/status` for default route, lifecycle and active-request state;
- `/api/v1/models/registry` for configured catalog and capability descriptors when enabled.

Configured identity, resident/cold state, backend, active requests and capability summary are source-backed. The remaining major lifecycle UX gap is explicit pin/evictability/automatic-eviction policy.

### Benchmark & Evaluation

The evaluation screen now supports:

- real resident-model selection;
- versioned test-set selection;
- valid sample multiples of 10 and deterministic seed;
- real evaluation execution;
- objective quality, execution success, per-sample result/error and sourced timing/token evidence;
- evidence-grade vs exploratory run state based on runtime fingerprint;
- persisted history inspection;
- compatibility-aware baseline/candidate comparison with `Not comparable`, `Exploratory comparison`, `Descriptive only` and attribution-safe states;
- no automatic better/worse verdict.

The backend additionally supports validated custom test-set import and multiple versions. The UI still needs the upload/catalog/version-selection slice.

## Immediate UX wave

### E6b — Custom test-set workflow

Implement now:

- JSON file picker and import action;
- built-in/custom source badge;
- catalog refresh after import;
- explicit version in option identity;
- send `test_set_version` on evaluation runs;
- surface 409 duplicate conflict without silently replacing;
- optional explicit replace action only if the user knowingly chooses it later;
- preserve source-backed/no-client-scoring boundary.

### E5b — Capability-driven Playground and Endpoints

Implement in parallel:

- derive available tasks from public model capability descriptors;
- keep text controls for text-compatible runtimes;
- show image controls only for image input support;
- expose transcription as a distinct audio -> text task when explicit ASR capability exists;
- feature controls such as streaming/structured output only when declared;
- endpoint compatibility matrix/card from server-owned capability metadata;
- unsupported combinations show explicit unavailable state rather than hidden/failing controls.

### E7 — Diagnostics and Settings completion

After E5b source composition stabilizes:

- move runtime/resource/scheduler evidence into a coherent Diagnostics surface without duplicating canonical source ownership;
- expose privacy/resource policy configuration state truthfully;
- retain Logs as a real operational source, not illustrative content.

## Evidence UX rules

- `0` is valid only when a source measured zero; missing data is `Unavailable`.
- resource estimate and observed footprint remain visually distinguishable.
- chunk throughput is never token throughput.
- exploratory benchmark runs may execute but are not presented as evidence-grade comparisons.
- reclamation evidence is not PASS merely because a subprocess exits or memory delta is positive once.
- capability truth is server-owned; JavaScript may filter/present it but must not invent support.
- custom test-set files are data, not executable scorer/plugin definitions.

## Acceptance still pending

Before primary UX surfaces can be marked DONE:

- keyboard-only navigation through shell, forms, tables and lifecycle controls;
- visible focus and semantic labels for icon-only actions;
- status not conveyed by color alone;
- contrast verification in supported light/dark modes;
- 200% zoom usability;
- responsive checks at representative phone/tablet/desktop widths;
- source failure/loading/empty/warning/error/success fixture coverage;
- real runtime screenshots for public documentation;
- representative hardware evidence for resource/performance claims.

## Update rule

Update this file in the same integration cycle whenever a UX workstream status or blocker changes. Keep detailed acceptance criteria in the target specification.

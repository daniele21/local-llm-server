# Local LLM Server UX/UI progress

Status: active
Document type: workstream-state
Owner: web-product
Canonical scope: state.web-ux
Read when: determining the remaining UX/UI redesign work and its data-contract blockers
Last reviewed: 2026-08-15

Canonical target specification: [`ux-ui-implementation-plan.md`](ux-ui-implementation-plan.md)

This tracker records concise implementation status only. Repository-wide truth and the immediate implementation wave belong in [`current-state.md`](current-state.md).

## Status legend

- `DONE`: implementation and applicable automated acceptance are integrated.
- `PARTIAL`: meaningful connected behavior exists but target acceptance remains.
- `BLOCKED`: a named upstream contract prevents truthful implementation.
- `EVIDENCE`: implementation exists; representative runtime/hardware/UX evidence remains.
- `PENDING`: implementation has not started.

## Current workstreams

| Workstream | Status | Integrated boundary | Remaining gate / dependency |
| --- | --- | --- | --- |
| Existing Local LLM Studio workflows | PARTIAL | Real Chat, model/runtime config, logs, examples and Swagger remain operational | Migrate into dedicated control-plane modules without regression |
| Brand/design-system foundation | PARTIAL | Shared tokens, primitives, focus/reduced-motion and dark/light semantics | Screen adoption + visual/accessibility regression |
| Application shell/navigation | PARTIAL | Overview, Models & Runtimes, Endpoints, Playground, Benchmark & Evaluation, System/Diagnostics, Settings are navigable | Migrate real content into each destination and test navigation/responsiveness |
| Overview | PARTIAL | Explicit shell view; current server/runtime facts remain visible in persistent sidebar | E4a source-backed health/runtime cards; later B1/B2/D2/D3 panels |
| Models & Runtimes inventory | PARTIAL | Existing real registry/residency view preserved and relabeled in IA | E3a lifecycle composition; C2b capabilities; B1/B2 resources; D3 fingerprint |
| Memory budget/pressure UX | BLOCKED | B1 resource contract now exists | Wait for B2 admission + connected observations before authoritative values |
| Model capability UX | BLOCKED | C2 capability descriptor exists | Wait for C2b registry/API exposure |
| Pin / auto-evict UX | BLOCKED | No residency policy contract | B6 |
| Runtime fingerprint UX | BLOCKED | D3a artifact identity exists | Full D3 backend/config/hardware fingerprint |
| Endpoints | PARTIAL | Real Swagger/examples links plus current OpenAI compatibility context | C2b capability-aware model/endpoint compatibility |
| Playground text | PARTIAL | Existing real chat flow preserved under new IA | AC1b canonical route wiring + D2 truthful metrics |
| Playground vision | PARTIAL | Existing multimodal flow preserved | AC1b policy enforcement + C2b capabilities |
| Playground transcription | BLOCKED | Audio helper + canonical TaskType + C2 schema foundations | First-class C3 transcription API |
| Benchmark & Evaluation | PARTIAL | Navigable shell with explicit no-engine/unavailable state | D4a schema, then D4 engine |
| System / Diagnostics | PARTIAL | Existing logs/status preserved under new IA | E4a composition + D2/B1 source wiring |
| Settings/privacy | PARTIAL | Current privacy defaults described without invented controls | AC1b enforcement + future resource policy controls |
| Responsive behavior | PARTIAL | New shell styles collapse multi-column control-plane grids | Screen-level narrow-width verification |
| Accessibility | PARTIAL | Focus/status/reduced-motion primitives | Keyboard/focus/contrast/zoom validation across migrated views |
| Visual regression | PENDING | No formal suite | Stable E3/E4 states |
| Representative hardware UX evidence | PENDING | No new source-backed hardware panels yet | B1/B2/D2 + hardware validation |

## E2 shell result

The shell was integrated incrementally instead of rewriting the existing ~38 KB `index.html` monolith.

New modules:

- `control-plane-shell.js` — information architecture and placeholder/source-aware destinations;
- `control-plane-shell.css` — shell-specific responsive layout;
- `config.js` loads the shell and design-system assets.

Important behavior:

- existing Chat/Models/Logs screens remain real operational views;
- new future-data views display explicit unavailable states;
- Benchmark does not show synthetic scores;
- Overview does not invent resource pressure;
- Settings does not pretend budget/eviction controls exist;
- Endpoints links to actual Swagger and integration examples.

## Newly available UX dependencies

- B1 resource schema exists, so E3/E4 can begin designing against stable source types while leaving values unavailable until connected.
- C2 capability schema exists, but capability UI remains blocked until registry/API exposure.
- D1 metric vocabulary exists, so final labels should use its exact token/chunk/duration terms.
- D3a artifact identity exists, enabling future model detail identity sections without private path disclosure.

## Immediate UX wave

Run E3a and E4a in parallel after the shell boundary:

### E3a — Models & Runtimes current-source composition

Use only currently real sources to show:

- configured model identity;
- resident vs non-resident distinction;
- default-route distinction;
- backend;
- runtime state/active requests where available;
- load/activate/unload actions already supported.

Do not yet show authoritative memory budget, eviction, runtime fingerprint or capability compatibility until their sources are wired.

### E4a — Overview/System current-source composition

Use existing sources to show:

- server connection/health;
- default route;
- resident runtime count/list;
- runtime state;
- links into Models and Diagnostics.

Keep resource pressure, TTFT/token throughput and evidence identity unavailable until B1/B2, D2 and D3 are connected.

## Subsequent parallel UX slices

- capability detail -> C2b;
- resource budget/pressure -> B1 runtime wiring + B2;
- request lifecycle -> B5/D1;
- truthful performance -> D2;
- artifact/runtime identity -> D3;
- transcription controls -> C3;
- benchmark selection/results -> D4;
- pin/LRU/TTL -> B6.

## Update rule

Update this tracker in the same integration cycle whenever a UX status or blocker changes. Detailed acceptance criteria remain in the target specification.

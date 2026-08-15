# Local LLM Server UX/UI progress

Status: active
Document type: workstream-state
Owner: web-product
Canonical scope: state.web-ux
Read when: determining the remaining UX/UI redesign work and its data-contract blockers
Last reviewed: 2026-08-15

Canonical target specification: [`ux-ui-implementation-plan.md`](ux-ui-implementation-plan.md)

This tracker records concise implementation status only. Repository-wide integrated state and the immediate implementation block belong in [`current-state.md`](current-state.md).

## Status legend

- `DONE`: implementation and applicable automated acceptance are integrated.
- `PARTIAL`: meaningful connected behavior exists but target acceptance remains.
- `BLOCKED`: a named upstream contract prevents truthful implementation.
- `EVIDENCE`: implementation exists; representative runtime/hardware/UX evidence remains.
- `PENDING`: implementation has not started.

## Current workstreams

| Workstream | Status | Current integrated boundary | Remaining gate / dependency |
| --- | --- | --- | --- |
| Existing Local LLM Studio | PARTIAL | Chat, model/runtime configuration, logs, examples and Swagger exist | Reframe shell/navigation around control-plane IA while preserving real workflows |
| Brand/design-system foundation | PARTIAL | Shared CSS now provides canonical brand/surface/status tokens, light/dark semantics, typography, spacing, radii, focus/reduced-motion and reusable primitives | Migrate real screens; add visual/accessibility regression evidence |
| Application shell/navigation | PENDING | Existing UI navigation/product sections | E2: new Overview, Models & Runtimes, Endpoints, Playground, Benchmark, System and Settings shell |
| Overview | PENDING | Existing health/status/model information available in separate sources | New composition; resource and metric panels remain source-contract gated |
| Models & Runtimes inventory | PARTIAL | Registry, generic external registry layers, load/activate/unload and runtime status APIs exist | New lifecycle taxonomy, zero-resident, capabilities and resource data |
| Memory budget/pressure UX | BLOCKED | Basic config/runtime fields only | Resource observation + ResourceManager (B1/B2) |
| Model capability UX | BLOCKED | Existing `modalities`/thinking plus canonical TaskType vocabulary | Capability descriptor (C2) |
| Pin / auto-evict UX | BLOCKED | No product policy contract | Residency policy (B6) |
| Runtime fingerprint UX | BLOCKED | Model/backend metadata partial | Artifact identity + runtime fingerprint (D3) |
| Endpoints catalog | PARTIAL | OpenAPI and examples exist; canonical task request vocabulary now exists | C2 capability-driven endpoint/model compatibility view |
| Playground text | PARTIAL | Chat Studio supports real prompt execution/configuration | Canonical request path wiring + D1/D2 exact metric contract |
| Playground vision | PARTIAL | Image helper + multimodal backend path exist | Canonical request/media-policy wiring + C2 capability states |
| Playground transcription | BLOCKED | Audio helper exists and temp WAV ownership is now deterministic | First-class transcription task/API (C3) |
| Benchmark & Evaluation | PENDING | Legacy batch test script only | Benchmark engine v1 + execution identity (D4) |
| System / Diagnostics | PARTIAL | Health, status and log stream exist | Unified resource/worker/request metrics and evidence composition |
| Settings/privacy policy | PARTIAL | host/CORS/admin config plus fail-closed remote-code/media config exists | Wire remote-media enforcement into request path; expose policy only when backed by real config |
| Responsive behavior | PENDING | Current web UI exists | E2 shell implemented at reference breakpoints |
| Accessibility | PARTIAL | Shared primitives include focus-visible, status text+indicator and reduced-motion foundations | Keyboard/focus/contrast/zoom screen-level validation |
| Visual regression | PENDING | No formal target-state screenshot suite | Stable component/screen fixtures after E2 migration begins |
| Representative hardware UX evidence | PENDING | Manual runtime guidance exists | New source-backed screens + hardware validation matrix |

## Integrated design-system slice

The first E1 slice is now in the application bundle through `static/design-system.css` and `static/config.js`.

Integrated primitives/tokens include:

- graphite, slate, electric blue, teal, violet and light-neutral brand tokens;
- dark-first semantic surfaces plus supported light tokens;
- `ready`, `resident`, `cold`, `loading`, `warning`, `error` and `unavailable` status semantics;
- UI/data/monospace font stacks;
- spacing, radius, control-height and focus tokens;
- card, button, field, metric, status, empty-state and table primitives;
- reduced-motion behavior.

This does **not** mean the current pages have completed the redesign. Existing page CSS/layout remains the active product surface until E2 migrates the shell and subsequent screen slices adopt the primitives.

## Current UX debt

- the current product surface still communicates “chat/configuration UI” more strongly than “local AI control plane” even though README/product language has been repositioned;
- model artifact state, default route and memory residency are not yet first-class separate presentation concepts;
- memory pressure/budget cannot be shown truthfully until B1/B2;
- current registry modality vocabulary remains insufficient for final task-aware UX until C2;
- benchmark/evaluation is not yet an integrated product workflow;
- observability terminology must be corrected by D1/D2 before final metric labels are frozen;
- the frontend remains a large static bundle and must be decomposed enough for parallel screen implementation without repeated conflicts;
- there is no screenshot/visual regression harness yet.

## Immediate UX block

Proceed with **E2 shell/navigation** in parallel with B1, C2 and D1.

E2 should:

1. establish the new control-plane navigation hierarchy;
2. reuse the integrated design-system tokens/primitives rather than create a second style vocabulary;
3. preserve existing working Chat/Models/Logs/API flows during incremental migration;
4. show only current source-backed values or explicit unavailable/coming-later states;
5. avoid authoritative memory, capability, benchmark or fingerprint values until their source contracts land;
6. create screen/module boundaries that allow later Overview, Models, Playground and Diagnostics slices to develop independently.

## Parallel UX slices after E2 foundation

As soon as the shell/module boundaries exist, these can proceed independently:

- **E3a Models inventory:** current registry/default/residency facts;
- **E4a Overview health:** current server and loaded-runtime health;
- **Endpoints current-state slice:** current routes/examples with canonical task vocabulary where already valid;
- **Playground text:** existing real chat execution adapted to the new shell;
- **Diagnostics/logs:** current health/status/log sources.

Dependency-gated slices remain:

- memory budget -> B1/B2;
- capability UI -> C2;
- transcription -> C3;
- queue/deadline UI -> B5/D1;
- pin/eviction -> B6;
- truthful cross-backend performance cards -> D2;
- runtime fingerprint -> D3;
- benchmark comparison/history -> D4/D5.

## Update rule

Update this file in the same integration change whenever a UX workstream status or blocker changes. Keep detailed acceptance criteria in the target specification; this file should remain a concise operational tracker rather than duplicating the full UX plan.

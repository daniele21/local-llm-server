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
| Existing Local LLM Studio | PARTIAL | Chat, model/runtime configuration, logs, examples and Swagger exist | Reframe shell and navigation around control-plane IA |
| Brand/design-system target | PENDING | Target mockups/visual direction defined outside implementation | Encode tokens/components from `brand-guidelines.md` |
| Application shell/navigation | PENDING | Existing UI navigation/product sections | New Overview, Models & Runtimes, Endpoints, Playground, Benchmark, System, Settings shell |
| Overview | PENDING | Existing status/log information available in separate surfaces | Source-backed resource/scheduler/metric contracts and new composition |
| Models & Runtimes inventory | PARTIAL | Registry, load/activate/unload and runtime status APIs exist | New lifecycle taxonomy, zero-resident, capabilities and resource data |
| Memory budget/pressure UX | BLOCKED | Basic config/runtime fields only | Resource observation + ResourceManager (B1/B2) |
| Model capability UX | BLOCKED | `modalities` and thinking modes exist | Canonical capability descriptor (C2) |
| Pin / auto-evict UX | BLOCKED | No product policy contract | Residency policy (B6) |
| Runtime fingerprint UX | BLOCKED | Model/backend metadata partial | Artifact identity + runtime fingerprint (D3) |
| Endpoints catalog | PARTIAL | OpenAPI and examples exist | Capability-driven endpoint/model compatibility view |
| Playground text | PARTIAL | Chat Studio supports real prompt execution/configuration | New task state model, exact metric contract and source-backed lifecycle |
| Playground vision | PARTIAL | Image helper + multimodal backend path exist | Capability-driven control states and real UI acceptance |
| Playground transcription | BLOCKED | Audio helper/chat pathway exists | First-class transcription task/API (C3) |
| Benchmark & Evaluation | PENDING | Legacy batch test script only | Benchmark engine v1 + execution identity (D4) |
| System / Diagnostics | PARTIAL | Health, status and log stream exist | Unified resource/worker/request metrics and evidence composition |
| Settings/privacy policy | PARTIAL | host/CORS/admin/runtime config exists | Explicit remote media/code/privacy controls and resource policy settings |
| Responsive behavior | PENDING | Current web UI exists | New shell implemented at reference breakpoints |
| Accessibility | PENDING | No complete target matrix recorded | Keyboard/focus/contrast/zoom/reduced-motion validation |
| Visual regression | PENDING | No formal target-state screenshot suite | Stable component/screen fixtures after design-system implementation |
| Representative hardware UX evidence | PENDING | Manual runtime guidance exists | New source-backed screens + hardware validation matrix |

## Current UX debt

- the current product surface communicates “chat/configuration UI” more strongly than “local AI control plane”;
- model artifact state, default route and memory residency are not yet first-class separate presentation concepts;
- memory pressure/budget cannot be shown truthfully until the resource contract exists;
- current modality vocabulary is insufficient for a clean ASR versus audio-language experience;
- benchmark/evaluation is not yet an integrated product workflow;
- observability terminology must be corrected before final metric UI labels are frozen;
- the frontend is currently a large static bundle and should be componentized enough to permit parallel screen implementation without repeated conflicts.

## Immediate UX block

Proceed with **E1 + E2 foundation** from [`roadmap.md`](roadmap.md):

1. encode brand/design tokens;
2. build reusable status, metric, lifecycle, table, unavailable and detail components;
3. establish the new sidebar/application shell and routes;
4. preserve existing real chat/model/log functionality during migration;
5. implement static visual fixtures only inside component/demo/test contexts;
6. do not show future memory/benchmark data as live product values.

## Parallel UX slices after shell foundation

Once E1/E2 land, these can proceed independently with narrow API contracts:

- **Models inventory slice:** current registry/residency facts;
- **Overview health slice:** current server/loaded-model health;
- **Endpoint documentation slice:** current routes/examples;
- **Playground text slice:** current chat execution;
- **Diagnostics/log slice:** current health/status/log data.

The following remain dependency-gated:

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

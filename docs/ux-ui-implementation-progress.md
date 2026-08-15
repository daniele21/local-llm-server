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
| Existing Studio workflows | PARTIAL | real Chat, Models, Logs, examples, Swagger preserved | migrate without regression |
| Design system | PARTIAL | tokens/primitives/focus/reduced-motion/light-dark | screen adoption + visual/accessibility evidence |
| Shell/navigation | PARTIAL | seven control-plane destinations navigable | screen-level navigation/responsive tests |
| Overview | PARTIAL | live `/health`, `/status`, `/v1/models`; unavailable-on-source-failure | resource/metric/fingerprint panels |
| Models & Runtimes | PARTIAL | legacy real registry/residency view remains | E3a source-backed lifecycle redesign |
| Resource budget/pressure | BLOCKED | B1 observers + B2 accounting exist | product API/runtime wiring |
| Capability UX | BLOCKED | C2 descriptor/catalog projection exists | public model-source exposure C2c |
| Pin/auto-evict | BLOCKED | no B6 policy | B6 |
| Runtime fingerprint | BLOCKED | artifact identity exists | D3b/D3 |
| Endpoints | PARTIAL | real Swagger/examples | capability-aware compatibility C2c |
| Playground text | PARTIAL | real chat preserved | AC1b + richer D2 metrics |
| Playground vision | PARTIAL | real multimodal path preserved | AC1b + public capabilities |
| Playground transcription | BLOCKED | task/capability foundations only | C3 |
| Benchmark & Evaluation | PARTIAL | shell + explicit no-engine state; D4a schema exists | D4b dataset, then D4 engine |
| System/Diagnostics | PARTIAL | real logs/status preserved | canonical metrics/resources/evidence exposure |
| Settings/privacy | PARTIAL | policy status described | AC1b route enforcement + future resource policy controls |
| Responsive | PARTIAL | control-plane grids collapse responsively | screen-level verification |
| Accessibility | PARTIAL | primitive-level focus/status/reduced motion | full keyboard/focus/contrast/zoom matrix |
| Visual regression | PENDING | none | stable E3/E4 states |
| Hardware UX evidence | PENDING | no connected resource evidence yet | runtime resource API + representative hardware |

## Integrated Overview behavior

`control-plane-live.js` now consumes current product APIs instead of mock values:

- `/health` -> server readiness/backend/default route where present;
- `/status` -> runtime/default/active-request state where present;
- `/v1/models` -> resident runtime count;
- source failure -> explicit `Unavailable`;
- resource pressure -> remains unavailable because B1/B2 are not yet product-exposed;
- navigation buttons route to the real Models & Runtimes and Diagnostics views.

The module polls at a bounded interval and does not persist stale values as current truth after a failed refresh.

## Current UX dependencies

Now available internally:

- B1 Linux/macOS resource source contracts;
- B2 reservation/admission accounting;
- C2 descriptor + catalog projection;
- D1 precise metric schema + D2a chunk adapter;
- D3a artifact identity;
- D4a evaluation schema.

Still missing for truthful UI panels:

- resource public/runtime wiring;
- public capability projection;
- backend/config/hardware runtime fingerprint;
- real backend token/TTFT/prefill/decode adapters;
- benchmark execution engine.

## Immediate UX wave

### E3a — Models & Runtimes redesign

Use existing real sources to present:

- configured identity;
- resident vs non-resident state;
- default route separately from residency;
- backend/runtime state/active requests;
- existing load/activate/unload actions.

Show capability/resource/fingerprint sections as unavailable until their public sources land.

### E4b — Overview enrichment after source wiring

Parallel dependency-driven panels:

- resource budget/pressure -> B1/B2 product exposure;
- exact performance -> richer D2 adapters;
- artifact/runtime identity -> D3;
- recent evaluation -> D4 engine.

### E6a — Evaluation setup after D4b

The shell can begin local test-set/sample/scorer configuration once the built-in dataset exists, while run execution remains disabled until D4.

## Update rule

Update this file in the same integration cycle whenever a UX workstream status or blocker changes. Keep acceptance detail in the target specification.

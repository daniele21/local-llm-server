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
| Existing Studio workflows | PARTIAL | real Chat, Models, Logs, examples, Swagger preserved | modular migration without regression |
| Design system | PARTIAL | tokens/primitives/focus/reduced-motion/light-dark | screen adoption + visual/accessibility evidence |
| Shell/navigation | PARTIAL | seven control-plane destinations navigable | screen-level navigation/responsive tests |
| Overview | PARTIAL | live `/health`, `/status`, `/v1/models`; unavailable-on-source-failure | resource/metric/fingerprint/evaluation panels |
| Models & Runtimes | PARTIAL | dedicated source-backed module over resident/status/admin catalog | resource/fingerprint sources + lifecycle UX evidence |
| Resource budget/pressure | BLOCKED | admission wiring exists internally | B2c configured product policy/API exposure |
| Capability UX | PARTIAL | capability descriptors now public via model/admin catalog and rendered in Models view | C2d enforcement + endpoint/playground compatibility presentation |
| Pin/auto-evict | BLOCKED | no B6 policy | B6 |
| Runtime fingerprint | BLOCKED | runtime snapshot contract exists | D3d automatic capture/public exposure |
| Endpoints | PARTIAL | real Swagger/examples + public capability metadata | capability-aware compatibility composition |
| Playground text | PARTIAL | real chat + public entrypoint policy enforcement | modular view + live canonical metrics |
| Playground vision | PARTIAL | real multimodal path + fail-closed remote-media middleware | C2d capability enforcement + modular controls |
| Playground transcription | BLOCKED | canonical/capability prerequisites now available | C3 first-class ASR API |
| Benchmark & Evaluation | PARTIAL | shell + 20-sample set + deterministic runner | D4d resident-runtime service/persistence + E6a wiring |
| System/Diagnostics | PARTIAL | real logs/status preserved | resource/metrics/fingerprint evidence API |
| Settings/privacy | PARTIAL | supported public/CLI entrypoints enforce canonical remote-media policy | expose policy state/config; legacy direct-app compatibility note |
| Responsive | PARTIAL | control-plane grids collapse responsively | screen-level verification |
| Accessibility | PARTIAL | primitive-level focus/status/reduced motion | full keyboard/focus/contrast/zoom matrix |
| Visual regression | PENDING | none | stable E3/E4/E6 states |
| Hardware UX evidence | PENDING | no connected reclamation evidence yet | B3c + representative hardware |

## Integrated source-backed Models behavior

`control-plane-models.js` now consumes:

- `/v1/models` for resident runtime identity;
- `/status` for default route, lifecycle and active-request state;
- `/api/v1/models/registry` for configured catalog and capability descriptors when the admin API is available.

It shows configured identity, resident/cold state, default route, backend, runtime state, active requests and capability summary only from real sources. If the admin API is disabled or fails, the screen explicitly degrades to **resident view only**. Resource admission and runtime fingerprint remain unavailable rather than inferred.

The existing model load/activate/unload controls remain reachable during migration.

## Integrated request/privacy UX boundary

Supported public Python and CLI server entrypoints now install canonical request-policy middleware. This means the existing Playground path receives fail-closed remote-media validation before backend inference when the product is started through supported entrypoints. Direct legacy use of `local_llm_server.server:app` remains a compatibility path and should not be presented as the primary setup flow.

## Newly available UX dependencies

Now available internally/publicly:

- B1 Linux/macOS resource source contracts;
- B2 real load/reload/unload admission accounting internally;
- public C2 capability descriptors/provenance;
- D1/D2 true token/timing adapters where backend evidence exists;
- D3 runtime fingerprint + immutable snapshot contract;
- D4 built-in dataset + executable deterministic runner.

Still missing for truthful product panels:

- configured ResourceManager/product resource API;
- live canonical metric attachment/API;
- automatic runtime identity snapshot capture/API;
- resident-runtime evaluation service + persistence;
- first-class transcription.

## Immediate UX wave

### E4b — Overview/System evidence enrichment

Parallel source-driven panels:

- resource budget/admission/pressure -> B2c;
- exact token/prefill/decode metrics -> D2c;
- runtime fingerprint -> D3d;
- recent evaluation summary -> D4d.

Every unavailable source must remain explicitly unavailable; do not reuse stale values as current truth after refresh failure.

### E6a — Benchmark & Evaluation workflow

Once D4d lands, implement:

- built-in test-set selector (`general-purpose` v1 initially);
- model selection;
- sample size and seed;
- start/cancel/status where supported;
- deterministic quality score summary;
- per-sample result/error view;
- runtime fingerprint/evidence-grade indicator;
- no cross-run comparison when identity is missing/incompatible.

### E5a — Capability-driven Playground/Endpoints

After C2d/C3:

- task-aware model filtering;
- text/image/audio controls only when supported;
- structured-output/thinking/streaming controls from capability features;
- explicit unavailable/unsupported state rather than optimistic backend assumptions.

## Evidence UX rules

- `0` is a valid measured value only when a source measured zero; missing data is `Unavailable`.
- resource estimate and observed footprint must be visually distinguishable.
- chunk throughput must never be labeled token throughput.
- exploratory benchmark runs without runtime identity may be shown, but not promoted as evidence-grade comparisons.
- reclamation evidence is not PASS merely because a subprocess exited.

## Update rule

Update this file in the same integration cycle whenever a UX workstream status or blocker changes. Keep detailed acceptance criteria in the target specification.

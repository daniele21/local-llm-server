# Control-plane and UX/UI roadmap

Status: active
Document type: roadmap
Owner: repository
Canonical scope: roadmap.repository
Read when: selecting the next capability milestone, understanding dependencies or parallelizing implementation
Last reviewed: 2026-08-15

Integrated truth belongs in [`current-state.md`](current-state.md). This file owns sequencing and dependency release points.

## Objective

Evolve Local LLM Server into a **resource-aware, observable local AI control plane and evaluation harness** while specialist runtimes retain backend execution ownership.

## Milestone summary

| Milestone | Status | Remaining outcome |
| --- | --- | --- |
| M0 documentation governance | DONE | keep plan synchronized |
| M1 trustworthy foundation | PARTIAL | physical route/direct-app cleanup + release review |
| M2 resource-aware runtime | PARTIAL | representative worker/pressure evidence + optional streaming isolation decision |
| M3 multi-task control plane | PARTIAL | broader specialist hardware/backend evidence |
| M4 evidence-grade observability | PARTIAL | in-process MLX wiring + wider device evidence |
| M5 control-plane UX | EVIDENCE | manual contrast/zoom + visual regression + legacy cleanup |
| M6 evaluation harness | PARTIAL | richer workloads + cold/warm orchestration |
| M7 product-grade candidate | BLOCKED | retained hardware matrix, manual UX evidence and integration-to-main gate |

## Integrated waves

### Foundation through Wave 7

Integrated:

- deterministic CI matrix and correctness gate;
- canonical request/media/capability contracts on supported product entrypoints;
- ResourceManager accounting, zero-resident semantics and bounded scheduler admission;
- worker protocol + bounded subprocess transport;
- public capability descriptors and truthful metric/runtime identity contracts;
- deterministic built-in evaluation, persistence, history/comparison and validated custom datasets;
- source-backed control-plane shell, Overview and evaluation workflow.

### Wave 8 — evaluation/capability UX and residency policy

Integrated:

- custom test-set upload/version propagation in Evaluation;
- capability-driven Endpoints/Playground and first-class transcription UX;
- pin/unpin plus current evictability evidence;
- deterministic explicit LRU/TTL selection with resident-default protection;
- explicit eviction preview/execution with no automatic pressure trigger;
- repeated reclamation checkpoint harness;
- resource/identity/residency-backed Models & Runtimes UI.

### Wave 9 — Settings and Diagnostics source completion

Integrated:

- bounded read-only policy evidence;
- source-backed Settings;
- canonical runtime/resource/scheduler/identity Diagnostics above existing live logs;
- truthful shell fallbacks.

### Wave 10 — evidence execution and deterministic hardening

Integrated:

- hysteretic pressure-policy evaluator with bounded one-attempt-per-episode semantics; UNKNOWN pressure is fail-conservative and automatic eviction remains disabled;
- canonical `InferenceRequest -> PreparedBackendRequest` translation owner;
- streaming SSE evidence retains explicit backend usage/timings alongside HTTP-boundary TTFT;
- explicit MLX generation evidence adapter using only backend-supplied count/rate fields;
- broader runtime identity via explicit specialist versions plus conservative llama-server build+commit probing;
- isolated non-streaming `WorkerBackedEngine` and child JSON-line entrypoint;
- repeated worker reclamation procedure wired to real start/health/infer/stop lifecycle;
- `local-llm evidence-reclamation` hardware runner with privacy-safe JSON reports, host checkpoints and child-PID RSS while live;
- ARIA tablist/tabpanel navigation, keyboard focus, skip link, visible-focus expansion, reduced-motion and zoom-resilient layout contracts.

### Wave 11 — review loop, specialist evidence and parity validation

Integrated:

- task-specific transcription metrics: backend wall-clock, backend-reported audio duration, realtime factor and segment count, exposed under `task_metrics.transcription` rather than generation token metrics;
- conservative repeated hardware-report reviewer with identity/procedure/hardware compatibility gates, minimum repetition thresholds and descriptive-only consistency states;
- `local-llm evidence-review` CLI for JSON report review with no policy mutation path;
- MLX-VLM regression contract proving OpenAI-compatible `usage`/`timings` survive non-streaming and terminal streaming proxy paths and map into canonical metrics without synthetic values;
- full supported-route parity tests proving the historical chat route sends the same engine kwargs as `PreparedBackendRequest` for default chat, overrides, legacy input, structured output, force-json, reasoning aliases and streaming;
- release-facing README aligned with current control-plane/evaluation behavior, verified admin routes and hardware run/review workflow;
- evidence-pending claims remain explicit: automatic pressure eviction, real reclamation/device performance, worker streaming/cancellation and manual UX acceptance.

## Immediate parallel Wave 12 — final code-path consolidation and representative evidence

### H3b — Execute and retain representative hardware matrix
Status: `READY`, requires real devices/runtimes
Dependencies: integrated run + review CLI
Ownership: evidence, not policy

- agree the minimum Mac/Linux device, memory and backend matrix;
- run repeated `local-llm evidence-reclamation` reports for exact artifacts/configs;
- review only compatible report groups with `local-llm evidence-review`;
- retain raw reports, review outputs, OS/device/backend limitations and failed/inconclusive cycles;
- do not treat `consistent_recovery_observed` as production-safety authorization;
- use results to decide whether B6 dry-run pressure integration can advance.

### A2 final — Physical canonical route cutover
Status: `READY`, semantic parity gate green
Dependencies: integrated parity tests
Ownership: request compatibility layer

- make the historical `/v1/chat/completions` implementation consume `request.state.prepared_inference_request.backend` on supported product entrypoints;
- preserve cache key behavior, stream/non-stream response construction and legacy direct-app fallback where still required;
- remove duplicate route-side message/kwargs construction once parity remains green;
- formalize supported-vs-legacy `server:app` deprecation/migration guidance.

### D2g — In-process MLX evidence wiring
Status: `READY`
Dependencies: explicit MLX response adapter already integrated

- propagate explicit `mlx_lm.stream_generate` prompt/generation token counts and rates into OpenAI-compatible engine chunks/responses;
- let existing completion/stream metric layers consume those fields rather than creating a parallel telemetry path;
- preserve `Unavailable` when upstream fields are absent/invalid;
- add non-stream + stream regression coverage without device-performance claims.

### B6d — Pressure integration dry-run
Status: `BLOCKED on H3b for production action`; dry-run design may proceed
Dependencies: hysteretic evaluator + residency selector + representative reports

- define actual sampled pressure source/cadence per supported platform;
- expose pressure episode/transition/candidate evidence without unloading first;
- retain pinned/active/default protections;
- enable any automatic unload only as explicit opt-in after evidence review establishes a defensible envelope.

### B3f — Worker protocol streaming/cancellation decision
Status: `DESIGN DECISION`

- decide whether interactive process isolation is a product requirement or the worker remains an evidence/batch boundary;
- if required, specify true incremental event transport, backpressure and interrupt ownership before implementation;
- never relabel buffered completed output as streaming.

### H1/H2b — Manual accessibility and visual regression
Status: `READY`

- light/dark contrast review;
- real keyboard traversal across forms/tables/lifecycle controls;
- 200% zoom and phone/tablet/desktop reference widths;
- destructive-action confirmation/feedback audit;
- deterministic fixture states for loading/empty/unavailable/warning/error/success;
- stable visual-regression screenshots clearly distinguished from real runtime evidence.

### H4b — Final evidence/release matrix
Status: `PARTIAL`; README baseline aligned

- link task/backend/artifact/config/hardware/procedure/result references;
- add representative real-state screenshots only after they exist;
- keep experimental/evidence-pending claims explicit;
- review examples/OpenAPI against the final physical route cutover;
- prepare cumulative integration-to-main review.

## Dependency release points

| Completion | Unlocks |
| --- | --- |
| H3b representative report groups | evidence review for B3 reclamation and B6 automatic-pressure policy |
| A2 final | one canonical request-to-backend path and clearer deprecation boundary |
| D2g | truthful end-to-end MLX in-process performance evidence when upstream supplies it |
| B3f decision | either bounded worker streaming implementation or explicit batch-only scope |
| H1/H2b | primary UX eligible for DONE review |
| H3b + H4b | product-grade/release-candidate evidence review |

## Integration-to-main gate

The long-lived `docs/control-plane-positioning-ux-plan` branch should not be promoted to `main` solely because feature PRs are merged. Consolidation requires:

1. cumulative CI green on the integration head;
2. living state/roadmap/workstream docs synchronized;
3. no known P0/P1 regression in supported entrypoints;
4. release-facing README/API examples aligned with real supported behavior;
5. explicit experimental/evidence-pending claim list;
6. representative smoke/evidence coverage for implemented task families where compatible hardware exists;
7. reviewed direct `server:app` migration/deprecation boundary and physical canonical-route cutover;
8. primary UX accessibility/responsive gate reviewed;
9. retained representative hardware reports before any memory-reclamation/auto-eviction production claim.

Hardware-dependent capabilities may remain experimental after a code merge, but documentation must say so explicitly.

## Active concurrency plan

Run H3b device evidence, A2 physical cutover, D2g MLX wiring, H1/H2b manual/visual hardening and H4b evidence-matrix work concurrently where ownership permits. B6 automatic action remains blocked until H3b review. B3f remains an explicit product/architecture decision rather than an assumed requirement.

## Evidence boundary

Automated tests prove deterministic contracts and make real testing reproducible. CI does not prove unified-memory reclamation, unload recovery, thermal behavior, device throughput or safe automatic pressure eviction. Retained representative hardware reports remain the release-quality source for those claims.

## Plan maintenance

After every coherent merge wave update this roadmap, [`current-state.md`](current-state.md) and affected workstream trackers. Target specifications change only when intended behavior changes.

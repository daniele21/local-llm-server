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
| M1 trustworthy foundation | PARTIAL | route/direct-app cleanup + release review |
| M2 resource-aware runtime | PARTIAL | representative worker/pressure evidence + optional streaming isolation |
| M3 multi-task control plane | PARTIAL | broader specialist runtime evidence |
| M4 evidence-grade observability | PARTIAL | wider VLM/ASR/device evidence |
| M5 control-plane UX | EVIDENCE | manual contrast/zoom + visual regression + legacy cleanup |
| M6 evaluation harness | PARTIAL | richer workloads + cold/warm orchestration |
| M7 product-grade candidate | BLOCKED | retained hardware matrix, release docs and integration-to-main gate |

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
- canonical `InferenceRequest -> PreparedBackendRequest` translation owner, preserving current engine defaults/aliases/structured-output/thinking behavior;
- streaming SSE evidence now retains explicit cumulative backend usage/timings alongside HTTP-boundary TTFT;
- explicit MLX generation metrics adapter using only backend-supplied token/rate evidence;
- broader runtime identity via explicit specialist backend versions plus conservative llama-server build+commit probing;
- isolated non-streaming `WorkerBackedEngine` and child JSON-line entrypoint;
- repeated worker reclamation procedure wired to real start/health/infer/stop lifecycle;
- `local-llm evidence-reclamation` hardware runner with atomic privacy-safe JSON reports, exact procedure identity, host resource snapshots and child-PID RSS during live worker stages;
- ARIA tablist/tabpanel navigation, roving keyboard focus, skip link, visible focus expansion, reduced-motion and narrow/zoom-resilient layout contracts.

## Immediate parallel Wave 11 — representative validation and consolidation

### H3a — Execute representative hardware matrix
Status: `READY`, requires real devices/runtimes
Dependencies: integrated worker hardware runner
Ownership: evidence, not policy

- agree a minimum Mac/Linux device matrix and representative text/backend artifacts;
- run repeated `local-llm evidence-reclamation` cycles with exact artifact/backend/config identity;
- preserve raw JSON reports and note OS/device/backend limitations;
- compare repeated available-memory recovery, live child RSS and lifecycle error rate;
- keep results observational when the evidence window is incomplete or noisy;
- do not enable automatic pressure eviction solely from a single positive run.

### A2 final — Canonical route cutover
Status: `READY with regression risk`
Dependencies: canonical prepared backend contract now integrated
Ownership: request compatibility layer

- replace historical route-side message/kwargs reconstruction with `request.state.prepared_inference_request.backend`;
- preserve cache, stream/non-stream response construction and public compatibility;
- delete/deprecate duplicate parsing only after parity tests are green;
- formalize the supported-vs-legacy `server:app` boundary.

### B6d — Pressure integration review
Status: `BLOCKED on H3a evidence for automatic action`
Dependencies: hysteretic evaluator + residency selection + hardware reports

- define the actual sampled pressure source/cadence for supported platforms;
- run dry-run/preview mode first and retain reason/candidate evidence;
- keep active/pinned/default protections mandatory;
- only then decide whether an opt-in automatic unload mode has a defensible safety envelope.

### D2f/D3f — Specialist evidence coverage
Status: `READY`

- map explicit VLM/ASR timing/token/termination data where backend APIs expose it;
- strengthen backend/artifact version capture per specialist runtime;
- keep unavailable fields unavailable;
- add cancellation/termination evidence only where the backend really supports it.

### B3f — Worker protocol streaming/cancellation decision
Status: `DESIGN DECISION`

- decide whether interactive process isolation is a product requirement or worker isolation remains evidence/batch focused;
- if required, design true incremental events and interrupt ownership before adding `stream()`/cancel claims;
- never convert buffered completed output into fake streaming.

### H1/H2b — Manual accessibility + visual regression
Status: `READY`

- light/dark contrast review;
- real keyboard traversal across forms/tables/lifecycle controls;
- 200% zoom and phone/tablet/desktop reference widths;
- destructive-action confirmation/feedback audit;
- deterministic fixture states for loading/empty/unavailable/warning/error/success;
- stable visual-regression screenshots clearly distinguished from real runtime evidence.

### H4 — Release documentation and evidence matrix
Status: `READY in parallel`, final status depends on H3a

- update README/API examples to current supported product paths and hardware evidence CLI;
- remove stale “roadmap” wording for capabilities already integrated;
- publish representative screenshots only from real implemented states;
- list evidence-pending/experimental claims explicitly;
- assemble release matrix linking task/backend/artifact/hardware/procedure/result references.

## Dependency release points

| Completion | Unlocks |
| --- | --- |
| H3a repeated hardware reports | evidence review for B3 reclamation and B6 automatic-pressure policy |
| A2 final | single canonical request-to-backend path and clearer deprecation boundary |
| D2f/D3f | broader evidence-grade cross-runtime evaluation |
| B3f decision | either bounded worker streaming work or explicit batch-only worker scope |
| H1/H2b | primary UX eligible for DONE review |
| H4 + H3a | product-grade/release-candidate evidence review |

## Integration-to-main gate

The long-lived `docs/control-plane-positioning-ux-plan` branch should not be promoted to `main` solely because feature PRs are merged. Consolidation requires:

1. cumulative CI green on the integration head;
2. living state/roadmap/workstream docs synchronized;
3. no known P0/P1 regression in supported entrypoints;
4. release-facing README/API examples aligned with real supported behavior;
5. explicit experimental/evidence-pending claim list;
6. representative smoke/evidence coverage for implemented task families where compatible hardware exists;
7. reviewed direct `server:app` migration/deprecation boundary;
8. primary UX accessibility/responsive gate reviewed;
9. retained representative hardware reports before any memory-reclamation/auto-eviction production claim.

Hardware-dependent capabilities may remain experimental after a code merge, but documentation must say so explicitly.

## Active concurrency plan

Run H3a device evidence, A2 cutover preparation, D2f/D3f specialist adapters, H1/H2b manual/visual hardening and H4 documentation concurrently. B6d automatic action remains blocked until H3a review. B3f is an explicit product/architecture decision rather than an assumed requirement.

## Evidence boundary

Automated tests prove deterministic contracts and the hardware runner makes real testing reproducible. CI does not prove unified-memory reclamation, unload recovery, thermal behavior, device throughput or safe automatic pressure eviction. Retained representative hardware reports remain the release-quality source for those claims.

## Plan maintenance

After every coherent merge wave update this roadmap, [`current-state.md`](current-state.md) and affected workstream trackers. Target specifications change only when intended behavior changes.

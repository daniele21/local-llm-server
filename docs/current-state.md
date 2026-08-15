# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Read when: determining the integrated baseline, open blockers or immediate next implementation block
Last reviewed: 2026-08-15

This is the operational ledger for the Local LLM Server evolution program. Target behavior belongs in [`implementation-plan.md`](implementation-plan.md); sequencing belongs in [`roadmap.md`](roadmap.md).

## Active direction

Local LLM Server is evolving into a **resource-aware, observable local AI control plane and evaluation harness** for product-grade local inference. Specialist inference engines retain backend execution ownership.

## Integrated baseline

### Delivery, contracts and privacy

Integrated:

- blocking pytest on Python 3.10/3.11/3.12 plus Ruff correctness checks;
- backend-neutral task/request/result/error contracts and OpenAI/legacy compatibility translation;
- supported public Python/CLI entrypoints install canonical request policy before inference;
- remote HTTP(S) media is fail-closed by default and policy rejection occurs before backend invocation;
- full runtime capability descriptors are consulted before supported chat execution through `enforce_request_capabilities`;
- `trust_remote_code` remains explicit opt-in;
- owned temporary audio cleanup is deterministic;
- external registry integration is consumer-agnostic.

Compatibility boundary:

- the historical chat route still rebuilds backend kwargs after canonical middleware validation;
- direct use of the legacy module-level `local_llm_server.server:app` remains a compatibility/deprecation path rather than the supported product entrypoint.

### Resources, runtime lifecycle and scheduling

Integrated:

- Linux/macOS resource observation with measured/estimated/configured/unavailable semantics;
- `ResourceManager` reservation, admission and accounting with `ADMIT`, `REJECT`, `UNKNOWN`;
- supported product bootstrap can configure resource policy before initial expensive model load;
- admin resource API exposes configured/disabled policy, usable budget, committed/reserved bytes and remaining capacity;
- load/reload/unload accounting is wired, including rollback and replacement-overlap checks;
- zero-resident server state is valid: configured default identity is distinct from current resident default route;
- the last idle runtime can unload without making the server unhealthy;
- bounded scheduler contracts plus async FIFO runtime admission are integrated;
- opt-in request queueing is wired to supported product requests with bounded capacity, queue timeout, model-isolated gates and streaming slot lifetime;
- admin scheduler evidence exposes aggregate queue/running state without request content;
- worker protocol and bounded JSON-line subprocess transport exist for health/generate/drain/cancel/stop ownership;
- reclamation evidence contracts record before/ready/peak/after-stop snapshots and only report observed recovery/inconclusive state, never an automatic PASS.

Remaining boundary:

- existing inference engines are not yet broadly routed through process-isolated worker ownership;
- pinning and automatic LRU/TTL eviction are not integrated;
- estimated residency is still distinct from representative measured footprint;
- real host-memory reclamation and repeated lifecycle stability still require representative hardware evidence.

### Multi-task capabilities and audio

Integrated:

- task/input/output/feature capability descriptors with explicit vs `legacy_conservative` provenance;
- capability descriptors are public in model/admin catalog sources;
- supported chat requests reject unsupported canonical capability combinations before backend execution;
- first-class resident transcription service exists independently from audio-language chat;
- modular `/v1/audio/transcriptions` accepts bounded multipart upload and requires explicit transcription capability;
- legacy audio modality alone never implies ASR support.

Remaining boundary:

- Playground and Endpoints UI are not yet capability-driven end to end;
- broader specialist runtime coverage remains backend-dependent.

### Observability and runtime identity

Integrated:

- canonical token/chunk/duration/throughput vocabulary with no chunk-as-token aliasing;
- non-streaming completions record explicit OpenAI usage and backend timing fields when supplied;
- streaming chat records true first non-empty model-content TTFT from request receipt;
- queue wait, prompt/output tokens, prefill/decode duration, decode throughput and total duration are exposed only when sourced;
- malformed/oversized completion capture degrades conservatively instead of inventing timing/token values;
- privacy-safe live evidence API exposes request/runtime evidence without generated content;
- path-free artifact identity, backend/config/hardware fingerprint contracts and immutable residency snapshots are integrated;
- automatic runtime identity capture occurs only when artifact SHA-256 and backend version are strong enough; otherwise the runtime remains exploratory.

Remaining boundary:

- backend-specific metric coverage is still incomplete across all MLX/VLM/ASR combinations;
- device-specific throughput/thermal claims remain evidence-pending.

### Evaluation harness

Integrated:

- versioned test-set/sample/scorer/run/report contracts;
- built-in `general-purpose` v1 deterministic set and objective scorer;
- seeded sample selection and per-sample failure isolation;
- resident-runtime evaluation service, run API and local immutable report persistence;
- history loading and compatibility-aware comparison API;
- comparison distinguishes `not comparable`, `exploratory`, `descriptive only` and attribution-safe states and emits no automatic better/worse verdict;
- runtime fingerprint is attached when verified and controls evidence-grade comparison status;
- test-set identity is content-sensitive, so prompt/expectation/task changes alter identity even under stable sample IDs;
- validated custom JSON test-set import is integrated with atomic local persistence, version coexistence, reserved built-in IDs and no executable code/templates/plugins;
- custom sets currently support deterministic `chat` and `structured_generation` samples with allowlisted objective expectations.

Remaining boundary:

- custom test-set upload/version-selection UX is not yet connected;
- cancellation/progress is still limited by the current synchronous evaluation execution model;
- broader benchmark families and cold/warm experiment orchestration remain later extensions.

### UX/UI

Integrated:

- shared design system and seven-destination control-plane shell;
- source-backed Overview, Models & Runtimes and Benchmark & Evaluation workflow;
- Overview consumes live health/status/models plus resource, runtime evidence and scheduler sources;
- missing values remain `Unavailable`, not zero;
- Benchmark & Evaluation supports model/test-set/sample-count/seed setup, real run execution and per-sample results;
- persisted evaluation history and compatibility-aware baseline/candidate comparison are source-backed;
- scheduler admission state and queue wait are visible without request IDs/content;
- configured default identity, resident default route and cold state are distinct in the UI.

Remaining boundary:

- custom dataset upload and explicit version selection;
- capability-driven Playground/Endpoints composition;
- modular System/Diagnostics and Settings policy presentation;
- full keyboard/focus/contrast/200%-zoom verification;
- visual regression suite and representative runtime screenshots.

## Program status

| Task | Status | Integrated outcome | Remaining gate |
| --- | --- | --- | --- |
| A1 truthful CI | DONE | blocking deterministic matrix | broader quality debt later |
| A2/C1 canonical policy | PARTIAL | supported entrypoints validate canonical request/media policy | retire duplicate parser + legacy direct-app path |
| A3 consumer decoupling | DONE | generic registry sources | — |
| B1 resource observation | EVIDENCE | Linux/macOS source contracts | representative device validation |
| B2 resource admission | PARTIAL | product policy + shared accounting/API | measured reconciliation/hardware evidence |
| B3 worker/reclamation | PARTIAL | protocol/transport + conservative evidence recorder | engine integration + hardware proof |
| B4 zero resident | DONE | healthy cold state + default/residency separation | automatic cold-load remains later policy |
| B5 scheduler | PARTIAL | bounded FIFO request admission + evidence | wider runtime/cancellation evidence |
| B6 pin/LRU/TTL | PENDING | — | B2/B3/B4/B5 maturity |
| C2 capabilities | PARTIAL | public descriptors + supported chat pre-backend enforcement | capability-driven UX + broader task paths |
| C3 transcription | PARTIAL | first-class service + multipart API | specialist backend/hardware evidence + UX |
| D1 metrics vocabulary | DONE | truthful canonical schema | — |
| D2 live metrics | PARTIAL | streaming TTFT + nonstreaming token/timing evidence | wider backend coverage/hardware validation |
| D3 runtime identity | PARTIAL | verified auto-capture + public evidence | stronger artifact coverage across runtimes |
| D4 evaluation | PARTIAL | real resident runs, persistence and custom dataset backend | custom dataset UX + richer workload families |
| D5 history/comparison | PARTIAL | persisted compatibility-aware comparison | baseline management/report UX later |
| E1/E2 design system + shell | PARTIAL | shared primitives and new IA | accessibility/visual evidence |
| E3 Models & Runtimes | PARTIAL | live source-backed runtime/catalog view | pin/eviction/action UX |
| E4 Overview | PARTIAL | resource/runtime/metric/scheduler evidence | hardware evidence + final diagnostics composition |
| E5 Playground/Endpoints | PARTIAL | real legacy workflows preserved | capability-driven task composition |
| E6 Evaluation UI | PARTIAL | real run/results/history/comparison | custom upload/version UX |
| H hardware/release evidence | PENDING | deterministic CI only | representative hardware matrix |

## Immediate next parallel wave

Prioritize the remaining high-leverage gaps behind narrow ownership boundaries:

1. **E6b custom test-set UI** — upload validated JSON, refresh catalog, distinguish built-in/custom source, preserve version identity and send `test_set_version` on runs.
2. **E5 capability-driven Playground/Endpoints** — filter controls and endpoint compatibility from public capability descriptors; unsupported paths remain explicit rather than optimistic.
3. **B6 residency policy foundation** — explicit pin/evictability metadata followed by lease-safe LRU/TTL policy; do not infer reclaimability from policy success.
4. **B3d worker integration + hardware evidence harness** — connect selected runtimes to process ownership where justified and execute before/ready/peak/after-stop evidence on representative hardware.
5. **D2/D3 backend coverage** — expand truthful metrics and verified identity across MLX/VLM/ASR adapters without fabricating unavailable fields.
6. **H1-H4 hardening** — accessibility, responsive/visual regression, repeated lifecycle tests, hardware evidence and release documentation.
7. **Integration consolidation** — keep the integration branch green, then merge the control-plane program toward `main` only after cumulative CI and release-gate review.

### Parallelization constraints

- E6b consumes the already-integrated custom dataset API and must not introduce client-side scoring semantics.
- E5 consumes capability metadata; it must not redefine runtime capability truth in JavaScript.
- B6 owns residency policy only; memory reclamation claims remain B3/hardware evidence.
- hardware evidence may run in parallel with UI work but cannot be replaced by CI fakes.
- documentation status changes only after the corresponding code is integrated.

## Evidence boundary

Automated tests establish contract and deterministic workflow correctness. They do **not** prove Apple unified-memory reclamation, actual unload recovery, thermal behavior, device-specific token throughput or safe auto-eviction under real pressure. Representative hardware evidence remains mandatory before those claims become DONE.

## Update rule

Update this file in the same integration cycle whenever task state, blockers or the immediate parallel wave changes.

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

### Delivery, canonical requests and privacy

Integrated:

- blocking pytest on Python 3.10/3.11/3.12 plus Ruff correctness checks;
- backend-neutral task/request/result/error contracts and OpenAI/legacy compatibility translation;
- supported public Python/CLI entrypoints install canonical request policy before inference;
- remote HTTP(S) media is fail-closed by default and policy rejection occurs before backend invocation;
- full runtime capability descriptors are consulted before supported chat execution;
- `trust_remote_code` and remote-media opt-in remain explicit runtime configuration;
- owned temporary audio cleanup is deterministic;
- read-only admin `/api/v1/policies` exposes bounded effective policy flags without local paths, prompt/output content or secret values;
- external registry integration is consumer-agnostic.

Compatibility boundary:

- the historical chat route still rebuilds backend kwargs after canonical middleware validation;
- direct use of the legacy module-level `local_llm_server.server:app` remains a compatibility/deprecation path rather than the supported product entrypoint.

### Resources, runtime lifecycle and scheduling

Integrated:

- Linux/macOS resource observation with measured/estimated/configured/unavailable semantics;
- `ResourceManager` reservation, admission and accounting with `ADMIT`, `REJECT`, `UNKNOWN`;
- supported product bootstrap can configure resource policy before initial expensive model load;
- admin `/api/v1/resources` exposes configured/disabled policy, usable budget, committed/reserved bytes and remaining capacity;
- load/reload/unload accounting is wired, including rollback and replacement-overlap checks;
- zero-resident server state is valid: configured default identity is distinct from current resident default route;
- the last idle runtime can unload without making the server unhealthy;
- bounded scheduler contracts plus async FIFO runtime admission are integrated;
- opt-in request queueing is wired with bounded capacity, queue timeout, per-runtime gates and streaming slot lifetime;
- admin scheduler evidence exposes aggregate queue/running state without request content;
- explicit runtime pin/unpin policy is integrated and exposed through admin residency APIs;
- `evictable` is a current eligibility state only: pinned, non-ready and active-leased runtimes are excluded;
- deterministic LRU/TTL candidate selection is integrated with resident-default protection enabled by default;
- eviction preview and execution are explicit admin actions; no pressure-triggered automatic eviction is enabled by default;
- a state/lease change between selection and unload causes the candidate to be skipped rather than forced;
- worker protocol and bounded JSON-line subprocess transport exist for health/generate/drain/cancel/stop ownership;
- reclamation evidence contracts record before/ready/peak/after-stop snapshots;
- a repeated lifecycle experiment harness now orchestrates those checkpoints, attempts cleanup on partial failures and aggregates `recovery_observed`, `no_recovery_observed` and `inconclusive` without emitting a PASS/FAIL claim.

Remaining boundary:

- existing inference engines are not yet broadly routed through process-isolated worker ownership;
- automatic eviction under real resource pressure is intentionally not enabled;
- estimated residency remains distinct from representative measured footprint;
- real host-memory reclamation, repeated lifecycle stability and safe pressure eviction still require representative hardware evidence.

### Multi-task capabilities and audio

Integrated:

- task/input/output/feature capability descriptors with explicit vs `legacy_conservative` provenance;
- capability descriptors are public in model/admin catalog sources;
- supported chat requests reject unsupported canonical capability combinations before backend execution;
- first-class resident transcription service exists independently from audio-language chat;
- modular `/v1/audio/transcriptions` accepts bounded multipart upload and requires explicit transcription capability;
- legacy audio modality alone never implies ASR support;
- Endpoints now derives chat, vision-language, structured-generation and transcription compatibility from server-owned descriptors;
- Playground controls are filtered from declared tasks/modalities/features rather than named-model allowlists;
- the Playground includes a first-class multipart audio -> text transcription flow for compatible resident runtimes;
- if capability metadata becomes unavailable, legacy controls are restored rather than left in a stale disabled state.

Remaining boundary:

- broader specialist runtime coverage remains backend-dependent;
- text/vision/audio hardware behavior still needs representative evidence and regression coverage.

### Observability and runtime identity

Integrated:

- canonical token/chunk/duration/throughput vocabulary with no chunk-as-token aliasing;
- non-streaming completions record explicit OpenAI usage and backend timing fields when supplied;
- streaming chat records true first non-empty model-content TTFT from request receipt;
- queue wait, prompt/output tokens, prefill/decode duration, decode throughput and total duration are exposed only when sourced;
- malformed/oversized completion capture degrades conservatively instead of inventing timing/token values;
- privacy-safe `/api/v1/evidence` exposes request/runtime evidence without generated content;
- path-free artifact identity, backend/config/hardware fingerprint contracts and immutable residency snapshots are integrated;
- automatic runtime identity capture occurs only when artifact SHA-256 and backend version are strong enough; otherwise the runtime remains exploratory;
- System / Diagnostics consumes the canonical `durations_ms` / `throughput` schema directly and preserves missing values as `Unavailable`.

Remaining boundary:

- backend-specific metric coverage is still incomplete across all MLX/VLM/ASR combinations;
- device-specific throughput, TTFT and thermal claims remain evidence-pending.

### Evaluation harness

Integrated:

- versioned test-set/sample/scorer/run/report contracts;
- built-in `general-purpose` v1 deterministic set and objective scorer;
- seeded sample selection and per-sample failure isolation;
- resident-runtime evaluation service, run API and local immutable report persistence;
- history loading and compatibility-aware comparison API/UI;
- comparison distinguishes `not comparable`, `exploratory`, `descriptive only` and attribution-safe states and emits no automatic better/worse verdict;
- runtime fingerprint controls evidence-grade comparison status;
- test-set identity is content-sensitive, so prompt/expectation/task changes alter identity even under stable sample IDs;
- validated custom JSON test-set import uses atomic local persistence, version coexistence, reserved built-in IDs and no executable code/templates/plugins;
- custom sets currently support deterministic `chat` and `structured_generation` samples with allowlisted objective expectations;
- Benchmark & Evaluation now provides JSON import, built-in/custom source labeling, explicit version identity and `test_set_version` propagation into runs;
- duplicate id/version import conflicts are surfaced explicitly and the UI never silently opts into replace.

Remaining boundary:

- cancellation/progress is limited by the current synchronous evaluation execution model;
- broader benchmark families and explicit cold/warm experiment orchestration remain later extensions;
- evidence-grade cross-runtime comparisons remain constrained by verified identity/backend coverage.

### UX/UI

Integrated:

- shared design system and seven-destination control-plane shell;
- Overview consumes live health/status/models plus resource, runtime-evidence and scheduler sources;
- Models & Runtimes consumes resident/status/catalog plus resource, runtime identity and residency policy sources;
- Models & Runtimes exposes real pin/unpin controls while keeping reclamation claims separate;
- Endpoints and Playground are capability-driven and include first-class transcription UX;
- Benchmark & Evaluation supports real setup/run/results, persisted history/comparison and custom dataset import/version selection;
- System / Diagnostics prepends source-backed runtime/resource/scheduler/identity summaries to the existing operational logs rather than replacing them;
- Settings is source-backed and read-only, showing effective request-privacy, resource, residency and scheduler state without inventing configuration mutations;
- shell fallback content no longer repeats obsolete milestone/blocker claims;
- missing values remain `Unavailable`, not zero;
- configured default identity, resident default route and cold state are distinct in product UI.

Remaining boundary:

- full keyboard/focus/contrast/200%-zoom verification;
- responsive evidence at representative widths;
- stable visual-regression coverage for loading/empty/unavailable/warning/error/success states;
- representative runtime screenshots for public documentation;
- final cleanup/migration of legacy view internals where overlays still preserve old working surfaces.

## Program status

| Task | Status | Integrated outcome | Remaining gate |
| --- | --- | --- | --- |
| A1 truthful CI | DONE | blocking deterministic matrix | broader quality debt later |
| A2/C1 canonical policy | PARTIAL | supported entrypoints validate canonical request/media/capability policy | retire duplicate parser + legacy direct-app path |
| A3 consumer decoupling | DONE | generic registry sources | — |
| B1 resource observation | EVIDENCE | Linux/macOS source contracts | representative device validation |
| B2 resource admission | PARTIAL | product policy + shared accounting/API | measured reconciliation/hardware evidence |
| B3 worker/reclamation | PARTIAL | protocol/transport + conservative evidence recorder + repeated experiment harness | engine integration + hardware proof |
| B4 zero resident | DONE | healthy cold state + default/residency separation | automatic cold-load remains later policy |
| B5 scheduler | PARTIAL | bounded FIFO request admission + evidence | wider runtime/cancellation evidence |
| B6 pin/LRU/TTL | PARTIAL | pinning + deterministic explicit LRU/TTL preview/execution | pressure trigger + representative safety/reclamation evidence |
| C2 capabilities | PARTIAL | descriptors + pre-backend enforcement + capability-driven UX | broader task/backend evidence |
| C3 transcription | PARTIAL | first-class service/API/UI | specialist backend/hardware evidence |
| D1 metrics vocabulary | DONE | truthful canonical schema | — |
| D2 live metrics | PARTIAL | streaming TTFT + nonstreaming token/timing evidence | wider backend coverage/hardware validation |
| D3 runtime identity | PARTIAL | verified auto-capture + public evidence | stronger artifact/backend coverage |
| D4 evaluation | PARTIAL | resident runs, persistence and custom dataset backend/UI | richer workload families/cold-warm orchestration |
| D5 history/comparison | PARTIAL | persisted compatibility-aware comparison | baseline management/report UX later |
| E1/E2 design system + shell | PARTIAL | shared primitives and seven-destination IA | accessibility/visual evidence |
| E3 Models & Runtimes | PARTIAL | runtime/catalog/resource/identity/residency sources + pin UX | lifecycle/hardware evidence + legacy cleanup |
| E4 Overview | PARTIAL | resource/runtime/metric/scheduler evidence | hardware evidence |
| E5 Playground/Endpoints | PARTIAL | capability-driven task composition + transcription UX | accessibility/regression/backend evidence |
| E6 Evaluation UI | PARTIAL | run/results/history/comparison + custom upload/version UX | richer experiments/accessibility evidence |
| E7 System/Settings | PARTIAL | source-backed diagnostics + effective policy presentation | accessibility/visual evidence + future mutation semantics if required |
| H hardware/release evidence | PENDING | deterministic CI and experiment harness only | representative hardware matrix |

## Immediate next parallel wave

The dominant work is now hardening/evidence rather than source wiring:

1. **B3e worker adoption + hardware evidence** — bind selected dynamic runtimes to explicit process ownership where useful, then run repeated before/ready/peak/after-stop experiments on representative hardware.
2. **B6c pressure-policy validation** — define deterministic pressure trigger semantics and test candidate selection under concurrency; keep automatic eviction disabled until hardware evidence supports the claim.
3. **D2e/D3e backend coverage** — expand truthful metrics and verified artifact/backend version capture across MLX text/VLM/ASR without fabricating unavailable fields.
4. **A2 final canonical-route migration** — remove the historical duplicate backend-kwargs parser boundary and formalize/deprecate direct `server:app` usage without breaking supported entrypoints.
5. **H1/H2 UX hardening** — keyboard/focus/status/contrast/200%-zoom checks, responsive reference widths and stable visual-regression states.
6. **H3/H4 release evidence/documentation** — representative screenshots, hardware evidence records, README/API examples and explicit experimental-claim labels.
7. **Integration consolidation** — cumulative CI/release-gate review, then promote the control-plane program toward `main` only when the agreed release boundary is satisfied.

### Parallelization constraints

- B6 pressure automation must not convert deterministic policy correctness into a memory-reclamation claim.
- B3/hardware evidence owns reclamation proof; B6 owns candidate/admission policy.
- D2/D3 may progress per backend independently of UX hardening.
- A2 route migration must preserve the canonical pre-backend policy already installed on supported product entrypoints.
- H1/H2 may use deterministic fixtures, but hardware/runtime claims require real source-backed evidence.
- documentation status changes only after corresponding code/evidence is integrated.

## Evidence boundary

Automated tests establish contract and deterministic workflow correctness. They do **not** prove Apple unified-memory reclamation, actual unload recovery, thermal behavior, device-specific token throughput or safe auto-eviction under pressure. Representative hardware evidence remains mandatory before those claims become DONE.

## Update rule

Update this file in the same integration cycle whenever task state, blockers or the immediate parallel wave changes.

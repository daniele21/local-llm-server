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
- supported product entrypoints install canonical request/media/capability policy before inference;
- remote HTTP(S) media is fail-closed by default; `trust_remote_code` and remote-media opt-in remain explicit;
- canonical request preparation now also produces one tested `PreparedBackendRequest` with the existing engine kwargs/default semantics, including aliases, structured output and switchable thinking;
- the exact resident model ID can be separated from the public request alias during backend preparation;
- owned temporary audio cleanup is deterministic;
- read-only admin `/api/v1/policies` exposes bounded effective policy flags without paths, prompt/output content or secrets;
- external registry integration is consumer-agnostic.

Compatibility boundary:

- `server.py` still reconstructs historical backend kwargs after middleware validation instead of consuming `prepared.backend`; the translation owner is ready but the route switch is not yet merged;
- direct use of legacy module-level `local_llm_server.server:app` remains a compatibility/deprecation path rather than the supported product entrypoint.

### Resources, runtime lifecycle, workers and scheduling

Integrated:

- Linux/macOS resource observation with measured/estimated/configured/unavailable semantics;
- `ResourceManager` reservation, admission and accounting with `ADMIT`, `REJECT`, `UNKNOWN`;
- supported product bootstrap can configure resource policy before initial expensive model load;
- admin `/api/v1/resources` exposes configured/disabled policy, usable budget, committed/reserved bytes and remaining capacity;
- load/reload/unload accounting, zero-resident state, default/residency separation and bounded request leases are integrated;
- bounded FIFO request scheduling exposes aggregate queue/running evidence without request content;
- explicit runtime pin/unpin, current `evictable` eligibility and deterministic LRU/TTL selection are integrated;
- resident default protection is enabled by default; selection is revalidated at unload and stale candidates are skipped;
- explicit eviction preview/execution remains administrative; automatic pressure eviction is disabled;
- deterministic pressure policy evaluation now uses hysteresis: repeated high-pressure samples trigger at most one bounded candidate attempt per episode, and clearing requires repeated lower-pressure samples;
- `UNKNOWN` pressure never triggers eviction and never clears an already-triggered episode;
- worker protocol + bounded JSON-line subprocess transport are integrated;
- `WorkerBackedEngine` provides real isolated **non-streaming** completed-response inference with private runtime config sent over stdin after process start;
- worker streaming and in-flight cancellation are explicitly unsupported in this first adapter rather than emulated;
- worker prepare/generation errors expose bounded codes instead of backend exception text/private paths;
- repeated reclamation orchestration records before-start/after-ready/peak/after-stop windows and preserves `recovery_observed`, `no_recovery_observed` and `inconclusive` without PASS/FAIL promotion;
- worker reclamation cycles now bind real isolated start/ready/infer/stop operations to that harness;
- `local-llm evidence-reclamation` produces atomic privacy-safe JSON reports on local hardware, with prompt/output and local model paths excluded;
- the hardware runner records artifact/config/backend/hardware identity, resolves backend versions where possible and can measure bound child-process RSS during READY/PEAK on Linux/macOS;
- child RSS is `Unavailable` before start and after stop rather than fabricated as zero; host available-memory remains the before/after recovery source.

Remaining boundary:

- worker isolation is not yet the default/general streaming runtime path;
- automatic pressure eviction remains disabled pending representative evidence review;
- actual host/unified-memory reclamation, repeated lifecycle stability and safe pressure behavior require hardware reports produced outside CI;
- worker cancellation and true incremental streaming need protocol extensions before they can be claimed.

### Multi-task capabilities and audio

Integrated:

- task/input/output/feature capability descriptors with explicit vs `legacy_conservative` provenance;
- capability descriptors are public in model/admin catalog sources;
- unsupported canonical chat combinations fail before backend execution;
- first-class resident transcription service and bounded multipart `/v1/audio/transcriptions` require explicit ASR capability;
- legacy audio modality alone never implies ASR support;
- Endpoints derives chat, vision-language, structured-generation and transcription compatibility from server-owned descriptors;
- Playground controls follow declared modalities/features and include a real audio -> text flow;
- capability-source loss restores legacy controls rather than leaving stale disabled state.

Remaining boundary:

- broader specialist runtime coverage remains backend-dependent;
- text/vision/audio device behavior still needs representative smoke/evidence coverage.

### Observability and runtime identity

Integrated:

- canonical token/chunk/duration/throughput vocabulary with no chunk-as-token aliasing;
- non-streaming completions map explicit OpenAI usage and backend timings when supplied;
- streaming chat measures first non-empty model-content TTFT at the HTTP boundary;
- streaming SSE events now retain explicit cumulative `usage`/`timings` evidence instead of discarding it after TTFT observation;
- HTTP-boundary TTFT/total sources remain distinct from backend timing sources;
- an explicit MLX generation adapter maps prompt/generation token counts and processing rates only when supplied by the backend, deriving durations only from valid count/rate pairs;
- malformed/missing measurements remain unavailable;
- privacy-safe `/api/v1/evidence` exposes runtime evidence without generated content;
- path-free artifact/backend/config/hardware fingerprint contracts and immutable residency snapshots are integrated;
- automatic identity capture requires strong artifact SHA + backend version; otherwise runs remain exploratory;
- generic/specialist backends may supply an explicit backend version, and llama-server build+commit can be probed conservatively without publishing its executable path;
- System / Diagnostics consumes canonical `durations_ms` / `throughput` fields and preserves missing values as `Unavailable`.

Remaining boundary:

- wider VLM/ASR metric and termination/cancellation coverage is still incomplete;
- device-specific throughput, TTFT and thermal claims remain evidence-pending.

### Evaluation harness

Integrated:

- versioned test-set/sample/scorer/run/report contracts, deterministic built-in general-purpose set and seeded selection;
- resident-runtime evaluation, per-sample failure isolation, immutable local persistence, history and compatibility-aware comparison;
- comparisons distinguish incompatible/exploratory/descriptive/attribution-safe states and never auto-declare better/worse;
- verified runtime fingerprint controls evidence-grade comparison status;
- validated custom JSON import uses atomic local persistence, explicit versions, reserved built-in IDs and no executable scorer/template/plugin definitions;
- custom deterministic `chat` and `structured_generation` samples execute through the same service;
- Benchmark & Evaluation provides JSON import, built-in/custom labels, explicit version propagation and duplicate-conflict feedback.

Remaining boundary:

- cancellation/progress remains limited by synchronous evaluation execution;
- broader workload families and explicit cold/warm orchestration remain later extensions;
- evidence-grade comparisons remain constrained by runtime/backend identity coverage.

### UX/UI

Integrated:

- shared design system and seven-destination source-backed control-plane shell;
- Overview, Models & Runtimes, Endpoints/Playground, Benchmark & Evaluation, System / Diagnostics and Settings consume real server-owned sources;
- Models exposes real pin/unpin while keeping eviction policy separate from reclamation evidence;
- Settings remains read-only rather than inventing undefined mutation contracts;
- control-plane navigation now uses a dedicated ARIA tablist/tabpanel model with roving tabindex, Arrow/Home/End keyboard navigation and a skip link;
- inactive panels are removed from the accessibility tree;
- visible focus styling covers design-system plus retained legacy native controls;
- decorative tab icons are hidden from assistive technology;
- responsive grid/action/table contracts are hardened for narrow effective viewports and high browser zoom; tables retain horizontal access;
- reduced-motion handling is broadened;
- status components retain visible text in addition to color indicators;
- missing values remain `Unavailable`, not zero.

Remaining boundary:

- manual light/dark contrast review;
- real end-to-end traversal at 200% zoom and representative device widths;
- stable visual-regression fixtures/screenshots for loading/empty/unavailable/warning/error/success states;
- destructive-action confirmation/feedback audit;
- representative runtime screenshots for public documentation;
- final cleanup of legacy view internals where overlays still preserve working surfaces.

## Program status

| Task | Status | Integrated outcome | Remaining gate |
| --- | --- | --- | --- |
| A1 truthful CI | DONE | blocking deterministic matrix | broader quality debt later |
| A2/C1 canonical policy | PARTIAL | canonical validation + canonical backend-kwargs adapter | switch historical route to prepared backend + legacy direct-app decision |
| A3 consumer decoupling | DONE | generic registry sources | — |
| B1 resource observation | EVIDENCE | Linux/macOS source contracts + worker PID RSS evidence path | representative device validation |
| B2 resource admission | PARTIAL | product policy + shared accounting/API | measured reconciliation/hardware evidence |
| B3 worker/reclamation | PARTIAL | isolated batch worker + repeated worker reclamation procedure + CLI | representative reports + streaming/cancellation adoption |
| B4 zero resident | DONE | healthy cold state + default/residency separation | automatic cold-load remains later policy |
| B5 scheduler | PARTIAL | bounded FIFO request admission + evidence | wider cancellation/runtime evidence |
| B6 pin/LRU/TTL/pressure | PARTIAL | pinning + LRU/TTL + hysteretic pressure evaluator | real pressure/hardware review before automation |
| C2 capabilities | PARTIAL | descriptors + pre-backend enforcement + capability-driven UX | broader backend evidence |
| C3 transcription | PARTIAL | first-class service/API/UI | specialist backend/hardware evidence |
| D1 metrics vocabulary | DONE | truthful canonical schema | — |
| D2 live metrics | PARTIAL | HTTP TTFT + nonstream/stream explicit usage/timing + MLX adapter | wider VLM/ASR/device validation |
| D3 runtime identity | PARTIAL | verified auto-capture + explicit/specialist version paths | stronger artifact/backend coverage |
| D4 evaluation | PARTIAL | resident runs, persistence and custom dataset backend/UI | richer workloads/cold-warm orchestration |
| D5 history/comparison | PARTIAL | persisted compatibility-aware comparison | baseline/report UX later |
| E1/E2 design system + shell | EVIDENCE | shared primitives + ARIA keyboard/focus/responsive contracts | manual contrast/zoom/visual evidence |
| E3 Models & Runtimes | PARTIAL | source-backed state + pin UX | lifecycle/hardware evidence + legacy cleanup |
| E4 Overview | PARTIAL | resource/runtime/metric/scheduler evidence | hardware evidence |
| E5 Playground/Endpoints | PARTIAL | capability-driven tasks + transcription UX | regression/backend evidence |
| E6 Evaluation UI | PARTIAL | run/results/history/comparison + custom upload/version UX | richer experiments/visual evidence |
| E7 System/Settings | PARTIAL | source-backed diagnostics + policy presentation | visual/manual evidence + future mutation semantics if required |
| H hardware/release evidence | PARTIAL | repeatable worker hardware CLI + evidence schema | execute/review representative device matrix |

## Immediate next parallel wave

The highest-value remaining work is now validation/consolidation rather than basic source wiring:

1. **H3 representative hardware execution** — run `local-llm evidence-reclamation` across agreed Mac/Linux devices/backends/artifacts, retain exact identity and review repeated recovery/stability results.
2. **A2 route cutover** — make `server.py` consume `prepared.backend`, remove duplicate request/kwargs construction, then decide/formalize the legacy direct `server:app` deprecation boundary.
3. **B6 pressure integration review** — feed real pressure observations into the hysteretic evaluator only after hardware results establish a defensible safety envelope; keep automatic unload off by default until then.
4. **D2/D3 specialist coverage** — add explicit VLM/ASR timing/token/termination evidence and stronger version/artifact capture without substituting estimates for unavailable values.
5. **B3 worker protocol expansion** — design real incremental worker streaming/cancellation if process-isolated interactive inference is required; do not emulate it with buffered completed output.
6. **H1/H2 manual + visual hardening** — contrast, real 200% zoom, reference widths, destructive-action review and stable visual-regression state fixtures.
7. **H4 release/docs consolidation** — README/API examples, representative screenshots, evidence matrix and experimental-claim labels, followed by cumulative integration-to-main review.

### Parallelization constraints

- pressure-policy correctness is not reclamation proof; B6 automation remains gated by H3 evidence;
- child PID RSS may describe READY/PEAK footprint, but after-stop recovery remains a host-memory observation rather than an invented zero;
- A2 route cutover must preserve the already-tested canonical request and backend translation contract;
- specialist metric adapters may map only explicit backend evidence;
- deterministic UX tests do not replace manual contrast/zoom or real runtime screenshots;
- documentation status changes only after code/evidence is integrated.

## Evidence boundary

Automated tests establish deterministic contract/workflow correctness and the hardware runner makes representative testing reproducible. CI still does **not** prove unified-memory reclamation, actual unload recovery, thermal behavior, device-specific throughput or safe automatic eviction under pressure. Those claims require retained reports from representative hardware.

## Update rule

Update this file in the same integration cycle whenever task state, blockers or the immediate parallel wave changes.

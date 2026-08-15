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

`LLS-ID-001` is integrated: the supported product stack exposes a public, versioned, path-free execution-identity producer for external evaluators. The aligned AI Performance Lab `INT-002` consumer uses the same `local-llm-identity-v1` protocol without creating a server-side dependency on Performance Lab.

## Integrated baseline

### Delivery, canonical requests and privacy

Integrated:

- blocking pytest on Python 3.10/3.11/3.12 plus Ruff correctness checks;
- backend-neutral task/request/result/error contracts and OpenAI/legacy compatibility translation;
- supported product entrypoints install canonical request/media/capability policy before inference;
- remote HTTP(S) media is fail-closed by default; `trust_remote_code` and remote-media opt-in remain explicit;
- canonical request preparation produces a tested `PreparedBackendRequest` with current engine kwargs/default semantics, including aliases, structured output and switchable thinking;
- exact resident model ID can be separated from the public request alias during backend preparation;
- a full product-stack parity gate proves that the historical chat route and `PreparedBackendRequest` send equivalent engine kwargs for default chat, sampling/penalties, legacy input/system prompt, structured output, force-json, reasoning aliases and streaming;
- owned temporary audio cleanup is deterministic;
- read-only admin `/api/v1/policies` exposes bounded effective policy flags without paths, prompt/output content or secrets;
- external registry integration is consumer-agnostic.

Compatibility boundary:

- `server.py` still reconstructs historical backend kwargs after middleware validation instead of directly consuming `prepared.backend`; parity is green, so the remaining work is a physical cleanup/cutover rather than unresolved semantics;
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
- deterministic pressure policy evaluation uses hysteresis: repeated high-pressure samples trigger at most one bounded candidate attempt per episode, clearing requires repeated lower-pressure samples and `UNKNOWN` never triggers/clears an episode;
- worker protocol + bounded JSON-line subprocess transport are integrated;
- `WorkerBackedEngine` provides real isolated **non-streaming** completed-response inference with private runtime config sent over stdin after process start;
- worker streaming and in-flight cancellation are explicitly unsupported in this first adapter rather than emulated;
- worker prepare/generation errors expose bounded codes instead of backend exception text/private paths;
- repeated reclamation orchestration records before-start/after-ready/peak/after-stop windows and preserves `recovery_observed`, `no_recovery_observed` and `inconclusive` without PASS/FAIL promotion;
- worker reclamation cycles bind real isolated start/ready/infer/stop operations to that harness;
- `local-llm evidence-reclamation` produces atomic privacy-safe JSON reports on local hardware, excluding prompt/output and local model paths;
- the hardware runner records artifact/config/backend/hardware identity, resolves backend versions where possible and can measure bound child-process RSS during READY/PEAK on Linux/macOS;
- hardware evidence serializes bounded hostname-free environment metadata (`system`, release, machine, Python version);
- child RSS is `Unavailable` before start and after stop rather than fabricated as zero; host available-memory remains the before/after recovery source;
- repeated reports can be reviewed with a conservative compatibility/repetition layer that refuses to pool different runtime/hardware/procedure identities;
- `local-llm evidence-review` exposes that reviewer directly from the CLI, with explicit thresholds and no residency/eviction mutation path.

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
- transcription records task-specific evidence (`backend_wall_clock_ms`, backend-reported audio duration, realtime factor and segment count) instead of forcing ASR into generation token/TTFT fields;
- latest transcription evidence is exposed under `task_metrics.transcription` while canonical generation metrics remain independent;
- backend transcription metadata is preserved on normalized results;
- Endpoints derives chat, vision-language, structured-generation and transcription compatibility from server-owned descriptors;
- Playground controls follow declared modalities/features and include a real audio -> text flow;
- capability-source loss restores legacy controls rather than leaving stale disabled state.

Remaining boundary:

- broader specialist runtime/device coverage remains backend-dependent;
- text/vision/audio device behavior still needs representative smoke/evidence coverage.

### Observability and runtime identity

Integrated:

- canonical token/chunk/duration/throughput vocabulary with no chunk-as-token aliasing;
- non-streaming completions map explicit OpenAI usage and backend timings when supplied;
- streaming chat measures first non-empty model-content TTFT at the HTTP boundary;
- streaming SSE events retain explicit cumulative `usage`/`timings` evidence instead of discarding it after TTFT observation;
- HTTP-boundary TTFT/total sources remain distinct from backend timing sources;
- an explicit MLX generation adapter maps prompt/generation token counts and processing rates only when supplied by the backend, deriving durations only from valid count/rate pairs;
- MLX-VLM proxy regression tests prove that OpenAI-compatible `usage`/`timings` survive both non-streaming and terminal streaming events and map into canonical evidence without synthetic metrics;
- missing VLM evidence remains unavailable;
- privacy-safe `/api/v1/evidence` exposes runtime and task evidence without generated content;
- path-free artifact/backend/config/hardware fingerprint contracts and immutable residency snapshots are integrated;
- automatic evidence-grade identity capture requires strong artifact SHA + backend version; otherwise runtimes remain exploratory/partial;
- generic/specialist backends may supply an explicit backend version, and llama-server build+commit can be probed conservatively without publishing its executable path;
- resolved runtime identity exposes the exact allowlisted path-free effective configuration covered by its config digest;
- built-in registry entries carry explicit quantization metadata rather than requiring downstream filename inference;
- **LLS-ID-001** exposes public read-only `GET /v1/runtime/identity` with protocol `local-llm-identity-v1`, resident model revision/digest/quantization when known, backend/version/config digest, bounded hardware identity and partial/verified evidence state;
- public identity excludes model paths, download URLs, credentials, prompt/output content, hostname and dynamic request counters;
- the producer is aligned with merged AI Performance Lab `INT-002`, which maps the same protocol into its immutable execution fingerprint;
- System / Diagnostics consumes canonical `durations_ms` / `throughput` fields and preserves missing values as `Unavailable`.

Validation evidence:

- the final producer head passed blocking Ruff plus deterministic tests on Python 3.10/3.11/3.12 before merge;
- the aligned Performance Lab consumer passed its Python 3.12/3.13 repository gate before merge;
- remaining identity-completeness and performance claims require representative resident-model/device evidence, not more deterministic contract tests.

Remaining boundary:

- the in-process MLX engine still needs to propagate upstream generation response counters/rates into emitted OpenAI-compatible chunks/responses so the integrated adapter becomes end-to-end rather than library-only;
- wider ASR/VLM termination/cancellation coverage is backend-dependent;
- device-specific throughput, TTFT, thermal and identity-completeness claims remain evidence-pending.

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
- evidence-grade comparisons remain constrained by runtime/backend/artifact identity coverage.

### UX/UI and release-facing documentation

Integrated:

- shared design system and seven-destination source-backed control-plane shell;
- Overview, Models & Runtimes, Endpoints/Playground, Benchmark & Evaluation, System / Diagnostics and Settings consume real server-owned sources;
- Models exposes real pin/unpin while keeping eviction policy separate from reclamation evidence;
- Settings remains read-only rather than inventing undefined mutation contracts;
- control-plane navigation uses a dedicated ARIA tablist/tabpanel model with roving tabindex, Arrow/Home/End keyboard navigation and a skip link;
- inactive panels are removed from the accessibility tree;
- visible focus styling covers design-system plus retained legacy native controls;
- decorative tab icons are hidden from assistive technology;
- responsive grid/action/table contracts are hardened for narrow effective viewports and high browser zoom; tables retain horizontal access;
- reduced-motion handling is broadened and status components retain visible text in addition to color;
- missing values remain `Unavailable`, not zero;
- release-facing documentation distinguishes deterministic contract evidence from hardware-dependent claims.

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
| A2/C1 canonical policy | PARTIAL | canonical validation + backend adapter + real route parity gate | physical route cutover + legacy direct-app decision |
| A3 consumer decoupling | DONE | generic registry sources | — |
| B1 resource observation | EVIDENCE | Linux/macOS source contracts + worker PID RSS evidence path | representative device validation |
| B2 resource admission | PARTIAL | product policy + shared accounting/API | measured reconciliation/hardware evidence |
| B3 worker/reclamation | PARTIAL | isolated batch worker + repeated reclamation runner/reviewer CLI | representative reports + streaming/cancellation decision |
| B4 zero resident | DONE | healthy cold state + default/residency separation | automatic cold-load remains later policy |
| B5 scheduler | PARTIAL | bounded FIFO request admission + evidence | wider cancellation/runtime evidence |
| B6 pin/LRU/TTL/pressure | PARTIAL | pinning + LRU/TTL + hysteretic pressure evaluator | real pressure/hardware review before automation |
| C2 capabilities | PARTIAL | descriptors + pre-backend enforcement + capability-driven UX | broader backend evidence |
| C3 transcription | PARTIAL | first-class service/API/UI + task-specific ASR evidence | specialist hardware/backend validation |
| D1 metrics vocabulary | DONE | truthful canonical schema | — |
| D2 live metrics | PARTIAL | HTTP TTFT + nonstream/stream evidence + VLM pass-through contract + ASR task metrics | in-process MLX wiring + wider device validation |
| D3 runtime identity | PARTIAL | verified capture + explicit/specialist versions + safe public identity producer | stronger artifact/backend/hardware coverage + representative evidence |
| LLS-ID-001 public identity API | DONE | `local-llm-identity-v1`, `/v1/runtime/identity`, explicit quantization, safe config digest/payload, privacy tests; aligned PL consumer merged | representative identity completeness on real runtimes/devices |
| D4 evaluation | PARTIAL | resident runs, persistence and custom dataset backend/UI | richer workloads/cold-warm orchestration |
| D5 history/comparison | PARTIAL | persisted compatibility-aware comparison | baseline/report UX later |
| E1/E2 design system + shell | EVIDENCE | shared primitives + ARIA keyboard/focus/responsive contracts | manual contrast/zoom/visual evidence |
| E3 Models & Runtimes | PARTIAL | source-backed state + pin UX | lifecycle/hardware evidence + legacy cleanup |
| E4 Overview | PARTIAL | resource/runtime/metric/scheduler evidence | hardware evidence |
| E5 Playground/Endpoints | PARTIAL | capability-driven tasks + transcription UX | regression/backend evidence |
| E6 Evaluation UI | PARTIAL | run/results/history/comparison + custom upload/version UX | richer experiments/visual evidence |
| E7 System/Settings | PARTIAL | source-backed diagnostics + policy presentation | visual/manual evidence + future mutation semantics if required |
| H hardware/release evidence | PARTIAL | repeatable hardware runner + conservative review CLI + release-facing README | execute/review representative device matrix + real screenshots |

## Immediate next parallel wave

The remaining work is concentrated in representative evidence and final consolidation:

1. **H3 representative hardware + identity execution** — run `/v1/runtime/identity` and `local-llm evidence-reclamation` across agreed Mac/Linux devices/backends/artifacts; retain identity completeness and use `local-llm evidence-review` only on compatible reports.
2. **A2 physical route cutover** — make `server.py` consume `prepared.backend`; the parity gate must remain green before duplicate construction is deleted. Then formalize the direct `server:app` compatibility/deprecation boundary.
3. **D2 MLX in-process wiring** — propagate explicit `stream_generate` token/rate evidence through MLXEngine response/chunk payloads so canonical metrics can consume it end to end; do not infer missing fields.
4. **B6 pressure integration review** — connect real pressure observations only after representative hardware review establishes a defensible safety envelope; automatic unload stays off by default until then.
5. **B3 worker protocol decision** — decide whether true incremental worker streaming/cancellation is a product requirement; never emulate it with buffered completed output.
6. **H1/H2 manual + visual hardening** — contrast, real 200% zoom, reference widths, destructive-action review and stable visual-regression fixtures.
7. **H4 final release matrix** — retained hardware result references, representative real-state screenshots and cumulative integration-to-main review.

### Parallelization constraints

- incompatible identity schema changes require a new protocol version and coordinated consumer support;
- pressure-policy correctness and a consistent recovery observation are not production-safety proof;
- child PID RSS may describe READY/PEAK footprint, while after-stop recovery remains a host-memory observation rather than invented zero;
- A2 cutover must preserve the green route-parity gate;
- specialist metric adapters map only explicit backend evidence;
- deterministic UX tests do not replace manual contrast/zoom or real runtime screenshots;
- documentation status changes only after code/evidence is integrated.

## Evidence boundary

Automated tests establish deterministic contract/workflow correctness and make representative testing reproducible. CI still does **not** prove unified-memory reclamation, actual unload recovery, thermal behavior, device-specific throughput, complete hardware/model identity or safe automatic eviction under pressure. Those claims require retained reports from representative hardware.

## Update rule

Update this file in the same integration cycle whenever task state, blockers or the immediate parallel wave changes.

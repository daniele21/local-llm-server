# Control-plane architecture evolution plan

Status: active
Document type: architecture
Owner: runtime-and-platform
Canonical scope: target.control-plane-architecture
Read when: changing runtime ownership, resource management, capability contracts, backend adapters, scheduling or observability
Last reviewed: 2026-08-15

This document owns the target architecture and migration boundaries required to evolve Local LLM Server into a resource-aware local AI control plane. It does not own workstream status; see [`current-state.md`](current-state.md) and [`roadmap.md`](roadmap.md).

## 1. Architectural problem statement

The current implementation already separates model configuration, engines, runtime management and HTTP serving, but several product responsibilities are still compressed into the same boundaries:

- `ModelRuntimeManager` owns lifecycle/concurrency but not global memory/resource decisions;
- engine adapters mix backend translation with residency ownership;
- `server.py` owns request models, routing behavior, caching, status, admin API and large presentation fragments;
- task semantics are represented mainly through chat requests plus `modalities`;
- current observability is backend-uneven and some names do not match the measured quantity;
- in-process engines do not yet provide a strong memory reclamation guarantee;
- artifact metadata is not yet a reproducibility identity.

The migration must strengthen these boundaries incrementally without breaking the useful OpenAI-compatible integration surface.

## 2. Target module topology

```text
local_llm_server/
  api/
    app.py
    schemas.py
    chat.py
    audio.py
    models.py
    admin.py

  core/
    requests.py
    responses.py
    capabilities.py
    errors.py
    policy.py

  runtime/
    manager.py
    scheduler.py
    resources.py
    lifecycle.py
    fingerprints.py

  backends/
    base.py
    llama_worker.py
    mlx_worker.py
    mlx_vlm_worker.py
    asr_worker.py

  artifacts/
    registry.py
    resolver.py
    downloader.py
    integrity.py

  observability/
    metrics.py
    events.py
    hardware.py
    evidence.py

  media/
    images.py
    audio.py
    cleanup.py

  static/
    ...
```

This is a target ownership map, not a mandatory one-shot file move. Refactoring should follow stable contracts, not cosmetic directory churn.

## 3. Workstream contracts

### ARC-01 — Canonical inference contract

Goal: introduce a backend-neutral request/response boundary while preserving existing API compatibility.

Required types:

- `TaskType`;
- `InferenceRequest`;
- `InferenceResult`;
- `GenerationOptions`;
- `OutputConstraints`;
- `TerminationReason`;
- typed public/internal errors.

Initial tasks:

- chat;
- structured generation;
- vision-language;
- transcription.

Compatibility rule:

- `/v1/chat/completions` remains supported and translates into the canonical request;
- a new task-specific endpoint must not duplicate runtime policy.

Exit gate:

- deterministic translation tests from current chat request shapes;
- no backend-specific type leaks into the canonical contract;
- current supported text/vision requests remain behaviorally compatible.

### ARC-02 — Capability descriptor

Goal: replace implicit backend/model assumptions with explicit task and feature declarations.

Descriptor fields:

- tasks;
- input modalities;
- output modalities;
- streaming support;
- structured-output support level;
- tool/function support level;
- reasoning/thinking support;
- backend-specific optional capabilities hidden behind a generic extension map only where necessary.

Exit gate:

- registry validation rejects impossible declarations;
- API rejects unsupported task/modality combinations before engine execution;
- UI can render unavailable versus supported capabilities from one source.

Hard dependency: ARC-01 contract vocabulary should be stable enough to name tasks/features.

### ARC-03 — Resource observation model

Goal: create truthful, source-labelled system and runtime resource observations before adding policy.

Global observation:

- total physical/unified memory;
- currently available memory where the platform exposes a meaningful value;
- configured AI budget;
- safety headroom;
- process/server resident memory;
- platform/hardware identity.

Per-runtime observation/profile:

- artifact bytes;
- estimated load footprint;
- observed idle/resident footprint;
- observed request peak;
- backend-exposed KV/prompt-cache usage when available;
- loaded-at and last-used timestamps;
- measurement count and confidence/source label.

Rule:

- estimated, configured and observed values are distinct types/fields;
- unavailable values are `null`/unavailable, never zero.

Exit gate:

- deterministic unit tests for budget arithmetic;
- platform adapters have safe unavailable behavior;
- source labels prevent an estimate from being displayed as an observation.

### ARC-04 — ResourceManager

Goal: centralize resource reservation/admission for runtime load and, later, request execution.

Responsibilities:

- evaluate whether a proposed load fits the configured budget;
- reserve expected resources during model startup to prevent concurrent overcommit;
- reconcile reservation with observed footprint after startup;
- classify pressure (`NORMAL`, `ELEVATED`, `HIGH`, `CRITICAL` or similarly bounded states);
- expose explicit `resource_exhausted` decisions;
- never kill an active leased runtime as an admission side effect.

Non-responsibilities:

- choosing a different model;
- making quality decisions;
- deleting artifacts;
- performing backend-specific memory allocation.

Hard dependency: ARC-03.

### ARC-05 — Verifiable runtime ownership / worker boundary

Goal: make `STOPPED` mean that owned residency resources are actually released.

Preferred daemon path:

- one controlled worker process per dynamically resident backend/model boundary, or another demonstrably equivalent ownership boundary;
- worker owns backend-specific model object and caches;
- parent owns lifecycle, IPC, policy and public API;
- process exit is the final reclamation boundary when backend APIs cannot prove cleanup.

Required lifecycle:

```text
COLD -> STARTING -> READY -> DRAINING -> STOPPING -> STOPPED
                         \-> FAILED
```

Requirements:

- bounded startup health check;
- bounded drain;
- cancellation propagation;
- TERM then KILL escalation;
- cleanup after startup failure;
- no orphan child process;
- worker identity exposed to diagnostics without exposing private internals.

Migration strategy:

1. keep current managed `llama_server` / `mlx_vlm_server` adapters as proven process-isolated references;
2. define worker protocol;
3. add isolated text worker path;
4. retain in-process mode only where explicitly chosen and documented.

Exit gate:

- repeated load/unload demonstrates no orphan process;
- resource observation shows post-stop reclamation on representative hardware;
- failure/cancel/shutdown tests cover child-process cleanup.

### ARC-06 — Zero-resident server state

Goal: allow the control plane to run with no model resident.

Requirements:

- `/health` remains useful without a default resident runtime;
- `/v1/models` distinguishes configured/downloaded/resident concerns;
- request to a cold model follows an explicit load policy or returns an explicit cold/not-resident result according to configuration;
- unloading the last resident model is allowed;
- default route can point to a configured model without implying residency.

Hard dependency: lifecycle semantics from ARC-05; resource admission should exist before automatic load-on-request is enabled.

### ARC-07 — Scheduler and request admission

Goal: make queueing, deadlines, concurrency and cancellation explicit.

Request states:

```text
accepted -> queued -> preparing -> running -> completed
                          |          |-> cancelled
                          |          \-> failed
                          \-> expired/rejected
```

Responsibilities:

- bounded queue;
- per-runtime concurrency policy;
- deadline expiry before execution;
- cancellation before and during execution;
- client-disconnect propagation where possible;
- queue wait measurement;
- explicit overload/retryable errors.

Non-goal:

- reimplement backend-native continuous batching; use backend-native batching where appropriate and expose its effective behavior.

Dependencies: ARC-01, ARC-04 and stable lifecycle ownership.

### ARC-08 — Residency policy: pin, LRU, TTL and eviction

Goal: automate memory-efficient residency only after measurement/admission foundations exist.

Policy inputs:

- configured budget/headroom;
- runtime observed/estimated footprint;
- pin state;
- active leases;
- last-used monotonic time;
- load cost;
- optional idle TTL.

Rules:

- active runtime cannot be evicted;
- pinned runtime is protected unless an explicit critical policy says otherwise;
- default model identity is not changed by eviction;
- eviction reason is observable;
- load-on-request failure remains explicit if no safe candidate can be evicted.

Dependencies: ARC-03, ARC-04, ARC-05, ARC-06.

### ARC-09 — Audio task boundary

Goal: make transcription a first-class task independent from audio-language chat.

Target public compatibility:

- `/v1/audio/transcriptions` for ASR;
- multimodal chat remains available for models that truly support audio-language reasoning.

Runtime strategy:

- adapter to a specialist local ASR worker/service, including the existing Local ASR Server where appropriate;
- multipart/stream/file-handle local transfer preferred over large JSON base64 when possible;
- deterministic temporary file ownership and cleanup.

Dependencies: ARC-01 and ARC-02. Worker implementation can proceed independently from ResourceManager if residency is initially explicit/manual.

### ARC-10 — Observability normalization

Goal: one metric contract across backends without fabricating unavailable values.

Metric vocabulary:

- request accepted time;
- queue wait;
- model load/startup;
- prompt/prefill tokens;
- prompt/prefill duration;
- TTFT;
- output tokens;
- decode duration;
- output tokens/second;
- total duration;
- response-cache hit;
- backend prompt/KV-cache data where exposed;
- resident/peak memory;
- termination reason;
- typed failure.

Requirements:

- remove/rename misleading `tokens_generated = output_chunks` semantics;
- preserve raw backend metrics only as diagnostic extensions;
- operational telemetry excludes prompt/output content by default.

Can start in parallel with ARC-03 after metric names are agreed.

### ARC-11 — Artifact identity and runtime fingerprint

Goal: make runs reproducible and attributable.

Artifact identity should include where applicable:

- registry key;
- upstream repository/source;
- immutable revision;
- filename/path-independent artifact identifier;
- size;
- SHA-256;
- quantization/format metadata.

Runtime fingerprint should include:

- artifact identity;
- backend name/version;
- resolved inference configuration digest;
- server version;
- hardware profile;
- capability descriptor version.

Dependencies: registry/integrity work can start independently; benchmark comparison must wait for a stable fingerprint contract.

### ARC-12 — Server/API decomposition

Goal: reduce `server.py` ownership after contracts stabilize.

Extraction order:

1. schemas/canonical translation;
2. inference routes;
3. model/admin routes;
4. observability routes;
5. static/example presentation.

Rule:

- do not perform broad file moves before contract tests exist;
- each extraction should be behavior-preserving and reviewable independently.

### ARC-13 — Consumer decoupling

Goal: make Local LLM Server independent from ClosedRoom or any other specific consumer.

Required change:

- remove direct read of ClosedRoom application-support configuration from core registry loading;
- expose explicit registry path/provider/library configuration instead;
- consumer application supplies its desired model configuration through a stable integration point.

This can run immediately and independently from the core runtime architecture.

### ARC-14 — Security/privacy defaults

Goal: make local-first behavior explicit in defaults.

Required changes:

- `trust_remote_code=false` by default;
- remote image/audio URL fetch disabled by default;
- temporary audio/media files deterministically deleted;
- logs/errors do not expose sensitive media payloads or private paths unnecessarily;
- future shared-network mode introduces authentication without changing loopback defaults.

This can run immediately in parallel, with focused compatibility tests.

## 4. Backend responsibility matrix

| Concern | Control plane | Backend adapter/worker |
| --- | --- | --- |
| model route identity | owns | consumes |
| capability validation | owns | reports support |
| global memory budget | owns | reports observations if available |
| tensor allocation | observes | owns |
| batching algorithm | policy/visibility | backend-native owner where available |
| KV/prompt cache mechanics | policy/visibility | backend-native owner |
| cancellation request | owns propagation | owns actual interruption |
| lifecycle state | owns canonical state | owns process/model resources |
| public errors | maps | supplies bounded cause |
| raw backend logs | bounds/redacts | emits |
| runtime fingerprint | assembles | supplies backend version/config facts |

## 5. Migration invariants

Throughout migration:

- current OpenAI-compatible chat clients remain supported unless a versioned breaking change is explicitly planned;
- no UI is allowed to depend directly on backend worker ports;
- no automatic model substitution is introduced;
- data shown as live/observed must come from a source-backed contract;
- implementation may temporarily support both old and new internal paths, but there must be one canonical product state;
- compatibility shims receive removal criteria rather than becoming permanent parallel architectures.

## 6. Validation layers

### Deterministic CI

- canonical request translation;
- capability validation;
- resource arithmetic;
- scheduler state machine;
- lifecycle race/cancellation cleanup;
- registry/integrity validation;
- API compatibility;
- UI state contracts using deterministic fixtures/fakes.

### Process integration

- start/readiness/terminate/kill;
- port reservation;
- no orphan workers;
- crash during startup and inference;
- cancellation and server shutdown.

### Representative hardware

Required before claiming:

- memory reclamation;
- peak/resident memory characteristics;
- safe memory budgets/headroom;
- latency/throughput values;
- thermal behavior;
- backend-specific concurrency safety.

## 7. Architecture completion boundary

This architecture workstream is complete when:

- canonical task/capability contracts own request semantics;
- global resource admission exists;
- zero-resident state is supported;
- daemon-mode unload has a verifiable reclamation boundary;
- scheduler/cancellation/deadlines are explicit;
- text, vision and transcription use truthful task capabilities;
- metrics use precise normalized semantics;
- artifact/runtime identity supports reproducible benchmark runs;
- consumer-specific coupling is removed;
- local privacy defaults are enforced;
- UX can consume all critical state without backend-specific inference or fake values.

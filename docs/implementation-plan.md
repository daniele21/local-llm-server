# Local LLM Server — target product specification

Status: active
Document type: target-specification
Owner: repository
Canonical scope: target.repository
Read when: a change affects repository-wide positioning, product behavior, runtime boundaries or acceptance criteria
Last reviewed: 2026-08-15

This document defines the repository-level target. It intentionally does not track implementation progress; integrated reality belongs in [`current-state.md`](current-state.md), capability sequencing in [`roadmap.md`](roadmap.md), and focused UX behavior in [`ux-ui-implementation-plan.md`](ux-ui-implementation-plan.md).

## Product target

Local LLM Server should be positioned and engineered as:

> **A resource-aware, observable control plane for product-grade local AI inference.**

It provides applications with one stable local execution boundary across specialist text, vision and audio runtimes while keeping model lifecycle, memory, task capability, request scheduling, artifact identity and evidence explicit.

The project is **not** trying to replace `llama.cpp`, MLX-LM, MLX-VLM, Whisper implementations or other specialist inference engines. Those systems own tensor execution and backend-native optimization. Local LLM Server owns the product-grade orchestration boundary around them.

## Mission alignment

The repository exists to make the broader local-first AI thesis measurable:

- local execution should provide control over sensitive data boundaries;
- local execution should provide control over model lifecycle and artifact identity;
- local execution should expose its real resource cost instead of hiding memory pressure;
- applications should not be coupled to one inference backend;
- local-first is not local-only: external execution can remain a future explicit policy choice, never a silent dependency or substitution;
- performance and support claims should be backed by reproducible evidence on representative hardware.

The practical product loop is:

```text
Build -> Run locally -> Observe -> Measure -> Compare -> Improve
```

## Primary users

### Application developer

Needs one durable API for local inference without embedding backend-specific model loading, subprocess, cache or lifecycle logic in each application.

### Local-AI engineer

Needs to understand which runtime/model/configuration is actually active, how much memory it consumes, how it performs and where failures occur.

### Privacy-sensitive product team

Needs a local execution boundary with explicit network/media policy and evidence sufficient to support local-first claims.

### Model evaluator

Needs reproducible comparisons across model artifacts, backends, configurations and hardware without mixing incompatible runs.

## Core product promises

### 1. Stable application contract

Applications address tasks and explicit model/runtime identity through a stable API. Backend-native ports, Python objects, model pointers and subprocess details remain implementation details.

### 2. Exact model semantics

If a request names a model, the server either runs that model or returns an explicit failure. It never silently substitutes another local or remote model.

### 3. Explicit lifecycle

Registered, downloaded, cold, loading, ready/resident, draining, stopped and failed are distinct concepts. Downloading does not imply residency; selection/default routing does not imply residency; unload does not delete the artifact.

### 4. Resource-aware admission

Model load and request execution are admitted against an explicit resource budget. Memory pressure is a product state, not an operating-system surprise.

### 5. Verifiable unload

A runtime reported as stopped must no longer own the resources attributed to its residency boundary. If an in-process backend cannot provide a reliable reclamation guarantee, process isolation is the preferred product boundary.

### 6. Capability truthfulness

Capabilities are explicit and machine-readable. A runtime declares supported tasks, input modalities, output modalities and features; unsupported combinations fail before backend execution.

### 7. Observable execution

Queueing, load, prompt/prefill, TTFT, decode, total latency, output tokens, throughput, cache behavior, failures and resource footprint use precise semantics. A chunk count is never presented as a token count.

### 8. Reproducible inference identity

A result can be tied to model artifact identity, revision/hash, explicit quantization, backend and version, effective serving-configuration digest and hardware profile.

Local LLM Server is the source of truth for identity it can observe about a resident runtime. It exposes that identity through a stable, path-free public contract rather than requiring downstream evaluators to infer semantics from model filenames, private paths or convenience response fields.

The current public contract is specified in [`runtime-identity-api.md`](runtime-identity-api.md). Incompatible wire-format changes require a new protocol version.

### 9. Local privacy by default

The default runtime path does not fetch remote media, send prompts to remote inference or leave avoidable sensitive temporary files. Network or remote-code exceptions require explicit configuration.

Public evidence/identity surfaces must not expose model paths, download URLs, credentials, prompt/output content or host/user identity.

### 10. Bounded shutdown and recovery

Cancellation, disconnect, failure, draining and shutdown are normal lifecycle paths. A stuck backend must not make server shutdown unbounded.

## Canonical product architecture

```text
Applications / external evaluators
    |
    v
Public API / Local SDK
    |
    +--> OpenAI-compatible inference
    +--> public execution identity
    +--> dynamic status/evidence
    |
    v
Canonical InferenceRequest
    |
    +--> Capability validation
    +--> Policy validation
    +--> RequestScheduler
              |
              v
        ResourceManager
              |
              v
        RuntimeManager
        /     |      \
       v      v       v
 llama.cpp   MLX     specialist workers
  worker    worker    (VLM / ASR / future)
       \      |       /
        +-----+------+
              |
        Artifact Store
              |
        Observability / Evidence
```

Detailed migration boundaries belong in [`architecture-evolution-plan.md`](architecture-evolution-plan.md).

## Canonical request model

The internal contract should evolve from backend-shaped chat payloads toward a task-aware request:

```text
InferenceRequest
- request_id
- task
- model / route
- input
- generation_options
- output_constraints
- priority
- deadline
- metadata
```

Initial task vocabulary should cover:

- `chat`
- `structured_generation`
- `vision_language`
- `transcription`

Future task types such as embeddings, reranking and speech synthesis should extend the contract without forcing unrelated work through chat-completion semantics.

## Capability model

Each configured model/runtime should expose a capability descriptor rather than a single `multimodal` boolean:

```yaml
capabilities:
  tasks: [chat, structured_generation]
  input_modalities: [text]
  output_modalities: [text]
  features:
    streaming: true
    json_object: true
    json_schema: false
    tools: false
    reasoning: true
```

A vision-language model may declare `input_modalities: [text, image]`. An ASR model may declare `tasks: [transcription]`, `input_modalities: [audio]`, `output_modalities: [text]` without pretending to be a text-chat model.

## Runtime and memory model

The server should allow **zero resident models**. Residency is an optimization/state choice rather than a requirement for server existence.

The target runtime lifecycle is:

```text
registered
  -> artifact available
  -> cold
  -> loading + resource reservation
  -> resident/ready
  -> active request leases
  -> idle/warm
  -> draining
  -> stopped/cold
```

The global resource manager should own:

- system memory observation;
- configured AI memory budget and safety headroom;
- estimated and observed model footprint;
- active KV/prompt-cache budget when exposed by the backend;
- load-time reservation;
- memory-pressure classification;
- pinned versus evictable residency;
- admission and explicit resource-exhausted decisions.

Automatic LRU/TTL eviction is a later policy over this foundation, not a substitute for resource accounting.

## Backend strategy

Backends are adapters with capability and observability mappings.

Preferred direction:

- `llama-server` or a controlled llama.cpp worker for GGUF when backend-native batching/cache/metrics are useful;
- process-isolated MLX text serving when dynamic unload/reload is required;
- process-isolated MLX-VLM serving for image-language workloads;
- specialist ASR worker/service for transcription rather than forcing ASR through a generic audio-chat prompt.

An in-process mode may remain available for embedding/minimal overhead, but the product-grade daemon path should favor ownership boundaries that make cleanup and failure isolation verifiable.

## Audio boundary

Audio must distinguish at least two products/tasks:

1. **ASR/transcription:** audio -> text through `/v1/audio/transcriptions` or equivalent canonical task;
2. **audio-language reasoning:** audio + text -> text through a multimodal language model.

Temporary media lifecycle is owned by the server/helper that creates it and must be deterministic. Large media should avoid unnecessary full-file duplication and base64 expansion where a streamed/multipart local boundary is available.

## Observability target

Normalized request metrics should include, when source data supports them:

- queue wait;
- model load/startup;
- prompt/prefill tokens and duration;
- TTFT;
- output tokens and decode duration;
- output tokens/second;
- total latency;
- cancellation/termination reason;
- response/prompt-cache result where applicable;
- resident and peak memory;
- backend/runtime errors mapped to typed public errors.

Unavailable metrics remain unavailable; they are never inferred from unrelated counters.

Dynamic operational telemetry and frozen execution identity are separate contracts. Request counters/phases/throughput belong to status/metrics surfaces; stable model/runtime/config/hardware identity belongs to the public identity surface.

## Public execution identity target

External evaluators need a stable contract that describes what is actually resident without importing server internals.

The identity surface must:

- expose a versioned protocol identifier;
- support multiple resident runtimes and identify the default route when present;
- expose model ID, explicit revision, verified artifact digest and quantization when known;
- expose effective backend name/version and an allowlisted runtime-configuration digest;
- expose bounded non-identifying hardware characteristics;
- distinguish partial identity from evidence-grade verified fingerprint state;
- preserve unknown values instead of deriving them from suggestive filenames or paths;
- never expose private artifact paths, download URLs, credentials, content, hostname or mutable request counters.

The first shared consumer is AI Performance Lab. The producer must remain consumer-agnostic and must not depend on Performance Lab packages or benchmark concepts.

## Evidence and benchmark target

The harness should support reproducible runs keyed by:

- exact artifact identity;
- backend + version;
- resolved configuration digest;
- task/test-set version;
- hardware profile;
- random seed where relevant;
- cold/warm classification.

Benchmark output should make it possible to answer:

> For this workload on this hardware, which local model/runtime provides the best quality/resource/latency trade-off?

The UX target is specified in [`ux-ui-implementation-plan.md`](ux-ui-implementation-plan.md).

## Security and privacy boundary

Default policy:

- bind public runtime to loopback;
- no cloud inference fallback;
- no remote media fetch;
- `trust_remote_code` disabled unless explicitly approved per model/source;
- administrative mutation endpoints opt-in;
- no prompt/output persistence in normal operational telemetry;
- no private paths or sensitive media in shared logs/reports/public identity;
- model downloads use explicit trusted source and future immutable integrity metadata.

Network-shared deployment and authentication are a separate opt-in concern and must not weaken local defaults.

## UX positioning

The UI should communicate the control-plane mental model:

- **Overview:** health, workload, residency and pressure;
- **Models & Runtimes:** artifacts, capabilities, state, memory and lifecycle;
- **Endpoints / Playground:** task execution and integration contract;
- **Benchmark & Evaluation:** evidence-based model selection;
- **System / Diagnostics:** hardware, logs, runtime events and privacy-safe evidence.

Brand and product language belong in [`brand-guidelines.md`](brand-guidelines.md).

## Non-goals for the active program

- reimplementing backend tensor kernels;
- inventing a universal model format;
- silent quality-based model substitution;
- cloud fallback hidden behind the local model name;
- arbitrary distributed cluster serving;
- multi-tenant internet-facing serving as the default deployment;
- presenting mock/illustrative telemetry as live product data;
- claiming memory/performance/identity completeness without representative evidence;
- embedding Performance Lab-specific benchmark logic in the serving runtime.

## Cross-cutting acceptance criteria

Every coherent implementation slice must satisfy the applicable criteria below.

### Contracts

- orchestration does not depend on UI state;
- backend-native objects remain inside adapters/workers;
- capability/task checks happen before backend execution;
- public error semantics remain bounded and typed enough for UI/client behavior;
- incompatible public identity schema changes use a new protocol version.

### Lifecycle

- load, admission, lease, cancellation, drain, unload and shutdown ownership are explicit;
- cleanup remains safe after success, failure and disconnect;
- zero-resident server state is valid;
- no automatic policy changes default model identity silently.

### Resources

- resource decisions distinguish estimate from observation;
- unavailable values remain explicit;
- eviction never targets an active leased runtime;
- resource exhaustion fails explicitly rather than relying on OOM as flow control.

### Identity and evidence

- runtime identity reuses the same artifact/backend/config/hardware primitives that own server-side truth;
- effective config display and config digest use the same safe allowlist;
- quantization is explicit metadata rather than downstream filename inference;
- missing revision/hash/version remains missing;
- public identity distinguishes partial from verified evidence;
- consumers can freeze a coherent identity before an evaluation run without accessing private paths.

### Privacy

- inference content stays out of ordinary telemetry and public identity;
- local media cleanup is deterministic;
- remote media/code/network behavior requires explicit policy;
- public identity/log/evidence surfaces do not expose private artifact paths, download URLs, credentials, hostname or user identity.

### Validation

- changed owners have deterministic unit/integration coverage;
- cross-domain contracts have end-to-end tests with deterministic fakes;
- cross-repository protocol consumers are validated against the same explicit protocol version;
- hardware-dependent claims remain labelled evidence-pending until measured;
- UX uses source-backed states and explicit unavailable states.

## Delivery boundary

The active program is complete when the control-plane architecture, resource-aware lifecycle, truthful capability/observability/identity contracts and redesigned primary UX surfaces satisfy [`definition-of-done.md`](definition-of-done.md). Future cloud routing, broader task families and advanced acceleration may build on this boundary without redefining its local-first guarantees.

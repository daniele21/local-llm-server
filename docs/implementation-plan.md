# Korgis / Local LLM Server — target product specification

Status: active
Document type: target-specification
Owner: repository
Canonical scope: target.repository
Read when: a change affects repository-wide positioning, product behavior, runtime boundaries or acceptance criteria
Last reviewed: 2026-08-31

This document defines the repository-level product target. It intentionally does not track implementation progress; integrated reality belongs in [`current-state.md`](current-state.md), capability sequencing in [`roadmap.md`](roadmap.md), architecture migration in [`architecture-evolution-plan.md`](architecture-evolution-plan.md), and focused UX behavior in [`ux-ui-implementation-plan.md`](ux-ui-implementation-plan.md).

## Product target

Korgis, implemented by Local LLM Server, should be positioned and engineered as:

> **A resource-aware runtime control plane for reliable multi-model local AI applications.**

The category is **Local AI Application Runtime**: infrastructure for applications that need several specialist local AI runtimes to coexist on constrained hardware behind one stable application-facing boundary.

The primary outcome is not merely “run a model locally.” It is:

> **Ship a local-first AI application without embedding model lifecycle, memory arbitration, backend-specific scheduling, process ownership and reproducibility logic into the application itself.**

The short product thesis is:

```text
One device. Many specialist models. Predictable resources.
```

Local LLM Server provides the control plane around specialist text, vision and audio engines while keeping model identity, lifecycle, resource ownership, scheduling, privacy, capabilities and execution evidence explicit.

The project is **not** trying to replace `llama.cpp`, MLX-LM, MLX-VLM, Whisper implementations or other specialist inference engines. Those systems own tensor execution and backend-native optimization. Local LLM Server owns the product-grade orchestration boundary around them.

## Positioning decisions

### Application-first, not model-runner-first

The core user is a developer shipping an application that may need reasoning, vision and transcription simultaneously. Model download and manual chat are supporting workflows, not the product category.

The control plane should therefore increasingly expose application/workload intent rather than forcing every consumer to manually reproduce model load order, residency choices, concurrency limits and cleanup behavior.

### Predictable before automatic

Automation is valuable only when its ownership and failure semantics are explicit. The project prefers a visible admission failure over an operating-system OOM, an explicit cold runtime over an implied resident default, and a declared unsupported task over backend guessing.

Automatic behavior must be built on measured resource/lifecycle foundations. Pressure-triggered eviction, model fallback and other high-impact policies remain disabled unless separately specified and evidenced.

### Orchestrate specialist engines instead of competing with them

Backend-native batching, KV-cache mechanics, tensor allocation and accelerator-specific optimization remain backend responsibilities. Local LLM Server should integrate the strongest specialist engine for a task through a stable adapter/worker contract rather than reimplementing inference breadth.

### Reproducibility is part of serving

A product-grade local runtime should be able to explain what actually executed: model artifact, quantization, backend/version, effective runtime configuration and bounded hardware identity. Execution identity and evidence are first-class runtime concerns, not an afterthought owned only by a benchmark tool.

Evaluation remains an important proof mechanism, but **benchmarking is not the primary product category**. Deep benchmark comparison may live in dedicated consumers such as AI Performance Lab while this repository remains the source of truth for resident execution identity and serving evidence.

### Apple Silicon first as the reference wedge

Apple Silicon is the first reference environment for resource and lifecycle quality because unified memory makes multi-model applications especially sensitive to residency, transient allocation and reclamation behavior.

This is a **reference-quality strategy, not a macOS-only architecture decision**. Backend-neutral contracts, explicit capability metadata and source-labelled evidence remain portable. Claims for Linux, NVIDIA, AMD or other environments must be bounded to evidence actually gathered there.

### Product brand and technical identity

**Korgis** is the product brand. **Local LLM Server** remains the repository/package and technical implementation identity during the brand rollout. The category remains **Local AI Application Runtime** / **runtime control plane**; brand naming does not change runtime contracts, evidence semantics or backend ownership.

**Local LLM Studio** remains the current bundled browser control-plane name until that implemented surface is deliberately migrated to Korgis. The brand rollout must not create a second product-policy implementation or rename technical public contracts without an explicit compatibility decision.

## Mission alignment

The repository exists to make the broader local-first AI thesis operational and measurable:

- sensitive workloads should be able to remain inside an explicit local trust boundary;
- applications should control model lifecycle and exact execution identity rather than depend on opaque remote routing;
- local inference should expose its real resource cost instead of hiding memory pressure;
- several specialist models should be able to share one constrained device without each consumer inventing its own resource manager;
- applications should not be coupled to one inference backend;
- local-first is not local-only: external execution can remain a future explicit policy choice, never a silent dependency or substitution;
- performance, lifecycle and support claims should be backed by reproducible evidence on representative environments.

The practical product loop remains:

```text
Build -> Run locally -> Observe -> Measure -> Compare -> Improve
```

## Primary users

### 1. Local-first application developer

The primary user builds a desktop, mobile-adjacent or local service product that needs one durable local AI boundary without embedding backend-specific model loading, subprocess ownership, cache, concurrency and cleanup logic in the application.

Typical application shape:

```text
meeting / document / creative / developer application
                  |
        +---------+---------+
        |         |         |
        v         v         v
 transcription  reasoning  vision
        |         |         |
        +---------+---------+
                  |
           one constrained device
```

### 2. Local-AI engineer

Needs to understand which runtime/model/configuration is active, how resource budget is allocated, why a request queued or failed, whether a runtime is really stopped, and where performance/resource regressions originate.

### 3. Privacy-sensitive product team

Needs a local execution boundary with explicit network/media trust policy and evidence sufficient to support privacy and local-first product claims.

### 4. Model/runtime evaluator

Needs reproducible execution identity and compatible evidence across model artifacts, backends, configurations and hardware. This user is important but secondary to the application-runtime category.

## Reference application journey

The target application flow is:

1. define the models/tasks the application needs and the resource envelope it is allowed to consume;
2. validate the configuration before expensive model work;
3. inspect a dry-run resource/residency plan before enabling automatic lifecycle behavior;
4. start the control plane in a valid zero-resident state;
5. load or keep resident only the runtimes required by current application policy;
6. route requests through exact task/capability boundaries with bounded admission and deadlines;
7. protect in-flight work from unload through runtime leases;
8. observe queue/resource/lifecycle state without leaking inference content;
9. freeze execution identity when reproducibility matters;
10. unload/shutdown through explicit ownership and cleanup semantics.

The application should not need to know backend worker ports, Python model objects, model-cache internals or backend-specific process trees.

## Application/workload profile target

The main new abstraction required by this positioning is a declarative **Application Profile** (also described as a workload profile until naming is stabilized).

The profile expresses application intent. It does not replace the model registry: the registry owns model/runtime configuration; the application profile composes exact configured models into a workload.

Illustrative target shape:

```yaml
schema_version: 1
application: meeting-assistant

resources:
  memory_budget: 20GB
  headroom: 4GB

roles:
  transcription:
    task: transcription
    model: whisper-small
    residency: pinned
    priority: realtime

  reasoning:
    task: chat
    model: qwen-4b
    residency: warm
    idle_ttl: 10m
    priority: interactive

  vision:
    task: vision_language
    model: qwen-vl-4b
    residency: on_demand
    priority: interactive
```

This example is a target model, not an implemented public schema.

### Profile invariants

- every role resolves to an explicit configured model/runtime identity;
- no role silently substitutes a different model because memory is tight or a runtime is unavailable;
- any future fallback list must be explicitly configured, ordered, observable and represented in execution identity;
- `pinned`, `warm` and `on_demand` describe residency intent, not proof that a model fits memory;
- resource planning distinguishes configured limits, estimates, observations and unavailable evidence;
- validation/planning must be possible without loading every model;
- automatic lifecycle actions must preserve active leases and exact default/role semantics;
- application policy must remain backend-neutral;
- the profile must have an explicit schema/version before it becomes a compatibility promise.

## Resource planner target

Before automatically loading or evicting models, the control plane should be able to answer:

> “Can this application profile plausibly fit on this device under the configured policy, and what evidence supports that answer?”

The planner should expose, where available:

- configured device/application budget;
- safety headroom;
- currently resident committed bytes;
- transient reservation envelope;
- per-runtime artifact size;
- estimated load footprint with source/confidence;
- observed historical resident/peak footprint where compatible;
- expected residency state after applying the profile;
- capacity gaps and explicit reasons;
- unknown/unmeasured facts separately from positive fit claims.

A dry-run result is evidence for a policy decision, not a memory-reclamation guarantee.

## Core product promises

### 1. Stable application contract

Applications address tasks and explicit model/runtime identity through a stable API. Backend-native ports, Python objects, model pointers and subprocess details remain implementation details.

### 2. Exact model semantics

If a request or application role names a model, the server either runs that model or returns an explicit failure. It never silently substitutes another local or remote model.

### 3. Explicit lifecycle

Registered, downloaded, cold, loading, ready/resident, draining, stopped and failed are distinct concepts. Downloading does not imply residency; selection/default routing does not imply residency; unload does not delete the artifact.

### 4. Resource-aware admission

Model load and request execution are admitted against an explicit resource budget where enforceable. Memory pressure is a product state, not an operating-system surprise.

### 5. Verifiable ownership and conservative unload

A runtime reported as stopped must no longer be canonically owned as resident by the control plane. Stronger host-memory reclamation claims require the applicable process boundary and representative evidence; in-process close is never silently promoted into such a claim.

### 6. Capability truthfulness

Capabilities are explicit and machine-readable. A runtime declares supported tasks, input modalities, output modalities and features; unsupported combinations fail before backend execution.

### 7. Workload-aware scheduling

Queueing, global/per-runtime concurrency, deadlines and priorities are explicit policy. The control plane coordinates work across specialist runtimes without reimplementing backend-native batching.

### 8. Observable execution

Queueing, load, prompt/prefill, TTFT, decode, total latency, output tokens, throughput, failures and resource footprint use precise semantics. A chunk count is never presented as a token count and an unavailable measurement is never rendered as zero.

### 9. Reproducible inference identity

A result can be tied to model artifact identity, revision/hash, explicit quantization, backend and version, effective serving-configuration digest and bounded hardware profile.

Local LLM Server is the source of truth for identity it can observe about a resident runtime. It exposes that identity through a stable, path-free public contract rather than requiring downstream consumers to infer semantics from filenames or private paths.

The current public contract is specified in [`runtime-identity-api.md`](runtime-identity-api.md). Incompatible wire-format changes require a new protocol version.

### 10. Local privacy by default

The default runtime path does not fetch remote media, send prompts to remote inference or leave avoidable sensitive temporary files. Network or remote-code exceptions require explicit configuration.

Public evidence/identity surfaces must not expose model paths, download URLs, credentials, prompt/output content or host/user identity.

### 11. Bounded shutdown and recovery

Cancellation, disconnect, failure, draining and shutdown are normal lifecycle paths. A stuck backend must not make server shutdown unbounded, and cleanup may affect only resources whose ownership is proven.

## Canonical product architecture

```text
Application
    |
    +--> Application Profile / workload intent (target)
    |          |
    |          v
    |    validation + resource planner
    |          |
    +----------+
    |
    v
Public API / Local SDK / Local LLM Studio
    |
    +--> OpenAI-compatible inference
    +--> task-specific inference
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

The internal contract should remain task-aware rather than forcing every workload through chat semantics:

```text
InferenceRequest
- request_id
- task
- model / explicit route
- input
- generation_options
- output_constraints
- priority
- deadline
- metadata
```

Initial task vocabulary:

- `chat`;
- `structured_generation`;
- `vision_language`;
- `transcription`.

Future task types such as embeddings, reranking and speech synthesis should extend the contract only when a real product/application need exists.

## Capability model

Each configured model/runtime should expose a capability descriptor rather than relying on backend names or filename inference:

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

Application-profile validation should consume the same capability source of truth.

## Runtime and memory model

The server must allow **zero resident models**. Residency is an optimization/policy state rather than a requirement for server existence.

The target lifecycle is:

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

The global resource manager owns:

- configured AI/application memory budget and safety headroom;
- system/resource observations where meaningful;
- resident and transient reservation accounting;
- estimated and observed model footprint as different evidence classes;
- load-time reservation and reconciliation;
- pinned versus policy-evictable residency;
- explicit resource-exhausted decisions.

### Residency modes

The application-runtime target uses three understandable intents:

- `pinned` — expected to remain resident while the profile is active; still manually unloadable when explicitly requested;
- `warm` — may remain resident while useful and may later be eligible for explicit TTL/LRU policy when idle;
- `on_demand` — cold is normal and loading is triggered only by an explicit supported policy/request path.

These modes must not silently override resource admission. A profile that cannot fit must surface that fact rather than relying on OOM or hidden model substitution.

Automatic pressure-triggered eviction remains a separate future decision. Existing explicit LRU/TTL administration does not imply that pressure automation is safe.

## Scheduler target

The scheduler should coordinate application classes rather than only raw endpoint concurrency.

Initial policy vocabulary may include:

- `realtime` — latency-sensitive flows such as interactive transcription where supported;
- `interactive` — user-facing reasoning/vision requests;
- `background` — evaluation, indexing or deferred work.

Priorities do not create unlimited queues or preempt backend execution that cannot truthfully be cancelled. One bounded deadline/timeout budget should span the waits owned by the control plane.

Cross-runtime fairness, per-runtime semaphores and backend-native batching remain separate owners.

## Backend strategy

Backends are specialist adapters with capability, lifecycle and observability mappings.

Preferred direction:

- attributable managed `llama-server`/llama.cpp workers for GGUF when backend-native batching/cache/metrics are useful;
- process-isolated MLX text serving when dynamic unload/reload and strong ownership boundaries justify it;
- process-isolated MLX-VLM for image-language workloads;
- specialist ASR worker/service for transcription rather than forcing ASR through a generic audio-chat prompt;
- in-process modes only where their lower overhead is worth weaker isolation/reclamation semantics and those semantics are explicit.

Backend breadth is not itself a product KPI. A new backend should enter because it unlocks a meaningful application task/device/runtime advantage and can satisfy the common contracts.

## Apple Silicon reference strategy

Apple Silicon is the first environment where the repository should aim for **reference-grade multi-model behavior**.

That means progressively proving, on representative hardware that is actually available:

- simultaneous residency of realistic specialist model combinations;
- admission/accounting under unified-memory constraints;
- load/infer/unload repetition;
- shutdown under concurrent work;
- process ownership and orphan-free cleanup;
- cold/warm application profile transitions;
- compatible resource observations and, only where justified, reclamation behavior;
- latency/throughput only for explicitly exercised model/runtime/device combinations.

The project should publish a support/evidence matrix that distinguishes:

```text
implemented contract
validated deterministic behavior
representative-device observation
production/general safety claim
```

These are never interchangeable.

## Audio boundary

Audio distinguishes at least two tasks:

1. **ASR/transcription:** audio -> text through `/v1/audio/transcriptions` or equivalent canonical task;
2. **audio-language reasoning:** audio + text -> text through a model that explicitly supports that capability.

Temporary media lifecycle is owned by the server/helper that creates it and must be deterministic. Large media should avoid unnecessary full-file duplication/base64 expansion where a streamed or multipart local boundary exists.

## Observability target

Normalized request/runtime metrics should include, when their source supports them:

- queue wait;
- model load/startup;
- prompt/prefill tokens and duration;
- TTFT;
- output tokens and decode duration;
- output tokens/second;
- total latency;
- cancellation/termination reason;
- cache result/usage where applicable;
- resident and peak memory;
- typed backend/runtime failures;
- application role/profile attribution when that contract becomes stable.

Dynamic operational telemetry and frozen execution identity remain separate contracts. Request counters/phases/throughput belong to status/metrics surfaces; stable model/runtime/config/hardware identity belongs to the public identity surface.

## Evidence and evaluation boundary

The server should make reproducible runs possible by exposing/fixing:

- exact artifact identity;
- backend + version;
- resolved configuration digest;
- task/test-set version where evaluation is executed here;
- hardware profile;
- seed where relevant;
- cold/warm classification.

Local LLM Server may retain lightweight evaluation workflows because they are valuable for product verification. Dedicated benchmark products can own richer quality comparison, reporting and experiment management. The serving runtime must not become coupled to a particular evaluator.

## Security and privacy boundary

Default policy:

- bind public runtime to loopback;
- no cloud inference fallback;
- no remote media fetch;
- remote model/tokenizer code requires explicit trust;
- administrative mutation endpoints are opt-in;
- no prompt/output persistence in normal operational telemetry;
- no private paths, credentials or sensitive media/content in shareable identity/evidence;
- model downloads use explicit trusted sources and integrity metadata where available.

Network-shared deployment and authentication are a separate opt-in concern and must not weaken local defaults.

## UX positioning

Local LLM Studio should increasingly communicate an **application runtime** mental model rather than a collection of backend controls:

- **Overview:** application health, active workload, resource envelope, residency and pressure;
- **Applications / Profiles** (target): declared roles, resource plan, validation failures and effective policy;
- **Models & Runtimes:** artifacts, capabilities, residency state, memory and lifecycle;
- **Endpoints / Playground:** task execution and integration contract;
- **Evaluation:** reproducible evidence, not a generic leaderboard claim;
- **System / Diagnostics:** hardware, scheduler, runtime events, ownership and privacy-safe evidence.

A future profile UX should first be read/validate/plan oriented. Automatic lifecycle actions should only become prominent when their semantics and recovery paths are proven.

Brand and visual language belong in [`brand-guidelines.md`](brand-guidelines.md).

## Explicit non-goals

The positioning is stronger when the project deliberately does **not** optimize for these categories:

- desktop chat UX as the primary product;
- the largest model catalog or one-click discovery experience;
- reimplementing backend tensor kernels;
- inventing a universal model format;
- a generic RAG/agent/MCP application framework;
- silent quality-based model substitution;
- hidden cloud fallback behind a local route;
- arbitrary distributed cluster serving;
- multi-tenant internet-facing serving as the default deployment;
- backend count as a success metric;
- presenting mock/estimated telemetry as observed truth;
- claiming memory/performance/identity completeness without representative evidence;
- embedding Performance Lab-specific benchmark logic in the serving runtime.

## Product success criteria

The application-runtime positioning becomes materially true when a representative application can:

1. define at least three specialist roles such as transcription, reasoning and vision using explicit configured models;
2. validate task/capability compatibility before loading models;
3. request a resource plan that distinguishes known, estimated, observed and unavailable evidence;
4. start with zero resident runtimes and reach the intended residency state through explicit policy;
5. run concurrent cross-role work within bounded scheduler/resource policy;
6. reject unsafe capacity requests explicitly rather than relying on OOM;
7. preserve active work from unsafe unload;
8. return to a clean bounded lifecycle state without orphaned owned resources;
9. expose path-free execution identity sufficient to reproduce or compare the exercised configuration;
10. complete the workflow on at least one representative Apple Silicon environment with retained claim-scoped evidence;
11. remain usable through the stable HTTP integration boundary without requiring application code to know backend implementation details.

## Delivery sequence

The product should evolve in this order:

```text
current trustworthy control plane
        |
        v
application profile schema + validation
        |
        v
resource planner / dry run
        |
        v
explicit residency policy + on-demand lifecycle
        |
        v
workload-aware scheduling / role integration
        |
        v
reference-grade Apple Silicon application evidence
        |
        v
stable developer integration + application-runtime release gate
```

The detailed milestone sequencing and acceptance outcomes are owned by [`roadmap.md`](roadmap.md).

## Cross-cutting acceptance criteria

### Contracts

- orchestration does not depend on UI state;
- backend-native objects remain inside adapters/workers;
- application roles map to explicit configured runtime identities;
- capability/task checks happen before backend execution;
- public error semantics remain bounded and typed enough for UI/client behavior;
- incompatible public identity or future application-profile schemas use explicit versioning.

### Lifecycle

- load, admission, lease, cancellation, drain, unload and shutdown ownership are explicit;
- cleanup remains safe after success, failure, disconnect and partial initialization;
- zero-resident server state is valid;
- no automatic policy changes model/default/role identity silently.

### Resources

- resource decisions distinguish configured limits, estimates, observations and unavailable evidence;
- queued work does not reserve expensive transient resources before the owning stage;
- eviction never targets an active leased runtime;
- resource exhaustion fails explicitly rather than relying on OOM as flow control.

### Identity and evidence

- runtime identity reuses the same artifact/backend/config/hardware primitives that own server-side truth;
- effective config display and config digest use the same safe allowlist;
- quantization is explicit metadata rather than filename inference;
- missing revision/hash/version remains missing;
- public identity distinguishes partial from verified evidence;
- consumers can freeze coherent identity without accessing private paths.

### Privacy

- inference content stays out of ordinary telemetry/public identity;
- local media cleanup is deterministic;
- remote media/code/network behavior requires explicit policy;
- public identity/log/evidence surfaces do not expose private artifact paths, download URLs, credentials, hostname or user identity.

### Validation

- changed owners have deterministic unit/integration coverage;
- cross-domain application-profile/resource/scheduler contracts have assembled E2E coverage before being advertised;
- hardware-dependent claims remain evidence-pending until measured;
- Apple Silicon reference claims retain exact model/runtime/device procedure identity;
- UX uses source-backed states and explicit unavailable states;
- real-human accessibility/usability evidence remains distinct from deterministic CI.

## Delivery boundary

The current 0.4/L2 program remains governed by the existing product-grade candidate gates. The application-runtime program builds on that trustworthy baseline rather than redefining it retroactively.

The positioning program is complete when application profiles, resource planning, explicit residency/on-demand policy, workload-aware scheduling, developer integration and reference-device evidence make it realistic for an external application to delegate multi-model local runtime ownership to Local LLM Server without giving up exact model semantics, privacy or evidence quality.

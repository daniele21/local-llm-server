# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Read when: determining the integrated baseline, open blockers or immediate next implementation block
Last reviewed: 2026-08-15

This is the single operational ledger for the Local LLM Server evolution program. Target behavior belongs in [`implementation-plan.md`](implementation-plan.md) and focused specifications. Capability sequencing and parallel work belong in [`roadmap.md`](roadmap.md).

## Active program

The active direction is to evolve Local LLM Server from a useful multi-backend local model server into a **resource-aware, observable local AI control plane and harness** for product-grade text, vision and audio workloads.

The positioning target is:

> One trustworthy local control plane that knows what can run, what is resident, what resources it consumes, how requests are scheduled, how it performed, and which exact runtime/artifact produced each result.

The server should orchestrate specialized inference runtimes rather than reimplement their tensor execution.

## Integrated baseline

### Public product boundary

Integrated today:

- OpenAI-compatible `/v1/chat/completions` API;
- streaming and non-streaming chat completions;
- explicit routing by registry key or model ID;
- multiple simultaneously resident runtimes behind one public server port;
- loopback-first default binding;
- opt-in administrative API;
- bundled Local LLM Studio web UI;
- Python client helpers for text, image and audio-oriented calls.

### Runtime lifecycle

Integrated today:

- `ModelRuntimeManager` owns loaded runtimes;
- `READY`, `DRAINING`, `STOPPED` and `FAILED` state vocabulary exists;
- per-runtime admission semaphore;
- request leases prevent unload while inference is active;
- reload preserves the previous runtime if replacement load fails;
- aliases are validated for collisions;
- managed subprocesses use bounded log tails and terminate process groups on shutdown;
- private subprocess ports are assigned per managed backend.

Known limitation:

- lifecycle removal is stronger than memory reclamation for in-process backends because current `LlamaCppEngine.close()` and `MLXEngine.close()` do not yet provide a demonstrated release guarantee.

### Model sources and registry

Integrated today:

- built-in plus user YAML registry;
- LM Studio model discovery;
- Hugging Face cache discovery for supported MLX paths;
- managed GGUF download with `.part`, resume, retry and atomic rename;
- MLX snapshot completeness validation;
- multimodal/projector validation;
- model modality and thinking-mode validation.

Known limitations:

- artifact identity is not yet cryptographically pinned as a first-class runtime contract;
- `size_gb` metadata is descriptive and not used for resource admission;
- the registry currently imports ClosedRoom-specific configuration directly, coupling infrastructure to one consumer application.

### Modalities

Integrated today:

- text generation through `llama-cpp-python` and MLX-LM;
- GGUF multimodal execution through managed `llama-server`;
- MLX vision-language execution through managed `mlx_vlm.server`;
- image helpers with local data-URL encoding and size/type validation;
- audio preprocessing and OpenAI-style `input_audio` message construction.

Known limitations:

- current capability representation is primarily `modalities`, not task + input/output capability contracts;
- audio transcription is currently modeled through multimodal chat helpers rather than a canonical ASR task endpoint;
- audio preprocessing creates a temporary WAV with no deterministic cleanup in the helper path;
- large audio paths may incur redundant decoded/WAV/base64/JSON memory copies.

### Observability

Integrated today:

- `/health` and `/status` surfaces;
- per-runtime active-request state;
- bounded log stream buffer;
- response usage normalization when backend usage exists;
- deterministic response cache for greedy non-streaming calls;
- basic runtime timing/status fields.

Known limitations:

- `tokens_generated` currently tracks output chunks for compatibility and is not a truthful token counter;
- queue wait, prompt/prefill, TTFT, decode, memory peak, cache reuse and termination reason are not normalized across backends;
- there is no stable runtime fingerprint tying result to artifact hash, backend version, resolved config and hardware profile.

### Testing and CI

Integrated today:

- unit/regression coverage for runtime routing, lifecycle, reload/unload races, multi-model requests, modality checks, image/audio helpers, config, model sources and backend adapters;
- CI matrix across Python 3.10, 3.11 and 3.12;
- Ruff lint job.

Critical gap:

- the CI test command currently ends in `|| true`, so a failing pytest suite can still produce a green job. This must be removed before later reliability claims are meaningful.

### UX/UI

Integrated today:

- Local LLM Studio web surface;
- Chat Studio;
- model/runtime configuration controls;
- live logs;
- integration examples;
- Swagger/OpenAPI access.

Target UX has been redesigned conceptually around four primary product questions:

1. **Overview** — is local AI healthy, what is resident and what is under resource pressure?
2. **Models & Runtimes** — what is installed, resident/cold/loading/stopped, and why?
3. **Playground / Endpoints** — can this task run through this capability contract?
4. **Benchmark & Evaluation** — which model/runtime is actually best for this workload on this hardware?

The detailed target belongs in [`ux-ui-implementation-plan.md`](ux-ui-implementation-plan.md). Current implementation progress belongs in [`ux-ui-implementation-progress.md`](ux-ui-implementation-progress.md).

## Open P0 blocks

1. **CI truthfulness** — remove test failure suppression and establish deterministic blocking gates.
2. **Resource ownership foundation** — introduce global resource accounting/admission before automatic residency/eviction work.
3. **Unload semantics** — establish a product-grade memory reclamation boundary, with process-isolated workers as the preferred direction where in-process release cannot be proved.
4. **Capability model** — separate task, input modalities, output modalities and backend features.
5. **Privacy hardening** — deterministic temporary media cleanup; remote media disabled by default; remote code trust opt-in only.
6. **Consumer decoupling** — remove ClosedRoom-specific registry loading from core infrastructure.
7. **UX design-system foundation** — encode stable visual/product tokens before implementing the redesigned screens.

## Immediate next block

Proceed with the **Foundation Batch** from [`roadmap.md`](roadmap.md):

- make CI test failures blocking;
- establish canonical resource/capability contracts without yet changing routing behavior;
- remove infrastructure-to-ClosedRoom configuration coupling;
- implement privacy-safe defaults for remote code/media/temp audio;
- create the UI design-system shell and navigation structure against explicit placeholder/unavailable states, not invented runtime metrics.

These tasks are intentionally selected because they can run in parallel with limited contract overlap.

## Current blockers and dependencies

- Automatic eviction must not begin until resource accounting and unload semantics are defined.
- Memory-budget UI must not present authoritative values until the resource observation contract exists.
- Benchmark comparisons must not claim token throughput until metric semantics are corrected.
- ASR UX should not be finalized until the canonical transcription task/API ownership is decided.
- Runtime fingerprint UI depends on artifact identity, backend metadata and hardware-profile contracts.
- Any cloud-routing/fallback feature is deferred until local execution, capability and privacy boundaries are explicit.

## Evidence boundary

Passing unit tests or mock-backed UI tests establishes merge readiness only for the covered contract. Claims about memory reclamation, model residency, throughput, latency, thermal behavior or Apple unified-memory behavior require representative hardware evidence.

## Update rule

When any item above changes in integrated reality, update this file in the same pull request. Do not use this file as a historical changelog: remove resolved blockers, move durable target behavior to the owning specification, and keep only the current baseline plus immediate next block.

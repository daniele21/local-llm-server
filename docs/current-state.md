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

The server orchestrates specialized inference runtimes rather than reimplementing their tensor execution.

## Integrated baseline

### Repository reliability and delivery

Integrated:

- pytest failures are blocking rather than suppressed;
- deterministic CI runs on Python 3.10, 3.11 and 3.12;
- CI installs the deterministic Hugging Face test dependency required by existing source-resolution tests;
- Ruff is blocking for syntax and high-confidence correctness rules (`E9,F63,F7,F82`);
- the program integration line can be validated cumulatively;
- pre-existing broad Ruff style/modernization debt is intentionally not hidden, but is not part of the current correctness gate.

Current evidence boundary:

- deterministic CI is merge evidence only;
- real runtime, memory, throughput and hardware claims still require representative physical hardware.

### Public product boundary

Integrated:

- OpenAI-compatible `/v1/chat/completions` API;
- streaming and non-streaming chat completions;
- explicit routing by registry key or model ID;
- multiple simultaneously resident runtimes behind one public server port;
- loopback-first default binding;
- opt-in administrative API;
- bundled Local LLM Studio web UI;
- Python client helpers for text, image and audio-oriented calls.

New Batch 1 foundation:

- backend-neutral core types now define `TaskType`, `InferenceRequest`, `InferenceResult`, generation options, output constraints, terminal reasons and typed errors;
- a compatibility translator can map current OpenAI/legacy chat payloads into canonical requests;
- canonical task vocabulary currently covers chat, structured generation, vision-language and transcription.

Remaining boundary gap:

- the existing HTTP request path does not yet execute through the canonical request translator; until that wiring lands, the new types are a stable foundation rather than the sole execution path.

### Runtime lifecycle

Integrated:

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

Integrated:

- built-in plus user YAML registry;
- generic opt-in external YAML/JSON registry layers through explicit paths or `LOCAL_LLM_REGISTRY_PATHS`;
- precedence is built-in < external layers < user registry;
- core infrastructure no longer reads or names ClosedRoom-specific Application Support state;
- LM Studio model discovery;
- Hugging Face cache discovery for supported MLX paths;
- managed GGUF download with `.part`, resume, retry and atomic rename;
- MLX snapshot completeness validation;
- multimodal/projector validation;
- model modality and thinking-mode validation.

Known limitations:

- artifact identity is not yet cryptographically pinned as a first-class runtime contract;
- `size_gb` metadata is descriptive and not used for resource admission.

### Privacy and media lifecycle

Integrated:

- `trust_remote_code` is fail-closed by default and requires explicit config/environment opt-in;
- the trust decision is propagated explicitly into MLX tokenizer configuration rather than relying on backend defaults;
- `allow_remote_media` is fail-closed by default;
- a pure media-policy validator rejects HTTP(S) image/audio references unless explicitly allowed;
- generated temporary WAV files owned by audio-message preparation are removed deterministically;
- tests cover fail-closed defaults, opt-in behavior and temporary-file cleanup.

Remaining privacy gap:

- the HTTP inference path has not yet wired the media-policy validator before backend execution. The policy exists and is tested, but server enforcement is not complete until that integration lands.

### Modalities and capabilities

Integrated:

- text generation through `llama-cpp-python` and MLX-LM;
- GGUF multimodal execution through managed `llama-server`;
- MLX vision-language execution through managed `mlx_vlm.server`;
- image helpers with local data-URL encoding and size/type validation;
- audio preprocessing and OpenAI-style `input_audio` message construction;
- canonical task vocabulary distinguishes transcription from audio-language/chat intent.

Known limitations:

- registry capability representation is still primarily `modalities` plus thinking/backend metadata rather than task + input/output + feature contracts;
- audio transcription is not yet exposed as a first-class canonical ASR API;
- large audio paths may incur redundant decoded/WAV/base64/JSON memory copies.

### Observability

Integrated:

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

### UX/UI and positioning

Integrated:

- Local LLM Studio web surface with chat, model/runtime configuration, logs, examples and Swagger;
- shared `design-system.css` with brand/surface/status tokens, dark/light semantics, typography, spacing, radius and focus/reduced-motion foundations;
- reusable card, button, field, metric, status, empty-state and table primitives;
- positioning now describes Local LLM Server as a **resource-aware local AI control plane for product-grade inference**;
- README explicitly states that the product orchestrates specialist runtimes rather than replacing them;
- README distinguishes current integrated capability from roadmap targets.

Known UX limitations:

- existing product screens have not yet migrated to the new information architecture or shared primitives;
- memory budget, capability, benchmark and fingerprint UI remain dependency-gated by source contracts;
- there is no formal visual-regression/accessibility matrix yet.

## Batch 1 completion state

| Task | Status | Integrated outcome | Remaining work |
| --- | --- | --- | --- |
| A1 — truthful CI | DONE | blocking pytest matrix + correctness Ruff gate | broader historical Ruff debt later |
| A2 — privacy/security defaults | PARTIAL | remote-code/media fail-closed policy + temp cleanup | enforce media policy in HTTP/canonical request path |
| A3 — consumer decoupling | DONE | no ClosedRoom-specific core registry read | consumer integration stays external |
| C1 — canonical request vocabulary | PARTIAL | core contracts + compatibility translator | route existing HTTP path through translator |
| E1 — design-system foundation | PARTIAL | tokens/primitives loaded by Studio | migrate shell/screens + visual/accessibility evidence |
| F1 — positioning | DONE | README/package description aligned | future promotion only as capabilities actually ship |

## Immediate next block

Proceed with **Batch 2** from [`roadmap.md`](roadmap.md) using isolated ownership boundaries.

Parallel streams that can start together:

1. **B1 Resource observation contract** — system/hardware snapshot, runtime resource profile, estimate vs observation, budget/headroom and unavailable semantics.
2. **C2 Capability descriptor** — tasks, inputs, outputs and feature flags with registry migration/validation.
3. **D1 Metric vocabulary** — exact lifecycle/latency/token/resource terminology and unavailable semantics.
4. **E2 Application shell/navigation** — new control-plane information architecture built on the integrated design-system foundation using only current source-backed values.
5. **D3a Artifact identity foundation** — content hash/revision/source identity contract without waiting for final metric/hardware fingerprint assembly.
6. **A2/C1 request-path integration** — one exclusive `server.py` stream that translates the current request into the canonical request and applies media policy before backend execution.

### Parallelization constraint

Do **not** run separate A2 and C1 branches against `server.py`. Their remaining work shares the same request normalization/execution boundary, so it is one coherent integration slice. B1, C2, D1, E2 and D3a should avoid `server.py` wherever possible and can progress concurrently.

## Current blockers and dependencies

- B2 ResourceManager waits for B1 resource observation types.
- Automatic eviction waits for B2 admission plus demonstrated unload/reclamation semantics.
- Memory-budget UI must not present authoritative values until B1/B2 exist.
- C3 first-class transcription waits for C2 capability contracts and completion of the canonical request boundary.
- Final metric labels and benchmark comparisons wait for D1/D2 normalization; chunk counts must not be presented as truthful token throughput.
- Full runtime fingerprint waits for artifact identity, backend/config identity and hardware-profile contracts.
- Benchmark execution comparisons wait for stable metric semantics and execution identity.
- Any cloud-routing/fallback feature remains deferred until local execution, capability and privacy boundaries are explicit.

## Evidence boundary

Passing unit tests or mock-backed UI tests establishes merge readiness only for the covered contract. Claims about memory reclamation, model residency, throughput, latency, thermal behavior or Apple unified-memory behavior require representative hardware evidence.

## Update rule

When any item above changes in integrated reality, update this file in the same integration change. Do not use this file as a historical changelog: remove resolved blockers, move durable target behavior to the owning specification, and keep only the current baseline plus immediate next block.

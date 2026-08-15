# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Read when: determining the integrated baseline, open blockers or immediate next implementation block
Last reviewed: 2026-08-15

This is the single operational ledger for the Local LLM Server evolution program. Target behavior belongs in [`implementation-plan.md`](implementation-plan.md); sequencing and parallel work belong in [`roadmap.md`](roadmap.md).

## Active direction

Local LLM Server is evolving into a **resource-aware, observable local AI control plane and evaluation harness** for product-grade text, vision and audio workloads. The server orchestrates specialist runtimes rather than reimplementing their inference engines.

## Integrated baseline

### Delivery and repository discipline

- pytest is blocking on Python 3.10/3.11/3.12;
- CI no longer suppresses test failures;
- Ruff blocks syntax and high-confidence correctness errors;
- pre-existing style/modernization debt remains separate from the correctness gate;
- the integration branch is validated through cumulative PRs;
- unit/CI evidence is merge evidence only, not physical-hardware performance evidence.

### Product/API foundation

Existing public behavior remains:

- OpenAI-compatible `/v1/chat/completions` with streaming/non-streaming responses;
- explicit registry-key/model-ID routing;
- multiple resident runtimes on one server;
- loopback-first binding and opt-in admin routes;
- Python client helpers and Local LLM Studio.

New canonical foundation now integrated:

- backend-neutral `TaskType`, `InferenceRequest`, `InferenceResult`, generation/output contracts, terminal reasons and typed errors;
- compatibility translator from current OpenAI/legacy request shapes;
- `request_pipeline.py` that canonicalizes requests, applies remote-media policy, checks current modality compatibility and produces bounded typed public errors.

Remaining API gap:

- `server.py` still executes through its historical parser. The new request pipeline is tested and integrated but has not yet replaced that duplicate route logic.

### Privacy and consumer boundaries

Integrated:

- core registry no longer reads or names ClosedRoom-specific Application Support state;
- external registry layers are explicit YAML/JSON inputs with built-in < external < user precedence;
- `trust_remote_code=false` by default with explicit opt-in;
- MLX tokenizer trust receives the resolved policy explicitly;
- `allow_remote_media=false` by default;
- HTTP(S) media validator rejects remote media unless explicitly allowed;
- generated temporary WAV files owned by preprocessing are cleaned deterministically.

Remaining privacy gap:

- route-level enforcement becomes complete only when `server.py` calls the integrated request pipeline.

### Resource observation foundation

Integrated in `resources.py`:

- `ResourceValue` distinguishes `measured`, `estimated`, `configured` and `unavailable`;
- unavailable data is represented as `None`, never fake zero;
- `SystemResourceSnapshot` and `RuntimeResourceProfile` contracts;
- explicit `ResourceBudget` limit/headroom semantics;
- `ResourcePressure` vocabulary and deterministic classification;
- observer protocol;
- best-effort Linux standard-library memory/RSS adapter;
- deterministic tests for budget, pressure and source semantics.

Remaining B1 work:

- add trustworthy Apple/macOS host and unified-memory observation where available;
- connect observations to runtime lifecycle/evidence rather than only exposing the contract;
- representative hardware validation remains required.

B2 ResourceManager contract work is now unblocked because the reservation/budget layer can consume B1 types without waiting for every platform adapter.

### Capability foundation

Integrated in `core/capabilities.py`:

- task set, input/output modality set and feature set;
- conservative legacy-registry translation;
- first-class `supports(request)` decision;
- client-safe stable serialization;
- validation such as image requirement for vision-language and audio requirement for transcription;
- audio modality alone does **not** imply first-class transcription support.

Remaining C2 work:

- add explicit capability fields to registry validation/migration;
- expose capability descriptors through model/catalog API sources;
- use capability rejection in the canonical request path before backend execution.

### Observability vocabulary

D1 foundation is integrated:

- admitted/queued/started/first-output/completed/failed/cancelled phase vocabulary;
- queue/load/prefill/TTFT/decode/total durations;
- input/output token counts kept distinct from output chunk counts;
- token/sec and chunk/sec kept as separate units;
- cache/load classification;
- unsupported metrics serialize as unavailable, not zero;
- public metric serialization excludes prompts/output.

The historical runtime counter named `tokens_generated` is still compatibility debt; D2 adapters must stop treating output chunks as true tokens.

### Artifact identity

D3a foundation is integrated:

- source kind and verification state;
- path-free stable serialization;
- explicit SHA-256 verification for concrete local files;
- stable identity key;
- Hugging Face source/revision metadata without falsely claiming directory verification;
- expensive hashing is explicit, not performed on every request/UI refresh.

Remaining D3 work:

- backend version identity;
- resolved configuration digest;
- hardware profile;
- final runtime fingerprint assembly and evidence linkage.

### Runtime lifecycle

Existing lifecycle remains:

- `ModelRuntimeManager` owns loaded runtimes;
- leases prevent unload while requests are active;
- per-runtime admission semaphore;
- reload preserves the old runtime if replacement load fails;
- managed subprocesses use bounded logs and process-group termination.

Major remaining differentiation:

- B2 resource-aware admission;
- B3 demonstrable memory reclamation/worker boundary;
- B4 zero-resident semantics;
- B5 bounded scheduling/deadlines/cancellation;
- B6 pin/LRU/TTL eviction.

### UX/UI

Integrated:

- shared design-system tokens/primitives;
- incremental control-plane shell module;
- top-level destinations now exist for Overview, Models & Runtimes, Endpoints, Playground, Benchmark & Evaluation, System/Diagnostics and Settings;
- existing real Chat/Models/Logs flows remain available during migration;
- dependency-gated areas show explicit unavailable states instead of fabricated values;
- Endpoints links to real Swagger/examples;
- responsive shell styles are separated from the legacy `index.html` monolith.

Remaining UX work:

- E3a real Models & Runtimes lifecycle composition;
- E4a real Overview health/runtime summary;
- current Playground/Diagnostics migration into the new shell modules;
- resource/capability/metric/fingerprint panels as their contracts are wired;
- screen-level accessibility and visual-regression evidence.

## Program status

| Task | Status | Integrated outcome | Remaining gate |
| --- | --- | --- | --- |
| A1 truthful CI | DONE | blocking deterministic matrix | broader Ruff debt later |
| A2 privacy defaults | PARTIAL | fail-closed config/policy + cleanup | `server.py` enforcement via request pipeline |
| A3 consumer decoupling | DONE | generic registry sources | consumer-specific integration stays external |
| C1 canonical request vocabulary | PARTIAL | contracts + translator + request pipeline | make HTTP route use pipeline |
| E1 design system | PARTIAL | tokens/primitives | screen migration + evidence |
| F1 positioning | DONE | README/package positioning | promote future claims only after shipping |
| B1 resource observation | PARTIAL | truthful contracts + Linux observer | macOS/runtime wiring/evidence |
| C2 capabilities | PARTIAL | conservative descriptor + supports() | registry/API/request wiring |
| D1 metric vocabulary | DONE | precise canonical schema | D2 backend adapters |
| D3a artifact identity | DONE | path-free source/hash identity | final runtime fingerprint D3 |
| E2 shell/navigation | PARTIAL | new IA + incremental shell | migrate real screens + UX evidence |
| AC1 request/security adapter | PARTIAL | canonical policy adapter | replace historical parser in `server.py` |

## Immediate next parallel wave

Start these ownership-isolated streams together:

1. **B2 ResourceManager foundation** — reservation ledger, budget checks, typed admission decision and rollback using B1 types.
2. **B1b macOS resource adapter** — trustworthy total/available/unified-memory sources with explicit unavailable behavior where unsupported.
3. **C2b registry/API capability wiring** — validate explicit capability declarations and expose descriptors without changing backend execution yet.
4. **D2 metric adapters foundation** — start with current runtime/llama sources behind D1; do not invent unavailable TTFT/token data.
5. **E3a/E4a source-backed UX** — Models inventory + Overview health/runtime summaries behind the E2 shell.
6. **D4a evaluation schema** — versioned test-set/sample/scorer/run-report contracts independent of final execution metrics.
7. **AC1b server wiring** — exclusive `server.py` ownership; replace duplicate request normalization with `request_pipeline.py` and enforce remote-media policy before backend invocation.

### Parallelization constraints

- AC1b exclusively owns broad `server.py` request-path changes.
- C2b may edit registry/model metadata modules but should not edit the request route.
- D2 adapters live behind D1 and should avoid changing UI labels directly.
- E3a/E4a consume only current source-backed APIs; resource/capability/performance cards remain unavailable until their corresponding wiring lands.
- B2 does not claim memory is reclaimable; admission and reclamation remain separate concerns until B3 evidence exists.

## Newly unblocked dependencies

- B1 contract -> B2 can start.
- D1 -> D2 backend adapters can start.
- E2 -> E3a/E4a/current Playground/Diagnostics module migration can start.
- D3a -> backend/config/hardware identity work can proceed toward D3.
- C2 contract -> registry/API capability wiring can start; C3 still waits for that wiring plus AC1b.

## Evidence boundary

No unit test can establish macOS unified-memory reclamation, real TTFT, true token throughput or model unload memory recovery. Those require representative runtime/device evidence after the corresponding adapters and lifecycle paths are integrated.

## Update rule

Update this file in the same integration cycle whenever task state, blockers or the immediate next wave changes. It is an operational ledger, not a historical changelog.

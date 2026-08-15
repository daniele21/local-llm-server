<p align="center">
  <img src="src/local_llm_server/static/logo.png" alt="Local LLM Server logo" width="180">
</p>

<h1 align="center">Local LLM Server</h1>

<p align="center">
  <strong>Resource-aware local AI control plane and evaluation harness.</strong>
</p>

<p align="center">
  One application-facing boundary for local text, vision and transcription workloads, with explicit runtime lifecycle, privacy policy, resource admission, observability and reproducible evaluation around specialist inference engines.
</p>

<p align="center">
  <a href="https://daniele21.github.io/#infrastructure">Local-first AI stack</a>
  ·
  <a href="docs/assets/local-llm-server%20demo.mp4">Guided product tour</a>
  ·
  <a href="#common-workflows">Quick start</a>
  ·
  <a href="#http-api">HTTP API</a>
  ·
  <a href="#hardware-evidence-workflow">Hardware evidence</a>
  ·
  <a href="docs/README.md">Architecture & roadmap</a>
</p>

`local-llm-server` gives applications a stable local inference boundary without coupling product code to model files, inference engines or backend subprocesses. Suitable workloads execute on user-owned hardware by default. Remote media/model code and network exposure remain explicit policy choices rather than hidden fallbacks.

The project **orchestrates specialist inference runtimes; it does not replace them**. `llama.cpp`, `llama-cpp-python`, MLX and task-specific engines own model execution. Local LLM Server owns the control-plane concerns around them: task/capability contracts, runtime lifecycle, resource policy, scheduling, privacy, evidence and evaluation.

The server is the infrastructure layer. **Local LLM Studio** is the bundled Web control plane for exercising supported tasks, inspecting configured/resident runtimes, viewing source-backed diagnostics, managing residency and running reproducible evaluations.

> **Status boundary:** the control-plane/evaluation architecture described below is integrated on the current development baseline. Claims that depend on real device behavior — memory reclamation, safe automatic eviction under pressure, throughput/TTFT, thermal behavior and representative backend stability — remain **evidence-pending** until retained hardware reports support them. Automatic pressure-triggered eviction is not enabled.

## What is integrated today

### Control plane

- seven source-backed Studio destinations: Overview, Models & Runtimes, Endpoints, Playground, Benchmark & Evaluation, System / Diagnostics and Settings;
- explicit configured vs resident vs default-route state, including valid zero-resident/cold operation;
- runtime pin/unpin plus current `evictable` eligibility;
- deterministic LRU/TTL eviction candidate preview/execution for administrative use;
- capability-driven text, image, structured-generation and transcription controls;
- source-backed resource, scheduler, runtime identity and policy evidence;
- ARIA tab/tabpanel navigation, keyboard roving focus, skip navigation and responsive/zoom-oriented layout contracts.

### Runtime and resource policy

- multiple resident runtimes behind one public HTTP server;
- active runtime leases that prevent unload while inference is in progress;
- configurable memory budget/headroom with reservation/accounting before expensive loads;
- bounded FIFO request admission with queue capacity/timeout evidence;
- explicit runtime pinning and deterministic LRU/TTL selection;
- hysteretic pressure-policy evaluation with fail-conservative `UNKNOWN` handling;
- automatic pressure eviction deliberately disabled pending representative hardware evidence.

### Tasks and compatibility

- OpenAI-compatible `/v1/chat/completions` for text and supported multimodal chat;
- first-class `/v1/audio/transcriptions` for runtimes that explicitly declare transcription capability;
- server-owned task/input/output/feature capability descriptors;
- unsupported task/modality combinations rejected before backend execution on supported product entrypoints;
- fail-closed remote HTTP(S) media unless explicitly enabled.

### Observability and evaluation

- canonical metric vocabulary separating tokens, chunks, queue wait, TTFT, prefill/decode duration and throughput;
- explicit streaming usage/timing retention when a backend provides it;
- task-specific transcription evidence (`backend_wall_clock_ms`, audio duration, realtime factor and segment count) kept separate from generation metrics;
- artifact/backend/config/hardware runtime fingerprinting with exploratory state when identity is incomplete;
- built-in deterministic evaluation plus validated custom JSON test sets;
- persisted run history and compatibility-aware baseline/candidate comparison;
- no automatic “better model” verdict when evidence is incompatible or exploratory.

### Process-isolated evidence path

- bounded JSON-line worker protocol and subprocess transport;
- `WorkerBackedEngine` for completed-response non-streaming workloads;
- repeated start → ready → infer → stop reclamation cycles;
- a local hardware evidence CLI that captures host memory checkpoints and live child-process RSS when available;
- a conservative multi-report reviewer that refuses to aggregate incompatible runtime/hardware/procedure identities.

Worker streaming and in-flight cancellation are **not** claimed by the current worker adapter. Interactive runtimes continue to use the existing engine paths until a true incremental worker protocol is designed and validated.

## Product in practice

### Local LLM Studio

Use the same local surface to exercise resident runtimes, inspect lifecycle state, explore endpoint compatibility, run evaluations and view operational evidence.

The screenshots below document real shipped Studio workflows from the repository. The current control-plane baseline extends these surfaces with source-backed Overview/Evaluation/Residency/Settings composition; public screenshots are intentionally not presented as performance evidence.

<p align="center">
  <img src="docs/assets/Chat-Studio.png" alt="Local LLM Studio chat running a structured meeting analysis" width="100%">
</p>

<table>
  <tr>
    <td width="50%" valign="top">
      <strong>Models and runtime configuration</strong><br><br>
      Inspect the local catalog, load/select runtimes and apply backend-supported parameters.<br><br>
      <img src="docs/assets/Models-configs.png" alt="Local model catalog and runtime configuration" width="100%">
    </td>
    <td width="50%" valign="top">
      <strong>Live server diagnostics</strong><br><br>
      Follow lifecycle/inference logs alongside source-backed runtime, resource and scheduler evidence.<br><br>
      <img src="docs/assets/Server-Logs.png" alt="Live local inference server logs" width="100%">
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <strong>Copy-ready integration examples</strong><br><br>
      Move from the console to an application with cURL, Python, JavaScript and Swift examples.<br><br>
      <img src="docs/assets/Example-Usage.png" alt="OpenAI-compatible API integration examples" width="100%">
    </td>
    <td width="50%" valign="top">
      <strong>Interactive API contract</strong><br><br>
      Explore request schemas and execute endpoints directly through bundled Swagger UI.<br><br>
      <img src="docs/assets/Swagger-Api.png" alt="Swagger documentation for the local LLM API" width="100%">
    </td>
  </tr>
</table>

## Product principles

- **Local-first, not local-only:** suitable workloads run on private, user-owned hardware; external execution is an explicit architectural choice.
- **Orchestration, not backend replacement:** specialist runtimes own model execution; the control plane owns lifecycle, policy and evidence around them.
- **Stable application contract:** product code integrates through public HTTP/Python boundaries rather than backend-specific inference code.
- **Explicit model routing:** requests resolve a configured model key/model ID; no silent model substitution.
- **Artifact ≠ configured model ≠ resident runtime ≠ default route:** these states remain distinct.
- **Source-backed observability:** measured, estimated, configured and unavailable values are not collapsed together.
- **Privacy by default:** loopback binding, disabled CORS/admin routes, fail-closed remote media and explicit remote-code trust.
- **Evidence before optimization claims:** deterministic CI proves contracts; representative hardware proves hardware-dependent behavior.
- **No fake streaming or reclamation:** buffered output is not labelled incremental streaming; process exit is not labelled memory recovery.
- **Reusable infrastructure:** downstream applications consume explicit integration points rather than embedding product-specific state in the core package.

## Repository map

```text
src/local_llm_server/core/                    Backend-neutral request/task/capability contracts
src/local_llm_server/product_composition.py   Supported product HTTP policy/middleware composition
src/local_llm_server/control_plane_api.py     Modular control-plane/evaluation APIs
src/local_llm_server/runtime.py               Resident runtime ownership, leases and routing
src/local_llm_server/product_runtime_manager.py
                                               Cold/default/residency/pinning state
src/local_llm_server/resource_manager.py      Memory reservation/admission/accounting
src/local_llm_server/request_scheduler.py     Bounded request admission
src/local_llm_server/residency_eviction.py    Explicit LRU/TTL candidate selection
src/local_llm_server/residency_pressure.py    Hysteretic pressure-policy evaluator
src/local_llm_server/engine.py                llama.cpp, MLX and VLM engine adapters
src/local_llm_server/worker_*.py               Isolated batch worker/evidence path
src/local_llm_server/metrics*.py              Canonical generation evidence
src/local_llm_server/transcription*.py        First-class ASR task/evidence
src/local_llm_server/evaluation*.py           Test sets, execution, persistence and comparison
src/local_llm_server/hardware_evidence*.py    Local device run/review workflow
src/local_llm_server/static/                  Local LLM Studio control-plane frontend
docs/                                         Current state, roadmap, architecture, UX and DoD
tests/                                        Deterministic contract/regression tests
.github/workflows/                            Ruff + Python 3.10/3.11/3.12 CI
```

The target ownership map and migration boundaries live in [`docs/architecture-evolution-plan.md`](docs/architecture-evolution-plan.md). The repository is migrating incrementally; working compatibility surfaces are retained until their replacements prove parity.

## Request resolution

Supported product entrypoints apply policy before backend execution:

```text
HTTP request
    ↓
canonical request + media/capability validation
    ↓
bounded scheduler admission (when configured)
    ↓
resident runtime resolution + lease
    ↓
backend engine complete/stream
    ↓
truthful completion/stream evidence
    ↓
OpenAI-compatible response / SSE
```

Canonical request preparation now also owns the tested request → engine-kwargs translation. The historical `server.py` chat route still contains duplicate compatibility construction and is an explicit cleanup item; direct module-level `local_llm_server.server:app` should therefore be treated as a compatibility/deprecation path rather than the preferred product composition entrypoint.

## Model lifecycle

```text
built-in registry + optional user/external registry
                  ↓
       validated model definition
                  ↓
complete local source / cache / explicit download
                  ↓
       artifact completeness checks
                  ↓
       resource admission reservation
                  ↓
             runtime load
                  ↓
        resident + optional pinned state
                  ↓
        explicit default-route choice
                  ↓
 lease-safe unload / explicit LRU-TTL selection
                  ↓
            valid cold state
```

A downloaded artifact is not automatically resident. A resident runtime is not automatically the default route. Changing the default route does not unload unrelated runtimes. Pinning changes automatic-eviction eligibility only; it is not a memory-reclamation claim.

## Backend matrix

| Backend | Model format | Execution | Intended workload |
|---|---|---|---|
| `llama_cpp` | GGUF | In-process through `llama-cpp-python` | Text generation / structured local reasoning |
| `mlx` | MLX | In-process through `mlx-lm` | Apple Silicon text inference |
| `llama_server` | GGUF + optional `mmproj` | Managed `llama-server` subprocess | GGUF multimodal models |
| `mlx_vlm_server` | Complete MLX VLM package | Managed `mlx_vlm.server` subprocess | Apple Silicon vision-language inference |
| explicit ASR runtime | backend-specific | Resident runtime adapter | First-class audio → text transcription |

Capabilities are explicit runtime metadata. This table is not a claim that every model/backend combination implements every task.

## Installation

Prerequisites:

- Python 3.10+
- macOS or Linux
- C/C++ toolchain when `llama-cpp-python` must compile locally
- Apple Silicon for MLX/MLX-VLM extras
- a `llama-server` executable when using that managed backend
- enough RAM/unified memory for the configured resident set

Install the default GGUF text backend:

```bash
pip install .
```

Optional development/backends:

```bash
pip install ".[dev]"       # pytest, httpx, ruff
pip install ".[mlx]"       # Apple Silicon text
pip install ".[vision]"    # Apple Silicon vision-language
pip install ".[audio]"     # local audio preprocessing helpers
```

Editable development with all extras:

```bash
pip install -e ".[dev,mlx,vision,audio]"
```

## Common workflows

List the merged model catalog:

```bash
local-llm models
```

Download a configured model without starting a server:

```bash
local-llm download nemotron-nano-4b-q8
```

Start one model with the full administrative control plane:

```bash
local-llm serve \
  --model nemotron-nano-4b-q8 \
  --enable-admin-api
```

Default local surfaces:

```text
Studio       http://127.0.0.1:1235/
API examples http://127.0.0.1:1235/example
Swagger UI  http://127.0.0.1:1235/docs
Health      http://127.0.0.1:1235/health
```

Start concurrent text + vision runtimes:

```bash
local-llm serve \
  --models nemotron-nano-4b-q8 qwen3-vl-4b \
  --default-model nemotron-nano-4b-q8 \
  --enable-admin-api
```

The server may also be healthy with zero resident runtimes. Configured identity and current resident/default-route state remain separate.

## Client integration

Standard chat completion:

```bash
curl http://127.0.0.1:1235/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nemotron-nano-4b-q8",
    "messages": [
      {"role": "user", "content": "Summarize the case for local-first AI."}
    ],
    "temperature": 0
  }'
```

OpenAI Python SDK:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:1235/v1",
    api_key="local",
)

response = client.chat.completions.create(
    model="nemotron-nano-4b-q8",
    messages=[{"role": "user", "content": "Extract decisions and action items."}],
)

print(response.choices[0].message.content)
```

First-class transcription (requires a resident runtime that explicitly declares the transcription task):

```bash
curl http://127.0.0.1:1235/v1/audio/transcriptions \
  -F "model=my-asr-runtime" \
  -F "file=@meeting.wav"
```

Bundled high-level client:

```python
from local_llm_server import LocalLLMClient

client = LocalLLMClient(
    base_url="http://127.0.0.1:1235",
    model="nemotron-nano-4b-q8",
)

result = client.analyze_text(
    "The team approved the Friday release. Marco owns rollback preparation.",
    language="en",
)
print(result["summary"])
```

Programmatic server ownership is available through `local_llm_server.serve(...)`, which returns an explicit shutdown handle when started in background mode.

## Runtime configuration

Built-in definitions live in `src/local_llm_server/models_registry.yaml`. Extend/override them in `~/.local-llm/models.yaml`:

```yaml
models:
  my-model:
    filename: my-model-Q4_K_M.gguf
    url: https://huggingface.co/example/my-model/resolve/main/my-model-Q4_K_M.gguf
    model_id: example/my-model
    backend: llama_cpp
    thinking_mode: switchable
    params:
      ctx_size: 8192
      n_gpu_layers: 35
      max_concurrent_requests: 1
    tags: [instruct, custom]
```

CLI flags override environment variables, which override model/registry defaults. Use `local-llm serve --help` for the current surface.

## HTTP API

Public runtime surface:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | server/runtime readiness |
| `GET` | `/status` | current inference/runtime status |
| `GET` | `/v1/models` | resident model list |
| `POST` | `/v1/chat/completions` | OpenAI-compatible chat + SSE streaming |
| `POST` | `/v1/audio/transcriptions` | first-class multipart audio → text |
| `GET` | `/` | Local LLM Studio |
| `GET` | `/example` | integration examples |
| `GET` | `/docs` | Swagger UI |

Additional routes are installed only when the administrative API is enabled. Key control-plane surfaces include:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/models/registry` | configured model catalog + capabilities |
| `POST` | `/api/v1/models/load` | load an additional resident runtime |
| `POST` | `/api/v1/models/activate` | load/select default runtime |
| `DELETE` | `/api/v1/models/{model}` | unload an idle runtime |
| `GET` | `/api/v1/resources` | configured resource budget/accounting |
| `GET` | `/api/v1/evidence` | privacy-safe runtime/task evidence |
| `GET` | `/api/v1/scheduler` | queue/admission evidence |
| `GET` | `/api/v1/policies` | effective privacy/resource policy evidence |
| `GET` | `/api/v1/residency` | pinned/evictable residency state |
| `POST` | `/api/v1/residency/pin` | explicit runtime pin/unpin |
| `POST` | `/api/v1/residency/eviction/preview` | deterministic LRU/TTL preview |
| `POST` | `/api/v1/residency/eviction/execute` | explicit administrative eviction attempt |
| `GET/POST` | `/api/v1/evaluation/...` | test sets, runs, history and comparison |
| `GET` | `/api/v1/logs/stream` | live server logs over SSE |

Route names evolve with the modular control plane; Swagger remains the executable contract for the checked-out revision.

## Hardware evidence workflow

Hardware-dependent claims require representative runs. The repository includes a repeatable isolated-worker procedure so this evidence can be retained rather than inferred from unit tests.

Run repeated load/infer/stop cycles:

```bash
local-llm evidence-reclamation \
  --model nemotron-nano-4b-q8 \
  --cycles 3 \
  --settle-seconds 2 \
  --output evidence/macbook-run-01.json \
  --no-download
```

The report records procedure/runtime identity plus available host memory checkpoints and live child-process RSS where the OS exposes it. Prompt text, generated output and local model paths are intentionally excluded. A child process disappearing after stop is **not** recorded as a measured RSS of zero.

Repeat the procedure rather than relying on one run. Review compatible reports together:

```bash
local-llm evidence-review \
  evidence/macbook-run-01.json \
  evidence/macbook-run-02.json \
  --output evidence/macbook-review.json
```

The reviewer checks procedure, artifact/backend/config and hardware compatibility before aggregation. Its states such as `consistent_recovery_observed`, `consistent_no_recovery_observed`, `mixed` or `insufficient` are **descriptive**, not an authorization to enable automatic eviction and not a production-safety verdict.

## Evaluation workflow

With `--enable-admin-api`, Benchmark & Evaluation can:

- use the built-in deterministic `general-purpose` test set;
- import validated custom JSON test sets with explicit versions;
- choose deterministic sample counts/seeds;
- execute against resident runtimes;
- persist immutable local run reports;
- inspect history;
- compare compatible baseline/candidate runs without silently pooling incompatible fingerprints.

Custom datasets are data only: uploaded files do not execute Python, templates, plugins or custom scorers.

## Security boundary

Defaults are local and fail-conservative:

- bind address `127.0.0.1`;
- CORS disabled unless explicitly configured;
- administrative endpoints disabled unless explicitly enabled;
- remote HTTP(S) media disabled by default;
- remote model/tokenizer code requires explicit trust;
- no silent cloud inference fallback;
- evidence/report surfaces omit prompt/output/media content and private local paths by default.

Binding to `0.0.0.0` exposes public routes to the network:

```bash
local-llm serve \
  --host 0.0.0.0 \
  --port 1235 \
  --model nemotron-nano-4b-q8
```

The server does not currently provide authentication. Use a trusted local boundary/reverse proxy and do not expose administrative routes to an untrusted network.

## Validation

Deterministic checks:

```bash
pytest tests/ -v --tb=short
ruff check src/ tests/
```

CI runs Ruff plus the test suite on Python 3.10, 3.11 and 3.12.

Optional inference verification against a running server:

```bash
uv run python test_inference.py \
  --server-url http://127.0.0.1:1235/v1
```

Contract tests do not establish real unified-memory recovery, accelerator footprint, device throughput, thermal behavior or safe automatic pressure eviction. Use retained hardware reports for those claims.

## Remaining product-grade gates

The highest-value open gates are deliberately narrow:

1. **Representative hardware matrix:** execute/review the evidence workflow across agreed devices/backends/artifacts.
2. **Canonical route cleanup:** switch the historical chat route to consume the already-integrated prepared backend request and formalize the direct `server:app` deprecation boundary.
3. **Specialist evidence coverage:** continue explicit VLM/ASR timing/identity mapping only where backends expose trustworthy sources.
4. **Worker streaming/cancellation decision:** add a true incremental protocol only if interactive process isolation is a product requirement; do not fake it with buffered output.
5. **Manual UX evidence:** light/dark contrast, complete keyboard traversal, real 200% zoom and stable visual-regression fixtures/screenshots.
6. **Release review:** reconcile evidence-pending claims before promoting the long-lived integration branch toward `main`.

See [`docs/current-state.md`](docs/current-state.md) for integrated truth and [`docs/roadmap.md`](docs/roadmap.md) for dependency sequencing.

## Documentation and ecosystem

- [`docs/README.md`](docs/README.md) routes canonical repository documentation.
- [`docs/current-state.md`](docs/current-state.md) is the operational ledger for integrated/blocking/next state.
- [`docs/roadmap.md`](docs/roadmap.md) owns sequencing and parallelization.
- [`docs/implementation-plan.md`](docs/implementation-plan.md) owns target implementation behavior.
- [`docs/architecture-evolution-plan.md`](docs/architecture-evolution-plan.md) owns target architecture/migration boundaries.
- [`docs/ux-ui-implementation-plan.md`](docs/ux-ui-implementation-plan.md) owns target UX behavior.
- [`docs/definition-of-done.md`](docs/definition-of-done.md) prevents implementation from being confused with product/evidence completion.
- The [Android Local LLM Harness](https://github.com/daniele21/android-local-llm-harness) provides documentation-governance and lifecycle precedent.

## License

Released under the MIT License as declared in `pyproject.toml`.

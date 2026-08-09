<p align="center">
  <img src="src/local_llm_server/static/logo.png" alt="Local LLM Server logo" width="180">
</p>

<h1 align="center">Local LLM Server</h1>

<p align="center">
  <strong>Product-grade local AI infrastructure for desktop and local-first applications.</strong>
</p>

<p align="center">
  A stable OpenAI-compatible API across GGUF and Apple Silicon MLX runtimes, with explicit model lifecycle, dynamic routing, observability, and a bundled inference console.
</p>

<p align="center">
  <a href="https://daniele21.github.io/#infrastructure">Local-first AI stack</a>
  ·
  <a href="docs/assets/local-llm-server%20demo.mp4">Guided product tour</a>
  ·
  <a href="#common-workflows">Quick start</a>
  ·
  <a href="#http-api">HTTP API</a>
</p>

`local-llm-server` gives applications a local execution path without coupling product code to model files, inference engines, or backend processes. It runs fully on user-owned hardware and keeps cloud models available as an architectural choice rather than a runtime dependency.

The server is the infrastructure layer. **Local LLM Studio** is the Web UI shipped with it for chat, runtime configuration, model management, and live diagnostics.

## Product in practice

### Chat Studio

Test real prompts against resident models, tune inference parameters, inspect reasoning controls, and validate structured output from the same interface used to monitor the runtime.

<p align="center">
  <img src="docs/assets/Chat-Studio.png" alt="Local LLM Studio chat running a structured meeting analysis" width="100%">
</p>

<table>
  <tr>
    <td width="50%" valign="top">
      <strong>Models and runtime configuration</strong><br><br>
      Inspect the local catalog, load or switch models, and apply only the parameters supported by the selected backend.<br><br>
      <img src="docs/assets/Models-configs.png" alt="Local model catalog and runtime configuration" width="100%">
    </td>
    <td width="50%" valign="top">
      <strong>Live server diagnostics</strong><br><br>
      Follow model loading, prompt evaluation, token generation, and runtime status through the administrative log stream.<br><br>
      <img src="docs/assets/Server-Logs.png" alt="Live local inference server logs" width="100%">
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <strong>Copy-ready integration examples</strong><br><br>
      Move from the console to an application with ready-to-run cURL, Python, JavaScript, and Swift examples.<br><br>
      <img src="docs/assets/Example-Usage.png" alt="OpenAI-compatible API integration examples" width="100%">
    </td>
    <td width="50%" valign="top">
      <strong>Interactive API contract</strong><br><br>
      Explore request schemas and execute endpoints directly through the bundled Swagger UI.<br><br>
      <img src="docs/assets/Swagger-Api.png" alt="Swagger documentation for the local LLM API" width="100%">
    </td>
  </tr>
</table>

## Core decisions

- **Local-first, not local-only:** suitable workloads run on private, user-owned hardware; external models remain an optional execution path for workloads that need them.
- **Stable client contract:** applications integrate through an OpenAI-compatible HTTP API or the Python client, not through backend-specific inference code.
- **Explicit model routing:** every request resolves a configured model key or model ID to an already resident runtime; the server does not silently substitute another model.
- **Backend-neutral lifecycle:** GGUF, MLX text, GGUF multimodal, and MLX vision engines share the same load, route, stream, drain, and unload boundary.
- **Control with observability:** health, runtime state, token timings, model management, and live logs are first-class product surfaces.
- **Private by default:** the server binds to loopback, CORS is disabled, and administrative endpoints are opt-in.
- **Reusable infrastructure:** Local LLM Server is a runtime pillar for applications such as ClosedRoom rather than an application-specific inference wrapper.

## Repository map

```text
src/local_llm_server/server.py          FastAPI app, OpenAI-compatible routes, admin API and Web UI
src/local_llm_server/runtime.py         Resident runtime ownership, leases, routing and shutdown
src/local_llm_server/engine.py          llama.cpp, MLX, llama-server and MLX-VLM engine adapters
src/local_llm_server/process.py         Managed subprocess lifecycle and bounded log draining
src/local_llm_server/model_sources.py   LM Studio, Hugging Face cache and download resolution
src/local_llm_server/registry.py        Built-in and user model-registry loading and validation
src/local_llm_server/config.py          CLI, environment and per-model configuration resolution
src/local_llm_server/client.py          High-level Python client for text, image and audio tasks
src/local_llm_server/static             Local LLM Studio frontend and guided tour
src/local_llm_server/models_registry.yaml
                                        Built-in model definitions and runtime defaults
tests                                   Runtime, API, source-resolution and lifecycle regression tests
.github/workflows                       Lint, multi-version test and release automation
```

## Request resolution

```text
OpenAI-compatible request
        model key or model ID
                 ↓
       ModelRuntimeManager.resolve
                 ↓
          resident runtime lease
                 ↓
      per-runtime admission semaphore
                 ↓
        engine.complete or engine.stream
                 ↓
     OpenAI-compatible response or SSE
```

The runtime lease prevents `unload`, reload, or shutdown from closing an engine while inference is active. Admission is enforced independently per runtime, so requests for different resident models can progress concurrently while each backend retains its own safe concurrency limit.

## Model lifecycle

```text
built-in registry + ~/.local-llm/models.yaml
                  ↓
       validated model definition
                  ↓
 complete LM Studio model → complete Hugging Face cache → explicit download
                  ↓
      artifact completeness validation
                  ↓
            backend engine load
                  ↓
             resident runtime
                  ↓
      explicit default-route selection
                  ↓
          request drain and unload
```

A downloaded model is not automatically resident. A resident model is not automatically the default route. Changing the default route does not unload any other model.

Incomplete MLX snapshots, missing GGUF multimodal projectors, invalid aliases, unsupported backends, and inconsistent modality declarations fail before inference begins. Use `--no-download` when startup must remain strictly offline and fail if required artifacts are absent.

## Backend matrix

| Backend | Model format | Execution | Intended workload |
|---|---|---|---|
| `llama_cpp` | GGUF | In-process through `llama-cpp-python` | Text generation and structured local reasoning |
| `mlx` | MLX | In-process through `mlx-lm` | Apple Silicon-optimized text inference |
| `llama_server` | GGUF + optional `mmproj` | Managed `llama-server` subprocess | GGUF multimodal and audio-capable models |
| `mlx_vlm_server` | Complete MLX VLM package | Managed `mlx_vlm.server` subprocess | Apple Silicon vision-language inference |

All backends remain behind the same public API. Ports assigned to managed subprocesses are private runtime details.

## Current integrated baseline

The current baseline includes:

- OpenAI-compatible chat completions with streaming and non-streaming responses;
- model selection through the request `model` field, registry key, or configured model ID;
- multiple resident runtimes behind one public HTTP port;
- independent runtime admission, active-request leases, safe unload, and bounded shutdown;
- GGUF text, MLX text, GGUF multimodal, and MLX vision engine adapters;
- centralized local artifact discovery, completeness checks, and explicit downloads;
- configurable context, GPU, CPU, batch, timeout, thinking, and backend-specific controls;
- a bounded response cache for deterministic greedy completions;
- an interactive Web UI with chat, model configuration, live logs, examples, and Swagger docs;
- an opt-in administrative surface for model lifecycle and log streaming;
- isolated FastAPI app instances for safe programmatic embedding;
- a Python client with structured text, local image, and audio helpers.

## Current priorities

1. Add desktop-friendly background lifecycle controls, auto-start, and tray integration.
2. Introduce task-oriented model presets for extraction, summaries, and fast structured output.
3. Expand the diagnostics surface with latency, throughput, and memory benchmarks.
4. Add local discovery for downstream applications looking for an available runtime.
5. Add a simple authentication boundary for deliberately shared local-network deployments.

## Build prerequisites

- Python 3.10 or newer
- macOS or Linux
- A C/C++ build toolchain when `llama-cpp-python` must be compiled locally
- Apple Silicon for the `mlx` and `vision` extras
- A `llama-server` binary for the external GGUF multimodal backend
- Enough RAM or unified memory for every model kept resident at the same time

## Installation

Install the default GGUF text backend from source:

```bash
pip install .
```

Install development tools or optional backends as needed:

```bash
pip install ".[dev]"       # pytest, httpx and ruff
pip install ".[mlx]"       # Apple Silicon text models
pip install ".[vision]"    # Apple Silicon vision-language models
pip install ".[audio]"     # local audio preprocessing helpers
```

For editable development with all extras:

```bash
pip install -e ".[dev,mlx,vision,audio]"
```

## Common workflows

List the merged built-in and user model catalog:

```bash
local-llm models
```

Download a configured model without starting a server:

```bash
local-llm download nemotron-nano-4b-q8
```

Start one model and enable the full Local LLM Studio administrative experience:

```bash
local-llm serve \
  --model nemotron-nano-4b-q8 \
  --enable-admin-api
```

The default runtime is available at:

```text
Web UI       http://127.0.0.1:1235/
API examples http://127.0.0.1:1235/example
Swagger UI  http://127.0.0.1:1235/docs
Health      http://127.0.0.1:1235/health
```

Start a text model and a vision model as concurrent resident runtimes:

```bash
local-llm serve \
  --models nemotron-nano-4b-q8 qwen3-vl-4b \
  --default-model nemotron-nano-4b-q8 \
  --enable-admin-api
```

The Chat Studio selector lists resident models only. The Models and Config view can load another configured model, change the default route, restart one runtime with new settings, or unload an idle model without stopping the server.

## Client integration

Send a standard chat completion:

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

Use the standard OpenAI Python SDK against the local endpoint:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:1235/v1",
    api_key="local",
)

response = client.chat.completions.create(
    model="nemotron-nano-4b-q8",
    messages=[
        {"role": "user", "content": "Extract the decisions and action items."}
    ],
)

print(response.choices[0].message.content)
```

Or use the bundled high-level client:

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

Programmatic server ownership is also available through `local_llm_server.serve(...)`, which returns a handle with an explicit `shutdown()` method when started in background mode.

## Runtime configuration

Built-in definitions live in `src/local_llm_server/models_registry.yaml`. Extend or override them locally in `~/.local-llm/models.yaml`:

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

CLI flags override environment variables, which override model and registry defaults. Run `local-llm serve --help` for the complete configuration surface.

## HTTP API

The public runtime surface is available by default:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Server, backend, runtime, and readiness metadata |
| `GET` | `/status` | Current inference status and telemetry |
| `GET` | `/v1/models` | OpenAI-compatible resident model list |
| `POST` | `/v1/chat/completions` | OpenAI-compatible chat completion and SSE streaming |
| `GET` | `/` | Local LLM Studio |
| `GET` | `/example` | Copy-ready client examples |
| `GET` | `/docs` | Interactive Swagger documentation |

The following routes exist only when `--enable-admin-api` or `serve(enable_admin_api=True)` is set:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/models/registry` | Full configured model catalog |
| `POST` | `/api/v1/models/load` | Load an additional resident runtime |
| `POST` | `/api/v1/models/activate` | Load or select the default runtime |
| `DELETE` | `/api/v1/models/{model}` | Unload one idle runtime |
| `GET` | `/api/v1/logs/stream` | Live server logs over SSE |

## Security boundary

The default bind address is `127.0.0.1`, CORS is disabled, and model-management and log endpoints are excluded unless explicitly enabled.

Binding to `0.0.0.0` exposes the public inference and status routes to the network:

```bash
local-llm serve \
  --host 0.0.0.0 \
  --port 1235 \
  --model nemotron-nano-4b-q8
```

The server does not currently include authentication. Use a host firewall or trusted local reverse proxy and do not enable the administrative API on an untrusted network.

## Validation

Run the automated test suite and linter:

```bash
pytest tests/ -v --tb=short
ruff check src/ tests/
```

Run batch inference verification against an already running server:

```bash
uv run python test_inference.py \
  --server-url http://127.0.0.1:1235/v1
```

Changes to engine or process lifecycle should additionally be checked on representative hardware with one GGUF text model and one VLM resident at the same time. Verify streaming interruption, concurrent cross-model requests, idle unload, offline `--no-download` behavior, and child-process cleanup after `Ctrl+C`.

## Documentation and ecosystem

- The broader architectural position is documented on [daniele21.github.io](https://daniele21.github.io/): local-first means controlling model lifecycle, costs, and data boundaries while retaining cloud models where their capability is valuable.
- The [Android Local LLM Harness](https://github.com/daniele21/android-local-llm-harness) applies the same explicit model-lifecycle and observability principles to native Android applications.
- Local LLM Server, Local ASR Server, and Android Local LLM Harness form three reusable infrastructure pillars for product-grade local AI.
- Reference applications such as ClosedRoom validate the stack against privacy-sensitive product workflows.

## License

Released under the MIT License as declared in `pyproject.toml`.

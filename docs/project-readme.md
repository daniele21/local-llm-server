# local-llm-server — Project README

## 1. Executive summary

`local-llm-server` is a local inference server designed to let desktop and local-first applications use Large Language Models without depending on external cloud APIs.

The project exposes local models through an OpenAI-compatible HTTP API, adds a Web UI to monitor the running server, and provides utilities to list, download, activate and switch models. It is intended to become the local AI runtime layer for applications such as **ClosedRoom**, where meeting transcripts, summaries, insights and action items should be processed privately on the user’s machine.

In practical terms, this repo is not just a script to run a model. It is a local AI service layer: an application can connect to it as if it were calling an OpenAI-compatible API, while the actual model runs locally on the user’s device.

---

## 2. One-line description

A self-contained local LLM server with an OpenAI-compatible API, Web UI, model registry, runtime monitoring and support for multiple local inference backends.

---

## 3. Why this project exists

Many AI applications start by calling cloud LLM APIs. That works well for prototyping, but it creates several problems when the product needs to handle private data, run offline, reduce variable API costs, or give users more control over the model.

This is especially relevant for products like **ClosedRoom**, where the application may process sensitive meeting content such as internal discussions, decisions, project updates, customer conversations or strategic information.

The goal of `local-llm-server` is to provide a reusable local runtime that can be embedded into or used alongside local applications, so those applications can perform LLM-based analysis while keeping data on the machine.

---

## 4. The problem it solves

### 4.1 Privacy and data control

Cloud LLM APIs require sending text, documents, transcripts or audio-derived content to an external provider. For some use cases, this is not acceptable or reduces user trust.

`local-llm-server` makes it possible to process data locally, reducing the need to send sensitive content outside the device.

### 4.2 Dependency on external providers

When an application depends entirely on a cloud LLM provider, it inherits that provider’s pricing, rate limits, latency, availability and model changes.

A local inference layer gives the application more control over model choice, runtime behavior and deployment strategy.

### 4.3 Lack of a reusable local AI backend

A desktop application should not need to know the details of every local inference engine. It should not have to directly manage `llama.cpp`, MLX, model paths, GGUF files, context sizes, GPU layers, logs and runtime status.

`local-llm-server` abstracts these concerns behind a stable API and a human-friendly dashboard.

### 4.4 Operational visibility

Running local models can be opaque. Users and developers need to understand whether the server is running, which model is active, whether a generation is in progress, how many tokens are being generated, and whether there are errors.

The Web UI and status endpoints are designed to make the local runtime observable instead of invisible.

---

## 5. The solution

`local-llm-server` provides a local HTTP server that runs on the user’s machine and exposes local LLMs through familiar interfaces.

It includes:

- an OpenAI-compatible `/v1/chat/completions` endpoint;
- a built-in Web UI dashboard;
- a model registry for managing available models;
- runtime model activation;
- live status and token-generation telemetry;
- streamed logs over Server-Sent Events;
- CLI commands for serving, listing and downloading models;
- a Python client for application-level integration;
- support for text models and optional multimodal/audio-oriented workflows.

This allows a local application to treat the server as its AI backend while keeping inference on the same machine.

---

## 6. Intended users

This project is useful for:

### Local-first application developers

Developers building desktop apps, internal tools or local agents that need LLM capabilities without relying fully on cloud APIs.

### Privacy-sensitive products

Applications that process confidential or sensitive data, such as meeting notes, customer data, company documents or personal knowledge bases.

### AI product builders

Teams that want a reusable local inference layer instead of integrating directly with each backend or model format.

### Advanced users and technical operators

Users who want to run models locally, switch between them, inspect status and test prompts through a local dashboard.

---

## 7. Example: role inside ClosedRoom

ClosedRoom is a local-first meeting application that records, transcribes and analyzes meetings on-device.

In that context, `local-llm-server` can act as the local reasoning and analysis layer after transcription.

A possible flow is:

1. ClosedRoom records a meeting locally.
2. The speech-to-text layer creates a transcript.
3. ClosedRoom sends the transcript to `local-llm-server` through the local HTTP API.
4. The active local model generates a summary, key points, decisions, risks and action items.
5. ClosedRoom stores the result locally and exposes it in the app.

This separation is valuable because ClosedRoom can focus on the product experience, while `local-llm-server` handles model loading, inference, monitoring and configuration.

---

## 8. Core value proposition

The value of this repo is not simply “run an LLM locally”. The value is creating a controllable local AI backend that other applications can depend on.

| Need | How the repo helps |
|---|---|
| Keep data local | Runs inference on the user’s machine instead of requiring cloud API calls. |
| Integrate easily | Exposes an OpenAI-compatible API, reducing integration friction. |
| Monitor runtime | Provides health, status, logs and telemetry. |
| Change model behavior | Supports model activation and configurable parameters. |
| Support different backends | Can use `llama-cpp-python`, MLX or an external `llama-server`. |
| Serve as app infrastructure | Can be used as the local LLM layer for apps like ClosedRoom. |

---

## 9. Current capabilities

### 9.1 OpenAI-compatible API

The server exposes a `/v1/chat/completions` endpoint designed to be compatible with OpenAI-style chat requests. This means many clients can integrate by changing the base URL to the local server.

Example:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:1235/v1",
    api_key="local"
)

response = client.chat.completions.create(
    model="qwen3-8b",
    messages=[{"role": "user", "content": "Summarize this meeting transcript."}],
)

print(response.choices[0].message.content)
```

### 9.2 Web UI dashboard

The local server exposes a dashboard at:

```text
http://127.0.0.1:1235/
```

The UI is intended to provide:

- interactive chat against the loaded model;
- model registry view;
- model activation;
- live status and telemetry;
- streamed server logs;
- local diagnostics;
- links to usage examples and API docs.

### 9.3 CLI

The package provides a `local-llm` command.

Common commands:

```bash
local-llm models
local-llm download qwen3-8b
local-llm serve --model qwen3-8b
```

### 9.4 Model registry

The project includes a model registry that defines available local models, default parameters and metadata. Users can extend or override the registry with their own local configuration.

The registry is important because it allows model management to become configuration-driven instead of hardcoded inside downstream applications.

### 9.5 Runtime model activation

The server includes an API endpoint to activate a model at runtime with optional configuration overrides. This is useful when a UI or application needs to switch from one model to another without manually restarting everything from the command line.

### 9.6 Runtime status and telemetry

The server exposes runtime status including whether generation is active, the current phase, tokens generated and token speed. This is useful both for the Web UI and for applications that want to show progress to the user.

### 9.7 Log streaming

Logs can be streamed through a Server-Sent Events endpoint. This helps developers inspect what is happening during model loading, prompt evaluation and generation.

### 9.8 Python client

The repo includes a higher-level Python client with helper methods for chat, text analysis and audio-oriented analysis flows.

This is useful for applications that do not want to manually build every HTTP request.

---

## 10. Supported backends

The project is designed to support multiple local inference backends:

### `llama_cpp`

Used for GGUF text models loaded in-process through `llama-cpp-python`.

### `mlx`

Used for MLX-compatible models, especially relevant on Apple Silicon machines.

### `llama_server`

Used for external `llama-server` processes, particularly when features such as multimodal projectors are needed.

This multi-backend design is important because local AI tooling is fragmented. The server provides a more stable application-facing layer above that fragmentation.

---

## 11. Why this matters for product development

For a product like ClosedRoom, the LLM runtime should not be tightly coupled to the UI or meeting workflow.

Separating the local model server from the main app creates several advantages:

- the app can use a stable API regardless of the underlying model;
- models can be changed without rewriting the product logic;
- inference can be monitored independently;
- local performance can be tuned separately from the app UX;
- future models can be added through configuration;
- the same server can potentially power multiple local workflows.

This makes `local-llm-server` a reusable infrastructure component rather than a one-off experiment.

---

## 12. Benefits

### For users

- More privacy, because sensitive content can remain local.
- Less dependency on internet connectivity.
- More transparency on which model is running.
- Better control over model choice and parameters.

### For developers

- Easier integration through an OpenAI-compatible API.
- Reusable runtime for multiple local apps.
- Clear separation between product logic and model execution.
- Faster experimentation with models and parameters.
- Built-in observability through UI, logs and status endpoints.

### For the product/business

- Stronger privacy-first positioning.
- Reduced marginal cost compared with purely cloud-based inference.
- Less vendor lock-in.
- More defensible architecture for local-first AI products.
- Clear foundation for a premium desktop AI experience.

---

## 13. What this repo is not

This repo is not intended to be:

- a full cloud model-hosting platform;
- a replacement for every feature of Ollama, LM Studio or llama.cpp;
- a finished end-user AI product by itself;
- a generic chat application;
- a long-term storage or knowledge management layer;
- a transcription engine by itself.

Its purpose is narrower and more strategic: provide a local LLM runtime layer that other applications can use.

---

## 14. Architecture overview

At a high level, the system can be understood as four layers:

```text
Local application
    ↓
OpenAI-compatible HTTP API / Python client
    ↓
local-llm-server runtime
    ↓
Local model backend
(llama-cpp-python, MLX, llama-server)
```

For ClosedRoom, the architecture could look like this:

```text
ClosedRoom UI
    ↓
Meeting transcript / notes / user query
    ↓
local-llm-server API
    ↓
Local LLM model
    ↓
Summary, insights, actions, decisions, risks
    ↓
ClosedRoom local database / UI
```

---

## 15. Main API surfaces

The main surfaces are:

| Surface | Purpose |
|---|---|
| Web UI `/` | Human dashboard for monitoring and interaction. |
| `/v1/chat/completions` | OpenAI-compatible local inference endpoint. |
| `/health` | Health check and server metadata. |
| `/status` | Runtime status and generation telemetry. |
| `/api/v1/models/registry` | Full configured model registry. |
| `/api/v1/models/activate` | Runtime model activation. |
| `/api/v1/logs/stream` | Server logs streamed over SSE. |
| `/docs` | Swagger/OpenAPI documentation. |
| Python client | Programmatic integration helper. |
| CLI | Serve, list and download models. |

---

## 16. Typical usage

### Install

```bash
pip install .
```

Optional extras:

```bash
pip install ".[mlx]"
pip install ".[audio]"
```

### Start the server

```bash
local-llm serve --model qwen3-8b
```

Default local URL:

```text
http://127.0.0.1:1235
```

### Open the dashboard

```text
http://127.0.0.1:1235/
```

### Call the local model

```bash
curl http://127.0.0.1:1235/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-8b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## 17. Example integration for ClosedRoom

A simplified integration could look like this:

```python
from local_llm_server import LocalLLMClient

client = LocalLLMClient(
    base_url="http://127.0.0.1:1235",
    model="nemotron-nano-4b"
)

result = client.analyze_text(
    transcript,
    language="it",
    output_schema={
        "title": "string",
        "summary": "string",
        "key_points": ["string"],
        "decisions": ["string"],
        "action_items": ["string"],
        "open_questions": ["string"]
    }
)
```

This allows ClosedRoom to request structured meeting analysis without embedding model-management logic directly inside the product code.

---

## 18. Design principles

### 18.1 Local-first

The server should prioritize on-device execution and local data control.

### 18.2 API compatibility

Applications should be able to integrate with minimal changes by using familiar OpenAI-compatible patterns.

### 18.3 Observability

A local model should not feel like a black box. Users and developers need status, logs and performance signals.

### 18.4 Backend flexibility

The project should support different model formats and inference engines, because local LLM tooling evolves quickly.

### 18.5 Product-oriented developer experience

The server should be useful not only for experiments, but also as infrastructure for real local applications.

---

## 19. Security and privacy considerations

Because the server can expose local inference and includes diagnostic capabilities, it should be treated as a local trusted component.

Recommended principles:

- bind to `127.0.0.1` by default;
- avoid exposing the server on public networks unless explicitly needed;
- add authentication or access control before using it in shared or remote environments;
- be careful with terminal/diagnostic features in any non-local deployment;
- make model paths and logs understandable to the user;
- keep sensitive transcripts, prompts and outputs local unless the downstream product explicitly syncs them.

The privacy value of this project depends on the full product architecture. Running the model locally is a strong foundation, but downstream storage, sync, analytics and crash reporting must also respect the same privacy-first design.

---

## 20. Suggested positioning

A good external positioning for the repo could be:

> `local-llm-server` is the local AI runtime layer for privacy-first desktop applications. It lets products use local LLMs through an OpenAI-compatible API, while giving developers and users visibility into model status, runtime behavior and configuration.

For ClosedRoom specifically:

> ClosedRoom uses a local-first architecture where meeting content can be transcribed and analyzed on-device. `local-llm-server` provides the local LLM backend that turns transcripts into summaries, decisions, action items and insights without requiring cloud inference by default.

---

## 21. Potential roadmap

The following areas would make the repo stronger as a reusable local runtime:

### Product/runtime

- Desktop-friendly lifecycle management: start, stop, restart, auto-start.
- Model presets optimized for different use cases: fast summary, deep analysis, JSON extraction, reasoning.
- Better model switch UX with loading progress and failure handling.
- Benchmark panel with tokens/sec, memory usage and latency per model.
- Safer diagnostic terminal or optional disable flag.

### Integration

- Stable SDK methods for meeting analysis, document analysis and structured extraction.
- Typed response schemas for common use cases.
- Better error contracts for downstream applications.
- Local app discovery: allow apps to detect whether the server is running.

### Distribution

- Packaged desktop/runtime installer.
- Preflight checks for macOS/Linux dependencies.
- Clear model download and storage management.
- Versioned configuration migration.

### Security

- Optional local authentication token.
- CORS restrictions configurable by default.
- Explicit safe mode for UI features.
- Clear warning when binding to `0.0.0.0`.

---

## 22. Success criteria

The repo is successful if:

- a developer can integrate a local LLM into an app using a familiar API;
- a user can see which model is running and whether inference is active;
- a local-first product can switch models without rewriting application logic;
- sensitive content can be processed locally by default;
- ClosedRoom and similar apps can reuse the server as their local AI layer.

---

## 23. Project status

The repository already contains the core components needed for a local LLM runtime: server, API, CLI, Web UI, registry, model activation, status endpoints, log streaming and client helpers.

The next strategic step is to make the project more productized: clearer onboarding, safer defaults, better lifecycle management, stronger UI around model switching, and a tighter integration story for local-first applications such as ClosedRoom.

---

## 24. License

MIT.

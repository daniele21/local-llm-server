# local-llm-server

Self-contained local LLM server with an OpenAI-compatible API, CLI, Python API,
interactive Web UI, and optional multimodal audio helpers.

It can serve:

- GGUF text models in-process through `llama-cpp-python`
- MLX models through `mlx-lm`
- multimodal llama.cpp models through an external `llama-server` subprocess with
  `--mmproj`

---

## Requirements

- Python >= 3.10
- A C/C++ compiler for `llama-cpp-python`
- macOS or Linux
- Optional: `llama-server` executable for multimodal models such as Voxtral
- Optional: `soundfile` and `numpy` for audio preprocessing

---

## Installation

```bash
pip install .
```

For development:

```bash
pip install ".[dev]"
```

Optional extras:

```bash
pip install ".[mlx]"      # MLX backend
pip install ".[audio]"    # audio preprocessing helpers
```

### Standalone wheel installation

If you have a built wheel, install it directly:

```bash
pip install local_llm_server-*.whl
```

Then start the server:

```bash
local-llm serve --model qwen3-8b
```

The package includes the Web UI, static assets, registry, and examples.

---

## Quick Start

### 1. List models

```bash
local-llm models
```

### 2. Start the server

```bash
local-llm serve --model qwen3-8b
```

The default server URL is `http://127.0.0.1:1235`.

Open:

- Web UI dashboard: `http://127.0.0.1:1235/`
- API examples: `http://127.0.0.1:1235/example`
- Swagger UI: `http://127.0.0.1:1235/docs`
- ReDoc: `http://127.0.0.1:1235/redoc`

### 3. Send a request

```bash
curl http://127.0.0.1:1235/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-8b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

Or with the OpenAI Python SDK:

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:1235/v1", api_key="local")
response = client.chat.completions.create(
    model="qwen3-8b",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

---

## Web UI

The server exposes a built-in dashboard at `/`.

The UI includes:

- interactive chat against the loaded model
- model registry view and model activation
- live status and token-generation telemetry
- server log console streamed over SSE
- terminal command runner for local diagnostics
- links to examples and OpenAPI docs

Static assets are served from `/static/{path}` and are packaged under
`src/local_llm_server/static/`.

---

## CLI Reference

### `local-llm serve`

Start the inference server.

| Flag | Default | Description |
|---|---:|---|
| `--model <key>` | registry `default_model` | Registry model key |
| `--model-path <path>` | - | Direct GGUF path, MLX path, or HF model ref |
| `--backend <backend>` | registry/backend fallback | `llama_cpp`, `mlx`, or `llama_server` |
| `--host <host>` | `127.0.0.1` | Bind address |
| `--port <port>` | `1235` | Public HTTP port |
| `--ctx-size <n>` | model default | Context window size |
| `--n-gpu-layers <n>` | model default | GPU-offloaded layers |
| `--n-threads <n>` | `8` | CPU inference threads |
| `--llama-server-port <n>` | `8091` | Internal subprocess port for `llama_server` backend |
| `--llama-server-bin <path>` | auto-detect | Path to `llama-server` executable |
| `--mmproj-path <path>` | registry/auto-detect | Multimodal projector GGUF |
| `--startup-timeout <s>` | `60` | `llama-server` readiness timeout |
| `--chat-format <fmt>` | model default | llama.cpp chat format override |
| `--force-json / --no-force-json` | `false` | Request JSON output by default |
| `--enable-thinking / --no-enable-thinking` | model default | Enable thinking mode |
| `--show-thinking / --no-show-thinking` | `false` | Include `<think>` blocks in output |
| `--no-download` | `false` | Fail if model is not already downloaded |
| `--verbose` | `false` | Verbose logging |

### `local-llm models`

Print the merged built-in and user model registry, including backend and
download status.

### `local-llm download <key>`

Pre-download a registry model without starting the server.

```bash
local-llm download qwen3-8b
```

---

## Built-in Models

| Key | Backend | Parameters | Size | Tags |
|---|---|---:|---:|---|
| `nemotron-nano-4b` | `llama_cpp` | 4B | ~2.5 GB | reasoning, small |
| `nemotron-nano-4b-q8` | `llama_cpp` | 4B | ~4.3 GB | reasoning, small |
| `qwen3-8b` | `llama_cpp` | 8B | ~4.9 GB | reasoning, medium |
| `phi-3-mini` | `llama_cpp` | 3.8B | ~2.3 GB | instruct, small |
| `qwen2.5-7b` | `llama_cpp` | 7B | ~4.4 GB | instruct, medium |
| `voxtral-mini-3b` | `llama_server` | 3B | ~3.8 GB | multimodal, audio, small |

`voxtral-mini-3b` expects both the model GGUF and the `mmproj` projector. The
registry can auto-detect the LM Studio layout configured in
`models_registry.yaml`; otherwise pass `--model-path`, `--mmproj-path`, and
`--llama-server-bin` explicitly.

---

## Configuration

All major CLI flags have matching environment variables.

| Variable | Description |
|---|---|
| `LOCAL_LLM_HOST` | Bind host |
| `LOCAL_LLM_PORT` | Public HTTP port |
| `LOCAL_LLM_BACKEND` | Backend override |
| `LOCAL_LLM_CTX_SIZE` | Context window size |
| `LOCAL_LLM_N_GPU_LAYERS` | GPU layers |
| `LOCAL_LLM_N_THREADS` | CPU threads |
| `LOCAL_LLM_N_BATCH` | Batch size |
| `LOCAL_LLM_N_UBATCH` | Micro-batch size |
| `LOCAL_LLM_CHAT_FORMAT` | Chat format |
| `LOCAL_LLM_FORCE_JSON` | Force JSON output (`1`/`0`) |
| `LOCAL_LLM_ENABLE_THINKING` | Enable thinking (`1`/`0`) |
| `LOCAL_LLM_SHOW_THINKING` | Show thinking blocks (`1`/`0`) |
| `LOCAL_LLM_VERBOSE` | Verbose logging (`1`/`0`) |
| `LOCAL_LLM_TIMEOUT` | Request timeout in seconds |
| `LOCAL_LLM_SERVER_PORT` | Internal `llama-server` port |
| `LOCAL_LLM_SERVER_BIN` | `llama-server` executable path |
| `LOCAL_LLM_STARTUP_TIMEOUT` | `llama-server` startup timeout |

### Custom model registry

Add or override models in `~/.local-llm/models.yaml`:

```yaml
models:
  my-model:
    filename: "my-model-Q4_K_M.gguf"
    url: "https://huggingface.co/.../my-model-Q4_K_M.gguf"
    model_id: "org/my-model"
    size_gb: 3.0
    backend: llama_cpp
    params:
      ctx_size: 8192
      n_gpu_layers: 35
      enable_thinking: false
    tags: [instruct, custom]
```

Multimodal example:

```yaml
models:
  my-audio-model:
    filename: "model.gguf"
    mmproj_filename: "mmproj-model.gguf"
    backend: llama_server
    multimodal: true
    modalities: [text, audio]
    params:
      ctx_size: 4096
```

Serve it:

```bash
local-llm serve --model my-model
```

---

## Python API

### Start the server

```python
import local_llm_server as llm

handle = llm.serve(model="qwen3-8b", port=1235, background=True)

# ... use the server ...

handle.shutdown()
```

Foreground mode blocks until shutdown:

```python
import local_llm_server as llm

llm.serve(model="qwen3-8b", host="0.0.0.0", port=1235)
```

### Registry helpers

```python
import local_llm_server as llm

llm.download_model("phi-3-mini")

for model in llm.list_models():
    print(model["key"], model["backend"], model["downloaded"])
```

### High-level client

`LocalLLMClient` wraps common text and audio analysis workflows.

```python
from local_llm_server import LocalLLMClient

client = LocalLLMClient(base_url="http://127.0.0.1:1235", model="qwen3-8b")

result = client.analyze_text(
    "Discussione: completare il rilascio entro venerdi e preparare rollback.",
    language="it",
)
print(result["summary"])
```

It can also auto-start a background server:

```python
from local_llm_server import LocalLLMClient

client = LocalLLMClient(model="nemotron-nano-4b", auto_serve=True)
try:
    print(client.chat([{"role": "user", "content": "What is 2 + 2?"}]))
finally:
    client.shutdown()
```

### Audio helpers

Install `local-llm-server[audio]` first.

```python
from local_llm_server import LocalLLMClient, prepare_audio_message

messages = prepare_audio_message("meeting.mp3", "Trascrivi e riassumi.")

client = LocalLLMClient(base_url="http://127.0.0.1:1235", model="voxtral-mini-3b")
summary = client.analyze_audio("meeting.mp3", task="summary", language="it")
```

---

## HTTP API

The server exposes these routes:

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Web UI dashboard |
| `GET` | `/static/{path}` | Web UI static assets |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/redoc` | ReDoc |
| `GET` | `/example` | Interactive API usage examples |
| `GET` | `/health` | Health check and server metadata |
| `GET` | `/status` | Runtime generation status |
| `GET` | `/api/v1/status` | Runtime generation status alias |
| `GET` | `/v1/models` | OpenAI-compatible loaded model list |
| `GET` | `/api/v1/models` | Loaded model list alias |
| `GET` | `/api/v1/models/registry` | Full configured model registry |
| `POST` | `/v1/chat/completions` | OpenAI-compatible chat completions, streaming supported |
| `POST` | `/api/v1/chat` | Chat completion alias |
| `POST` | `/api/v1/models/load` | LM Studio compatibility endpoint |
| `POST` | `/api/v1/models/activate` | Activate a registry model at runtime |
| `GET` | `/api/v1/logs/stream` | Server logs over SSE |
| `POST` | `/api/v1/terminal/run` | Run terminal commands from the Web UI |

---

## Remote or VM Access

Bind to all interfaces when the server must be reachable outside the local
machine:

```bash
local-llm serve --host 0.0.0.0 --port 1235 --model qwen3-8b
```

Then open `http://<server-ip>:1235/`.

---

## Development

Run tests:

```bash
pytest
```

Run the batch inference example against a running server:

```bash
uv run python test_inference.py --server-url http://127.0.0.1:1235/v1
```

Build distribution artifacts:

```bash
./deploy.sh
```

The v0.2 implementation plan is tracked in
`docs/IMPLEMENTATION_PLAN_v0.2.md`.

---

## License

MIT

# local-llm-server

Self-contained local LLM server with an **OpenAI-compatible API**, powered by [`llama-cpp-python`](https://github.com/abetlen/llama-cpp-python).  
Run quantised GGUF models locally and query them with any OpenAI SDK or HTTP client.

---

## Requirements

- Python ≥ 3.10
- A C/C++ compiler (for `llama-cpp-python` build)
- macOS / Linux (GPU offload supported via Metal on Apple Silicon or CUDA on Linux)

---

## Installation

```bash
pip install .
```

For development (adds `pytest`, `httpx`, `ruff`):

```bash
pip install ".[dev]"
```

---

## Quick start

### 1 — List available models

```bash
local-llm models
```

### 2 — Start the server

```bash
local-llm serve --model qwen3-8b
```

The server starts on `http://127.0.0.1:1235` by default.  
The model is downloaded automatically on first run (stored in `~/.local-llm/models/`).

### 3 — Send a request

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

### 4 — Batch Inference & Testing

For a complete, modular example of how to perform batch inference tests (e.g. classification of items using structured JSON output and performance reporting), refer to [test_inference.py](file:///Users/moltisantid/Personal/local-llm-server/test_inference.py).

You can run this test suite using:
```bash
uv run python test_inference.py --server-url http://127.0.0.1:1235/v1
```

---

## CLI reference

### `local-llm serve`

Start the inference server.

| Flag | Default | Description |
|---|---|---|
| `--model <key>` | registry `default_model` | Registry model key (e.g. `qwen3-8b`) |
| `--model-path <path>` | — | Direct path to a `.gguf` file (bypasses registry) |
| `--host <host>` | `127.0.0.1` | Bind address |
| `--port <port>` | `1235` | Listen port |
| `--ctx-size <n>` | model default | Context window size in tokens |
| `--n-gpu-layers <n>` | model default | Layers offloaded to GPU (0 = CPU only) |
| `--n-threads <n>` | `8` | CPU inference threads |
| `--chat-format <fmt>` | model default | llama.cpp chat format override |
| `--force-json / --no-force-json` | `true` | Enforce JSON output format |
| `--enable-thinking / --no-enable-thinking` | model default | Enable chain-of-thought reasoning |
| `--show-thinking / --no-show-thinking` | `false` | Include `<think>` blocks in the response |
| `--no-download` | — | Fail if model is not already downloaded |
| `--verbose` | — | Enable verbose llama.cpp logging |

### `local-llm models`

Print all models available in the registry with their size and tags.

### `local-llm download <key>`

Pre-download a model without starting the server.

```bash
local-llm download qwen3-8b
```

---

## Built-in models

| Key | Parameters | Size | Tags |
|---|---|---|---|
| `qwen3-8b` | 8B | ~4.9 GB | reasoning, medium |
| `qwen2.5-7b` | 7B | ~4.4 GB | instruct, medium |
| `nemotron-nano-4b` | 4B | ~2.5 GB | reasoning, small |
| `phi-3-mini` | 3.8B | ~2.3 GB | instruct, small |

---

## Configuration

### Environment variables

All CLI flags have a corresponding environment variable:

| Variable | Description |
|---|---|
| `LOCAL_LLM_HOST` | Bind host |
| `LOCAL_LLM_PORT` | Listen port |
| `LOCAL_LLM_CTX_SIZE` | Context window size |
| `LOCAL_LLM_N_GPU_LAYERS` | GPU layers |
| `LOCAL_LLM_N_THREADS` | CPU threads |
| `LOCAL_LLM_CHAT_FORMAT` | Chat format |
| `LOCAL_LLM_FORCE_JSON` | Force JSON output (`1`/`0`) |
| `LOCAL_LLM_ENABLE_THINKING` | Enable thinking (`1`/`0`) |
| `LOCAL_LLM_SHOW_THINKING` | Show thinking blocks (`1`/`0`) |
| `LOCAL_LLM_VERBOSE` | Verbose logging (`1`/`0`) |
| `LOCAL_LLM_TIMEOUT` | Request timeout in seconds |

### Custom model registry

Add your own models by creating `~/.local-llm/models.yaml`:

```yaml
models:
  my-model:
    filename: "my-model-Q4_K_M.gguf"
    url: "https://huggingface.co/.../my-model-Q4_K_M.gguf"
    model_id: "org/my-model"
    size_gb: 3.0
    params:
      ctx_size: 8192
      n_gpu_layers: 35
      enable_thinking: false
    tags: [instruct, custom]
```

Then serve it:

```bash
local-llm serve --model my-model
```

### Use a local GGUF file directly

```bash
local-llm serve --model-path /path/to/model.gguf --ctx-size 8192 --n-gpu-layers 35
```

---

## Use as a library

Install the package and import directly — no CLI needed.

### Start the server in the background

```python
import local_llm_server as llm

# Starts in a background thread, returns a handle
handle = llm.serve(model="qwen3-8b", port=1235, background=True)

# … do other work …

handle.shutdown()
```

### Start the server in the foreground (blocking)

```python
import local_llm_server as llm

# Blocks until SIGINT / SIGTERM
llm.serve(model="qwen3-8b", host="0.0.0.0", port=1235)
```

Pass any inference parameter as a keyword argument:

```python
llm.serve(
    model="qwen3-8b",
    background=True,
    ctx_size=8192,
    n_gpu_layers=35,
    enable_thinking=True,
    show_thinking=False,
)
```

### Use a local GGUF file

```python
llm.serve(model_path="/path/to/model.gguf", background=True)
```

### Pre-download a model

```python
llm.download_model("phi-3-mini")
```

### Query the model registry

```python
models = llm.list_models()
for m in models:
    status = "✓" if m["downloaded"] else "✗"
    print(f"{status} {m['key']} ({m['size_gb']} GB) — {m['tags']}")
```

### Full example: start + query

```python
import time
import local_llm_server as llm
from openai import OpenAI

handle = llm.serve(model="qwen3-8b", port=1235, background=True)
time.sleep(2)  # wait for the server to be ready

client = OpenAI(base_url="http://127.0.0.1:1235/v1", api_key="local")
response = client.chat.completions.create(
    model="qwen3-8b",
    messages=[{"role": "user", "content": "What is 2 + 2?"}],
)
print(response.choices[0].message.content)

handle.shutdown()
```

---

## API endpoints & Interactive Documentation

The server automatically generates interactive OpenAPI documentation. When the server is running, you can access the specifications at:
* 📖 **Swagger UI (Interactive)**: `http://127.0.0.1:1235/docs`
* 📘 **ReDoc**: `http://127.0.0.1:1235/redoc`

The following endpoints are exposed:

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/chat/completions` | Chat completion (OpenAI compatible, supports streaming) |
| `POST` | `/api/v1/chat` | Chat completion (alias) |
| `GET` | `/v1/models` | List loaded models |
| `GET` | `/api/v1/models` | List loaded models (alias) |
| `GET` | `/health` | Health check and server metadata |
| `GET` | `/status` | Real-time performance & status monitoring |
| `GET` | `/api/v1/status` | Real-time performance & status monitoring (alias) |
| `GET` | `/api/v1/models/registry` | List all models available in registry |
| `GET` | `/api/v1/logs/stream` | Server console log stream (SSE format) |
| `POST` | `/api/v1/models/load` | LM Studio compatibility endpoint |
| `GET` | `/example` | Dynamic code examples (cURL, Python SDK, batch tests) |
| `GET` | `/docs` | Interactive Swagger UI API documentation |
| `GET` | `/redoc` | ReDoc API documentation |

---

## License

MIT

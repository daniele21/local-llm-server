# Analisi: Server LLM Locale — Libreria Autoinstallante

## Problema

Il server attuale (`llama_cpp_server.py`) è fortemente accoppiato a un singolo modello (Nemotron-3-Nano-4B). Nomi di classi, logger, URL di download, percorsi e parametri sono hardcoded. Se si vuole cambiare modello (es. passare a Mistral, Phi-3, Qwen, DeepSeek), bisogna modificare il codice sorgente in più punti. Inoltre, l'installazione è manuale e richiede conoscenze tecniche.

**Obiettivo**: creare un **pacchetto Python installabile** (`pip install`) che:
1. Si installa con tutte le dipendenze in un comando
2. Scarica automaticamente il modello scelto al primo avvio
3. Espone un comando CLI per lanciare il server (`local-llm serve`)
4. Funziona come libreria importabile da altri progetti Python
5. È model-agnostic — cambiare modello = un flag, non una modifica al codice

---

## 1. Esperienza Utente Target

```bash
# Installazione completa (una sola volta)
pip install local-llm-server

# Primo avvio — scarica il modello di default e lancia il server
local-llm serve

# Avvio con modello specifico
local-llm serve --model qwen3-8b

# Lista modelli disponibili nel registry
local-llm models

# Scarica un modello senza avviare il server
local-llm download qwen3-8b

# Uso come libreria Python da un altro progetto
from local_llm_server import serve
serve(model="qwen3-8b", port=1235)
```

**Zero configurazione manuale. Zero dipendenze da gestire a mano. Un comando e funziona.**

---

## 2. Struttura del Pacchetto

```
local-llm-server/
├── pyproject.toml              # Metadata pacchetto + dipendenze
├── setup.py                    # Backward-compat (opzionale, wrappa pyproject)
├── README.md
├── LICENSE
├── src/
│   └── local_llm_server/
│       ├── __init__.py         # Exports pubblici (serve, download_model)
│       ├── __main__.py         # python -m local_llm_server
│       ├── cli.py              # Entry point CLI (local-llm)
│       ├── server.py           # HTTP server + handlers
│       ├── engine.py           # Wrapper llama-cpp-python
│       ├── registry.py         # Caricamento/merge model registry
│       ├── downloader.py       # Download modelli con resume + progress bar
│       ├── config.py           # Config resolution (CLI > env > registry > default)
│       └── models_registry.yaml  # Registry built-in (shipped col pacchetto)
└── tests/
    ├── test_registry.py
    ├── test_server.py
    └── test_smoke.sh
```

---

## 3. Packaging: `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "local-llm-server"
version = "0.1.0"
description = "Self-contained local LLM server with OpenAI-compatible API"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
authors = [{name = "Your Name"}]

dependencies = [
    "llama-cpp-python>=0.3.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
# Per chi vuole Metal (macOS Apple Silicon) — compilazione automatica
metal = ["llama-cpp-python>=0.3.0"]
# Per chi vuole CUDA (NVIDIA)
cuda = ["llama-cpp-python[cuda]>=0.3.0"]
# Dev/test
dev = ["pytest", "httpx", "ruff"]

[project.scripts]
# Comandi CLI installati globalmente
local-llm = "local_llm_server.cli:main"

[project.entry-points."local_llm_server.models"]
# Plugin point per registry custom (futuro)

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
local_llm_server = ["models_registry.yaml"]
```

### 3.1 Perché `pyproject.toml` e non solo `setup.py`

- Standard moderno (PEP 621) — supportato da pip, build, poetry, pdm
- `setup.py` rimane come shim per backward-compat:

```python
# setup.py (opzionale, per pip install -e . su Python vecchi)
from setuptools import setup
setup()
```

### 3.2 Dipendenze: Strategia Minimale

| Dipendenza | Ruolo | Perché |
|-----------|-------|--------|
| `llama-cpp-python` | Engine inference GGUF | Core — senza questo nulla funziona |
| `pyyaml` | Parsing registry YAML | Leggero (~100KB), stabile |

**Nessuna altra dipendenza**. Il server HTTP usa `http.server` della stdlib. Niente Flask, FastAPI, uvicorn — si mantiene la filosofia attuale di zero-overhead.

### 3.3 Compilazione llama-cpp-python

Su macOS Apple Silicon, `pip install llama-cpp-python` compila automaticamente con Metal se Xcode CLI tools sono presenti. Per semplificare:

```bash
# macOS (Metal auto-detected)
pip install local-llm-server

# Linux/Windows con NVIDIA GPU
CMAKE_ARGS="-DGGML_CUDA=on" pip install local-llm-server

# CPU-only (fallback universale)
pip install local-llm-server
```

Il `README.md` documenterà queste varianti. Il pacchetto non forza CUDA/Metal — lascia che `llama-cpp-python` gestisca l'auto-detect.

---

## 4. CLI: Comandi e Subcomandi

```python
# src/local_llm_server/cli.py
"""
Entry point CLI.

Comandi:
  local-llm serve [--model NAME] [--port N] [--host H] [...]
  local-llm models [--verbose]
  local-llm download MODEL_NAME
  local-llm info MODEL_NAME
"""
```

### 4.1 `local-llm serve`

| Flag | Default | Descrizione |
|------|---------|-------------|
| `--model` | `nemotron-nano-4b` | Chiave dal registry |
| `--model-path` | (da registry) | Override: path GGUF diretto |
| `--port` | `1235` | Porta HTTP |
| `--host` | `127.0.0.1` | Bind address |
| `--ctx-size` | (da registry) | Override context window |
| `--n-gpu-layers` | (da registry) | Override GPU offload |
| `--no-force-json` | `false` | Disabilita output JSON forzato |
| `--show-thinking` | `false` | Mostra blocchi `<think>` |
| `--no-download` | `false` | Fallisce se modello assente (no auto-download) |

### 4.2 `local-llm models`

```
$ local-llm models

Available models:
  nemotron-nano-4b    nvidia/nemotron-3-nano-4b       2.5 GB   [reasoning, 4b]    ✅ downloaded
  qwen3-8b           qwen/qwen3-8b                   4.9 GB   [reasoning, 8b]    ❌ not downloaded
  phi-3-mini          microsoft/phi-3-mini            2.3 GB   [instruct, 3.8b]   ❌ not downloaded
  qwen2.5-7b         qwen/qwen2.5-7b-instruct        4.4 GB   [instruct, 7b]     ❌ not downloaded

Default: nemotron-nano-4b
Models dir: ~/.local-llm/models/
```

### 4.3 `local-llm download`

```
$ local-llm download qwen3-8b

Downloading qwen/qwen3-8b (4.9 GB)...
Source: https://huggingface.co/unsloth/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf
Target: ~/.local-llm/models/Qwen3-8B-Q4_K_M.gguf

[████████████████████░░░░░░░░░░] 68% — 3.3/4.9 GB — 45 MB/s — ETA 36s
```

---

## 5. Model Registry (Built-in)

Shipped dentro il pacchetto come risorsa (`package_data`). L'utente può sovrascrivere con `~/.local-llm/models.yaml`.

```yaml
# src/local_llm_server/models_registry.yaml
models_dir: ~/.local-llm/models

defaults:
  n_threads: 8
  n_batch: 512
  n_ubatch: 512
  offload_kqv: true
  flash_attn: true
  use_mmap: true

models:
  nemotron-nano-4b:
    filename: "NVIDIA-Nemotron-3-Nano-4B-Q4_K_M.gguf"
    url: "https://huggingface.co/lmstudio-community/NVIDIA-Nemotron-3-Nano-4B-GGUF/resolve/main/NVIDIA-Nemotron-3-Nano-4B-Q4_K_M.gguf"
    model_id: "nvidia/nemotron-3-nano-4b"
    size_gb: 2.5
    params:
      ctx_size: 36466
      n_gpu_layers: 42
      enable_thinking: true
    tags: [reasoning, small, 4b]

  qwen3-8b:
    filename: "Qwen3-8B-Q4_K_M.gguf"
    url: "https://huggingface.co/unsloth/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf"
    model_id: "qwen/qwen3-8b"
    size_gb: 4.9
    params:
      ctx_size: 40960
      n_gpu_layers: 37
      enable_thinking: true
      default_temperature: 0.6
    tags: [reasoning, medium, 8b]

  phi-3-mini:
    filename: "Phi-3-mini-4k-instruct-Q4_K_M.gguf"
    url: "https://huggingface.co/bartowski/Phi-3-mini-4k-instruct-GGUF/resolve/main/Phi-3-mini-4k-instruct-Q4_K_M.gguf"
    model_id: "microsoft/phi-3-mini"
    size_gb: 2.3
    params:
      ctx_size: 4096
      n_gpu_layers: 35
      enable_thinking: false
    tags: [instruct, small, 3.8b]

  qwen2.5-7b:
    filename: "Qwen2.5-7B-Instruct-Q4_K_M.gguf"
    url: "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
    model_id: "qwen/qwen2.5-7b-instruct"
    size_gb: 4.4
    params:
      ctx_size: 32768
      n_gpu_layers: 35
      enable_thinking: false
      chat_format: "chatml"
    tags: [instruct, medium, 7b]

default_model: nemotron-nano-4b
```

### 5.1 Registry Resolution (merge order)

```
1. Built-in registry (nel pacchetto)          ← base
2. User registry (~/.local-llm/models.yaml)   ← aggiunge/sovrascrive modelli
3. CLI flags                                   ← override puntuale
```

L'utente può aggiungere modelli custom senza toccare il pacchetto:

```yaml
# ~/.local-llm/models.yaml (user override)
models:
  my-custom-model:
    filename: "my-finetuned-7b-q5.gguf"
    model_id: "custom/my-model"
    params:
      ctx_size: 8192
      n_gpu_layers: 35
```

---

## 6. Auto-Download dei Modelli

### 6.1 Flusso al Primo Avvio

```
local-llm serve --model qwen3-8b
        │
        ▼
┌─ Modello presente in ~/.local-llm/models/ ? ─┐
│                                                │
│  SÌ → carica e avvia                         │
│  NO → scarica con progress bar → poi avvia    │
└────────────────────────────────────────────────┘
```

### 6.2 Implementazione Download

```python
# src/local_llm_server/downloader.py

def download_model(url: str, dest: Path, *, resume: bool = True) -> None:
    """
    Download con:
    - Resume automatico (Range header)
    - Progress bar in terminale (no dipendenze extra)
    - Scrittura su file .part, rename atomico a completamento
    - Timeout e retry (3 tentativi)
    """
```

Caratteristiche:
- **Resume**: se il download si interrompe, riprende da dove era rimasto
- **Atomic write**: scrive su `.gguf.part`, rinomina solo a successo
- **Progress bar**: usa `\r` + ANSI escape (zero dipendenze)
- **Nessun `tqdm`/`rich` richiesto** — mantiene dipendenze minime

### 6.3 Flag `--no-download`

Per ambienti CI/air-gapped dove non si vuole download automatico:

```bash
local-llm serve --model qwen3-8b --no-download
# → errore se il modello non è già presente
```

---

## 7. Uso come Libreria Python

Oltre al CLI, il pacchetto è importabile programmaticamente:

```python
# Da un altro progetto Python
from local_llm_server import serve, download_model, list_models

# Avvia server in background thread
server = serve(
    model="qwen3-8b",
    port=1235,
    background=True  # ritorna subito, server gira in thread
)

# ... il tuo codice che interroga http://localhost:1235/v1/chat/completions ...

server.shutdown()
```

```python
# Pre-download modello (es. in uno script di setup)
from local_llm_server import download_model

download_model("qwen3-8b")  # Scarica se assente, no-op se presente
```

```python
# Integrazione con __main__ per python -m
# python -m local_llm_server serve --model qwen3-8b
```

---

## 8. Installazione: Scenari Concreti

### 8.1 Utente Finale (macOS Apple Silicon)

```bash
# 1. Installa
pip install local-llm-server

# 2. Lancia (scarica modello al primo avvio, ~2.5 GB)
local-llm serve

# 3. Da un altro terminale, testa
curl http://localhost:1235/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"ciao"}]}'
```

### 8.2 Sviluppatore (in un progetto esistente)

```bash
# Aggiunge come dipendenza
pip install local-llm-server

# Oppure in requirements.txt / pyproject.toml
# dependencies = ["local-llm-server>=0.1.0"]
```

```python
# Nel codice del progetto
from local_llm_server import serve
import threading

# Avvia il server LLM come parte del tuo stack
server = serve(model="nemotron-nano-4b", port=1235, background=True)
```

### 8.3 Docker / CI

```dockerfile
FROM python:3.11-slim
RUN pip install local-llm-server
# Pre-download modello nel layer Docker
RUN local-llm download nemotron-nano-4b
EXPOSE 1235
CMD ["local-llm", "serve"]
```

### 8.4 Sviluppo locale (editable install)

```bash
git clone <repo>
cd local-llm-server
pip install -e ".[dev]"

# Ora puoi modificare il codice e testare immediatamente
local-llm serve --model phi-3-mini
```

---

## 9. API Contract (OpenAI-Compatible)

Il consumer **non deve sapere** quale modello gira. L'interfaccia esposta:

### 9.1 Endpoints

| Metodo | Path | Descrizione |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/v1/models` | Lista modelli caricati |
| `GET` | `/status` | Stato inferenza corrente |
| `POST` | `/v1/chat/completions` | Chat inference |

### 9.2 Integrazione con SDK Esistenti

```python
# OpenAI SDK — funziona senza modifiche
from openai import OpenAI
client = OpenAI(base_url="http://localhost:1235/v1", api_key="not-needed")
response = client.chat.completions.create(
    model="local",
    messages=[{"role": "user", "content": "Hello"}]
)

# LangChain — funziona senza modifiche
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(base_url="http://localhost:1235/v1", api_key="x", model="local")
```

### 9.3 Environment-Based Discovery (per il consumer)

```bash
# .env del servizio consumer
LLM_BASE_URL=http://localhost:1235/v1
LLM_API_KEY=not-needed
```

Se domani passi a OpenAI cloud, cambi solo l'env — il codice consumer resta invariato.

---

## 10. Config Resolution

Ordine di precedenza (dalla più alta alla più bassa):

```
1. CLI flags            (--ctx-size 8192)           ← massima priorità
2. Environment vars     (LOCAL_LLM_CTX_SIZE=8192)
3. User registry        (~/.local-llm/models.yaml)
4. Built-in registry    (nel pacchetto)
5. Defaults hardcoded   (fallback sicuri)           ← minima priorità
```

---

## 11. Gestione Differenze tra Modelli

### Chat Template

`llama-cpp-python` auto-detecta il template dal GGUF nella maggior parte dei casi. Il registry specifica `chat_format` solo quando serve un override esplicito.

### Reasoning Models (Think Tokens)

La logica `_strip_thinking_blocks()` è già model-agnostic. Funziona con qualsiasi modello che emetta `<think>...</think>`.

### Parametri Ottimali

Ogni modello ha i suoi parametri pre-configurati nel registry. L'utente non deve sapere che Qwen3 vuole `temperature=0.6` o che Nemotron ha `ctx_size=36466` — il registry li fornisce automaticamente.

---

## 12. Checklist di Implementazione

### Fase 1: Packaging
- [ ] Creare struttura `src/local_llm_server/`
- [ ] Scrivere `pyproject.toml` con dipendenze e entry points
- [ ] Creare `__init__.py` con exports pubblici
- [ ] Creare `__main__.py` per `python -m local_llm_server`
- [ ] Creare `cli.py` con subcomandi (`serve`, `models`, `download`)

### Fase 2: Generalizzazione
- [ ] Rinominare classi (da `Nemotron*` a `LocalLLM*`)
- [ ] Creare `models_registry.yaml` built-in con 4 modelli
- [ ] Implementare `registry.py` (load + merge built-in e user)
- [ ] Implementare `config.py` (resolution CLI > env > registry > defaults)
- [ ] Generalizzare `downloader.py` (progress bar, resume, atomic write)
- [ ] Cambiare directory default a `~/.local-llm/models/`

### Fase 3: Testing
- [ ] Smoke test script (`local-llm serve` + curl)
- [ ] Test unitari per registry e config resolution
- [ ] Verificare `pip install -e .` funziona end-to-end
- [ ] Testare con almeno 2 modelli diversi

---

## 13. Principi di Design

| Principio | Applicazione |
|-----------|-------------|
| **Un comando per partire** | `pip install` + `local-llm serve` = funziona |
| **Convention over Configuration** | Registry fornisce default sensati per ogni modello |
| **Zero dipendenze superflue** | Solo `llama-cpp-python` + `pyyaml`. HTTP server = stdlib |
| **Model-Agnostic** | Nessuna logica specifica per nessun modello |
| **Backward-Compatible** | `--model-path` diretto funziona ancora (no registry obbligatorio) |
| **Libreria + CLI** | Usabile da terminale O da codice Python |
| **Offline-Friendly** | Dopo il primo download, funziona senza internet |

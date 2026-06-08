"""
example_server.py — esempio di utilizzo di local-llm-server come libreria.

Avvia il server con un modello locale (path diretto), esegue una chiamata
di test via OpenAI SDK e poi spegne il server.

Eseguire con:
    python example_server.py
"""

import time
import sys

import local_llm_server as llm

# ── Configurazione ─────────────────────────────────────────────────────────────

# MODEL_PATH = "~/.redactguard/models/NVIDIA-Nemotron-3-Nano-4B-Q4_K_M.gguf"
MODEL_PATH = "/Users/moltisantid/.lmstudio/models/smdesai/Nemotron-Labs-Diffusion-3B-4bit"


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 1235

INFERENCE_PARAMS = {
    "ctx_size": 36466,
    "n_gpu_layers": 42,   # imposta 0 per usare solo CPU
    "n_threads": 8,
    "enable_thinking": True,
    "show_thinking": False,
    "verbose": False,
}

# ── Avvio server ───────────────────────────────────────────────────────────────

print(f"[*] Avvio server su {SERVER_HOST}:{SERVER_PORT} ...")
print(f"[*] Modello: {MODEL_PATH}")

handle = llm.serve(
    model_path=MODEL_PATH,
    host=SERVER_HOST,
    port=SERVER_PORT,
    background=True,
    **INFERENCE_PARAMS,
)

# Attende che il server sia pronto ad accettare connessioni
print("[*] Attendo che il server sia pronto ...", end="", flush=True)
time.sleep(5)
print(" pronto.")

# ── Test con OpenAI SDK ────────────────────────────────────────────────────────

try:
    from openai import OpenAI
except ImportError:
    print("\n[!] openai non installato. Installa con: pip install openai")
    handle.shutdown()
    sys.exit(1)

client = OpenAI(
    base_url=f"http://{SERVER_HOST}:{SERVER_PORT}/v1",
    api_key="local",        # qualsiasi stringa non vuota è accettata
)

MESSAGES = [
    {"role": "system", "content": "Sei un assistente utile e conciso."},
    {"role": "user",   "content": "Cos'è un Large Language Model? Rispondi in 2 frasi."},
]

print("\n[*] Invio richiesta al server ...")
print(f"    User: {MESSAGES[-1]['content']}\n")

t0 = time.perf_counter()
response = client.chat.completions.create(
    model="local-model",    # il valore è ignorato dal server, può essere qualsiasi stringa
    messages=MESSAGES,
    temperature=0.6,
    max_tokens=256,
)
elapsed = time.perf_counter() - t0

answer = response.choices[0].message.content
completion_tokens = response.usage.completion_tokens
tokens_per_sec = completion_tokens / elapsed if elapsed > 0 else 0

print(f"    Assistant: {answer}")
print(f"\n[*] Token utilizzati:  prompt={response.usage.prompt_tokens}  completion={completion_tokens}  total={response.usage.total_tokens}")
print(f"[*] Tempo risposta:    {elapsed:.2f}s")
print(f"[*] Velocità:          {tokens_per_sec:.1f} token/s")

# ── Spegnimento ────────────────────────────────────────────────────────────────

print("\n[*] Spegnimento server ...")
handle.shutdown()
print("[*] Done.")

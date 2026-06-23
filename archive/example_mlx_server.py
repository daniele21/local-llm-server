"""
example_mlx_server.py — esempio di utilizzo di local-llm-server con backend MLX.

Avvia il server con un modello MLX locale, esegue una chiamata
di test via OpenAI SDK e poi spegne il server.

Eseguire con:
    .venv/bin/python example_mlx_server.py
"""

import time
import sys

import local_llm_server as llm

# ── Configurazione ─────────────────────────────────────────────────────────────

MODEL_PATH = "mlx-community/Qwen2.5-0.5B-Instruct-4bit"
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 1235

INFERENCE_PARAMS = {
    "backend": "mlx",
    "force_json": False,
    "show_thinking": False,
    "verbose": False,
}

# ── Avvio server ───────────────────────────────────────────────────────────────

print(f"[*] Avvio server su {SERVER_HOST}:{SERVER_PORT} ...")
print(f"[*] Modello MLX: {MODEL_PATH}")

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
    print("\n[!] openai non installato. Installa con: .venv/bin/pip install openai")
    handle.shutdown()
    sys.exit(1)

client = OpenAI(
    base_url=f"http://{SERVER_HOST}:{SERVER_PORT}/v1",
    api_key="local",
)

MESSAGES = [
    {"role": "system", "content": "Sei un assistente utile e conciso."},
    {"role": "user",   "content": "Cos'è un Large Language Model? Rispondi in 2 frasi."},
]

print("\n[*] Invio richiesta al server ...")
print(f"    User: {MESSAGES[-1]['content']}\n")

t0 = time.perf_counter()
response = client.chat.completions.create(
    model="local-mlx-model",
    messages=MESSAGES,
    temperature=0.0,
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

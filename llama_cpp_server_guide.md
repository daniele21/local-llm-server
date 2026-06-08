# Guida all'utilizzo di llama_cpp_server.py

Questa guida spiega come configurare, avviare e interrogare il server locale [llama_cpp_server.py](file:///Users/moltisantid/Personal/local-anonimizer/anonimizer/llama_cpp_server.py). 

Il server è basato su `llama-cpp-python` ed espone un'interfaccia HTTP compatibile con le API di OpenAI e LM Studio, consentendo sia l'uso strutturato (JSON) sia quello general-purpose (testo libero).

---

## 1. Prerequisiti

Prima di avviare il server, assicurasi di aver installato le dipendenze richieste. Puoi installarle tramite `pip`:

```bash
pip install llama-cpp-python
```

> [!NOTE]
> Su macOS, l'installazione di `llama-cpp-python` compilerà automaticamente il backend Metal se sono presenti i command line tools di Xcode, permettendo l'accelerazione hardware su chip Apple Silicon (M1/M2/M3/M4).

### Download manuale del modello (opzionale)
Il server scarica automaticamente il modello alla prima esecuzione. Se preferisci scaricarlo manualmente tramite `wget` prima di lanciare il server:

1. Crea la directory di destinazione:
   ```bash
   mkdir -p ~/.redactguard/models
   ```
2. Scarica il file GGUF tramite `wget`:
   ```bash
   wget -O ~/.redactguard/models/NVIDIA-Nemotron-3-Nano-4B-Q4_K_M.gguf \
     https://huggingface.co/lmstudio-community/NVIDIA-Nemotron-3-Nano-4B-GGUF/resolve/main/NVIDIA-Nemotron-3-Nano-4B-Q4_K_M.gguf
   ```
   *(In alternativa, con `curl`:)*
   ```bash
   curl -L -o ~/.redactguard/models/NVIDIA-Nemotron-3-Nano-4B-Q4_K_M.gguf \
     https://huggingface.co/lmstudio-community/NVIDIA-Nemotron-3-Nano-4B-GGUF/resolve/main/NVIDIA-Nemotron-3-Nano-4B-Q4_K_M.gguf
   ```

---

## 2. Come avviare il server

Il server può essere avviato direttamente da terminale posizionandosi nella directory contenente lo script.

### Avvio base (Modalità predefinita - Forza JSON)
Per impostazione predefinita, il server scarica automaticamente il modello preconfigurato (Nemotron-3-Nano-4B, ~2.5 GB) se non presente nella cartella `~/.redactguard/models/`, e forza le risposte in formato JSON:

```bash
python anonimizer/llama_cpp_server.py
```

### Avvio in modalità General-Purpose (Disattiva JSON forzato)
Se vuoi usare il server per scopi generici (ad esempio conversare in linguaggio naturale senza che l'output debba essere un JSON strutturato), avvia il server passando il flag `--no-force-json`:

```bash
python anonimizer/llama_cpp_server.py --no-force-json
```

### Parametri e Opzioni utili

Puoi personalizzare il comportamento del server con le seguenti opzioni della linea di comando:

| Parametro | Descrizione | Default |
| :--- | :--- | :--- |
| `--host <host>` | Indirizzo IP su cui ascoltare | `127.0.0.1` |
| `--port <port>` | Porta su cui avviare il server | `1235` |
| `--model-path <path>` | Percorso locale del file del modello `.gguf` | `~/.redactguard/models/NVIDIA-Nemotron-3-Nano-4B-Q4_K_M.gguf` |
| `--ctx-size <num>` | Dimensione del contesto (Context Window) | `36466` |
| `--n-gpu-layers <num>` | Numero di layer da scaricare sulla GPU (Metal/CUDA) | `42` |
| `--no-force-json` | Disabilita la costrizione a rispondere in formato JSON | Attivo di default |
| `--show-thinking` | Mostra i blocchi `<think>` se presenti nel modello | `false` |

---

## 3. Come interrogare l'endpoint

Una volta avviato, il server rimarrà in ascolto all'indirizzo `http://127.0.0.1:1235/v1/chat/completions`. Puoi interrogarlo tramite client HTTP (es. `curl`, Postman, o client Python).

### Esempio 1: Richiesta General-Purpose (Testo Libero)
> [!IMPORTANT]
> Richiede che il server sia stato avviato con `--no-force-json` oppure che si stia specificando un formato testo.

#### Richiesta cURL:
```bash
curl -X POST http://127.0.0.1:1235/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "messages": [
         {"role": "system", "content": "Sei un assistente utile e sintetico."},
         {"role": "user", "content": "Scrivi una poesia di quattro righe sull'intelligenza artificiale."}
       ],
       "temperature": 0.7
     }'
```

#### Esempio in Python (usando la libreria `requests`):
```python
import requests

url = "http://127.0.0.1:1235/v1/chat/completions"
payload = {
    "messages": [
        {"role": "system", "content": "Sei un traduttore dall'italiano all'inglese."},
        {"role": "user", "content": "Il codice funziona perfettamente al primo colpo."}
    ],
    "temperature": 0.3
}

response = requests.post(url, json=payload)
data = response.json()

print(data["choices"][0]["message"]["content"])
```

---

### Esempio 2: Richiesta Strutturata (JSON Output)
Se vuoi che l'output sia forzatamente un JSON strutturato (ad esempio se usi il server per compiti di classificazione, estrazione di entità o PII), puoi richiedere esplicitamente il formato JSON nel payload.

#### Richiesta cURL:
```bash
curl -X POST http://127.0.0.1:1235/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "messages": [
         {"role": "system", "content": "Estrai il nome e la città dal testo fornito e restituisci un JSON con chiavi name e city."},
         {"role": "user", "content": "Mi chiamo Mario e vivo a Milano."}
       ],
       "response_format": {"type": "json_object"}
     }'
```

---

## 4. Monitorare lo stato e la velocità

Il server include un endpoint utile per controllare lo stato di avanzamento della generazione in tempo reale:

*   **Endpoint di health-check**: `GET http://127.0.0.1:1235/health`
*   **Endpoint delle performance**: `GET http://127.0.0.1:1235/status`

Quest'ultimo restituisce metriche utili come il numero di token generati, la velocità di inferenza (tokens per secondo) e se il modello sta attualmente elaborando una richiesta:

```json
{
  "active": false,
  "phase": "idle",
  "tokens_generated": 142,
  "max_tokens": 0,
  "tokens_per_second": 34.5,
  "model": "nvidia/nemotron-3-nano-4b"
}
```

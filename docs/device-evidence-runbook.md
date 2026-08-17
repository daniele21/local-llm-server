# Representative device evidence runbook

Status: active procedure
Owner: local-llm-server
Read when: executing TH-E1, EV-3, HE-2 or RES-2 on the representative Mac

This runbook turns the remaining evidence wave into repeatable commands. It intentionally uses placeholders because local model keys and filesystem paths are private/device-specific.

## Scope and safety

Run these procedures from the converged `dev` branch after installing the current package/environment.

Set local placeholders once:

```bash
MODEL="<model-key>"
MODEL_PATH="<absolute-path-to-model.gguf>"
EVIDENCE_DIR="$HOME/.local-llm-server/evidence/2026-08-17-converged"
mkdir -p "$EVIDENCE_DIR"
```

Rules:

- use the same exact GGUF for all comparable runs;
- do not put private model paths into committed evidence/docs;
- do not run multiple heavy model loads concurrently on one Mac merely to simulate plan parallelism;
- do not induce OOM, critical OS pressure or automatic eviction;
- retain negative, mixed and inconclusive results;
- do not generalize one-device or ten-sample observations into production-safety/model-quality claims.

## 0. Verify the exact artifact

Before HE-2 and preferably before TH-E1/EV-3, explicitly create/refresh the local verification receipt:

```bash
local-llm verify-artifact "$MODEL" --model-path "$MODEL_PATH"
```

Expected contract:

- command succeeds and reports a strong SHA-256 summary;
- receipt remains machine-local;
- later public runtime/evidence payloads may expose digest/fingerprint but never the private path;
- if the file changes, verification must be repeated.

## TH-E1 — real thinking OFF/ON smoke

Start the converged server with the representative runtime and admin API. Keep `Show thinking` disabled for the hidden-output checks.

```bash
local-llm serve \
  --model "$MODEL" \
  --model-path "$MODEL_PATH" \
  --backend llama_cpp \
  --enable-admin-api
```

In a second terminal, use the same prompt and deterministic sampling for both requests.

### OFF

```bash
curl -sS http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d "{
    \"model\": \"$MODEL\",
    \"messages\": [{\"role\": \"user\", \"content\": \"Reply with a concise explanation of why local inference can improve privacy.\"}],
    \"temperature\": 0,
    \"enable_thinking\": false,
    \"show_thinking\": false,
    \"stream\": false
  }" | tee "$EVIDENCE_DIR/thinking-off-response.json"
```

### ON, hidden

```bash
curl -sS http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d "{
    \"model\": \"$MODEL\",
    \"messages\": [{\"role\": \"user\", \"content\": \"Reply with a concise explanation of why local inference can improve privacy.\"}],
    \"temperature\": 0,
    \"enable_thinking\": true,
    \"show_thinking\": false,
    \"stream\": false
  }" | tee "$EVIDENCE_DIR/thinking-on-hidden-response.json"
```

Optionally perform one ON request with `show_thinking=true` to confirm visibility is independently controlled. Do not use the visible reasoning text as a correctness oracle.

Record alongside the local responses:

- runtime identity payload from `/v1/runtime/identity`;
- whether both requests completed or returned typed errors;
- confirmation that hidden mode did not mix reasoning into normal application content;
- any model-output difference as an observation only.

TH-E1 is complete when explicit OFF and ON are both exercised on the representative converged runtime and the output-exposure contract is confirmed.

## EV-3 — repeatable post-convergence evaluation

Run the server with `--enable-admin-api`, then execute the exact OFF workload twice.

### OFF run A

```bash
curl -sS http://127.0.0.1:8000/api/v1/evaluation/runs \
  -H 'Content-Type: application/json' \
  -d "{
    \"model\": \"$MODEL\",
    \"test_set_id\": \"general-purpose\",
    \"test_set_version\": \"1.0.0\",
    \"sample_count\": 10,
    \"seed\": 0,
    \"reasoning_policy\": \"off\"
  }" | tee "$EVIDENCE_DIR/evaluation-off-a.json"
```

### OFF run B

```bash
curl -sS http://127.0.0.1:8000/api/v1/evaluation/runs \
  -H 'Content-Type: application/json' \
  -d "{
    \"model\": \"$MODEL\",
    \"test_set_id\": \"general-purpose\",
    \"test_set_version\": \"1.0.0\",
    \"sample_count\": 10,
    \"seed\": 0,
    \"reasoning_policy\": \"off\"
  }" | tee "$EVIDENCE_DIR/evaluation-off-b.json"
```

Verify in both reports:

- same `test_set_identity`;
- same ten `sample_ids`;
- same seed;
- reasoning profile requested/effective state is explicitly represented;
- runtime fingerprint is present when verified identity/backend evidence are complete;
- every sample is either successful or carries an explicit failure code.

An optional ON run must be treated as a separate experiment:

```bash
curl -sS http://127.0.0.1:8000/api/v1/evaluation/runs \
  -H 'Content-Type: application/json' \
  -d "{
    \"model\": \"$MODEL\",
    \"test_set_id\": \"general-purpose\",
    \"test_set_version\": \"1.0.0\",
    \"sample_count\": 10,
    \"seed\": 0,
    \"reasoning_policy\": \"on\"
  }" | tee "$EVIDENCE_DIR/evaluation-on.json"
```

Do not describe score deltas as global model-quality improvement. Inspect concrete sample/scorer changes.

## HE-2 — two verified 3-cycle reclamation reports

Artifact verification must have succeeded first. Run two independent reports with the same model/backend/procedure.

```bash
local-llm evidence-reclamation \
  --model "$MODEL" \
  --model-path "$MODEL_PATH" \
  --backend llama_cpp \
  --cycles 3 \
  --max-tokens 32 \
  --settle-seconds 2 \
  --no-download \
  --output "$EVIDENCE_DIR/reclamation-a.json"
```

```bash
local-llm evidence-reclamation \
  --model "$MODEL" \
  --model-path "$MODEL_PATH" \
  --backend llama_cpp \
  --cycles 3 \
  --max-tokens 32 \
  --settle-seconds 2 \
  --no-download \
  --output "$EVIDENCE_DIR/reclamation-b.json"
```

Then run the conservative reviewer without exploratory overrides:

```bash
local-llm evidence-review \
  "$EVIDENCE_DIR/reclamation-a.json" \
  "$EVIDENCE_DIR/reclamation-b.json" \
  --min-reports 2 \
  --min-complete-cycles 6 \
  --output "$EVIDENCE_DIR/reclamation-review.json"
```

Acceptance:

- two reports are compatible on artifact/backend/config/environment/procedure;
- six cycles are attempted and lifecycle errors are reported truthfully;
- reviewer consumes verified identity by default;
- whatever recovery state is observed is retained;
- no automatic-eviction recommendation or production-safety claim is inferred.

Do **not** use `--allow-exploratory-identity` for HE-2 acceptance.

## RES-2 — bounded real-device resource policy smoke

Run the dedicated macOS safety-gated procedure:

```bash
python -m local_llm_server.resource_policy_smoke \
  --model "$MODEL" \
  --model-path "$MODEL_PATH" \
  --backend llama_cpp \
  --max-tokens 8 \
  --headroom-gib 0.5 \
  --success-margin-gib 0.5 \
  --host-safety-gib 2.0 \
  --output "$EVIDENCE_DIR/resource-policy-smoke.json"
```

The runner itself refuses execution when measured macOS available memory is below the model estimate plus configured success and host-safety margins.

A valid retained report must show:

- successful safe admission/load;
- positive committed accounting while resident;
- one successful HTTP inference;
- unload returns committed/reserved bytes and reservation count to zero;
- health is green and `cold` after final unload;
- deliberately insufficient budget is rejected before backend load;
- zero residency/reservations remain after reject;
- `automatic_eviction_exercised` is `false`.

If the safety gate refuses the run, record that result and free ordinary host memory before trying later; do not lower the host-safety margin merely to force a pass.

## Evidence completion checklist

Wave D is complete only when the local evidence directory contains, at minimum:

```text
thinking-off-response.json
thinking-on-hidden-response.json
evaluation-off-a.json
evaluation-off-b.json
reclamation-a.json
reclamation-b.json
reclamation-review.json
resource-policy-smoke.json
```

The local directory may contain private inference outputs and therefore should not be committed wholesale. Durable repository docs should record bounded conclusions, compatible identities/fingerprints where public-safe, and references/metadata needed for reproducibility without private paths or prompts.

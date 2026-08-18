# Representative device evidence runbook

Status: active procedure
Owner: local-llm-server
Read when: executing TH-E1, EV-3, HE-2 or RES-2 on the representative Mac
Last reviewed: 2026-08-18

This runbook turns the remaining L2 evidence wave into repeatable commands. Private model paths stay local. The final bundle validator emits a bounded public-safe summary and never promotes repository maturity automatically.

## Scope and safety

Run from the converged `dev` branch after installing the current environment.

```bash
MODEL="<model-key>"
MODEL_PATH="<absolute-path-to-model.gguf>"
EVIDENCE_DIR="$HOME/.local-llm-server/evidence/$(date +%F)-l2"
mkdir -p "$EVIDENCE_DIR"
```

Rules:

- use the same exact GGUF for all comparable runs;
- do not commit private model paths or raw inference content;
- serialize heavy model executions on one Mac;
- do not induce OOM, critical OS pressure or automatic eviction;
- retain negative, mixed and inconclusive observations;
- do not generalize one-device or ten-sample observations into production-safety/model-quality claims.

## 0. Verify the exact artifact

Before HE-2 and preferably before all comparable runs:

```bash
local-llm verify-artifact "$MODEL" --model-path "$MODEL_PATH"
```

The receipt remains machine-local. Public evidence may expose only the strong digest/fingerprint and verification grade, never the private path. If the file changes, verification must be repeated.

## 1. Start the representative runtime

TH-E1 and EV-3 use the same running server:

```bash
local-llm serve \
  --model "$MODEL" \
  --model-path "$MODEL_PATH" \
  --backend llama_cpp \
  --enable-admin-api
```

Keep this server isolated from other heavy model loads while the comparable runs execute.

## TH-E1 — explicit thinking OFF/ON without retaining output

In a second terminal run the packaged capture bridge:

```bash
python -m local_llm_server.l2_evidence_bridge capture-thinking \
  --base-url http://127.0.0.1:8000 \
  --model "$MODEL" \
  --output "$EVIDENCE_DIR/thinking-campaign.json"
```

The command itself sends the same deterministic local workload twice:

- explicit `enable_thinking=false`, `show_thinking=false`;
- explicit `enable_thinking=true`, `show_thinking=false`.

It retains only bounded request-policy flags, HTTP/result state, whether normal application content contains a `<think>` boundary, and the public runtime identity. It does **not** retain the prompt, output, raw response or private paths.

TH-E1 is acceptance-ready only when both requests complete with normal content and neither hidden response mixes reasoning boundaries into normal application content. Typed failures are still retained truthfully but do not become a fabricated successful campaign.

## EV-3 — repeatable post-convergence evaluation

With the same verified resident runtime, execute the exact OFF workload twice.

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
  }" > "$EVIDENCE_DIR/evaluation-off-a.json"
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
  }" > "$EVIDENCE_DIR/evaluation-off-b.json"
```

The final bundle validator checks that the two reports have:

- `general-purpose` `v1.0.0`, exactly ten samples and seed `0`;
- identical test-set identity and sample selection;
- explicit requested/effective reasoning `off`;
- compatible verified runtime fingerprint;
- complete results where every failed sample carries an explicit error code.

An optional ON evaluation is a separate experiment and is not part of the minimum L2 bundle:

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
  }" > "$EVIDENCE_DIR/evaluation-on.json"
```

Do not describe score deltas as global model-quality improvement.

## HE-2 — two verified 3-cycle reclamation reports

Stop the long-running server before starting isolated reclamation workers. Artifact verification must already have succeeded.

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

Do **not** use `--allow-exploratory-identity` for HE-2 acceptance. The final bundle validator recomputes the review from the two raw reports and rejects a stored review that disagrees with the conservative recomputation.

The observed recovery state may be positive, negative, mixed or inconclusive. No automatic-eviction recommendation or production-safety claim is inferred.

## RES-2 — bounded real-device resource-policy smoke

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

The runner refuses execution when measured macOS available memory is below the model estimate plus configured success and host-safety margins. Do not lower the safety margin merely to force a pass.

A complete report must show safe admission, positive committed accounting while resident, one HTTP inference, zero committed/reserved accounting after unload, green/cold health, insufficient-budget rejection before backend construction and `automatic_eviction_exercised=false`.

## 5. Validate the complete hardware bundle

After the four campaigns exist, run one deterministic review over the local directory:

```bash
python -m local_llm_server.l2_evidence_bridge validate-hardware-bundle \
  --directory "$EVIDENCE_DIR" \
  --output "$EVIDENCE_DIR/l2-device-bundle-summary.json"
```

The command exits successfully only when the minimum L2 evidence contracts are complete. It:

- verifies explicit TH-E1 OFF/ON-hidden evidence;
- uses the canonical evaluation comparison logic for EV-3;
- recomputes the HE-2 conservative review from both reclamation reports;
- verifies the RES-2 admit/account/release/reject invariants;
- emits no input paths, prompts or model outputs in the summary;
- never changes `.engineering/baseline.json` or authorizes automatic eviction.

A non-zero exit is evidence of an incomplete/incompatible bundle, not a reason to edit thresholds until green.

## Evidence completion checklist

The local evidence directory must contain at minimum:

```text
thinking-campaign.json
evaluation-off-a.json
evaluation-off-b.json
reclamation-a.json
reclamation-b.json
reclamation-review.json
resource-policy-smoke.json
l2-device-bundle-summary.json
```

The source evidence directory may contain private evaluation/model content and must not be committed wholesale. Durable repository truth should use only bounded public-safe conclusions, compatible identities/fingerprints and the validated summary needed for reproducibility.

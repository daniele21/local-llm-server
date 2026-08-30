# One-command representative-device campaign

Status: active procedure helper
Owner: `docs/device-evidence-runbook.md`
Read when: you want to execute the representative Apple Silicon evidence without manually sequencing TH-E1, EV-3, HE-2, RES-2 and RRG-5
Last reviewed: 2026-08-30

The canonical evidence contracts remain the individual procedures documented in `docs/device-evidence-runbook.md`. `scripts/run_device_evidence_campaign.py` is a thin orchestrator: it reuses those owners, applies their existing thresholds, owns the temporary HTTP server it starts, and writes a bounded `campaign-summary.json` after every phase.

It does **not** enable automatic eviction, lower memory margins, infer a production-safety claim from memory deltas, or turn a host-safety refusal into a product failure.

## Before running

Use a clean, converged `dev` checkout on the representative Apple Silicon Mac. Sync the repository with the canonical setup command first. The two model artifacts must already be local; the campaign uses `--no-download` for evidence execution.

For the full campaign choose:

- `MODEL_A`: the primary model used for TH-E1, EV-3, HE-2 and RES-2;
- `MODEL_B`: a distinct second model that can legitimately be resident at the same time for RRG-5;
- `REQUEST_ESTIMATE_MIB`: the configured or conservatively calibrated transient total per running request. There is intentionally no default.

Do not tune `REQUEST_ESTIMATE_MIB` or the model choice downward merely to make the campaign fit in memory.

## Full campaign

Example for a GGUF deployment where the minimum bundle is exercised through `llama_cpp` and the two-model governor path through `llama_server`:

```bash
uv run --frozen python scripts/run_device_evidence_campaign.py \
  --model-a "$MODEL_A" \
  --model-a-path "$MODEL_A_PATH" \
  --backend llama_cpp \
  --model-b "$MODEL_B" \
  --model-b-path "$MODEL_B_PATH" \
  --multi-model-backend llama_server \
  --request-estimate-mib "$REQUEST_ESTIMATE_MIB"
```

Do not copy those backend flags mechanically. They must describe the deployment/runtime path you actually want to validate. Omitting an override lets normal repository configuration resolve the backend.

The default scope is `full` and executes, in order:

1. representative-host/source/privacy preflight;
2. explicit artifact verification for both models;
3. owned loopback HTTP server startup;
4. TH-E1 thinking OFF / ON-hidden capture;
5. EV-3 two identical OFF evaluation runs and attribution-safe comparison;
6. owned server shutdown and listener cleanup verification;
7. HE-2 two isolated three-cycle reclamation reports plus conservative review;
8. RES-2 bounded admission/accounting/inference/unload/rejection smoke;
9. minimum L2 bundle recomputation;
10. RRG-5 twice: two resident models, concurrent HTTP inference, transient-overlap accounting, unload cleanup and shutdown-under-load retry;
11. conservative RRG-5 review.

## Minimum L2 only

To execute TH-E1 + EV-3 + HE-2 + RES-2 without RRG-5:

```bash
uv run --frozen python scripts/run_device_evidence_campaign.py \
  --scope minimum-l2 \
  --model-a "$MODEL" \
  --model-a-path "$MODEL_PATH" \
  --backend llama_cpp
```

## What preflight checks

The campaign refuses to make a representative-device conclusion unless:

- the host is macOS on Apple Silicon;
- the checkout is the clean `dev` branch, so evidence is attributable to one exact Git revision;
- the temporary HTTP server binds only to `127.0.0.1`;
- the selected port is free before the runner starts its owned server;
- the evidence directory is outside the repository checkout;
- full scope has two distinct model keys and a positive request estimate;
- the individual RES-2/RRG-5 safety gates have enough measured available memory for their configured margins.

The last item is intentionally checked again by the owning evidence procedures immediately before heavy backend construction.

## Result semantics

Every phase is persisted with one status:

- `PASS` — the phase executed and its expected contract was satisfied;
- `FAIL` — execution reached the product path and an expected invariant/contract was violated;
- `INCONCLUSIVE` — the environment, safety margin, artifact/precondition or evidence quality was insufficient to make the requested claim safely;
- `SKIPPED` — the phase is outside the requested scope or could not run because an earlier prerequisite failed.

Process exit codes:

- `0` — requested campaign is complete;
- `1` — at least one real phase failed an expected invariant;
- `2` — campaign is not complete but there is no product failure; evidence is inconclusive/refused;
- `130` — interrupted by the operator.

A memory-safety refusal is therefore **not** mislabeled as a product regression.

## Evidence directory

By default the runner creates a timestamped directory below:

```text
~/.local-llm-server/evidence/
```

The top-level `campaign-summary.json` is bounded and omits private model paths, prompts, model outputs and process IDs. Raw evaluation JSON and `representative-server.log` are machine-local diagnostic/source evidence and may contain content that should not be published or committed wholesale.

The runner writes the summary after every phase so an interruption still leaves the last completed state.

Expected full-scope artifacts can include:

```text
campaign-summary.json
representative-server.log
thinking-campaign.json
evaluation-off-a.json
evaluation-off-b.json
reclamation-a.json
reclamation-b.json
reclamation-review.json
resource-policy-smoke.json
l2-device-bundle-summary.json
multimodel-a.json
multimodel-b.json
multimodel-review.json
```

A safety-refused phase may deliberately leave fewer files. Missing evidence in that case is `INCONCLUSIVE`, not fabricated as a successful run.

## Interpreting memory results

`PASS` for HE-2 or RRG-5 means the required repeated lifecycle/ownership/accounting observation set is structurally complete and attributable. It does **not** mean that automatic eviction is safe or that every observed RSS/available-memory delta proves reclamation.

The existing conservative reviewers remain authoritative. Negative, mixed and inconclusive memory observations must remain visible for engineering review. Automatic pressure eviction stays disabled until its separate evidence gate is explicitly satisfied.

## Manual fallback

If the one-command campaign fails or is inconclusive, use `docs/device-evidence-runbook.md` to rerun the affected phase manually. The individual commands are the diagnostic source of truth; the campaign intentionally avoids creating a second evidence contract.

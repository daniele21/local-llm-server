# Representative evidence runner

Status: active procedure helper
Owner: local-llm-server
Read when: executing the remaining representative Mac evidence wave together with Performance Lab
Last reviewed: 2026-08-24

This helper turns the existing [`device-evidence-runbook.md`](device-evidence-runbook.md) into one serial, safety-gated execution path. The detailed runbook remains the canonical explanation of every evidence slice and its acceptance criteria.

## What it runs

In order:

1. exact artifact verification;
2. Local LLM Server startup on loopback with admin API;
3. runtime identity and `/status` capture;
4. TH-E1 thinking OFF and ON-hidden requests;
5. EV-3 OFF run A and B on frozen `general-purpose@1.0.0`, 10 samples, seed 0;
6. Performance Lab real-runtime smoke against the same Local LLM Server process;
7. post-PL `/status` capture and graceful server shutdown;
8. HE-2 reclamation report A, report B and conservative reviewer;
9. RES-2 bounded resource-policy smoke;
10. local evidence manifest with SHA-256 for every retained file.

The model path is intentionally omitted/redacted from the manifest and dry-run plan. The evidence directory itself is still private because response files may contain prompts/model outputs.

## Dry run first

Dry-run is safe on non-macOS hosts and does not require the model or Performance Lab checkout to exist:

```bash
python scripts/run_representative_evidence.py \
  --dry-run \
  --model <model-key> \
  --model-path /private/path/model.gguf \
  --performance-lab-repo ../performance-lab
```

The printed JSON must contain all planned slices and no raw model path.

## Real run on the representative Mac

Use the converged Local LLM Server `main` and Performance Lab `dev` checkouts, with their dependencies installed. The default port is `1235`, matching the Performance Lab real-runtime smoke.

```bash
python scripts/run_representative_evidence.py \
  --model <model-key> \
  --model-path /absolute/path/model.gguf \
  --performance-lab-repo /absolute/path/performance-lab
```

If Performance Lab uses a separate virtualenv, pass its interpreter explicitly:

```bash
python scripts/run_representative_evidence.py \
  --model <model-key> \
  --model-path /absolute/path/model.gguf \
  --performance-lab-repo /absolute/path/performance-lab \
  --performance-lab-python /absolute/path/performance-lab/.venv/bin/python
```

Default evidence destination:

```text
~/.local-llm-server/evidence/representative-<UTC timestamp>/
```

Override it with `--output-dir` when needed.

## Review the retained evidence

After the physical run, execute the public-safe reviewer against the evidence directory:

```bash
python scripts/review_representative_evidence.py \
  ~/.local-llm-server/evidence/representative-<UTC timestamp>
```

It writes `representative-review.json` and exits with:

- `0` — `ready_for_mig003`: all automated evidence-completeness/identity/comparability checks passed;
- `1` — `blocked`: one or more required artifacts/contracts are missing, invalid, non-comparable or failed;
- `2` — `review_required`: evidence is structurally valid but needs a conservative human decision, for example mixed HE-2 observations.

The reviewer verifies the SHA-256 inventory before trusting evidence, checks the exact EV-3 identity and sample selection across both runs, confirms the real LLS fingerprint, checks the hidden-thinking response boundary, verifies Performance Lab produced a successful run plus SQLite and `.plab.zip`, checks graceful server lifecycle, interprets the existing HE-2 conservative review and verifies the bounded RES-2 admit/release/reject contract.

It deliberately does **not** copy prompts, outputs, model paths, raw evidence paths or Performance Lab store/bundle paths into the public-safe summary. EV-3 sample failures remain descriptive evidence and do not become a synthetic gate failure when the run is complete and the failures are explicitly recorded.

`ready_for_mig003` means the automated prerequisite evidence is complete enough to start the migration-removal review. It is not a broad performance, thermal, memory-reclamation safety or production-safety claim.

## Safety behavior

- Real execution refuses non-macOS hosts.
- Heavy phases are serialized; the runner never launches multiple model loads in parallel.
- Local LLM Server is stopped before HE-2/RES-2 so those phases do not compete with an already-resident server process.
- RES-2 keeps the existing 0.5 GiB headroom, 0.5 GiB success margin and 2.0 GiB host-safety margin. The runner does not expose a convenience flag to weaken them.
- A failed HTTP/CLI slice is retained in the manifest rather than being rewritten as success.
- The process exits non-zero when any required slice fails.
- Server shutdown is marked failed if graceful SIGINT shutdown does not complete within the bounded window.

Do not lower safety margins, induce OOM/critical memory pressure or delete negative/inconclusive outputs simply to make the evidence wave pass.

## Completion evidence

A successful full run should retain at least:

```text
artifact-verification.stdout.txt
local-llm-server.log
runtime-identity.json
status-before.json
thinking-off-response.json
thinking-on-hidden-response.json
evaluation-off-a.json
evaluation-off-b.json
performance-lab/
performance-lab-real-smoke.stdout.txt
status-after-pl.json
reclamation-a.json
reclamation-b.json
reclamation-review.json
resource-policy-smoke.json
evidence-manifest.json
representative-review.json   # after reviewer execution
```

Performance Lab's nested output is expected to include its SQLite run evidence and `.plab.zip` bundle. The manifest SHA-256 list provides a local integrity index; it is not a release/publication mechanism.

After the run, review the detailed acceptance criteria in `device-evidence-runbook.md`. Completion is evidence-driven: a runner exit of zero plus a reviewer `ready_for_mig003` result proves the automated prerequisite contracts completed; durable claims still depend on the bounded interpretation rules in the detailed runbook.

# Current repository state

Status: active
Owner: repository
Read when: understanding what is integrated, blocked or executable next
Last reviewed: 2026-08-17

Keep this file operational and small. Detailed active planning belongs in `docs/workstreams/`; durable behavior belongs in the owning API/config/architecture/evidence docs.

## Current milestone

The runtime-correctness code convergence is complete. The milestone is now to execute and retain representative-device evidence on the converged Apple Silicon runtime before final documentation/release claims.

## Active workstream

| Workstream | Executable now | State | Blocker |
| --- | --- | --- | --- |
| [`runtime-correctness-evidence-hardening`](workstreams/runtime-correctness-evidence-hardening.md) | `TH-E1`, `EV-3`, `HE-2`, `RES-2` | ACTIVE — evidence wave | requires physical target-Mac execution; REL-1 waits on retained evidence |

Executable commands and evidence boundaries are in [`device-evidence-runbook.md`](device-evidence-runbook.md).

## Integrated baseline

`dev` currently includes the converged correctness implementation through PR #111.

- `llama_cpp` request-level thinking is no longer silently discarded; advertised switchability has an effective ON/OFF backend path.
- Streaming reasoning uses a chunk-safe boundary; hidden reasoning does not rely on delimiters landing in one transport chunk.
- Playground execution (`Enable thinking`) and visibility (`Show thinking`) are separate server-owned capability controls.
- Structured output is validated only after reasoning/final separation. Successful structured application content is valid JSON; malformed model JSON is a typed `invalid_model_output`, not silently repaired.
- Evaluation uses canonical backend preparation, pins a resident runtime, records requested/effective reasoning policy and applies the same final-output normalization before scoring.
- `local-llm verify-artifact` persists an exact-file SHA-256 receipt locally; runtime identity and hardware evidence reuse it while keeping public payloads path-free.
- Hardware evidence can therefore become verified when the exact receipt, backend/config and environment remain compatible.
- ResourceManager admit/account/release/reject behavior has deterministic product-boundary coverage, and a bounded macOS real-device runner is integrated.
- Ctrl+C shutdown notifies long-lived ASGI streams before Uvicorn drain, avoiding the previous graceful-shutdown ordering deadlock.
- Automatic pressure eviction remains disabled. Worker streaming/cancellation remains explicitly unsupported rather than emulated.

The PR #111 CI gate passed Ruff plus Python 3.10/3.11/3.12. The Python 3.11 job executed **518 passing tests**.

## Historical device evidence

The first 2026-08-17 Apple Silicon smoke remains useful as a pre-convergence baseline only:

- GGUF Nemotron loaded and interactive streaming inference completed;
- the earlier 10-sample `general-purpose` run completed transport/inference but its observed 20% score was not attribution-safe under the old evaluation/request boundary;
- two old reclamation reports produced six complete windows and six `recovery_observed` observations, but were exploratory because verified artifact identity was absent;
- resource policy was disabled in that smoke.

Do not upgrade those old observations after the fact. New evidence must be produced from the converged runtime and its current identity/request contracts.

## Remaining blockers

There are no known code-contract blockers from the original hardening graph. Remaining blockers are evidence/release gates:

- **TH-E1:** real Nemotron ON/OFF smoke has not yet been executed on the converged `dev` baseline.
- **EV-3:** two comparable `general-purpose v1.0.0 / 10 / seed 0 / reasoning off` runs have not yet been retained after convergence.
- **HE-2:** two new compatible verified 3-cycle Apple Silicon reports and conservative review are still required.
- **RES-2:** the bounded runner is merged, but its real Mac admit/account/release/reject report is still pending.
- **DOC-1/REL-1:** durable docs and final release gate must use the actual observed Wave D results, not expected outcomes.
- Broader backend/device coverage and manual visual/accessibility acceptance remain release-candidate gates outside this immediate correctness workstream.

## Next

Run the four representative-device slices from `device-evidence-runbook.md`. They are logically parallel but should be serialized where simultaneous model loads would compete for the same Mac memory/residency.

Retain negative, mixed or inconclusive evidence exactly as observed. Do not induce OOM/critical pressure and do not enable automatic eviction as part of these runs.

# Current repository state

Status: active
Owner: repository
Read when: understanding what is integrated, blocked or executable next
Last reviewed: 2026-08-24

Keep this file operational and small. Detailed active planning belongs in `docs/workstreams/`; durable behavior belongs in the owning API/config/architecture/evidence docs.

## Current milestone

The runtime-correctness code convergence is complete. The milestone is to execute and retain representative-device evidence on the converged Apple Silicon runtime before final documentation/release claims.

A cross-repository ownership transition is also now explicit: long-term benchmark/evaluation product ownership moves to `daniele21/performance-lab`; Local LLM Server remains the serving/runtime control plane. Existing evaluation behavior is retained temporarily because the current evidence wave still depends on its frozen identities.

## Active work

| Workstream / transition | Executable now | State | Blocker |
| --- | --- | --- | --- |
| [`runtime-correctness-evidence-hardening`](workstreams/runtime-correctness-evidence-hardening.md) | `TH-E1`, `EV-3`, `HE-2`, `RES-2` | ACTIVE — evidence wave | requires physical target-Mac execution; REL-1 waits on retained evidence |
| [Performance Lab evaluation migration](performance-lab-evaluation-migration.md) | consumer/history inventory and replacement preparation | ACTIVE — no removal yet | EV-3 + Performance Lab representative real-runtime evidence + cross-repo replacement smoke |

Executable device commands and evidence boundaries are in [`device-evidence-runbook.md`](device-evidence-runbook.md).

## Integrated baseline

The converged correctness implementation is integrated through PR #111 and the 0.4.0 release baseline.

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

## Evaluation ownership transition

The current evaluation subsystem is a transitional compatibility/evidence surface, not a target for new product scope.

Migration candidates include evaluation test-set/score/run contracts, generic built-in/custom evaluation data, evaluation-specific execution/history/comparison APIs and Studio evaluation surfaces. These move to Performance Lab only after parity, history and consumer evidence.

Runtime responsibilities stay here: `/v1/models`, `/v1/chat/completions`, resident runtime lifecycle, capability truth, `/v1/runtime/identity`, `/status`, provider-observed metrics, resource/reclamation behavior and hardware correctness evidence.

Most importantly, `general-purpose@1.0.0` is frozen through EV-3. Do not remove or semantically change it before two post-convergence `10 / seed 0 / reasoning off` real-device runs are retained. See [`performance-lab-evaluation-migration.md`](performance-lab-evaluation-migration.md).

## Historical device evidence

The first 2026-08-17 Apple Silicon smoke remains useful as a pre-convergence baseline only:

- GGUF Nemotron loaded and interactive streaming inference completed;
- the earlier 10-sample `general-purpose` run completed transport/inference but its observed 20% score was not attribution-safe under the old evaluation/request boundary;
- two old reclamation reports produced six complete windows and six `recovery_observed` observations, but were exploratory because verified artifact identity was absent;
- resource policy was disabled in that smoke.

Do not upgrade those old observations after the fact. New evidence must be produced from the converged runtime and its current identity/request contracts.

## Remaining blockers

There are no known code-contract blockers from the original hardening graph. Remaining blockers are evidence/release/migration gates:

- **TH-E1:** real Nemotron ON/OFF smoke has not yet been executed on the converged baseline.
- **EV-3:** two comparable `general-purpose v1.0.0 / 10 / seed 0 / reasoning off` runs have not yet been retained after convergence.
- **HE-2:** two new compatible verified 3-cycle Apple Silicon reports and conservative review are still required.
- **RES-2:** the bounded runner is merged, but its real Mac admit/account/release/reject report is still pending.
- **DOC-1/REL-1:** durable docs and final release gate must use the actual observed Wave D results, not expected outcomes.
- **Evaluation migration:** redundant evaluation UI/API/code cannot be removed until EV-3, Performance Lab representative runtime evidence, explicit history/consumer handling and cross-repository smoke are complete.
- Broader backend/device coverage and manual visual/accessibility acceptance remain release-candidate gates outside this immediate correctness workstream.

## Next

Run the four representative-device slices from `device-evidence-runbook.md`. They are logically parallel but should be serialized where simultaneous model loads would compete for the same Mac memory/residency.

In parallel, perform non-destructive evaluation migration preparation: inventory consumers/history, decide exact `general-purpose@1.0.0` continuity, and define the Performance Lab mapping for custom-test-set and reasoning-policy semantics. Do not disable evaluation routes or remove code yet.

Retain negative, mixed or inconclusive evidence exactly as observed. Do not induce OOM/critical pressure and do not enable automatic eviction as part of these runs.

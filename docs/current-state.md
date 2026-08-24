# Current repository state

Status: active
Owner: repository
Read when: understanding what is integrated, blocked or executable next
Last reviewed: 2026-08-24

Keep this file operational and small. Detailed active planning belongs in `docs/workstreams/`; durable behavior belongs in the owning API/config/architecture/evidence docs.

## Current milestone

Runtime-correctness code convergence is complete. The milestone is to execute and retain representative-device evidence on the converged Apple Silicon runtime before final documentation/release claims.

Cross-repository ownership is also settled: long-term benchmark/evaluation product ownership belongs to `daniele21/performance-lab`; Local LLM Server remains the serving/runtime control plane. Existing evaluation behavior is transitional because the current evidence wave still depends on its frozen identities.

## Active work

| Workstream / transition | Executable now | State | Blocker |
| --- | --- | --- | --- |
| [`runtime-correctness-evidence-hardening`](workstreams/runtime-correctness-evidence-hardening.md) | `TH-E1`, `EV-3`, `HE-2`, `RES-2` | ACTIVE — evidence wave | requires physical target-Mac execution; REL-1 waits on retained evidence |
| [Performance Lab evaluation migration](performance-lab-evaluation-migration.md) | replacement-path preparation and deprecation redirect | MIG-002 POLICY DONE / EVIDENCE-BLOCKED | EV-3 + PL representative real-runtime run + user redirect + cross-repo smoke |

Executable device commands and evidence boundaries are in [`device-evidence-runbook.md`](device-evidence-runbook.md).

## Integrated baseline

The converged correctness implementation is integrated through PR #111 and the 0.4.0 release baseline.

- `llama_cpp` request-level thinking has an effective ON/OFF backend path; advertised switchability is not silently discarded.
- Streaming reasoning uses a chunk-safe boundary; hidden reasoning does not rely on delimiters landing in one transport chunk.
- Playground execution (`Enable thinking`) and visibility (`Show thinking`) are separate server-owned capability controls.
- Structured output is validated only after reasoning/final separation. Malformed model JSON is a typed `invalid_model_output`, not silently repaired.
- Evaluation uses canonical backend preparation, pins a resident runtime, records requested/effective reasoning policy and applies the same final-output normalization before scoring.
- `local-llm verify-artifact` persists an exact-file SHA-256 receipt locally; runtime identity and hardware evidence reuse it while public payloads remain path-free.
- ResourceManager admit/account/release/reject behavior has deterministic product-boundary coverage and a bounded macOS real-device runner.
- Ctrl+C shutdown notifies long-lived ASGI streams before Uvicorn drain.
- Automatic pressure eviction remains disabled. Worker streaming/cancellation remains explicitly unsupported rather than emulated.

PR #111 CI passed Ruff plus Python 3.10/3.11/3.12; Python 3.11 executed 518 passing tests. The evaluation-ownership transition PR #147 also passed Ruff, Python 3.10/3.11/3.12 and Playwright E2E.

## Evaluation ownership and history policy

The current evaluation subsystem is a transitional compatibility/evidence surface, not a target for new product scope.

Runtime responsibilities stay here: `/v1/models`, `/v1/chat/completions`, resident runtime lifecycle, capability truth, `/v1/runtime/identity`, `/status`, provider-observed metrics, resource/reclamation behavior and hardware correctness evidence.

The migration continuity decision is now explicit:

- existing and EV-3 evaluation reports remain immutable **historical Local LLM Server evidence**;
- after cutover, all new evaluation evidence is created/stored by Performance Lab;
- no automatic legacy-history import into Performance Lab is required;
- `general-purpose@1.0.0` and Performance Lab's `general-diagnostic-starter` remain distinct evidence identities and are not cross-compared by assumption;
- exact custom-test-set/reasoning/request semantics are not cloned unless an actual retained consumer requires them.

Repository-known evaluation consumers are the Studio Benchmark & Evaluation surface, its history/compare surface, their API/UI tests and the EV-3 evidence workflow. Route removal still requires visible deprecation/redirect because repository inspection cannot prove that no external script exists.

Most importantly, `general-purpose@1.0.0` remains frozen through EV-3. Do not remove or semantically change it before two post-convergence `10 / seed 0 / reasoning off` real-device runs are retained. See [`performance-lab-evaluation-migration.md`](performance-lab-evaluation-migration.md).

## Historical device evidence

The first 2026-08-17 Apple Silicon smoke remains a pre-convergence baseline only:

- GGUF Nemotron loaded and interactive streaming inference completed;
- the earlier 10-sample `general-purpose` run completed transport/inference but its 20% score was not attribution-safe under the old evaluation/request boundary;
- two old reclamation reports produced complete recovery observations but lacked verified artifact identity;
- resource policy was disabled in that smoke.

Do not upgrade those observations after the fact. New evidence must come from the converged runtime/current identity/request contracts.

## Remaining blockers

There are no known code-contract blockers from the original hardening graph. Remaining blockers are evidence/release/migration gates:

- **TH-E1:** real Nemotron ON/OFF smoke pending on the converged baseline.
- **EV-3:** two comparable `general-purpose v1.0.0 / 10 / seed 0 / reasoning off` runs pending after convergence.
- **HE-2:** two new compatible verified 3-cycle Apple Silicon reports and conservative review required.
- **RES-2:** bounded runner merged; real Mac admit/account/release/reject report pending.
- **DOC-1/REL-1:** final docs/release gate must use actual Wave D observations.
- **Evaluation migration:** architecture/history policy is decided; redundant evaluation UI/API/code remains blocked only by EV-3, Performance Lab representative runtime evidence, user redirect and cross-repository smoke.
- Broader backend/device coverage and manual visual/accessibility acceptance remain release-candidate gates outside this immediate correctness workstream.

## Next

Run the four representative-device slices from `device-evidence-runbook.md`; serialize them where simultaneous model loads would compete for the same Mac memory/residency.

In parallel, prepare the non-destructive cutover: point Studio/users toward Performance Lab, keep legacy reports under their original identities, and prepare removal of evaluation run/write/history product paths only after EV-3 and the real Performance Lab replacement run are retained.

Retain negative, mixed or inconclusive evidence exactly as observed. Do not induce OOM/critical pressure and do not enable automatic eviction as part of these runs.

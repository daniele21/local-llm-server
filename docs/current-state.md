# Current repository state

Status: active
Owner: repository
Read when: understanding what is integrated, blocked or executable next
Last reviewed: 2026-08-24

Keep this file operational and small. Detailed active planning belongs in `docs/workstreams/`; durable behavior belongs in the owning API/config/architecture/evidence docs.

## Current milestone

Runtime-correctness code convergence is complete. The milestone is to execute and retain representative-device evidence on the converged Apple Silicon runtime before final documentation/release claims.

Cross-repository ownership is settled: benchmark/evaluation product ownership belongs to `daniele21/performance-lab`; Local LLM Server remains the serving/runtime control plane. Existing evaluation behavior is transitional because the current evidence wave still depends on its frozen identities.

## Active work

| Workstream / transition | Executable now | State | Blocker |
| --- | --- | --- | --- |
| [`runtime-correctness-evidence-hardening`](workstreams/runtime-correctness-evidence-hardening.md) | `TH-E1`, `EV-3`, `HE-2`, `RES-2` | ACTIVE — evidence wave | requires physical target-Mac execution; REL-1 waits on retained evidence |
| [Performance Lab evaluation migration](performance-lab-evaluation-migration.md) | real-runtime replacement evidence | MIG-002 NON-HARDWARE DONE / EVIDENCE-BLOCKED | EV-3 + PL representative real-runtime run + cross-repo smoke |

Detailed commands and evidence boundaries are in [`device-evidence-runbook.md`](device-evidence-runbook.md). The serial one-command helper is [`representative-evidence-runner.md`](representative-evidence-runner.md).

## Integrated baseline

The converged correctness implementation is integrated through PR #111 and the 0.4.0 release baseline.

- `llama_cpp` request-level thinking has an effective ON/OFF backend path.
- Streaming reasoning uses a chunk-safe boundary; hidden reasoning does not rely on delimiters landing in one transport chunk.
- Playground execution (`Enable thinking`) and visibility (`Show thinking`) are separate server-owned capability controls.
- Structured output is validated only after reasoning/final separation; malformed model JSON is a typed `invalid_model_output`.
- Evaluation uses canonical backend preparation, pins a resident runtime, records requested/effective reasoning policy and applies the same final-output normalization before scoring.
- `local-llm verify-artifact` persists an exact-file SHA-256 receipt locally; runtime identity and hardware evidence reuse it while public payloads remain path-free.
- ResourceManager admit/account/release/reject behavior has deterministic product-boundary coverage and a bounded macOS real-device runner.
- Ctrl+C shutdown notifies long-lived ASGI streams before Uvicorn drain.
- Automatic pressure eviction remains disabled. Worker streaming/cancellation remains explicitly unsupported rather than emulated.
- PR #149 added the visible Performance Lab transition notice while deliberately keeping EV-3 and legacy history operational.

## Evaluation ownership and history policy

The evaluation subsystem is a transitional compatibility/evidence surface, not a target for new product scope.

Runtime responsibilities stay here: `/v1/models`, `/v1/chat/completions`, resident runtime lifecycle, capability truth, `/v1/runtime/identity`, `/status`, provider-observed metrics, resource/reclamation behavior and hardware correctness evidence.

Migration continuity is explicit:

- existing and EV-3 evaluation reports remain immutable historical Local LLM Server evidence;
- after cutover, all new evaluation evidence is created/stored by Performance Lab;
- no automatic legacy-history import into Performance Lab is required;
- `general-purpose@1.0.0` and Performance Lab's `general-diagnostic-starter` remain distinct identities and are not cross-compared by assumption;
- exact custom-test-set/reasoning/request semantics are not cloned unless an actual retained consumer requires them.

Repository-known legacy consumers are Studio evaluation/history, their tests and EV-3. The Studio transition notice is now merged, so the remaining migration blockers are empirical rather than architectural.

Most importantly, `general-purpose@1.0.0` remains frozen through EV-3. Do not remove or semantically change it before two post-convergence `10 / seed 0 / reasoning off` real-device runs are retained.

## Historical device evidence

The first 2026-08-17 Apple Silicon smoke remains a pre-convergence baseline only. GGUF Nemotron loaded and streamed successfully, but the old evaluation score was not attribution-safe, earlier reclamation reports lacked verified artifact identity and resource policy was disabled. Do not upgrade those observations after the fact.

## Remaining blockers

- **TH-E1:** real Nemotron ON/OFF smoke pending on the converged baseline.
- **EV-3:** two comparable `general-purpose v1.0.0 / 10 / seed 0 / reasoning off` runs pending after convergence.
- **HE-2:** two compatible verified 3-cycle Apple Silicon reports plus conservative review.
- **RES-2:** real Mac admit/account/release/reject report pending.
- **Performance Lab replacement evidence:** real PL run against this LLS endpoint with identity/status/fingerprint/bundle retained.
- **DOC-1/REL-1:** final docs/release gate must use actual Wave D observations.
- **MIG-003:** redundant evaluation UI/API/history removal waits on the evidence above plus a post-disable cross-repository smoke.

## Next

Run the serial helper from `representative-evidence-runner.md`. It executes the required heavy phases sequentially, preserves negative/mixed outputs and leaves RES-2 safety margins unchanged.

Do not disable evaluation run/write/history paths until EV-3 and the real Performance Lab replacement run are retained. Do not induce OOM/critical pressure or enable automatic eviction as part of these runs.

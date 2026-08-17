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
| [`repo-template-sw-adoption`](workstreams/repo-template-sw-adoption.md) | `STD-10` | BLOCKED — external enforcement only | `main` and `dev` are unprotected; L0 requires protected canonical branches with CI enforcement |

Executable commands and evidence boundaries are in [`device-evidence-runbook.md`](device-evidence-runbook.md).

## Integrated baseline

`dev` includes the converged runtime-correctness implementation plus the repository-side `repo-template-sw 0.3.0` adoption through PR #123.

### Runtime correctness

- `llama_cpp` request-level thinking is no longer silently discarded; advertised switchability has an effective ON/OFF backend path.
- Streaming reasoning uses a chunk-safe boundary; hidden reasoning does not rely on delimiters landing in one transport chunk.
- Playground execution (`Enable thinking`) and visibility (`Show thinking`) are separate server-owned capability controls.
- Structured output is validated only after reasoning/final separation. Successful structured application content is valid JSON; malformed model JSON is a typed `invalid_model_output`, not silently repaired.
- Evaluation uses canonical backend preparation, pins a resident runtime, records requested/effective reasoning policy and applies the same final-output normalization before scoring.
- `local-llm verify-artifact` persists an exact-file SHA-256 receipt locally; runtime identity and hardware evidence reuse it while keeping public payloads path-free.
- ResourceManager admit/account/release/reject behavior has deterministic product-boundary coverage, and a bounded macOS real-device runner is integrated.
- Ctrl+C shutdown notifies long-lived ASGI streams before Uvicorn drain.
- Automatic pressure eviction remains disabled. Worker streaming/cancellation remains explicitly unsupported rather than emulated.

### Repository engineering baseline

- canonical operating commands are recorded in `.engineering/commands.json` and validated in CI;
- Python/Node dependency state is committed and CI is lock-backed across Python 3.10/3.11/3.12;
- repository/operations/docs/agent-context validators are blocking through `Repository Health`;
- Playwright uses an owned process/temp-root lifecycle and an independent zero-residue gate;
- material wheel/sdist builds carry unique build/source identity, manifest, SHA-256 inventory, build delta and retention=2;
- the canonical `./deploy.sh` build and release-style version/lock bump are exercised by the permanent artifact lifecycle gate;
- security/data-lifecycle policy, MIT license, current architecture, ADR/feature routing and delete-by-default workstream lifecycle are integrated.

Full `repo-template-sw` L0 compliance is **not yet claimed** because authenticated GitHub state shows both `main` and `dev` are unprotected and required status checks are off. Repository-side implementation is complete; branch enforcement is the remaining external blocker.

## Historical device evidence

The first 2026-08-17 Apple Silicon smoke remains useful as a pre-convergence baseline only:

- GGUF Nemotron loaded and interactive streaming inference completed;
- the earlier 10-sample `general-purpose` run completed transport/inference but its observed 20% score was not attribution-safe under the old evaluation/request boundary;
- two old reclamation reports produced six complete windows and six `recovery_observed` observations, but were exploratory because verified artifact identity was absent;
- resource policy was disabled in that smoke.

Do not upgrade those old observations after the fact. New evidence must be produced from the converged runtime and its current identity/request contracts.

## Remaining blockers

### Runtime/device evidence

- **TH-E1:** real Nemotron ON/OFF smoke has not yet been executed on the converged `dev` baseline.
- **EV-3:** two comparable `general-purpose v1.0.0 / 10 / seed 0 / reasoning off` runs have not yet been retained after convergence.
- **HE-2:** two new compatible verified 3-cycle Apple Silicon reports and conservative review are still required.
- **RES-2:** the bounded runner is merged, but its real Mac admit/account/release/reject report is still pending.
- **DOC-1/REL-1:** durable docs and final release gate must use the actual observed Wave D results, not expected outcomes.
- Broader backend/device coverage and manual visual/accessibility acceptance remain release-candidate gates outside this immediate correctness workstream.

### Repository baseline external enforcement

- **STD-10:** protect canonical branches and require repository CI/health checks, then re-verify authenticated GitHub state before marking L0 adoption complete and deleting the workstream.

## Next

Run the four representative-device slices from `device-evidence-runbook.md`. They are logically parallel but should be serialized where simultaneous model loads would compete for the same Mac memory/residency.

Separately, configure GitHub protection/rulesets for the canonical branches. No further repository code work is required for repo-template adoption unless re-verification exposes a new mismatch.

Retain negative, mixed or inconclusive evidence exactly as observed. Do not induce OOM/critical pressure and do not enable automatic eviction as part of these runs.

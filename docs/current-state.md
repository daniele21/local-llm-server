# Current repository state

Status: active
Owner: repository
Read when: understanding what is integrated, blocked or executable next
Last reviewed: 2026-08-17

Keep this file operational and small. Detailed planning belongs in `docs/workstreams/`; durable behavior belongs in its owning docs/tests.

## Current milestone

Runtime-correctness code convergence is complete. The milestone is representative-device evidence on the converged Apple Silicon runtime before final release claims.

## Active workstream

| Workstream | Executable now | State | Blocker |
| --- | --- | --- | --- |
| [`runtime-correctness-evidence-hardening`](workstreams/runtime-correctness-evidence-hardening.md) | `TH-E1`, `EV-3`, `HE-2`, `RES-2` | ACTIVE — evidence wave | physical target-Mac execution; REL-1 waits on retained evidence |
| [`repo-template-sw-adoption`](workstreams/repo-template-sw-adoption.md) | `STD-10` | BLOCKED — external enforcement only | `main`/`dev` unprotected; L0 requires protected canonical branches with CI enforcement |

Executable device commands/evidence boundaries are in [`device-evidence-runbook.md`](device-evidence-runbook.md).

## Integrated baseline

`dev` includes converged runtime correctness plus repository-side `repo-template-sw 0.3.0` adoption through PR #123.

### Runtime correctness

- `llama_cpp` thinking has effective request-level ON/OFF behavior; streaming reasoning is chunk-safe.
- Thinking execution and visibility are separate controls; structured final output is validated after reasoning separation.
- Evaluation uses canonical request preparation and records requested/effective reasoning policy.
- Verified artifact receipts feed path-free runtime/hardware identity.
- Resource admission/account/release/reject has deterministic coverage and a bounded macOS real-device runner.
- Ctrl+C shutdown orders long-lived streams before Uvicorn drain.
- Automatic pressure eviction remains disabled; worker streaming/cancellation remains explicitly unsupported.

### Repository engineering baseline

- canonical operations are machine-validated; Python/Node dependency state is committed and lock-backed;
- repository/operations/docs/agent-context checks are blocking through `Repository Health`;
- Playwright has owned process/temp-root lifecycle plus independent zero-residue verification;
- wheel/sdist builds carry unique identity, manifest, SHA-256 inventory, delta and retention=2;
- canonical `./deploy.sh`, failed staging and release-style version/lock bump are exercised permanently;
- security/data policy, MIT license, current architecture and ADR/feature routing are integrated.

Full L0 compliance is **not claimed**: authenticated GitHub state shows `main` and `dev` unprotected with required status checks off. Repository-side implementation is complete; branch enforcement is the remaining external blocker.

## Historical device evidence

The first 2026-08-17 Apple Silicon smoke is pre-convergence evidence only: GGUF Nemotron loaded/inferred, the old 10-sample evaluation was not attribution-safe, reclamation observations lacked verified artifact identity, and resource policy was disabled. Do not upgrade those observations after the fact.

## Remaining blockers

### Runtime/device evidence

- **TH-E1:** converged real Nemotron ON/OFF smoke pending.
- **EV-3:** two comparable `general-purpose v1.0.0 / 10 / seed 0 / reasoning off` runs pending.
- **HE-2:** two compatible verified 3-cycle Apple Silicon reports + conservative review pending.
- **RES-2:** real Mac admit/account/release/reject report pending.
- **DOC-1/REL-1:** final docs/release gate must use observed Wave D results.
- Broader backend/device coverage and manual visual/accessibility acceptance remain release-candidate gates.

### Repository baseline external enforcement

- **STD-10:** protect canonical branches and require repository CI/health checks, then re-verify authenticated GitHub state before marking L0 adoption complete/deleting the workstream.

## Next

Run the four representative-device slices from `device-evidence-runbook.md`, serializing simultaneous model loads that would compete for Mac memory/residency.

Separately, configure GitHub protection/rulesets for canonical branches. No further repository code work is required for repo-template adoption unless re-verification exposes a mismatch.

Retain negative/mixed/inconclusive evidence exactly as observed. Do not induce OOM/critical pressure or enable automatic eviction during these runs.

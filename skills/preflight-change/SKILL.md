# preflight-change

Use immediately before pushing/opening/updating a PR or otherwise publishing a meaningful change. `validate-change` owns iteration; this skill owns final exact-head readiness.

1. **Resolve material ambiguity.** Inspect canonical contracts, owner code, direct consumers/fakes/tests and active workstream acceptance. Ask the user only if two reasonable interpretations would materially change behavior, compatibility, persistence, security/privacy, lifecycle/resource semantics, acceptance criteria or meaningful UX.
2. **Refresh the intended base.** Record target branch/revision and current head. Reconcile stale or stacked work; invalidate affected evidence after any head/base/dependency change.
3. **Review the complete diff.** Look for generated/private/debug residue, unrelated edits, duplicate ownership, weakened tests, stale docs/contracts, missed consumers, unsafe cleanup or changed security/UX semantics.
4. **Select validation profile.** Run the project selector from `.engineering/commands.json`. `LEAN` = docs/governance only; `SCOPED` = contained owner/direct consumers; `STRONG` = cross-boundary/runtime/security/E2E/package-sensitive; `FULL` = promotion/release or changes to CI, selector, global build/dependency/toolchain machinery, or unknown executable paths. Never silently downgrade below `auto`.
5. **Select E2E fidelity when needed.** Read `.engineering/e2e.json`, pick the affected critical journey and cheapest declared automated environment sufficient for the claim. Built/package claims require the built surface. Preserve residual real-environment gaps explicitly.
6. **Classify every required gate for this session.** `AGENT_LOCAL` if executable here; `REMOTE_AUTOMATED` if deterministic but only repository automation can run it; `REAL_ENVIRONMENT` only for genuinely hardware/protected/manual claims. Lack of a local SDK/toolchain never turns an automatable gate into a user task.
7. **Execute or route.** Run available local gates on the exact head. If deterministic gates remain remote, publish/refresh the same-repository PR and use `remote-preflight` to inspect GitHub Actions. Real-device evidence may remain pending but blocks any claim that depends on it.
8. **Diagnose failures before editing.** Classify as change regression, baseline failure, environment/toolchain, flaky, base drift or wrong assumption; fix the owning invariant. Do not suppress or weaken legitimate gates to obtain green CI.
9. **Require parity.** CI should invoke the same project-owned command/validator semantics. If target hardware repeatedly discovers ordinary automatable workflow failures, strengthen the automated journey rather than normalizing manual discovery.

Report:

`HEAD`, `TARGET`, `AMBIGUITY`, `BASE_FRESHNESS`, `FULL_DIFF_REVIEW`, `VALIDATION_PROFILE` + reason, `AGENT_LOCAL`, `REMOTE_AUTOMATED`, `REAL_ENVIRONMENT`, affected E2E journey/environment/fidelity, residual gaps and `READINESS`.

Readiness is one of `READY_FOR_CI`, `READY_FOR_REMOTE_PREFLIGHT`, `AUTOMATED_PREFLIGHT_CONFIRMED`, or `NOT_READY_FOR_AUTOMATED_PREFLIGHT`. Any material edit/rebase/base change invalidates affected evidence.

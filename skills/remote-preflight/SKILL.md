# remote-preflight

Use when `preflight-change` classifies one or more required deterministic gates as `REMOTE_AUTOMATED`.

For this repository the safe remote path is the same-repository pull request against `dev`: GitHub `pull_request` workflows execute deterministic CI/Repository Health on the exact PR head with read-only contents permission, and status checks report results on the PR.

1. Record PR target and exact head SHA before relying on any run. Never reuse evidence from an older head/base relationship.
2. Run/read `scripts/select_validation_profile.py` and record `LEAN`, `SCOPED`, `STRONG` or `FULL` plus reason. Existing PR workflows may execute a deliberately stronger deterministic set; never weaken below `auto` just to save time.
3. Inspect CI and Repository Health results and logs, not only the headline. Record each required gate as PASS/FAIL/PENDING/N/A.
4. On failure classify root cause: current change, baseline failure, environment/toolchain, flaky, base drift or wrong assumption. Fix the owning source/configuration and retrigger on the new exact head.
5. Never ask the user to run pytest/Ruff/Playwright/build/repository validators solely because the current agent cannot run them. Use repository automation.
6. Keep remote execution capability separate from E2E fidelity. A GitHub-hosted Playwright run is `REMOTE_AUTOMATED` but `ci-studio-deterministic` remains `host_or_fake`; it cannot satisfy Apple Silicon/model/backend/memory/performance evidence.
7. Preserve least privilege: same-repository heads, trusted requester, exact-head correlation, no production/signing secrets in change-code execution, bounded artifact retention.
8. If no usable automation exists for a deterministic required gate, report `AUTOMATION_CAPABILITY_GAP`; if blast radius cannot be selected safely, report `VALIDATION_SCOPE_GAP` and fail safe stronger.

`AUTOMATED_PREFLIGHT_CONFIRMED` means all deterministic gates selected for the exact head/base passed. It does not imply representative-hardware, target-environment, manual accessibility or representative-user evidence.

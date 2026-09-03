---
name: remote-preflight
description: Satisfy Local LLM Server integration/release deterministic gates through repository-owned automation, reusing equivalent successful evidence before executing only missing work.
---

# Remote Preflight

Use only after `preflight-change` reaches `INTEGRATION` or `RELEASE` and required deterministic gates need `REMOTE_AUTOMATED` execution.

Read `.engineering/commands.json` and record exact head/source tree, target/base, stage, risks, required gates, profile and applicable E2E identity. Search successful evidence before triggering new CI.

Reuse exact-head evidence when candidate head/base/gates/profile/E2E claim remain sufficient. On `dev`, repository automation may also reuse a prior integration proof after a content-preserving squash/rebase merge only when the post-merge Git tree equals the validated source tree and the merge parent equals the validated target/base. A direct push, moved base, changed tree, broadened gates or expired evidence requires normal validation.

If evidence is sufficient, confirm without rerunning expensive gates. Otherwise execute only missing/stale/insufficient gates through `.github/workflows/ci.yml`; do not request FULL merely because it is simpler operationally.

On failure inspect the owning job/log, classify `CHANGE_REGRESSION|BASELINE_FAILURE|ENVIRONMENT|FLAKY|BASE_DRIFT|ASSUMPTION`, repair the owner, reselect risks/gates and rerun only invalidated evidence. Keep change-branch execution read-only, same-repository by default, without production secrets and with bounded retention.

Executor class never upgrades fidelity: GitHub Playwright remains deterministic host evidence, while production model/backend/memory/performance claims remain representative/target Apple Silicon evidence.

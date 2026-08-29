# validate-change

Choose validation by claim, blast radius and environment fidelity rather than running every expensive gate by default.

1. Read `.engineering/commands.json`; when a complete workflow or environment-dependent claim is affected also read `.engineering/e2e.json`.
2. Start with the cheapest deterministic falsifier available to the current agent: syntax/static checks and focused owner tests.
3. Add direct-consumer/contract/persistence tests when a shared boundary changes; add canonical `check`/`test` and repository health when scope crosses owners or governance.
4. When `product-ui` behavior changes, read `design/ux-contract.json`/`brand-kit.json`, confirm proportional `design-product-experience` reasoning, and validate the experience property actually changed: task/hierarchy/disclosure, states/recovery, accessibility, adaptive layout, semantic component/token reuse, purposeful motion and critical journeys.
5. Run E2E only when the claim crosses the assembled product boundary. Use the smallest affected journey and cheapest declared automated environment in `.engineering/e2e.json`; require built-wheel execution when package/install behavior is material.
6. Keep execution capability separate from fidelity: GitHub CI can be `REMOTE_AUTOMATED` while `ci-studio-deterministic` remains only `host_or_fake`. Do not infer Apple Silicon/model/memory/performance evidence from it.
7. Run `build` for distributable/build changes and `smoke` for minimum real-runtime viability when applicable. Representative-device procedures remain the owner for model/backend/memory/latency/throughput/thermal claims.
8. Verify project-owned process/listener/temp/evidence cleanup whenever lifecycle/E2E behavior changes.
9. On a red gate, classify root cause before editing: current regression, baseline failure, environment/toolchain, flaky behavior, base drift or wrong assumption. Fix the owning invariant rather than suppressing the gate.
10. If the current agent cannot run a deterministic gate, mark it `REMOTE_AUTOMATED` for `preflight-change`; do not ask the user to become the CI runner.
11. Report exact PASS/FAIL/PENDING/N/A evidence plus E2E environment/fidelity and residual gaps. Before publication hand this evidence to `preflight-change` for exact-head readiness.

# validate-change

Choose validation by claim and blast radius rather than running every expensive gate by default.

1. Run syntax/static checks for edited languages and zero-dependency repository validators for governance changes.
2. Run focused unit/contract tests for local behavior, then the canonical `test` intent when shared behavior changed.
3. Run browser `e2e` only when the claim crosses the assembled Studio/product boundary.
4. Run `build` when distributable output or build scripts changed; run `smoke` when minimum built/runtime viability is the claim.
5. Run representative-device procedures only for hardware/model/resource/performance claims.
6. Verify project-owned process/listener/temp/evidence cleanup whenever lifecycle/E2E behavior changed.
7. Report unavailable checks and evidence as pending; never infer a stronger result from a weaker test class.

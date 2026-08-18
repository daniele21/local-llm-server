# validate-change

Choose validation by claim and blast radius rather than running every expensive gate by default.

1. Run syntax/static checks for edited languages and zero-dependency repository validators for governance changes.
2. Run focused unit/contract tests for local behavior, then the canonical `test` intent when shared behavior changed.
3. When `product-ui` is adopted and user-facing behavior changes, read `design/ux-contract.json` and `design/brand-kit.json`; run `scripts/verify_product_experience.py` plus `scripts/verify_product_ui_l2.py` at repository integration scope.
4. Validate the experience properties actually changed: task/information hierarchy, progressive disclosure/cognitive load, loading/empty/error/disabled and recovery states, accessibility, adaptive layout, canonical component/token reuse and critical-journey evidence.
5. Run browser `e2e` only when the claim crosses the assembled Studio/product boundary; screenshots alone do not prove interaction, accessibility, recovery or usability.
6. Run `build` when distributable output or build scripts changed; run `smoke` when minimum built/runtime viability is the claim.
7. Run representative-device procedures only for hardware/model/resource/performance claims. Run manual accessibility or representative-user procedures only when the UX claim requires human evidence; label unavailable evidence `PENDING` rather than inferring it from automation.
8. Verify project-owned process/listener/temp/evidence cleanup whenever lifecycle/E2E behavior changed.
9. Report exact PASS/FAIL/PENDING/N/A evidence and never infer a stronger result from a weaker test class.

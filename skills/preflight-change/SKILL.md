---
name: preflight-change
description: Establish exact-head readiness for a Local LLM Server integration or release candidate, reusing equivalent evidence before running only missing gates.
---

# Preflight Change

Use this Skill when a coherent observable outcome moves to `INTEGRATION` or `RELEASE`. Do not require full publication ceremony for ordinary `ITERATION` edits, temporary pushes or draft collaboration updates.

1. Record stage, exact head and target/base. RELEASE requires FULL; INTEGRATION uses the narrowest sufficient risk profile.
2. Resolve material ambiguity, review the complete diff and make affected durable documentation current.
3. Run `scripts/select_validation_profile.py` and record risk dimensions, concrete required gates and profile shorthand.
4. When E2E is required, select the smallest affected journey, cheapest sufficient environment and `ASSERTIONS|SCREENSHOTS|FULL_MEDIA`. Preserve representative/target Apple Silicon gaps separately.
5. Classify required gates as `AGENT_LOCAL`, `REMOTE_AUTOMATED` or `REAL_ENVIRONMENT`.
6. Reuse successful evidence when head/source tree, target/base, required gates/profile and relevant E2E identity remain equivalent. Collaboration metadata alone does not invalidate proof.
7. A content-preserving squash/rebase merge into `dev` may reuse trusted integration evidence only when repository automation proves the merge tree equals the validated source tree and the merge parent equals the validated target/base. Direct pushes without equivalent evidence validate normally.
8. Route only missing, stale or insufficient deterministic gates through `.github/workflows/ci.yml`; never delegate automatable work to the user.
9. Classify failures as change regression, baseline, environment, flaky, base drift or assumption and fix the owning invariant rather than weakening a gate.

Report stage/head/target, documentation impact, risks/profile/gates, reused evidence, new deterministic evidence, E2E environment/mode, residual real-environment gaps and readiness.

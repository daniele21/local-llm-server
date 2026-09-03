---
name: validate-change
description: Select the cheapest sufficient Local LLM Server validation by delivery stage and risk, escalating only when changed invariants require stronger browser/package/security/L2 or real-hardware evidence.
---

# Validate Change

Optimize for sufficient confidence per feedback time. `.engineering/commands.json` owns stage/gate routing; `.engineering/e2e.json` owns journey, fidelity and evidence mode.

## ITERATION
Run focused owner-local checks. A contained Python change normally needs lint + fast Python evidence, not a 3-version matrix, Playwright, package smoke, security audit or L1/L2 fitness. No exact-head/documentation/preflight ceremony merely because those gates exist.

## INTEGRATION
For a coherent observable outcome, use the selector's `risk dimensions -> required gates -> profile` mapping. Runtime/UI/E2E boundaries may add Playwright; packaging/dependency changes may add wheel smoke/security; FULL adds L1/L2 specialist fitness.

## RELEASE
Use FULL plus release-critical package/E2E/security/L1-L2 and residual target-environment evidence.

UI evidence modes are `ASSERTIONS`, `SCREENSHOTS`, `FULL_MEDIA`. Status/navigation and stable evaluation review use screenshots; chat failure/recovery and model-runtime lifecycle visibility use full media; external application API and cleanup contracts use assertions. Real model/backend/memory/thermal claims remain representative/target Apple Silicon evidence.

Classify every red gate before editing as change regression, baseline, environment, flaky, base drift or assumption. Fix the owning invariant; never suppress a legitimate gate. Hand exact-head integration/release readiness to `preflight-change`.

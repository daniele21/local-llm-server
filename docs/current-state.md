# Current State

Status: active
Last reviewed: 2026-08-18

Local LLM Server is a local-first, privacy-preserving multi-backend inference server with deterministic hosted-CI boundaries and representative-device evidence for hardware-dependent claims. Local LLM Studio is the bundled browser control-plane surface.

## Engineering baseline

- Standard: `daniele21/repo-template-sw` **0.4.0**, pinned to revision `60e0f498a459e2de114ccb23f6cd50994c19513f`.
- Target maturity is **L2**; the browser UI adopts `product-ui`.
- Repository-side 0.3.0 L2 acceptance: `d528b6c5b676e705e7ccf24800929da6d5534203`.
- 0.4.0 `product-ui` repository guardrails were accepted on exact head `89d360698234016ddfe1f3fff0bacbc4f9bb7852` after the complete deterministic gate set passed.
- Full engineering L2 remains **hardware-gate pending**; full `product-ui` L2 remains **manual-evidence pending**.
- L1 acceptance: `d068a76d07bf204ca58ee2dfc29890bf3f1177cb`.
- Canonical branch protection remains owner-deferred.
- Profiles: Python, local-AI, TypeScript, macOS and product-ui.

## L2 repository capabilities

The accepted repository baseline includes:

- architecture ownership/dependency fitness rules;
- deterministic resource-ledger and retained-Python-heap regression evidence with native/unified-memory non-claims;
- reproducible request-preparation performance regression with repeated identity-bearing evidence;
- critical fault-injection/recovery and lifecycle repeatability coverage;
- fresh-installed-wheel HTTP failure → retry → recovery with bounded shutdown;
- complexity/dependency review plus privacy-safe reproducible evidence identity;
- documentation/repository drift detection.

Repository Health permanently runs the L1/L2 structural fitness functions. L2 Performance Regression, Artifact Lifecycle, Security Audit, Package Install Smoke, Python 3.10/3.11/3.12, lint, Playwright and zero-residue remain blocking validation surfaces.

## 0.4.0 product experience guardrails

The accepted migration preserves the existing code-first UI system:

- `src/local_llm_server/static/design-system.css` owns semantic tokens/components;
- `docs/brand-guidelines.md` owns durable brand/product language;
- `design/ux-contract.json` owns task model, progressive disclosure, critical states, WCAG 2.2 AA target, adaptive layout and critical journeys;
- `design/brand-kit.json` routes machine-readable brand roles to existing `--ds-*` tokens and shipped assets;
- Repository Health blocks on upstream Product Experience plus local product-ui L2 drift/evidence checks;
- accessibility tests and Playwright journeys map to the claims they can prove;
- token/component ownership and adaptive breakpoints are drift-checked;
- significant UI changes review hierarchy, cognitive load, recovery, accessibility, adaptive behavior, design-system reuse and evidence;
- product telemetry stays off by default; usability evidence is bounded and sanitized.

Pixel visual regression remains deferred until a stable high-risk visual surface justifies a maintained pixel contract.

## Remaining L2 gates

### Engineering / hardware

Full engineering L2 requires retained physical evidence from `docs/workstreams/runtime-correctness-evidence-hardening.md`: target-Mac thinking comparison, comparable evaluation runs, Apple Silicon reclamation cycles and bounded resource-policy smoke.

Hosted CI does not prove Apple unified/native/accelerator memory reclamation, backend/model performance, thermal behavior or backend-specific thinking behavior.

### Product experience

Two independent real-human tasks remain under `docs/product-experience-validation.md`:

- manual accessibility review of built primary journeys;
- representative-user usability with bounded non-sensitive task/outcome evidence.

Until both are resolved with real evidence or a justified product-risk decision, claim **0.4.0 product-ui repository guardrails accepted**, not **full product-ui L2 evidence complete**.

## Active workstreams

- `docs/workstreams/l2-reference-grade.md` — full engineering L2 hardware gate.
- `docs/workstreams/runtime-correctness-evidence-hardening.md` — representative-device runtime evidence.
- `docs/workstreams/v040-product-ui-l2.md` — manual accessibility and representative-user usability evidence.

## Durable operational references

- `docs/architecture.md`
- `docs/architecture-fitness.md`
- `docs/resource-regression-contract.md`
- `docs/performance-regression.md`
- `docs/fault-injection-contract.md`
- `docs/repeatability-contract.md`
- `docs/built-surface-e2e.md`
- `docs/change-review-evidence-identity.md`
- `docs/brand-guidelines.md`
- `docs/product-experience-validation.md`
- `docs/device-evidence-runbook.md`

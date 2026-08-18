# Current State

Status: active
Last reviewed: 2026-08-18

Local LLM Server is a local-first, privacy-preserving multi-backend inference server with deterministic hosted-CI boundaries and representative-device evidence for hardware-dependent claims. Local LLM Studio is the bundled browser control-plane surface.

## Engineering baseline

- Standard: `daniele21/repo-template-sw` **0.4.0**, pinned to revision `60e0f498a459e2de114ccb23f6cd50994c19513f`.
- Target maturity is **L2**; the material browser UI adopts the `product-ui` profile.
- Repository-side 0.3.0 L2 acceptance remains recorded at `d528b6c5b676e705e7ccf24800929da6d5534203`.
- The 0.4.0 `product-ui` deterministic repository guardrails were accepted on exact head `89d360698234016ddfe1f3fff0bacbc4f9bb7852` after Repository Health, L2 Performance Regression, Artifact Lifecycle, Security Audit, Package Install Smoke, lint, Python 3.10/3.11/3.12, Playwright E2E and zero-residue all passed.
- Full engineering L2 remains **hardware-gate pending**; representative Apple Silicon/model/backend claims are not inferred from hosted CI.
- Full `product-ui` L2 remains **manual-evidence pending**; automated checks are not relabelled as representative-user or manual accessibility evidence.
- L1 acceptance revision: `d068a76d07bf204ca58ee2dfc29890bf3f1177cb`.
- Canonical branch protection remains intentionally deferred by the owner.
- Profiles: Python, local-AI, TypeScript, macOS and product-ui.

## L2 repository capabilities

The accepted repository baseline includes:

- AST-backed architecture ownership/dependency fitness rules;
- deterministic resource-ledger and retained-Python-heap regression evidence with native/unified-memory non-claims;
- reproducible synthetic request-preparation performance regression with warm-up, repeated samples and identity-bearing evidence;
- critical fault-injection/recovery coverage across resource, worker, persistence, pressure and request lifecycles;
- explicit repeatability/cleanliness evidence for development, test, E2E, build, smoke and runtime lifecycles;
- fresh-installed-wheel HTTP failure → retry → recovery using real localhost Uvicorn and bounded shutdown;
- five-question complexity/dependency review plus privacy-safe reproducible evidence identity;
- documentation/repository drift detection for freshness, canonical scope, duplicate bodies, workstream consistency and completed-workstream cleanup.

Repository Health permanently runs the L1/L2 structural fitness functions. `L2 Performance Regression` is a separate blocking timed gate; Artifact Lifecycle, Security Audit, Package Install Smoke, Python 3.10/3.11/3.12, lint, Playwright and zero-residue remain part of the accepted validation surface.

## 0.4.0 product experience guardrails

The accepted migration preserves the existing code-first UI system rather than introducing a second framework:

- `src/local_llm_server/static/design-system.css` remains the canonical semantic token/component owner;
- `docs/brand-guidelines.md` remains the durable brand/product-language owner;
- `design/ux-contract.json` declares the user-task model, progressive disclosure, critical states, WCAG 2.2 AA target, adaptive layout classes and critical journeys;
- `design/brand-kit.json` routes machine-readable brand roles to the existing `--ds-*` tokens and real shipped assets;
- Repository Health treats the upstream Product Experience Contract and local product-ui L2 drift/evidence policy as blocking fitness functions;
- existing accessibility tests and Playwright journeys are mapped to the experience claims they can actually prove;
- reserved design-system token/component ownership and required adaptive breakpoints are checked for drift;
- significant UI changes must review information hierarchy, cognitive load, recovery, accessibility, adaptive behavior, design-system reuse and evidence;
- product telemetry remains off by default and usability evidence is restricted to bounded sanitized task/outcome fields.

Pixel visual regression is intentionally deferred until a stable high-risk visual surface justifies a maintained pixel contract. That scope decision does not turn semantic/E2E evidence into a visual-regression claim.

## Remaining L2 gates

### Engineering / hardware

Full engineering L2 requires compatible retained physical evidence from `docs/workstreams/runtime-correctness-evidence-hardening.md`, including target-Mac thinking comparison, comparable evaluation runs, Apple Silicon reclamation cycles and bounded resource-policy smoke.

Hosted CI does not prove Apple unified/native/accelerator memory reclamation, backend/model TTFT or throughput, thermal behavior, backend-specific thinking behavior, or representative-hardware pressure-eviction safety.

### Product experience

Two independent real-human evidence tasks remain under `docs/product-experience-validation.md`:

- manual accessibility review of the built primary journeys;
- representative-user usability session using bounded non-sensitive task/outcome evidence.

Until both are completed or explicitly resolved through a justified product-risk decision, the repository may claim **0.4.0 product-ui repository guardrails accepted**, but not **full product-ui L2 evidence complete**.

## Active workstreams

- `docs/workstreams/l2-reference-grade.md` — full engineering L2 hardware evidence gate.
- `docs/workstreams/runtime-correctness-evidence-hardening.md` — representative-device runtime correctness and evidence.
- `docs/workstreams/v040-product-ui-l2.md` — only the remaining manual accessibility and representative-user usability evidence for full product-ui L2.

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

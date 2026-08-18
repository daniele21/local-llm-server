# Current State

Status: active
Last reviewed: 2026-08-18

Local LLM Server is a local-first, privacy-preserving multi-backend inference server with deterministic hosted-CI boundaries and representative-device evidence for hardware-dependent claims. Local LLM Studio is the bundled browser control-plane surface.

## Engineering baseline

- Migration target: `daniele21/repo-template-sw` **0.4.0**, pinned to revision `60e0f498a459e2de114ccb23f6cd50994c19513f`.
- Target maturity remains **L2**; the material browser UI adopts the `product-ui` profile.
- The previously accepted 0.3.0 repository-side L2 revision remains `d528b6c5b676e705e7ccf24800929da6d5534203` while the 0.4.0 product-experience delta is being validated.
- Full engineering L2 remains **hardware-gate pending**; representative Apple Silicon/model/backend claims are not inferred from hosted CI.
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

Repository Health permanently runs the existing L1/L2 structural fitness functions. `L2 Performance Regression` is a separate blocking timed gate; Artifact Lifecycle, Security Audit, Package Install Smoke, Python 3.10/3.11/3.12, lint, Playwright and zero-residue remain part of the accepted validation surface.

## 0.4.0 product experience migration

The migration preserves the existing code-first UI system rather than introducing a second framework:

- `src/local_llm_server/static/design-system.css` remains the canonical semantic token/component owner;
- `docs/brand-guidelines.md` remains the durable brand/product-language owner;
- `design/ux-contract.json` declares the user-task model, progressive disclosure, critical states, WCAG 2.2 AA target, adaptive layout classes and critical journeys;
- `design/brand-kit.json` routes machine-readable brand roles to the existing `--ds-*` tokens and real shipped assets;
- Repository Health now treats the upstream Product Experience Contract and local product-ui L2 drift/evidence policy as fitness functions;
- existing accessibility tests and Playwright journeys are mapped to the experience claims they can actually prove;
- significant UI changes must review information hierarchy, cognitive load, recovery, accessibility, adaptive behavior, design-system reuse and evidence;
- product telemetry remains off by default and usability evidence is restricted to bounded sanitized task/outcome fields.

Manual accessibility and representative-user usability evidence are **pending**. Automated source/E2E evidence is not relabelled as human evidence. Pixel visual regression is intentionally deferred until a stable high-risk visual surface justifies a maintained pixel contract.

## Remaining L2 gates

### Engineering / hardware

Full engineering L2 requires compatible retained physical evidence from `docs/workstreams/runtime-correctness-evidence-hardening.md`, including target-Mac thinking comparison, comparable evaluation runs, Apple Silicon reclamation cycles and bounded resource-policy smoke.

Hosted CI does not prove Apple unified/native/accelerator memory reclamation, backend/model TTFT or throughput, thermal behavior, backend-specific thinking behavior, or representative-hardware pressure-eviction safety.

### Product experience

Full `product-ui` L2 must not be claimed while manual accessibility and representative-user usability remain pending under `docs/product-experience-validation.md`.

## Active workstreams

- `docs/workstreams/l2-reference-grade.md` — full engineering L2 hardware evidence gate.
- `docs/workstreams/runtime-correctness-evidence-hardening.md` — representative-device runtime correctness and evidence.
- `docs/workstreams/v040-product-ui-l2.md` — 0.4.0/product-ui integration acceptance and manual product-experience evidence boundary.

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

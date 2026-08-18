# Current State

Status: active
Last reviewed: 2026-08-18

Local LLM Server is a local-first, privacy-preserving multi-backend inference server. Local LLM Studio is its bundled browser control plane. Hosted CI proves deterministic software contracts; hardware- and human-dependent claims require identified real evidence.

## Engineering baseline

- Standard: `daniele21/repo-template-sw` **0.4.0**, revision `60e0f498a459e2de114ccb23f6cd50994c19513f`.
- Target maturity: **L2** with Python, local-AI, TypeScript, macOS and `product-ui` profiles.
- L1 acceptance: `d068a76d07bf204ca58ee2dfc29890bf3f1177cb`.
- Engineering repository-side L2 acceptance: `d528b6c5b676e705e7ccf24800929da6d5534203`.
- `product-ui` repository guardrails acceptance: `89d360698234016ddfe1f3fff0bacbc4f9bb7852`.
- Real-evidence bridge acceptance: `de899cc945e1d1c735a2ded91c5da717ce0fe2b0`.
- Full engineering L2 remains **real-hardware-evidence pending**; full `product-ui` L2 remains **real-human-evidence pending**.
- Canonical branch protection remains owner-deferred.

## Accepted deterministic L2 surface

Repository Health permanently blocks on L1/L2 architecture, resource, lifecycle, security, repeatability, built-surface, product-experience, design-system and real-evidence-bridge fitness functions. Separate blocking surfaces include L2 Performance Regression, Artifact Lifecycle, Security Audit, Package Install Smoke, Python 3.10/3.11/3.12, lint, Playwright and zero residue.

The accepted product-ui system keeps `design-system.css` as semantic token/component owner; `design/ux-contract.json` owns task/state/accessibility/adaptive/journey contracts; `design/brand-kit.json` routes brand roles to existing shipped assets/tokens. Product telemetry remains off by default.

The accepted L2 evidence bridge adds:

- privacy-safe explicit thinking ON/OFF-hidden capture without retaining prompt/output;
- deterministic validation of the complete representative-device TH-E1/EV-3/HE-2/RES-2 bundle;
- conservative reclamation-review recomputation rather than trusting a stored verdict;
- bounded manual accessibility/usability templates and validators that reject example/private/incomplete evidence;
- explicit evidence-readiness output that never mutates maturity claims automatically.

## Remaining L2 evidence

### Representative Mac

`docs/device-evidence-runbook.md` owns the executable procedure. Still required:

- TH-E1 — explicit thinking OFF + ON-hidden on the target runtime;
- EV-3 — two attribution-safe `general-purpose v1.0.0`, 10-sample, seed-0 OFF runs;
- HE-2 — two compatible verified 3-cycle Apple Silicon reclamation reports plus conservative review;
- RES-2 — bounded safe admit/account/infer/unload/reject resource-policy smoke.

The bundle is acceptance-ready only when `python -m local_llm_server.l2_evidence_bridge validate-hardware-bundle` reports complete. Hosted CI does not prove Apple unified/native/accelerator memory reclamation, backend/model performance, thermal behavior or real-model thinking behavior.

### Product experience

Two independent human tasks remain:

- PX4-09 — manual accessibility review of the built primary journeys;
- PX4-10 — representative-user usability with bounded non-sensitive task/outcome evidence.

`python -m local_llm_server.l2_evidence_bridge validate-product-ui` validates the bounded evidence but does not promote baseline status. Negative/inconclusive findings remain evidence and require remediation/judgment rather than being hidden or rerun merely to obtain a pass.

## Active workstreams

- `docs/workstreams/l2-reference-grade.md` — cumulative L2 completion gate.
- `docs/workstreams/runtime-correctness-evidence-hardening.md` — representative-device evidence.
- `docs/workstreams/v040-product-ui-l2.md` — manual accessibility/usability evidence.

## Durable operational references

- `docs/architecture.md`
- `docs/resource-regression-contract.md`
- `docs/performance-regression.md`
- `docs/repeatability-contract.md`
- `docs/product-experience-validation.md`
- `docs/device-evidence-runbook.md`

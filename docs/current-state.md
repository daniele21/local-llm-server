# Current State

Status: active
Last reviewed: 2026-08-30

Local LLM Server is a local-first, privacy-preserving multi-backend inference server. Local LLM Studio is its bundled browser control plane. Hosted CI proves deterministic software contracts; hardware- and human-dependent claims require identified real evidence.

## Engineering baseline

- Standard: `daniele21/repo-template-sw` **0.8.0**, revision `4167fe353c53cff0849fc23c9a698c0655aac4ea`.
- Target maturity: **L2** with Python, local-AI, TypeScript, macOS and `product-ui` profiles.
- L1 acceptance: `d068a76d07bf204ca58ee2dfc29890bf3f1177cb`.
- Engineering repository-side L2 acceptance: `d528b6c5b676e705e7ccf24800929da6d5534203`.
- `product-ui` repository guardrails acceptance: `89d360698234016ddfe1f3fff0bacbc4f9bb7852`.
- Real-evidence bridge acceptance: `de899cc945e1d1c735a2ded91c5da717ce0fe2b0`.
- Template 0.8 adds publication preflight, execution-capability classification, blast-radius validation profiles and environment-aware E2E fidelity without weakening specialist L1/L2 gates.
- Full engineering L2 remains **real-hardware-evidence pending**; full `product-ui` L2 remains **real-human-evidence pending**.
- Canonical branch protection remains owner-deferred.

## Accepted deterministic L2 surface

Repository Health blocks on L1/L2 architecture, resource, lifecycle, security, repeatability, built-surface, product-experience, design-system and real-evidence-bridge fitness plus the repo-template 0.8 operating/E2E contracts. Separate blocking surfaces include L2 Performance Regression, Artifact Lifecycle, Security Audit, Package Install Smoke, Python 3.10/3.11/3.12, lint, Playwright and zero residue.

Runtime hardening is fail-conservative: routing/accounting remains owned until teardown succeeds, failed teardown stays retryable, and explicit in-process close is not a reclamation claim. Resident and active-request estimates now share one configured budget with distinct ownership; chat/vision streams and first-class ASR retain transient accounting through execution. Missing memory evidence stays unavailable rather than becoming zero or guessed KV bytes.

Managed `llama_server` uses the attributable llama.cpp `v0.3.0` feature floor (`b10621`, `c1d0e7a...`) by default. Explicit executable selection is authoritative; legacy/unparseable binaries require an escape hatch and receive no v0.3-only flags. Local LLM Server maps admitted concurrency to `--parallel`; llama.cpp owns runtime-local batching/KV. No upstream multi-model router or silent executable download/replacement is adopted. Build/version attribution is identity, not cryptographic provenance.

The automated E2E boundary is environment-aware:

- `ci-studio-deterministic` proves browser -> UI JavaScript -> HTTP -> middleware/runtime-contract behavior with deterministic fake inference and zero residue;
- `ci-installed-wheel` proves the built/package surface independently of Apple Silicon runtime behavior;
- representative Apple Silicon runs remain separate evidence for model/backend compatibility, unified-memory behavior, reclamation, latency/throughput and thermal/power claims.

The accepted product-ui system keeps `design-system.css` as semantic token/component owner; `design/ux-contract.json` owns user/task/decision-order/state/accessibility/adaptive/motion/journey contracts; `design/brand-kit.json` routes brand/motion roles to shipped assets/tokens. Product telemetry remains off by default.

The accepted L2 evidence bridge adds:

- privacy-safe thinking ON/OFF-hidden capture without retaining prompt/output;
- deterministic validation of the representative-device TH-E1/EV-3/HE-2/RES-2 bundle;
- conservative reclamation-review recomputation rather than trusting a stored verdict;
- bounded manual accessibility/usability templates that reject example/private/incomplete evidence;
- evidence-readiness output that never mutates maturity claims automatically.

## Remaining L2 evidence

### Representative Mac

`docs/device-evidence-runbook.md` owns the procedure. Still required:

- TH-E1 — thinking OFF + ON-hidden on the target runtime;
- EV-3 — two attribution-safe `general-purpose v1.0.0`, 10-sample, seed-0 OFF runs;
- HE-2 — two compatible verified 3-cycle Apple Silicon reclamation reports plus conservative review;
- RES-2 — bounded safe admit/account/infer/unload/reject resource-policy smoke.

The bundle is acceptance-ready only when `python -m local_llm_server.l2_evidence_bridge validate-hardware-bundle` reports complete. Hosted CI does not prove Apple unified/native/accelerator memory reclamation, backend/model performance, thermal behavior or real-model thinking behavior.

### Product experience

Two independent human tasks remain:

- PX4-09 — manual accessibility review of the built primary journeys;
- PX4-10 — representative-user usability with bounded non-sensitive task/outcome evidence.

`python -m local_llm_server.l2_evidence_bridge validate-product-ui` validates bounded evidence but does not promote baseline status. Negative/inconclusive findings require remediation/judgment rather than being hidden or rerun merely to obtain a pass.

## Active workstreams

- `docs/workstreams/runtime-resource-governor.md` — global governor and representative pressure/reclamation evidence.
- `docs/workstreams/l2-reference-grade.md` — cumulative L2 completion gate.
- `docs/workstreams/runtime-correctness-evidence-hardening.md` — representative-device evidence.
- `docs/workstreams/v040-product-ui-l2.md` — manual accessibility/usability evidence.

## Durable operational references

- `docs/architecture.md`
- `.engineering/e2e.json`
- `docs/resource-regression-contract.md`
- `docs/performance-regression.md`
- `docs/repeatability-contract.md`
- `docs/product-experience-validation.md`
- `docs/device-evidence-runbook.md`

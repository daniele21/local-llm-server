# Current State

Status: active
Last reviewed: 2026-08-30

Local LLM Server is a local-first multi-backend inference server with Local LLM Studio as its browser control plane. Hosted CI proves deterministic software contracts; hardware- and human-dependent claims require real evidence.

## Engineering baseline

- Standard: `daniele21/repo-template-sw` **0.8.0**, revision `4167fe353c53cff0849fc23c9a698c0655aac4ea`.
- Target maturity: **L2** with Python, local-AI, TypeScript, macOS and `product-ui` profiles.
- L1 acceptance: `d068a76d07bf204ca58ee2dfc29890bf3f1177cb`.
- Repository-side L2 acceptance: `d528b6c5b676e705e7ccf24800929da6d5534203`.
- `product-ui` guardrails: `89d360698234016ddfe1f3fff0bacbc4f9bb7852`; real-evidence bridge: `de899cc945e1d1c735a2ded91c5da717ce0fe2b0`.
- Template 0.8 adds publication preflight, execution-capability classification, blast-radius validation and environment-aware E2E.
- Full engineering L2 remains **real-hardware-evidence pending**; full `product-ui` L2 remains **real-human-evidence pending**.
- Canonical branch protection remains owner-deferred.

## Accepted deterministic L2 surface

Repository Health blocks on architecture, resource, lifecycle, security, repeatability, built-surface, product-experience, design-system and real-evidence-bridge fitness plus operating/E2E contracts. Separate blocking surfaces include performance regression, artifact lifecycle, security, package smoke, Python 3.10/3.11/3.12, lint, Playwright and zero residue.

Runtime hardening is fail-conservative: routing/accounting persists until teardown succeeds; failed teardown stays retryable; in-process close is not a reclamation claim. Resident and transient requests share one configured memory budget; queued work reserves no transient memory. Optional global execution admission bounds cross-runtime compute with round-robin fairness while preserving runtime semaphores and backend batching. Chat/vision, ASR and evaluation share it when configured; streams retain ownership through the final byte. Missing memory evidence remains unavailable.

Managed `llama_server` uses the attributable llama.cpp `v0.3.0` feature floor (`b10621`, `c1d0e7a...`) by default. Explicit executable selection is authoritative; legacy/unparseable binaries require an escape hatch and receive no v0.3-only flags. Local LLM Server maps admitted concurrency to `--parallel`; llama.cpp owns runtime-local batching/KV. No upstream multi-model router or silent executable replacement is adopted.

Automated E2E is environment-aware:

- `ci-studio-deterministic` proves browser journeys plus a direct external API-consumer journey over the real loopback HTTP boundary with the real FastAPI/middleware/task-policy/runtime/evaluation stack and deterministic inference;
- API black-box coverage includes discovery/identity/status, routing/default mutation, cross-runtime concurrency, fail-closed task/media policy, vision, hidden-reasoning SSE, backend failure/recovery, transcription, residency policy and built-in/custom evaluation;
- browser and API lanes share the run-owned process/listener/temp-root lifecycle; mutable custom evaluation state is reset before later visual evidence;
- `ci-installed-wheel` proves the built/package surface independently of Apple Silicon behavior;
- representative Apple Silicon evidence remains required for production backend compatibility, unified-memory reclamation, native cancellation, performance and thermal/power claims.

The accepted product-ui system keeps `design-system.css` as semantic token/component owner; `design/ux-contract.json` owns task/state/accessibility/adaptive/motion/journey contracts; `design/brand-kit.json` routes brand/motion roles. Product telemetry remains off by default.

The L2 evidence bridge supports privacy-safe thinking evidence, deterministic TH-E1/EV-3/HE-2/RES-2 bundle validation, conservative reclamation review, bounded manual accessibility/usability evidence and explicit readiness without automatic maturity promotion.

## Remaining L2 evidence

### Representative Mac

`docs/device-evidence-runbook.md` owns the procedure. Still required:

- TH-E1 — thinking OFF + ON-hidden on the target runtime;
- EV-3 — two attribution-safe `general-purpose v1.0.0`, 10-sample, seed-0 OFF runs;
- HE-2 — two compatible verified 3-cycle Apple Silicon reclamation reports plus conservative review;
- RES-2 — bounded safe admit/account/infer/unload/reject resource-policy smoke.

The bundle is ready only when `python -m local_llm_server.l2_evidence_bridge validate-hardware-bundle` reports complete. Hosted CI does not prove Apple memory reclamation, backend/model performance, thermals or real-model thinking behavior.

### Product experience

Two human tasks remain:

- PX4-09 — manual accessibility review of primary journeys;
- PX4-10 — representative-user usability with bounded non-sensitive evidence.

`python -m local_llm_server.l2_evidence_bridge validate-product-ui` validates evidence but does not promote baseline status. Negative/inconclusive findings require remediation or judgment.

## Active workstreams

- `docs/workstreams/api-blackbox-e2e-hardening.md` — direct external application-to-HTTP product acceptance coverage and final exact-head validation.
- `docs/workstreams/runtime-resource-governor.md` — representative pressure/reclamation evidence after deterministic governor completion.
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

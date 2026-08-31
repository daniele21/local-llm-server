# Current State

Status: active
Last reviewed: 2026-08-31

Local LLM Server is a local-first multi-backend inference server with Local LLM Studio as its browser control plane. Hosted CI proves deterministic software contracts; hardware- and human-dependent claims require the corresponding real evidence.

## Engineering baseline

- Standard: `daniele21/repo-template-sw` **0.8.0**, revision `6677c5349d64ea6d935f1b460d03a47c236821bc`.
- Target maturity: **L2** with Python, local-AI, TypeScript, macOS and `product-ui` profiles.
- Repository-side L2 acceptance: `d528b6c5b676e705e7ccf24800929da6d5534203`.
- Representative Apple Silicon hardware evidence is accepted for the minimum L2 runtime bundle and RRG-5 multi-model ownership/accounting procedure.
- Full L2 remains blocked only by the two real-human `product-ui` evidence tasks: manual accessibility and representative-user usability.

## Accepted deterministic L2 surface

Repository Health blocks on architecture, resource, lifecycle, security, repeatability, built-surface, product-experience, design-system and real-evidence-bridge fitness plus operating/E2E contracts. Separate blocking surfaces include performance regression, artifact lifecycle, security, package smoke, Python 3.10/3.11/3.12, lint, Playwright and zero residue.

Runtime hardening is fail-conservative: routing/accounting persists until teardown succeeds; failed teardown stays retryable; in-process close is not a reclamation claim. Resident and transient requests share one configured memory budget; queued work reserves no transient memory. Optional global execution admission bounds cross-runtime compute with round-robin fairness while preserving runtime semaphores and backend batching. Chat/vision, ASR and evaluation share it when configured; streams retain ownership through the final byte. Missing memory evidence remains unavailable.

Managed `llama_server` uses the attributable llama.cpp `v0.3.0` feature floor (`b10621`, `c1d0e7a...`) by default. Explicit executable selection is authoritative; legacy/unparseable binaries require an escape hatch and receive no v0.3-only flags. Positive build+commit attribution for an unchanged executable is reused within the owning process instead of reprobed for every resident runtime; binary replacement invalidates that reuse. Local LLM Server maps admitted concurrency to `--parallel`; llama.cpp owns runtime-local batching/KV. No upstream multi-model router or silent executable replacement is adopted.

Automated E2E is environment-aware:

- `ci-studio-deterministic` proves browser journeys plus a direct external API-consumer journey over loopback HTTP with the real FastAPI/middleware/task-policy/runtime/evaluation stack and deterministic inference;
- API black-box coverage includes discovery/status, routing/default mutation, cross-runtime concurrency, fail-closed task/media policy, vision, hidden-reasoning SSE, backend failure/recovery, transcription, residency policy and built-in/custom evaluation;
- browser and API lanes share the run-owned lifecycle; mutable custom evaluation state is reset before later visual evidence;
- `ci-installed-wheel` proves the built/package surface independently of Apple Silicon behavior;
- representative Apple Silicon evidence is still required for any new production-backend, performance, native cancellation, thermal/power or cross-device claim not covered by the accepted campaigns below.

The accepted product-ui system keeps `design-system.css` as semantic token/component owner; `design/ux-contract.json` owns task/state/accessibility/adaptive/motion/journey contracts. Product telemetry remains off by default.

The L2 evidence bridge supports privacy-safe thinking evidence, TH-E1/EV-3/HE-2/RES-2 bundle validation, conservative reclamation review and bounded manual accessibility/usability evidence.

## Accepted representative Mac evidence

The 2026-08-31 representative-device campaign completed the minimum L2 hardware bundle:

- TH-E1 — explicit thinking OFF and ON-hidden completed under the bounded policy/exposure contract;
- EV-3 — two comparable attribution-safe `general-purpose v1.0.0`, 10-sample, seed-0 reasoning-OFF runs completed;
- HE-2 — two compatible verified 3-cycle Apple Silicon reclamation reports passed conservative review;
- RES-2 — bounded safe admit/account/infer/unload/reject resource-policy smoke completed;
- the minimum L2 bundle validator reported PASS.

RRG-5 was then completed separately on the representative Mac after fixing repeated external-runtime attribution during second-resident construction. The final conservative review reported `sufficient_observation_set` across 2 compatible reports, 4 complete cycles, 4 verified-identity cycles, 4 transient-overlap cycles, 4 clean-accounting cycles and 2 complete shutdown-under-load procedures.

The retained post-stop RSS and available-memory deltas remain observational. `automatic_eviction_recommendation=not_provided`, `reclamation_safety_claim=false` and `production_safety_claim=false`; automatic pressure eviction therefore remains disabled. This evidence confirms the exercised target-Mac procedures only and is not a cross-device, thermal, throughput or production-safety claim.

## Remaining L2 evidence

### Product experience

- PX4-09 — manual accessibility review of primary journeys;
- PX4-10 — representative-user usability with bounded non-sensitive evidence.

## Active workstreams

- `docs/workstreams/l2-reference-grade.md` — cumulative L2 completion gate, now waiting on the two human product-experience evidence tasks.
- `docs/workstreams/v040-product-ui-l2.md` — manual accessibility/usability evidence.

## Durable operational references

- `docs/architecture.md`
- `.engineering/e2e.json`
- `docs/resource-regression-contract.md`
- `docs/performance-regression.md`
- `docs/repeatability-contract.md`
- `docs/product-experience-validation.md`
- `docs/device-evidence-runbook.md`

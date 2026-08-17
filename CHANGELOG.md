# Changelog

## 0.4.0 — 2026-08-17

Turns Local LLM Server into a resource-aware local inference control plane with
source-backed administration, evaluation and runtime evidence.

### Added

- a unified Studio control plane for models and runtimes, endpoints, Playground,
  benchmark and evaluation, diagnostics and settings;
- deterministic evaluation datasets, custom dataset import, persisted run history,
  comparison summaries and per-sample inspection with retained prompt, expected
  answer, model output, checks and raw metrics for new runs;
- explicit runtime capability, task and feature contracts for text, structured
  output, vision and transcription workflows;
- bounded request scheduling, runtime admission, residency accounting, eviction,
  pressure-policy foundations and isolated worker lifecycle contracts;
- privacy-safe runtime identity, verified GGUF artifact receipts, backend identity,
  completion metrics, hardware evidence and conservative evidence review tooling;
- a Playwright Chromium end-to-end gate covering critical Studio workflows.

### Changed

- server startup now prints the UI address and shutdown handles Ctrl+C without an
  application traceback;
- reasoning is controlled through an explicit requested/effective policy and its
  state is recorded in evaluation manifests;
- release artifacts now validate tag, `VERSION` and package metadata identity and
  publish SHA-256 checksums;
- CI now validates pushes to `dev` and audits high-severity npm vulnerabilities.

### Fixed

- evaluation details remain open during asynchronous history refreshes and explain
  clearly when older runs did not retain sample content;
- source-backed evaluation policy initialization no longer races during startup;
- long-lived responses follow the correct graceful-shutdown ordering;
- Playground capability defaults and API error reporting are aligned with text-only
  models;
- Playwright is updated to a non-vulnerable dependency release.

### Release evidence and limits

- deterministic Python tests and browser E2E are release gates;
- the npm dependency audit has no known vulnerabilities at publication time;
- representative-device memory-pressure and reclamation evidence remains an
  explicit follow-up gate, so this version does not claim universal hardware or
  production-load qualification.

## 0.3.8 — 2026-07-13

- Previous packaged release baseline.

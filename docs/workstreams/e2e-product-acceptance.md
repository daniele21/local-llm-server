# E2E product acceptance hardening

Status: active
Document type: workstream-state
Owner: repository
Canonical scope: workstreams.e2e-product-acceptance
Read when: changing automated browser acceptance, deterministic product E2E coverage, or real-runtime smoke boundaries
Last reviewed: 2026-08-17

## Purpose

This workstream adds automated **product-boundary acceptance** without weakening the distinction between deterministic CI evidence and representative real-device evidence.

It does not replace [`runtime-correctness-evidence-hardening.md`](runtime-correctness-evidence-hardening.md) or the representative-device runbook. Hosted CI must never be presented as proof of real model quality, memory reclamation, Apple Silicon resource behavior, or performance.

## E2E-001 — automated product acceptance

State: `VALIDATION`

### Lane A — deterministic browser product gate

The existing Playwright gate remains mandatory on pull requests and uses the real FastAPI/Studio product stack with deterministic resident fake runtimes.

Coverage must include:

- first-party public contract coherence across `/v1/models`, `/v1/runtime/identity` and `/status`;
- explicit multi-model routing from the Playground;
- thinking execution/visibility contracts;
- structured-output separation from hidden reasoning;
- runtime status becoming observable while a request is genuinely active;
- typed API failures rendering actionable UI errors;
- recovery of the next inference after a failed request;
- evaluation request/reasoning-policy behavior;
- keyboard navigation already owned by the Studio acceptance suite.

The fixture may delay deterministic chunks solely to let the 300 ms UI status poll observe a real active request. That delay is not a latency benchmark.

### Lane B — public API/product contract

Browser request-context checks use the same fixture server to verify the public serving surfaces independently from DOM assertions. Identity must remain path-free and versioned; status remains dynamic telemetry rather than stable identity.

### Lane C — real-runtime smoke

`tests/real_runtime/smoke_runtime.py` is an opt-in bounded preflight against an already running real Local LLM Server.

It checks:

```text
/health
/v1/models
/v1/runtime/identity
/status
/v1/chat/completions
```

The smoke retains only bounded metadata and does not print or persist prompt/model-output content. It is intentionally excluded from hosted PR CI.

## Acceptance

E2E-001 can move to `DONE` when:

1. the deterministic Playwright product gate passes on the final feature head;
2. the normal Python/lint matrix passes unchanged on the same head;
3. failure traces/screenshots remain available only when the browser gate fails;
4. the real-runtime smoke is documented and stays opt-in;
5. no deterministic fixture result is promoted as representative hardware/model evidence;
6. the workstream is merged into `dev`.

## Relationship to real evidence

After E2E-001, the intended sequence is:

```text
unit/integration green
        +
Playwright product acceptance green
        +
real-runtime smoke green on target machine
        |
        v
human/manual acceptance + representative device evidence
```

The final two stages remain necessary. Automated product acceptance reduces avoidable manual regressions; it does not eliminate human UX review or physical-device evidence.

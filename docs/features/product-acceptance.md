# Product acceptance

Status: active
Document type: feature
Owner: repository
Canonical scope: features.product-acceptance
Read when: changing automated Studio/product acceptance or interpreting deterministic E2E evidence
Last reviewed: 2026-08-17

Local LLM Server has a mandatory deterministic browser acceptance gate that exercises the real FastAPI/Studio product stack with synthetic resident runtimes. It validates assembled product journeys that unit tests alone cannot prove while preserving a strict boundary from real model/hardware evidence.

## Deterministic browser boundary

The Playwright fixture runs the shipped product composition and Studio assets against deterministic fake engines. Current coverage includes:

- public contract coherence across `/v1/models`, `/v1/runtime/identity` and `/status`;
- explicit multi-model routing from the Playground;
- reasoning/thinking execution versus visibility controls;
- structured JSON final-output separation from hidden reasoning;
- runtime status becoming observable while a request is genuinely active;
- typed API failures rendering actionable UI errors;
- recovery of the next inference after a failed request;
- evaluation request/reasoning-policy behavior;
- control-plane keyboard navigation.

The default synthetic runtime returns `42`; an alternate runtime returns `84`. A special slow fixture request can delay chunks just long enough for the Studio status poller to observe active generation. That delay is test synchronization, not latency evidence.

## Public API checks

Browser request-context tests use the same fixture server to inspect product HTTP behavior independently from DOM assertions. Runtime identity remains stable/path-free execution identity; `/status` remains mutable telemetry.

## Run lifecycle and failure evidence

The fixture uses a run-owned temporary evaluation root. Cleanup is ownership-checked and covers normal shutdown plus process-finally fallback. Playwright failure traces/screenshots are bounded diagnostics and synthetic fixture content must not include user model files or private evaluation data.

`tests/e2e/README.md` owns the executable browser instructions and lifecycle details. The repository-health/integration workflow owns whether post-run residue checks are blocking.

## Real-runtime smoke

`tests/real_runtime/smoke_runtime.py` is an opt-in bounded preflight against an already running real Local LLM Server. It checks the minimum serving surface:

```text
/health
/v1/models
/v1/runtime/identity
/status
/v1/chat/completions
```

It retains bounded metadata and does not print/persist prompt or model-output content. It is intentionally excluded from hosted PR CI.

## Evidence boundary

The intended evidence ladder is:

```text
unit / contract tests
        +
Playwright deterministic product acceptance
        +
real-runtime smoke on the target machine
        |
        v
manual acceptance + representative-device evidence
```

The deterministic gate proves assembled product contracts, not real model quality, memory reclamation, Apple Silicon resource behavior, throughput or thermal stability. Those claims remain owned by the representative-device runbook and runtime-correctness workstream.

The browser acceptance implementation was originally integrated through PR #114 and validated there by lint, Python 3.10/3.11/3.12 tests and the mandatory Playwright job. Git history owns that implementation chronology; this document owns the durable behavior.

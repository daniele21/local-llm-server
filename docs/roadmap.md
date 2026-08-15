# Control-plane and UX/UI roadmap

Status: active
Document type: roadmap
Owner: repository
Canonical scope: roadmap.repository
Read when: selecting the next capability milestone, understanding dependencies or parallelizing implementation
Last reviewed: 2026-08-15

Integrated truth belongs in [`current-state.md`](current-state.md). This file owns sequencing and dependency release points.

## Objective

Evolve Local LLM Server into a **resource-aware, observable local AI control plane and evaluation harness** while specialist runtimes retain backend execution ownership.

## Milestone summary

| Milestone | Status | Remaining outcome |
| --- | --- | --- |
| M0 documentation governance | DONE | keep plan synchronized |
| M1 trustworthy foundation | PARTIAL | retire legacy direct-app/parser boundary + UX evidence |
| M2 resource-aware runtime | PARTIAL | product budget policy, reclamation evidence, zero-resident, scheduler, eviction |
| M3 multi-task control plane | PARTIAL | full capability enforcement + first-class ASR/task routing |
| M4 evidence-grade observability | PARTIAL | live canonical metrics/fingerprint exposure + representative evidence |
| M5 control-plane UX | PARTIAL | resource/evidence panels, Playground/Diagnostics, accessibility |
| M6 evaluation harness | PARTIAL | resident-runtime binding, persistence/history and real UI workflow |
| M7 product-grade candidate | BLOCKED | representative hardware/release evidence |

## Completed foundations

- **A1 CI** — blocking deterministic Python 3.10/3.11/3.12 tests and Ruff correctness gate.
- **A3 decoupling** — no ClosedRoom-specific core registry dependency.
- **F1 positioning** — control-plane product language with current-vs-target separation.
- **D1 metrics vocabulary** — truthful token/chunk/duration/throughput semantics.
- **D3a artifact identity** — path-free artifact source/verification identity.
- **D4a/b evaluation foundation** — versioned schema, deterministic selection, 20-sample built-in set and objective scorer.

## Wave 4 integrated results

### A2/C1/AC1 — PARTIAL

Integrated:

- canonical request-policy middleware for supported public/CLI server entrypoints;
- remote HTTP(S) media rejected before backend invocation by default;
- explicit opt-in preserved;
- prepared canonical request attached to request state;
- public `serve()`, package `run_server()` and CLI server path install policy;
- automated acceptance proves a policy rejection performs zero backend calls.

Remaining:

- historical route still rebuilds backend kwargs with duplicate parsing;
- direct legacy `local_llm_server.server:app` does not automatically install policy;
- full task/feature capability rejection remains C2d.

### B2 ResourceManager — PARTIAL

Integrated real lifecycle wiring:

- pre-load estimate resolution;
- reserve before backend load;
- commit on success;
- rollback on failed load;
- reload enforces old+replacement peak overlap and preserves current runtime on rejection;
- unload/shutdown release accounting after engine close;
- admission metadata appears in runtime status.

Remaining B2c:

- supported entrypoints need explicit memory-budget/headroom configuration and a ResourceManager instance;
- measured post-load reconciliation/product exposure.

### B3 worker/reclamation — PARTIAL

Integrated concrete JSON-line subprocess transport with bounded start/health/generate/drain/cancel/stop and request correlation.

Remaining B3c:

- route appropriate engines through worker ownership where isolation is justified;
- bind B1 snapshots to before-ready/peak/after-stop evidence;
- validate reclamation on representative hardware.

### C2 capabilities — PARTIAL

`list_models()` and admin registry now expose capability object + provenance while preserving legacy fields.

Remaining C2d: make canonical execution reject unsupported task/feature combinations before backend invocation.

### D2 metrics — PARTIAL

Integrated:

- OpenAI usage token counters as explicit token evidence;
- llama.cpp timing fields when present;
- prompt/decode durations and true token throughput where sourced;
- merge with chunk evidence without aliasing;
- TTFT remains unavailable from completed responses.

Remaining D2c: live request/status/evidence attachment plus streaming first-output measurement and wider backend coverage.

### D3 runtime identity — PARTIAL

Integrated immutable privacy-safe residency identity snapshot that can be captured once and reused by API/evaluation evidence.

Remaining D3d: lifecycle capture policy and public evidence exposure.

### D4 evaluation — PARTIAL

Integrated backend-neutral executor/runner over canonical requests:

- deterministic sample execution;
- objective scoring;
- per-sample failure isolation;
- test-set identity validation;
- runtime fingerprint propagation when supplied.

Remaining D4d/D5: bind to resident runtimes, persist runs/reports, history/regression and compatible-fingerprint comparisons.

### E3a Models & Runtimes — PARTIAL

Dedicated source-backed module combines resident API, runtime status and admin catalog. It presents configured identity, residency, default route, backend, state, active requests and capabilities where available. Missing admin/resource/fingerprint sources remain explicit.

## Immediate parallel wave 5

### B2c — Resource policy configuration and product exposure
Status: `READY`
Dependencies: B1/B2
Ownership: server configuration + resource state API

- optional configured memory limit/headroom in supported entrypoints;
- construct/pass ResourceManager when policy is configured;
- expose budget, committed/reserved accounting and admission decisions;
- unconfigured policy remains explicit `unknown`/disabled;
- measured reconciliation stays distinct from estimates.

### B3c — Reclamation evidence harness
Status: `READY`
Dependencies: B1 + B3 transport
Ownership: worker/evidence lifecycle

- capture before-start/after-ready/peak/after-stop snapshots;
- calculate evidence deltas without automatically converting them to PASS;
- retain raw source/provenance;
- hardware acceptance remains separate.

### B4 — Zero-resident semantics
Status: `READY` for state/API work
Dependencies: lifecycle vocabulary; automatic cold-load later depends B2/B3 policy

- healthy server with no resident model;
- configured/default model identity separate from residency;
- last runtime can unload;
- APIs/UI represent cold/unavailable truthfully.

### B5a — Scheduler foundation
Status: `READY` for contracts/deterministic queue tests
Dependencies: canonical requests + B2; worker integration improves cancellation later

- bounded queue;
- queue/admit/start lifecycle;
- deadlines and cancellation tokens;
- explicit overload/timeout outcomes;
- backend-native batching remains backend-owned.

### C2d + C3 — Capability enforcement and first-class transcription
Status: `READY`
Dependencies: public C2 descriptor + canonical policy entrypoints

Parallel substreams:

- C2d descriptor lookup/enforcement before backend invocation;
- C3 request/result/API contract for `/v1/audio/transcriptions`;
- ASR adapter boundary remains distinct from audio-language chat;
- media lifecycle remains local and bounded.

### D2c + D3d — Live evidence API
Status: `READY`
Dependencies: D2/D3 producer contracts

- canonical per-request metrics object where evidence exists;
- explicit unavailable fields otherwise;
- attach immutable runtime identity snapshot at controlled readiness point;
- expose public evidence without prompts/output/private paths.

### D4d — Evaluation service
Status: `READY`
Dependencies: D4 runner; evidence-grade comparison needs D3 identity

- resident-runtime executor adapter;
- built-in test-set discovery;
- sample size/seed/model selection;
- run lifecycle/status;
- persist manifest + report locally;
- run without fingerprint may be exploratory but not evidence-grade comparison.

### E4b + E6a — Evidence and Evaluation UI
Status: `READY` in source-dependent slices

- Overview/System resource/evidence cards from B2c/D2c/D3d;
- Benchmark setup for built-in dataset, model, sample size and seed;
- run progress/result summary from D4d;
- no synthetic scores or performance fields.

## Dependency release points

| Completion | Unlocks |
| --- | --- |
| B2c | authoritative resource budget/pressure UX; policy-aware scheduler/eviction |
| B3c + hardware evidence | credible reclaimability and stronger B4/B6 claims |
| B4 | true cold-state/load-on-demand product behavior |
| B5 | cancellation/deadline UI and later B6 lease-safe eviction |
| C2d | capability-driven Playground/Endpoints and safe C3 routing |
| C3 | ASR metrics/evaluation/UI |
| D2c + D3d | evidence-grade live cards and matched run identity |
| D4d | real Evaluation UI execution; D5 history/regression |

## Later work

- **B6 pin/LRU/TTL** after B2/B3/B4/B5 semantics are stable.
- **D5 history/regression** after D4d persistence and runtime identity compatibility checks.
- **E5 Playground** capability-driven text/vision/audio controls after C2d/C3.
- **H1-H4 hardening** accessibility, responsive/visual regression, hardware matrix, memory evidence and documentation promotion.

## Evidence boundary

Automated tests prove contract and deterministic workflow behavior, not real unified-memory reclamation, unload recovery, thermal behavior, streaming TTFT or device-specific token throughput. Representative hardware evidence remains a release gate.

## Active concurrency plan

Run B2c, B3c, B4 state semantics, B5a, C2d/C3, D2c/D3d, D4d and E4b/E6a concurrently only behind narrow ownership boundaries. Producer APIs/evidence land before dependent UI. Finish every wave with a cumulative living-plan validation PR.

## Plan maintenance

After every coherent merge wave update this roadmap, [`current-state.md`](current-state.md) and affected progress trackers. Target specifications change only when intended behavior changes.

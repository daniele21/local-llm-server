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
| M1 trustworthy foundation | PARTIAL | retire legacy direct-app/parser boundary + final UX evidence |
| M2 resource-aware runtime | PARTIAL | worker adoption, pin/LRU/TTL and representative reclamation evidence |
| M3 multi-task control plane | PARTIAL | capability-driven UX + wider specialist runtime evidence |
| M4 evidence-grade observability | PARTIAL | wider backend metric/identity coverage + representative device evidence |
| M5 control-plane UX | PARTIAL | Playground/Endpoints/Diagnostics migration + accessibility/visual regression |
| M6 evaluation harness | PARTIAL | custom-dataset UI + richer workload/cold-warm orchestration |
| M7 product-grade candidate | BLOCKED | hardware matrix, hardening and integration-to-main release gate |

## Integrated waves

### Foundation through Wave 4

Integrated:

- deterministic CI matrix and correctness gate;
- canonical request/media policy on supported product entrypoints;
- ResourceManager contracts and load/reload/unload accounting;
- worker protocol + bounded subprocess transport;
- capability descriptors/catalog exposure;
- truthful metric adapters and runtime identity contracts;
- deterministic built-in evaluation runner;
- source-backed control-plane shell and Models & Runtimes view.

### Wave 5 — product exposure

Integrated:

- resource-policy-aware product bootstrap and `/api/v1/resources`;
- modular `/api/v1/evidence` and evaluation run/test-set APIs;
- first-class `/v1/audio/transcriptions` with explicit ASR capability;
- zero-resident/cold product state;
- verified runtime identity auto-capture;
- source-backed Overview with resources, metrics and fingerprint evidence;
- real Benchmark & Evaluation setup/run/results UI.

### Wave 6 — observability, scheduling and regression loop

Integrated:

- persisted evaluation history and compatibility-aware comparison API/UI;
- streaming first-content TTFT producer and product wiring;
- async FIFO scheduler plus request-path bounded admission;
- queue timeout/overflow semantics and scheduler evidence UI;
- bounded non-streaming completion metrics with explicit usage/timing mapping.

### Wave 7 — custom evaluation datasets

Integrated backend boundary:

- content-sensitive test-set identity;
- validated `schema_version=1` JSON parser and atomic local custom test-set store;
- no Python/template/plugin execution from uploaded datasets;
- deterministic chat and structured-generation samples with allowlisted objective expectations;
- version coexistence and explicit version disambiguation;
- admin-only import endpoint and catalog integration;
- custom sets execute through the same resident evaluation service.

Remaining Wave 7 UI boundary: upload/catalog/version selection in the Benchmark & Evaluation screen.

## Immediate parallel wave 8

### E6b — Custom test-set UI
Status: `READY`
Dependencies: integrated custom dataset import/catalog API
Ownership: evaluation control-plane UI only

- JSON file picker and explicit import action;
- clear built-in vs custom source label;
- refresh catalog after successful import;
- preserve `id + version + identity` semantics;
- include `test_set_version` in run request;
- duplicate conflict shown explicitly; no silent replace;
- no client-side execution/scoring interpretation.

### E5b — Capability-driven Playground and Endpoints
Status: `READY`
Dependencies: public capability descriptors + pre-backend enforcement + transcription API
Ownership: frontend composition; runtime truth remains server-owned

- derive task availability from public capability metadata;
- text/image/audio controls only when supported;
- transcription presented as its own task rather than generic chat;
- endpoint compatibility view per resident/configured runtime;
- explicit unsupported/unavailable states;
- preserve legacy working chat path during migration.

### B6a — Residency policy metadata and pinning
Status: `READY`
Dependencies: ResourceManager + zero-resident + scheduler leases
Ownership: runtime residency policy

- explicit pinned/evictable state;
- pinned runtimes excluded from automatic eviction;
- state visible through admin/runtime evidence;
- no automatic memory-reclamation claim.

### B6b — Lease-safe LRU/TTL eviction
Status: `BLOCKED` on B6a and evidence review
Dependencies: B6a + scheduler/runtime leases + resource pressure semantics

- deterministic candidate ranking;
- never evict an active leased runtime;
- observable eviction reason;
- pressure-triggered policy remains bounded;
- hardware evidence required before production-grade claim.

### B3d/H3 — Worker integration and reclamation evidence
Status: `READY` in controlled backend slices
Dependencies: existing worker transport + reclamation recorder
Ownership: backend process boundary + hardware evidence

- route selected dynamic runtimes through worker ownership where isolation materially improves cleanup/failure containment;
- capture before-start/after-ready/peak/after-stop resource snapshots;
- repeat load/infer/unload cycles;
- preserve `inconclusive` when observations cannot support a reclamation claim;
- record OS/device/backend/artifact/config identity with every evidence run.

### D2e/D3e — Backend evidence coverage
Status: `READY`
Dependencies: canonical metrics/identity producers

- MLX text/VLM/ASR adapters map only explicit evidence;
- unavailable metrics remain unavailable;
- broaden verified artifact/backend version capture;
- add cancellation/termination evidence where backend semantics support it.

### H1/H2/H4 — Product hardening
Status: `READY` in parallel with backend evidence

- keyboard/focus/status/contrast/200%-zoom acceptance;
- responsive and visual regression states;
- privacy-policy/settings presentation;
- representative runtime screenshots only from real states;
- release documentation and examples synchronized with supported entrypoints.

## Dependency release points

| Completion | Unlocks |
| --- | --- |
| E6b | complete first custom-dataset evaluation workflow |
| E5b | task-aware user workflow and truthful endpoint discovery |
| B6a | safe candidate set for automatic residency policy |
| B6b + H3 | credible automatic eviction under real pressure |
| B3d + hardware evidence | stronger unload/reclamation and failure-isolation claims |
| D2e/D3e | broader evidence-grade cross-runtime evaluation |
| H1/H2/H4 | release-candidate UX/documentation gate |

## Integration-to-main gate

The long-lived `docs/control-plane-positioning-ux-plan` integration branch should not be promoted to `main` solely because feature PRs are merged. Consolidation requires:

1. cumulative CI green on the integration head;
2. living plan/current-state/workstream trackers synchronized;
3. no known P0/P1 regression in supported product entrypoints;
4. release-facing README examples aligned with real supported entrypoints;
5. explicit list of evidence-pending claims that remain experimental;
6. representative smoke test for text + vision path already supported and first-class transcription where a compatible runtime is available;
7. review of migration/deprecation boundary for direct legacy `server:app` use.

Hardware-dependent claims may remain experimental after merge, but must be labelled as such rather than treated as DONE.

## Active concurrency plan

Run E6b, E5b, B6a, controlled B3d/H3 backend work, D2e/D3e and H1/H2/H4 concurrently behind narrow owners. Do not start automatic LRU/TTL eviction until pin/lease/resource semantics are explicit. Finish each coherent wave with a cumulative state/roadmap synchronization change.

## Evidence boundary

Automated tests prove deterministic contract and workflow behavior, not real unified-memory reclamation, unload recovery, thermal behavior, device-specific throughput or safe auto-eviction under pressure. Representative hardware evidence remains a release-quality gate for those claims.

## Plan maintenance

After every coherent merge wave update this roadmap, [`current-state.md`](current-state.md) and affected workstream trackers. Target specifications change only when intended behavior changes.

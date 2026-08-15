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
| M2 resource-aware runtime | PARTIAL | broader worker adoption + real pressure/reclamation evidence |
| M3 multi-task control plane | PARTIAL | broader specialist runtime evidence |
| M4 evidence-grade observability | PARTIAL | wider backend metric/identity coverage + representative device evidence |
| M5 control-plane UX | PARTIAL | accessibility, visual regression and legacy-internal cleanup |
| M6 evaluation harness | PARTIAL | richer workload families + cold/warm orchestration |
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
- source-backed control-plane shell and Models & Runtimes foundation.

### Wave 5 — product exposure

Integrated:

- resource-policy-aware product bootstrap and `/api/v1/resources`;
- modular `/api/v1/evidence` and evaluation run/test-set APIs;
- first-class `/v1/audio/transcriptions` with explicit ASR capability;
- zero-resident/cold product state;
- verified runtime identity auto-capture;
- source-backed Overview;
- real Benchmark & Evaluation setup/run/results UI.

### Wave 6 — observability, scheduling and regression loop

Integrated:

- persisted evaluation history and compatibility-aware comparison API/UI;
- streaming first-content TTFT producer and product wiring;
- async FIFO scheduler plus request-path bounded admission;
- queue timeout/overflow semantics and scheduler evidence UI;
- bounded non-streaming completion metrics with explicit usage/timing mapping.

### Wave 7 — custom evaluation datasets

Integrated:

- content-sensitive test-set identity;
- validated `schema_version=1` JSON parser and atomic local custom test-set store;
- no Python/template/plugin execution from uploaded datasets;
- deterministic chat and structured-generation samples with allowlisted objective expectations;
- version coexistence and explicit version disambiguation;
- admin-only import endpoint and catalog integration;
- custom sets execute through the same resident evaluation service.

### Wave 8 — evaluation UX, capability UX and residency policy

Integrated:

- custom JSON test-set upload, source labeling, catalog refresh and explicit version propagation in Evaluation;
- capability-driven Endpoints and Playground derived from public server-owned descriptors;
- first-class transcription mini-playground over the real multipart endpoint;
- conservative capability-source fallback that restores legacy controls instead of leaving stale disabled state;
- explicit runtime pin/unpin policy and `/api/v1/residency` evidence;
- deterministic LRU/TTL candidate ranking with current resident default protected by default;
- explicit eviction preview/execution APIs with no automatic pressure trigger and no reclamation claim;
- repeated reclamation lifecycle experiment harness over before/ready/peak/after-stop checkpoints;
- Models & Runtimes now consumes resource, runtime-identity and residency-policy sources and exposes pin/unpin controls.

### Wave 9 — Settings and Diagnostics source completion

Integrated:

- bounded read-only `/api/v1/policies` evidence source;
- effective remote-media/remote-code flags per resident runtime without paths/content/secrets;
- Settings consumes request privacy, resource, residency and scheduler policy sources;
- System / Diagnostics consumes runtime identity, canonical metrics, scheduler and resource evidence while preserving existing live logs;
- shell fallbacks no longer contain obsolete milestone blocker text.

## Immediate parallel wave 10 — evidence and hardening

### B3e — Worker adoption and real reclamation evidence
Status: `READY`
Dependencies: worker transport + repeated reclamation harness
Ownership: backend process boundary + evidence

- select runtimes where process ownership materially improves cleanup/failure isolation;
- bind lifecycle callbacks to real start/ready/infer/stop operations;
- run repeated cycles on representative macOS/Linux hardware;
- capture OS/device/artifact/backend/config identity with raw evidence;
- preserve `inconclusive` when observations cannot support a claim.

### B6c — Pressure-policy validation
Status: `READY`, automatic trigger remains disabled
Dependencies: B6 pinning + LRU/TTL selection + scheduler leases + ResourceManager pressure state
Ownership: residency policy, not memory-proof semantics

- define deterministic pressure transition and candidate-selection rules;
- never target active or pinned runtimes;
- keep resident-default protection explicit;
- record eviction reason and failed/skipped attempts;
- enable automatic pressure-triggered behavior only after representative evidence review.

### D2e/D3e — Backend evidence coverage
Status: `READY`
Dependencies: canonical metrics/identity contracts

- extend explicit metric mappings across MLX text/VLM/ASR;
- broaden artifact/backend version capture;
- include cancellation/termination evidence where backend semantics support it;
- unavailable values remain unavailable.

### A2 final — Canonical route migration
Status: `READY with regression risk`
Dependencies: canonical middleware/task policy already integrated

- retire duplicate historical request parsing where the canonical prepared request can own behavior;
- formalize/deprecate direct `server:app` compatibility path;
- preserve OpenAI/client compatibility and pre-backend fail-closed policy;
- keep route migration behind deterministic compatibility tests.

### H1/H2 — UX hardening
Status: `READY`

- keyboard-only navigation and visible focus;
- semantic labels for icon-only actions;
- status not conveyed only by color;
- contrast checks in supported light/dark modes;
- 200% zoom and representative phone/tablet/desktop widths;
- stable loading/empty/unavailable/warning/error/success fixture states;
- visual-regression screenshots from deterministic source-backed fixtures.

### H3/H4 — Representative evidence and release documentation
Status: `BLOCKED` only by access to representative runtime/hardware evidence

- execute text/vision/transcription smoke/evidence procedures where compatible runtimes are available;
- collect real screenshots only from implemented states;
- synchronize README/API examples with supported product entrypoints;
- label hardware-dependent or backend-incomplete claims `experimental`/`evidence pending`;
- produce a release evidence matrix tied to exact runtime fingerprints.

## Dependency release points

| Completion | Unlocks |
| --- | --- |
| B3e representative cycles | stronger unload/reclamation and failure-isolation claims |
| B6c + B3e evidence | candidate for bounded automatic eviction under pressure |
| D2e/D3e | broader evidence-grade cross-runtime evaluation |
| A2 final | cleaner single request-contract architecture |
| H1/H2 | primary UX screens eligible for DONE review |
| H3/H4 | release-candidate evidence/documentation gate |

## Integration-to-main gate

The long-lived `docs/control-plane-positioning-ux-plan` integration branch should not be promoted to `main` solely because feature PRs are merged. Consolidation requires:

1. cumulative CI green on the integration head;
2. living plan/current-state/workstream trackers synchronized;
3. no known P0/P1 regression in supported product entrypoints;
4. release-facing README examples aligned with real supported entrypoints;
5. explicit list of evidence-pending claims that remain experimental;
6. representative smoke/evidence coverage for implemented task families where compatible hardware/runtime is available;
7. review of migration/deprecation boundary for direct legacy `server:app` use;
8. primary UX accessibility/responsive gate reviewed.

Hardware-dependent claims may remain experimental after a code merge, but they must be labelled as such rather than treated as DONE.

## Active concurrency plan

Run B3e, B6c design/tests, D2e/D3e, A2 migration preparation and H1/H2 in parallel behind narrow owners. H3/H4 hardware evidence proceeds whenever representative devices/runtimes are available. Do not enable pressure-triggered automatic eviction merely because deterministic candidate selection passes CI.

## Evidence boundary

Automated tests prove deterministic contract and workflow behavior, not real unified-memory reclamation, unload recovery, thermal behavior, device-specific throughput or safe auto-eviction under pressure. Representative hardware evidence remains a release-quality gate for those claims.

## Plan maintenance

After every coherent merge wave update this roadmap, [`current-state.md`](current-state.md) and affected workstream trackers. Target specifications change only when intended behavior changes.

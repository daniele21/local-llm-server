# Control-plane and UX/UI roadmap

Status: active
Document type: roadmap
Owner: repository
Canonical scope: roadmap.repository
Read when: selecting the next capability milestone, understanding dependencies or parallelizing implementation
Last reviewed: 2026-08-15

This roadmap tracks capability milestones, hard dependencies and parallel delivery lanes for the Local LLM Server repositioning and UX/UI evolution. It does not own branch narratives or detailed current implementation truth; those belong in [`current-state.md`](current-state.md).

## 1. Delivery objective

Move from the current multi-backend local model server toward a **resource-aware, observable local AI control plane and evaluation harness** with a coherent product experience for text, vision and audio.

The active program has six parallel lanes:

| Lane | Scope | Primary owner boundary |
| --- | --- | --- |
| A | Reliability, security and repository foundations | CI / core platform |
| B | Runtime lifecycle, workers and resources | runtime |
| C | Canonical tasks, capabilities and APIs | core/API |
| D | Observability, artifact identity and evaluation | observability/harness |
| E | UX/UI and design system | web product surface |
| F | Brand, positioning and documentation | product/docs |

## 2. Status legend

- `PENDING`: not started.
- `READY`: dependencies complete; safe to start.
- `IN_PROGRESS`: active work.
- `PARTIAL`: useful implementation exists; acceptance incomplete.
- `BLOCKED`: explicit dependency/evidence prevents progress.
- `EVIDENCE`: code integrated; representative hardware/product evidence remains.
- `DONE`: implementation, automated gates and required evidence are complete.
- `DEFERRED`: intentionally outside current program.

## 3. Program milestone summary

| Milestone | Status | Hard completion outcome |
| --- | --- | --- |
| M0 — Planning and documentation governance | DONE | Canonical target/state/roadmap/UX/brand/completion docs exist and are maintained |
| M1 — Trustworthy foundation | READY | Blocking CI, privacy defaults, consumer decoupling and stable core contracts |
| M2 — Resource-aware runtime | PENDING | ResourceManager, verifiable unload, zero-resident state and bounded lifecycle |
| M3 — Multi-task control plane | PENDING | Task/capability model, first-class ASR and scheduler/admission |
| M4 — Evidence-grade observability | PENDING | Precise metrics, artifact/runtime fingerprint and representative resource evidence |
| M5 — Redesigned control-plane UX | PENDING | Overview, Models & Runtimes, Playground/Endpoints, Diagnostics use source-backed state |
| M6 — Benchmark & Evaluation harness | PENDING | Reproducible test sets/runs/comparisons tied to exact runtime identity |
| M7 — Product-grade release candidate | PENDING | Completion policy satisfied on representative macOS/Linux hardware |

## 4. Dependency graph

```text
M0 Planning
 |
 +----------------------------+-----------------------------+
 |                            |                             |
 v                            v                             v
A1 CI gate                C1 Canonical request         E1 Design system
A2 privacy hardening      C2 Capability model          F1 positioning copy
A3 consumer decoupling          |                             |
 |                              |                             |
 +------------+-----------------+-----------------------------+
              |
              v
         B1 Resource observation ---- D1 metric vocabulary
              |                         |
              v                         v
         B2 ResourceManager        D2 metric normalization
              |
      +-------+-------+
      |               |
      v               v
 B3 worker/reclaim   B4 zero-resident
      |               |
      +-------+-------+
              v
         B5 scheduler/admission
              |
              v
         B6 LRU/TTL eviction

C1 + C2 ------------------> C3 ASR task/API
C1 + C2 + B5 -------------> C4 task-aware execution routing

D2 + artifact integrity ---> D3 runtime fingerprint
D2 + D3 + B1 -------------> D4 benchmark engine v1

E1 + source contracts -----> E2 shell/navigation
B1/B2 + E1 ----------------> E3 Models & Runtimes UX
D2 + B1 + E1 -------------> E4 Overview/Diagnostics UX
C3 + E1 -------------------> E5 audio/endpoint UX
D4 + E1 -------------------> E6 Benchmark & Evaluation UX

E2..E6 + hardware evidence -> M7 release candidate
```

## 5. Parallel Batch 1 — Foundation

**Can start immediately in parallel.** These tasks deliberately touch different ownership boundaries.

### Lane A — Reliability/security

#### A1 — Make CI truthful
Status: `READY`
Dependencies: none

Deliverables:

- remove `|| true` from pytest CI command;
- run lint against `src/` and `tests/` as appropriate;
- ensure deterministic unit suite passes in Python 3.10/3.11/3.12;
- explicitly separate mocked CI from real-backend/hardware validation;
- fail merge checks on actual regression.

Exit gate:

- intentionally failing test makes CI red;
- current green suite passes without suppression.

#### A2 — Privacy/security defaults
Status: `READY`
Dependencies: none

Deliverables:

- `trust_remote_code=false` default;
- opt-in registry/config flag for models that require remote code;
- remote HTTP(S) media disabled by default in local inference messages;
- deterministic cleanup of generated temporary audio;
- tests proving defaults fail closed.

Exit gate:

- local image/audio helpers leave no avoidable temp artifact after owned lifecycle;
- remote behavior requires explicit opt-in.

#### A3 — Remove ClosedRoom-specific registry coupling
Status: `READY`
Dependencies: none

Deliverables:

- remove direct Application Support/ClosedRoom read from core registry;
- add explicit registry/provider/config integration point if needed;
- update ClosedRoom integration guidance separately, without core importing consumer state.

Exit gate:

- core package behavior no longer names or requires ClosedRoom;
- user/built-in registry merge behavior remains covered.

### Lane C — Contracts

#### C1 — Canonical task/request vocabulary
Status: `READY`
Dependencies: none

Deliverables:

- `TaskType`, canonical request/result and termination reason contracts;
- compatibility adapter from current chat request;
- typed errors suitable for API/UI.

Exit gate:

- current text request tests pass through compatibility translation;
- new core types have no FastAPI/backend dependency.

#### C2 — Capability descriptor
Status: `PENDING`
Dependencies: C1 vocabulary

Can begin in parallel with later C1 implementation once task vocabulary is frozen in a small contract PR.

### Lane E — Design foundation

#### E1 — Design-system tokens and primitives
Status: `READY`
Dependencies: none

Deliverables:

- implement brand token source for graphite/slate/electric-blue/teal/violet/light-neutral palette;
- typography and spacing/radius scale;
- status semantics (`ready`, `resident`, `cold`, `loading`, `warning`, `error`, `unavailable`) not expressed by color alone;
- reusable card, badge, button, field, metric, empty/unavailable and table primitives;
- dark-first control-plane shell with a supported light variant where appropriate.

Important constraint:

- design foundation may use static component fixtures for visual tests, but product screens must not present invented runtime values as live data.

### Lane F — Product/documentation

#### F1 — Positioning and information-language contract
Status: `READY`
Dependencies: target specification exists

Deliverables:

- README/homepage positioning aligned to “resource-aware, observable local AI control plane”;
- clear “orchestrates runtimes; does not replace them” statement;
- local-first/not-local-only language;
- terminology alignment across README, UI and API docs;
- product-language rules from [`brand-guidelines.md`](brand-guidelines.md).

F1 can progress independently from runtime implementation as long as it distinguishes current from target capabilities.

## 6. Parallel Batch 2 — Resource and capability foundation

Start after the narrow foundation contracts land. Several tasks remain parallel.

### Lane B

#### B1 — Resource observation contract
Status: `PENDING`
Dependencies: A1 recommended, not technically hard

Deliverables:

- system/hardware resource snapshot;
- per-runtime resource profile;
- estimate vs observation distinction;
- configured budget/headroom model;
- safe unavailable behavior.

#### B2 — ResourceManager admission
Status: `PENDING`
Dependencies: B1

Deliverables:

- load-time reservation;
- budget check;
- pressure classification;
- explicit resource-exhausted decision;
- reconciliation from estimate to observation.

#### B3 — Worker ownership and memory reclamation
Status: `PENDING`
Dependencies: lifecycle contract; B1 for measurement/evidence

Implementation may start in parallel with B2 after resource observation types are stable.

Deliverables:

- worker protocol;
- isolated text runtime path;
- bounded startup/health/drain/terminate;
- no orphan processes;
- repeated unload evidence.

#### B4 — Zero-resident runtime manager
Status: `PENDING`
Dependencies: lifecycle semantics, preferably B2 before load-on-demand policy

Deliverables:

- server healthy with zero resident models;
- last model can unload;
- configured/default model identity survives cold state;
- registry/residency API semantics separated.

B4 state/API work may run in parallel with B3; automatic cold-load should wait for B2/B3.

### Lane C

#### C2 — Capability descriptor
Status: `PENDING`
Dependencies: C1

Deliverables:

- tasks/input/output/features schema;
- registry migration/validation;
- pre-backend capability rejection;
- client-visible capability metadata.

#### C3 — First-class transcription task/API
Status: `PENDING`
Dependencies: C1, C2

Deliverables:

- `/v1/audio/transcriptions` compatibility surface;
- ASR adapter/worker boundary;
- audio-language chat remains separate;
- efficient local media transfer and cleanup.

C3 can run in parallel with B3/B4 because initial residency may be explicit/manual.

### Lane D

#### D1 — Precise metric vocabulary
Status: `READY`
Dependencies: none; coordinate with C1 request lifecycle names

Deliverables:

- canonical metric schema;
- correct token/chunk naming;
- unavailable-source semantics;
- privacy-safe event fields.

D1 should finish before UI metric labels stabilize.

## 7. Parallel Batch 3 — Scheduling, observability and core UX

### Lane B

#### B5 — Scheduler, deadlines and cancellation
Status: `PENDING`
Dependencies: C1, B2, stable lifecycle/worker boundary

Deliverables:

- bounded request queue;
- queue state and wait time;
- deadline expiry;
- cancellation before/during execution;
- client disconnect propagation where supported;
- explicit overload responses;
- backend-native batching remains backend-owned.

#### B6 — Residency policy: pin/LRU/TTL
Status: `PENDING`
Dependencies: B2, B3, B4, B5 lease semantics

Deliverables:

- pin/unpin;
- monotonic idle TTL;
- LRU candidate ordering;
- eviction reason;
- no active-runtime eviction;
- safe no-candidate/resource-exhausted behavior.

### Lane D

#### D2 — Metric normalization adapters
Status: `PENDING`
Dependencies: D1; backend-specific implementation can be parallelized by adapter

Subtasks that can run in parallel:

- D2a llama/llama-server metrics;
- D2b MLX text metrics;
- D2c MLX-VLM metrics;
- D2d ASR metrics after C3.

Exit gate:

- UI/client consumes one schema;
- unsupported metrics remain unavailable.

#### D3 — Artifact integrity and runtime fingerprint
Status: `PENDING`
Dependencies: artifact schema work can start early; final fingerprint depends on D1/D2 and hardware-profile contract

Subtasks that can run in parallel:

- SHA/revision metadata and verification;
- backend version/config digest;
- hardware profile;
- fingerprint assembly and stable serialization.

### Lane E

#### E2 — New application shell/navigation
Status: `PENDING`
Dependencies: E1

Deliverables:

- sidebar navigation;
- Overview;
- Models & Runtimes;
- Endpoints;
- Playground;
- Benchmark & Evaluation placeholder route;
- System/Settings;
- consistent loading/unavailable/error patterns.

#### E3 — Models & Runtimes screen
Status: `PENDING`
Dependencies: E1; can begin with existing runtime data, but authoritative memory-budget controls require B1/B2

Implementation split:

- E3a registry/residency table and lifecycle state — can start early;
- E3b capability details — waits for C2;
- E3c memory budget/pressure — waits for B1/B2;
- E3d pin/auto-evict controls — waits for B6;
- E3e runtime fingerprint — waits for D3.

This decomposition is intentionally designed for parallel delivery rather than blocking the entire screen on the final resource manager.

#### E4 — Overview and Diagnostics
Status: `PENDING`
Dependencies: E1; each panel has its own data dependency

Parallel subcomponents:

- server/runtime health — current source can be adapted immediately;
- resident model summary — existing source;
- activity/request lifecycle — B5/D1;
- resource pressure — B1/B2;
- truthful latency/throughput — D2;
- fingerprint/evidence links — D3.

## 8. Parallel Batch 4 — Evaluation harness and complete product surfaces

### Lane D

#### D4 — Benchmark engine v1
Status: `PENDING`
Dependencies: D2, D3; quality datasets can be prepared earlier

Deliverables:

- versioned benchmark/test-set definition;
- sample-size selection;
- deterministic run manifest;
- cold/warm distinction;
- latency/TTFT/throughput/memory/success metrics;
- task quality evaluator interface;
- result persistence with execution identity;
- comparison rules that reject incompatible run identity.

Parallel preparation before D2/D3:

- dataset/test-set interface;
- general-purpose starter dataset design;
- scorer contracts;
- report schema draft.

#### D5 — Benchmark history/regression
Status: `PENDING`
Dependencies: D4

Deliverables:

- immutable run history;
- explicit baseline promotion;
- matched-identity regression checks;
- no comparison across incompatible runtime fingerprints.

### Lane E

#### E5 — Endpoints/Playground multimodal UX
Status: `PENDING`
Dependencies: C2; ASR portion depends C3

Deliverables:

- task-aware model selection;
- capability-driven controls;
- text/image/audio inputs only when supported;
- structured-output settings;
- streaming/cancel state;
- exact runtime/result metadata access;
- no fake “supported” capability.

#### E6 — Benchmark & Evaluation screen
Status: `PENDING`
Dependencies: E1, D4; visual shell can be built earlier against fixture contracts

Deliverables:

- model/backend/test-set/sample-size/task selection;
- progress/status;
- TTFT/tokens/sec/latency/success/memory/cache/load metrics;
- model/backend comparison table;
- run manifest/fingerprint;
- history/regression when D5 lands;
- explicit confidence/unavailable states rather than automated marketing conclusions.

## 9. Final hardening batch

### H1 — Accessibility and responsive web validation
Status: `PENDING`
Dependencies: primary surfaces implemented

Requirements:

- keyboard navigation;
- visible focus;
- semantic labels;
- status not color-only;
- WCAG AA contrast where applicable;
- 200% zoom/readability;
- narrow laptop/tablet width behavior;
- reduced-motion compatible transitions.

### H2 — Cross-platform runtime matrix
Status: `PENDING`
Dependencies: B3, D2

Representative matrix:

- Apple Silicon macOS: MLX text + MLX-VLM + GGUF path;
- Linux CPU: GGUF text;
- Linux NVIDIA where supported/configured: GGUF/GPU path;
- one real audio transcription path;
- concurrent multi-runtime scenario where resource policy allows it.

### H3 — Memory lifecycle evidence
Status: `PENDING`
Dependencies: B1-B4

Must record:

- cold baseline;
- load footprint;
- repeated inference peak;
- unload/post-stop footprint;
- repeated load/unload cycle;
- model switch;
- cancellation and failure cleanup;
- pressure/eviction behavior after B6.

### H4 — Documentation and positioning promotion
Status: `PENDING`
Dependencies: target features actually integrated

Deliverables:

- README reflects only shipped capability;
- screenshots updated from real implementation;
- architecture diagrams match code;
- examples cover text, vision and transcription;
- benchmark evidence clearly identifies hardware/artifact/runtime;
- homepage/portfolio wording distinguishes measured facts from roadmap.

## 10. Critical path

The shortest technical path to the differentiated product is:

```text
A1 -> B1 -> B2 -> B3 -> B4 -> B5 -> B6
              \                    \
               -> D1 -> D2 -> D3 -> D4

C1 -> C2 -> C3

E1 -> E2 -> E3/E4 -> E5/E6
```

The **longest risk-bearing chain** is resource observation -> admission -> reclaimable worker lifecycle -> scheduler/residency policy -> hardware evidence. UX and evaluation work should run in parallel around that chain rather than wait for it wholesale.

## 11. Recommended concurrency plan

If multiple implementation agents/developers are available, use these simultaneous assignments.

### Batch 1 — up to 6 parallel workers

1. A1 CI reliability.
2. A2 security/privacy hardening.
3. A3 consumer decoupling.
4. C1 canonical request/task contract.
5. E1 design system.
6. F1 README/positioning language preparation.

### Batch 2 — up to 5 parallel workers

After C1 and basic CI are stable:

1. B1 resource observation.
2. C2 capability model.
3. D1 metric vocabulary.
4. E2 shell/navigation.
5. artifact identity schema portion of D3.

### Batch 3 — up to 6 parallel workers

After B1/C2/D1 contracts stabilize:

1. B2 ResourceManager.
2. B3 worker isolation/reclamation.
3. B4 zero-resident semantics.
4. C3 transcription API/ASR adapter.
5. D2 backend metric adapters split by backend.
6. E3a/E4 source-backed UI portions not waiting for later policy.

### Batch 4 — up to 5 parallel workers

1. B5 scheduler/cancellation.
2. D3 fingerprint completion.
3. E3 resource/capability integrations.
4. E5 Playground/Endpoints.
5. D4 benchmark test-set/scorer foundation.

### Batch 5

1. B6 eviction policy.
2. D4 benchmark execution/persistence.
3. E6 benchmark UI.
4. H1 accessibility/responsive.
5. H2/H3 hardware evidence preparation/execution.

## 12. Merge-conflict minimization

Parallel tasks should avoid repeatedly editing the same monolith.

Before broad UI/runtime parallelization:

- establish core types in new narrow modules;
- avoid simultaneous large changes to `server.py` until route extraction boundaries are agreed;
- split frontend components/views before multiple UX workstreams implement separate screens;
- backend-specific metric adapters should live behind a shared interface so they can be implemented independently;
- update roadmap/current-state in the integration PR after parallel branches land, not independently with conflicting status claims.

## 13. Plan maintenance

At the end of every merged coherent slice:

1. update task status in this roadmap;
2. add/change dependencies discovered during implementation;
3. update [`current-state.md`](current-state.md) with integrated baseline and immediate next block;
4. update workstream progress files affected by the slice;
5. leave target specifications unchanged unless intended behavior changed;
6. link evidence/tests in the relevant completion record or PR rather than bloating this roadmap with commit history.

The roadmap is considered stale if merged implementation has changed any task state/dependency and this file was not updated in the same integration change.

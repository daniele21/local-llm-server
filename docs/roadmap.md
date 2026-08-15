# Control-plane and UX/UI roadmap

Status: active
Document type: roadmap
Owner: repository
Canonical scope: roadmap.repository
Read when: selecting the next capability milestone, understanding dependencies or parallelizing implementation
Last reviewed: 2026-08-15

Integrated truth belongs in [`current-state.md`](current-state.md). This file owns sequencing, dependency release points and parallel work.

## Delivery objective

Evolve Local LLM Server into a **resource-aware, observable local AI control plane and evaluation harness** while specialist runtimes retain backend execution ownership.

| Lane | Scope |
| --- | --- |
| A | reliability/security |
| B | resources/runtime/workers/scheduling |
| C | tasks/capabilities/APIs |
| D | observability/identity/evaluation |
| E | UX/UI |
| F | positioning/docs |

## Status legend

`READY` dependency-complete · `PARTIAL` useful implementation/incomplete acceptance · `BLOCKED` hard dependency · `DONE` complete · `EVIDENCE` code complete/representative evidence pending.

## Milestones

| Milestone | Status | Remaining outcome |
| --- | --- | --- |
| M0 documentation governance | DONE | keep state synchronized |
| M1 trustworthy foundation | PARTIAL | AC1b route wiring + screen evidence |
| M2 resource-aware runtime | PARTIAL | load wiring, reclamation, zero-resident, scheduler, eviction |
| M3 multi-task control plane | PARTIAL | public capabilities + ASR/task routing |
| M4 evidence-grade observability | PARTIAL | richer adapters + runtime fingerprint |
| M5 redesigned control-plane UX | PARTIAL | Models/Playground/Diagnostics/data panels |
| M6 evaluation harness | PARTIAL | built-in dataset/scorers + execution/history |
| M7 product-grade candidate | BLOCKED | hardening + representative hardware evidence |

## Completed foundations

### A1 truthful CI — DONE

Blocking deterministic pytest on Python 3.10/3.11/3.12 plus Ruff correctness gate.

### A3 consumer decoupling — DONE

Core registry no longer reads ClosedRoom-specific state; external registry layers are generic.

### F1 positioning — DONE

README/package language reflects control-plane positioning and separates current from target behavior.

### D1 metric vocabulary — DONE

Canonical lifecycle/duration/token/chunk/throughput vocabulary with unavailable semantics.

### D3a artifact identity — DONE

Path-free source/verification identity, stable key and explicit optional SHA-256.

### D4a evaluation schema — DONE

Versioned test sets, stable sample IDs, deterministic seeded selection, scorer protocol and run/report contracts.

## Active foundation work

### A2 + C1 + AC1 — PARTIAL

Integrated:

- fail-closed remote-code/media policy;
- backend-neutral request contracts;
- compatibility translator;
- tested `request_pipeline.py`.

Remaining AC1b:

- make the FastAPI route call the canonical pipeline;
- enforce remote-media policy before backend invocation;
- preserve streaming/non-streaming compatibility.

### B1 resource observation — PARTIAL

Integrated:

- source-aware resource contracts;
- budget/headroom/pressure vocabulary;
- Linux observer;
- macOS total/reclaimable-memory adapter;
- Apple unified memory is not represented as separate VRAM.

Remaining:

- runtime/API exposure;
- representative hardware evidence.

### B2 ResourceManager — PARTIAL

Integrated reservation/admission ledger:

- `ADMIT`, `REJECT`, `UNKNOWN`;
- reserved/committed accounting;
- observed-footprint reconciliation;
- rollback/release;
- no false approval when no enforceable budget exists.

Remaining B2b: connect load/reload to reservations without conflating accounting with memory reclamation.

### C2 capabilities — PARTIAL

Integrated:

- task/input/output/feature descriptor;
- conservative legacy migration;
- `supports(request)`;
- catalog projection with explicit vs legacy provenance.

Remaining C2c:

- expose capability projection from model listing/admin source;
- pre-backend capability rejection after AC1b.

### D2 metric normalization — PARTIAL

Integrated D2a:

- runtime `output_chunks` -> canonical `output_chunks`;
- `chunks_per_second` -> chunk throughput;
- misleading historical `tokens_generated/tokens_per_second` ignored.

Remaining:

- real token/TTFT/prefill/decode adapters where backend evidence exists;
- API/UI exposure.

### E1/E2/E4a UX — PARTIAL

Integrated:

- design-system foundation;
- control-plane shell and navigation;
- real Overview polling `/health`, `/status`, `/v1/models`;
- unavailable states instead of invented resource/performance values.

Remaining:

- E3a Models & Runtimes redesign;
- capability/resource/metric/fingerprint panels;
- Playground/Diagnostics modular migration;
- accessibility/visual evidence.

## Active parallel wave 3

### B2b — Runtime admission wiring
Status: `READY`
Dependencies: B1, B2
Ownership: runtime load lifecycle

Deliverables:

- derive/receive estimated load footprint;
- reserve before load;
- commit on success, rollback on failure;
- release accounting on unload;
- typed rejection before expensive load;
- preserve current reload rollback semantics;
- no claim that accounting proves memory reclamation.

### B3 — Worker/reclamation protocol
Status: `READY`
Dependencies: B1 measurement types; B2 useful but not hard for protocol
Ownership: new worker/lifecycle boundary

Deliverables:

- worker commands/states;
- bounded startup/health/drain/terminate;
- deterministic shutdown ownership;
- evidence hook for pre-load/peak/post-stop resource snapshots;
- process isolation only where needed for provable reclaimability.

### C2c — Public capability exposure
Status: `READY`
Dependencies: C2 catalog projection
Ownership: model/catalog presentation

Deliverables:

- add capability object and provenance to model-list/catalog data;
- keep backward-compatible existing fields;
- no backend invocation;
- request capability enforcement waits for AC1b.

### D3b — Execution identity contracts
Status: `READY`
Dependencies: D3a
Ownership: identity module

Deliverables:

- backend implementation/version identity;
- resolved-config canonical digest;
- hardware profile identity;
- stable runtime fingerprint composition;
- no private paths/prompts/output in identity;
- probes/costly hashes remain explicit or cached, never per-token.

### D4b — Built-in general-purpose evaluation set
Status: `READY`
Dependencies: D4a
Ownership: harness dataset/scorers

Deliverables:

- curated starter test set spanning instruction following, extraction, classification, structured output and simple reasoning;
- deterministic sample IDs/version/provenance;
- baseline deterministic scorers where objective scoring is valid;
- no LLM-as-judge requirement for the initial deterministic core;
- configurable sample selection remains D4a-owned.

### E3a — Models & Runtimes source-backed redesign
Status: `READY`
Dependencies: E2
Ownership: frontend Models module

Show only current real state:

- configured identity;
- resident/non-resident;
- default-route distinction;
- backend/runtime state/active requests;
- existing load/activate/unload actions.

Capability/resource/fingerprint sections remain unavailable until corresponding public sources land.

### AC1b — FastAPI request-path wiring
Status: `READY`
Dependencies: AC1 adapter
Ownership: exclusive broad `server.py` changes

Must:

- replace duplicate request normalization with `prepare_chat_request()`;
- enforce fail-closed remote media before backend work;
- map typed errors to bounded HTTP detail;
- retain OpenAI compatibility and current thinking/sampling behavior;
- keep this as the only wave-3 branch making broad request-route edits.

## Dependency release points

| Completion | Unlocks |
| --- | --- |
| AC1b | route-level privacy completion; C3/C4 request integration |
| B2b | resource-aware load policy; later B5/B6 |
| B3 | credible unload/reclamation evidence; stronger B4/B6 |
| C2c | E3/E5 capability UI; C3 model eligibility |
| D3b | execution-compatible benchmark identity; E3/E4 fingerprint UI |
| D4b | D4 engine can execute a real built-in dataset once D2/D3 are stable |
| E3a | screen-level accessibility/visual regression can begin |

## Later runtime work

### B4 zero-resident semantics — PENDING

Server remains healthy with zero resident runtimes; artifact/default/resident state are separate.

### B5 scheduler/deadline/cancellation — BLOCKED by B2b + stable lifecycle

Bounded queue, queue wait, deadlines, cancellation and explicit overload behavior.

### B6 pin/LRU/TTL — BLOCKED by B2b/B3/B4/B5

No active-runtime eviction; deterministic pin/TTL/LRU semantics and typed no-candidate rejection.

## Multi-task work

### C3 first-class transcription — BLOCKED by AC1b + C2c

Add ASR-specific API/contracts; audio-language chat remains a different task.

### C4 task-aware routing — BLOCKED by capability + resource/scheduler policy

No silent incompatible substitution.

## Observability/evaluation work

### D2 richer backend adapters — IN_PROGRESS

Split per backend after D2a; unsupported metrics stay unavailable.

### D3 runtime fingerprint — IN_PROGRESS

D3a artifact identity done; D3b completes backend/config/hardware identity.

### D4 benchmark engine — BLOCKED by D2 + D3, dataset can precede execution

Deterministic manifest, cold/warm identity, performance/resource/quality results and incompatible-run rejection.

### D5 history/regression — BLOCKED by D4

Immutable history and matched-fingerprint baseline comparison.

## UX completion

- E3 Models & Runtimes: current lifecycle -> capabilities -> resources -> residency -> fingerprint.
- E4 Overview/Diagnostics: health -> resources -> truthful metrics -> evidence.
- E5 Endpoints/Playground: capability-aware task controls; ASR after C3.
- E6 Benchmark & Evaluation: real runs after D4; history after D5.

## Evidence/hardening

Accessibility/responsive validation, cross-platform runtime matrix, memory lifecycle evidence and screenshot/documentation promotion remain release gates. Unit tests do not establish real unified-memory reclamation, TTFT or token throughput.

## Active concurrency plan

Run concurrently:

1. B2b runtime admission wiring.
2. B3 worker/reclamation protocol.
3. C2c public capability exposure.
4. D3b runtime fingerprint contracts.
5. D4b built-in general-purpose test set/scorers.
6. E3a Models & Runtimes redesign.
7. AC1b request-route wiring with exclusive `server.py` ownership.

Merge narrow contract branches before their consumers and run a cumulative living-plan validation PR after the wave.

## Plan maintenance

After every coherent merge wave update this roadmap, [`current-state.md`](current-state.md) and the affected progress tracker. Target specifications change only when intended behavior changes.

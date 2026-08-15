# Control-plane and UX/UI roadmap

Status: active
Document type: roadmap
Owner: repository
Canonical scope: roadmap.repository
Read when: selecting the next capability milestone, understanding dependencies or parallelizing implementation
Last reviewed: 2026-08-15

This roadmap tracks capability milestones, hard dependencies and parallel delivery lanes. Integrated truth and the immediate implementation block belong in [`current-state.md`](current-state.md).

## 1. Delivery objective

Evolve Local LLM Server into a **resource-aware, observable local AI control plane and evaluation harness** for text, vision and audio, while specialist inference engines retain tensor/backend ownership.

| Lane | Scope |
| --- | --- |
| A | reliability, security, repository foundations |
| B | runtime lifecycle, resources, workers, scheduling |
| C | canonical tasks, capabilities, APIs |
| D | observability, artifact/runtime identity, evaluation |
| E | UX/UI and design system |
| F | positioning and documentation |

## 2. Status legend

`PENDING` not started · `READY` dependency-complete · `IN_PROGRESS` active · `PARTIAL` useful implementation/incomplete acceptance · `BLOCKED` hard dependency · `EVIDENCE` code done/representative evidence missing · `DONE` complete · `DEFERRED` outside current program.

## 3. Milestone summary

| Milestone | Status | Remaining outcome |
| --- | --- | --- |
| M0 documentation governance | DONE | keep living plan synchronized |
| M1 trustworthy foundation | PARTIAL | final AC1 route wiring + screen-level E1 adoption |
| M2 resource-aware runtime | IN_PROGRESS | B1 runtime/macOS observation, B2-B6 |
| M3 multi-task control plane | IN_PROGRESS | C2 registry/API wiring, AC1 route, C3 ASR |
| M4 evidence-grade observability | IN_PROGRESS | D1/D3a foundations done; D2/D3 remain |
| M5 redesigned control-plane UX | IN_PROGRESS | E2 shell integrated; E3-E6 remain |
| M6 benchmark/evaluation harness | READY | D4a can start before final execution engine |
| M7 product-grade candidate | PENDING | hardening + representative hardware evidence |

## 4. Integrated foundation

### A1 — Truthful CI
Status: `DONE`

Blocking pytest on Python 3.10/3.11/3.12 plus Ruff correctness gate. Broader legacy style debt remains separate.

### A2 — Privacy/security defaults
Status: `PARTIAL`

Integrated: fail-closed remote code, fail-closed remote-media config/policy, explicit tokenizer trust and owned temp-WAV cleanup.

Remaining: route-level enforcement through AC1b.

### A3 — Consumer decoupling
Status: `DONE`

Core no longer reads ClosedRoom state. External YAML/JSON registry layers are generic and explicit.

### C1 — Canonical request vocabulary
Status: `PARTIAL`

Integrated: backend-neutral tasks/requests/results/errors plus compatibility translator and tested request-policy adapter.

Remaining: historical FastAPI route must execute through that adapter.

### E1 — Design system
Status: `PARTIAL`

Integrated shared tokens/primitives. Remaining screen adoption and visual/accessibility evidence.

### F1 — Positioning
Status: `DONE`

README/package language matches the control-plane direction while separating current vs target capability.

## 5. Batch 2 wave 1 — integrated results

### B1 — Resource observation
Status: `PARTIAL`

Integrated:

- measured/estimated/configured/unavailable source semantics;
- system snapshot and runtime profile contracts;
- explicit budget/headroom;
- pressure classification;
- observer protocol;
- Linux standard-library memory/RSS adapter;
- deterministic tests.

Remaining:

- B1b macOS/unified-memory observation where trustworthy;
- runtime/evidence wiring;
- representative hardware validation.

B2 contract work is now unblocked.

### C2 — Capability descriptor
Status: `PARTIAL`

Integrated:

- task/input/output/feature capability descriptor;
- conservative legacy migration;
- stable serialization;
- `supports(request)`;
- consistency validation;
- audio modality does not automatically imply transcription.

Remaining:

- C2b registry validation/migration fields;
- catalog/API exposure;
- canonical pre-backend capability rejection.

### D1 — Metric vocabulary
Status: `DONE`

Integrated exact request phases, duration fields, token/chunk distinction, throughput units, load/cache classifications and unavailable semantics. D2 adapters are unblocked.

### D3a — Artifact identity
Status: `DONE`

Integrated path-free source identity, verification state, optional explicit SHA-256, stable keys and Hugging Face source/revision metadata. Full runtime fingerprint remains D3.

### E2 — Control-plane shell/navigation
Status: `PARTIAL`

Integrated incremental shell with Overview, Models & Runtimes, Endpoints, Playground, Benchmark & Evaluation, System/Diagnostics and Settings. Existing real Chat/Models/Logs workflows remain available. Unsupported future data renders explicitly unavailable.

Remaining:

- E3/E4/E5 real screen composition;
- navigation/responsive/accessibility/visual evidence.

### AC1 — Canonical request/security adapter
Status: `PARTIAL`

Integrated `request_pipeline.py` canonicalization, media-policy enforcement, modality validation and bounded public errors.

Remaining AC1b:

- replace duplicate request parsing in `server.py`;
- apply adapter before backend execution for streaming and non-streaming paths;
- preserve OpenAI compatibility tests.

## 6. Active wave 2 — parallel work

### B2 — ResourceManager foundation
Status: `READY`
Dependencies: B1 contract available
Ownership: new resource-management module before runtime wiring

Deliverables:

- reservation ledger keyed by runtime/load attempt;
- configured budget/headroom evaluation;
- estimated requested bytes;
- typed `ADMIT`, `REJECT`, `UNKNOWN` decision;
- deterministic reserve/commit/release/rollback;
- no double reservation;
- no negative accounting;
- reconciliation hook for later measured footprint;
- resource exhaustion remains distinct from memory reclamation.

Exit gate: deterministic concurrent/race-friendly contract tests pass without requiring hardware.

### B1b — macOS resource adapter
Status: `READY`
Dependencies: B1 contract

Deliverables:

- trustworthy host total/available memory source on macOS;
- Apple unified-memory semantics documented rather than pretending a separate GPU pool exists;
- explicit unavailable fields where no stable public source exists;
- injectable command/reader boundary for deterministic tests;
- physical Apple Silicon evidence later.

### C2b — Registry/API capability wiring
Status: `READY`
Dependencies: C2 descriptor

Deliverables:

- optional explicit `tasks`, `input_modalities`, `output_modalities`, `features` registry fields;
- validation of explicit declarations;
- conservative fallback from legacy metadata;
- model/catalog API representation;
- no inference-path changes in this branch;
- migration compatibility for current registry.

### D2a — Runtime metric adapter foundation
Status: `READY`
Dependencies: D1

First slice:

- normalize current runtime timestamps/status into D1 where truth exists;
- map output chunk count to `output_chunks`, never `output_tokens`;
- keep TTFT/prefill/token throughput unavailable unless source exists;
- adapter interface permits llama.cpp/MLX/ASR-specific extensions;
- privacy-safe serialization.

Backend-specific richer slices can proceed in parallel afterward.

### E3a/E4a — Source-backed UI composition
Status: `READY`
Dependencies: E2 shell

Can split into two frontend workers after stable module boundaries:

**E3a Models & Runtimes**
- configured identity;
- resident/non-resident;
- default route;
- backend/state/active work where source exists;
- current load/activate/unload controls.

**E4a Overview/System**
- server health;
- default route;
- resident count/list;
- runtime state;
- navigation into Models/Diagnostics.

Do not show authoritative resource budget, capabilities, throughput or fingerprint until source wiring is integrated.

### D4a — Evaluation schema/test-set foundation
Status: `READY`
Dependencies: none for schema work

Deliverables:

- versioned test-set definition;
- stable sample IDs and provenance;
- task type per sample;
- sample-size selection contract;
- scorer protocol;
- run/report schema draft;
- deterministic selection/seed semantics;
- no benchmark comparison claims before D2/D3 execution identity exists.

### AC1b — FastAPI request-path wiring
Status: `READY`
Dependencies: AC1 adapter
Ownership: exclusive broad `server.py` changes

Deliverables:

- current request object -> `prepare_chat_request()`;
- canonical messages/options become route source of truth where represented;
- remote HTTP(S) media rejected before backend invocation by default;
- opt-in retains compatible behavior;
- typed request errors mapped to bounded HTTP detail;
- streaming/non-streaming compatibility remains green;
- historical `_normalize_messages` becomes redirect/helper or is retired without breaking tests.

## 7. Dependency release points from wave 2

| Completed item | Unlocks |
| --- | --- |
| B2 | resource-aware load policy, E3/E4 budget panels, later B5/B6 |
| B1b | trustworthy Apple resource presentation/evidence |
| C2b | C3 transcription, E3/E5 capability UI |
| D2a | truthful Overview/Diagnostics metrics, D3/D4 runtime evidence |
| E3a/E4a | screen-level accessibility/visual regression and deeper source panels |
| D4a | D4 execution engine once D2/D3 identity is stable |
| AC1b | single canonical request policy path and route-level privacy completion |

## 8. Next runtime wave

### B3 — Worker ownership/reclamation
Status: `PENDING`
Dependencies: B1 observation types; B2 useful for policy integration

Define worker protocol, bounded startup/health/drain/terminate, orphan prevention and repeated unload evidence. Isolation is justified by reclaimability/evidence, not architecture fashion.

### B4 — Zero-resident semantics
Status: `PENDING`
Dependencies: lifecycle state; B2 preferred before automatic cold load

Server stays healthy with zero resident runtimes; configured/default artifact identity survives cold state; registry/default/resident are separate concepts.

### B5 — Scheduler/deadlines/cancellation
Status: `PENDING`
Dependencies: AC1b, B2, stable lifecycle/worker boundary

Bounded queue, queue wait, deadline expiry, cancellation, client disconnect propagation and explicit overload response.

### B6 — Pin/LRU/TTL residency policy
Status: `PENDING`
Dependencies: B2-B5

Pin/unpin, monotonic TTL, deterministic LRU, eviction reason, no active-runtime eviction and safe no-candidate rejection.

## 9. Multi-task/API wave

### C3 — First-class transcription
Status: `BLOCKED`
Dependencies: C2b + AC1b

Add `/v1/audio/transcriptions`, ASR-specific request/result translation, efficient local media path and explicit capability checks. Audio-language chat remains distinct.

### C4 — Task-aware execution routing
Status: `PENDING`
Dependencies: C2b plus scheduler/resource policy as applicable

Route canonical task to eligible runtime/backend without hiding unsupported capability or silently substituting incompatible models.

## 10. Observability/evaluation wave

### D2 — Backend metric normalization
Status: `IN_PROGRESS`
Dependencies: D1 done

Parallel after D2a interface:

- llama.cpp/llama-server;
- MLX text;
- MLX-VLM;
- ASR after C3.

### D3 — Runtime fingerprint
Status: `IN_PROGRESS`
Dependencies: D3a done; backend/config/hardware identity remain

Compose artifact identity + backend version + resolved config digest + hardware profile into stable execution identity.

### D4 — Benchmark engine v1
Status: `PENDING`
Dependencies: D4a + D2 + D3

Deterministic run manifest, cold/warm classification, performance/resource/success metrics, quality evaluator interface, persistence and incompatible-run rejection.

### D5 — Benchmark history/regression
Status: `PENDING`
Dependencies: D4

Immutable history, explicit baseline promotion and matched-fingerprint regression checks.

## 11. UX completion wave

### E3 — Models & Runtimes
Status: `IN_PROGRESS`

- E3a current lifecycle facts — active wave 2;
- E3b capability details — C2b;
- E3c memory budget/pressure — B1/B2;
- E3d pin/eviction — B6;
- E3e runtime fingerprint — D3.

### E4 — Overview/Diagnostics
Status: `IN_PROGRESS`

- E4a health/residency — active wave 2;
- request lifecycle — B5/D1;
- resource pressure — B1/B2;
- truthful performance — D2;
- fingerprint/evidence — D3.

### E5 — Endpoints/Playground
Status: `PENDING`
Dependencies: C2b; ASR portion C3

Task-aware model selection, capability-driven inputs/controls, structured output, streaming/cancel and exact runtime/result metadata.

### E6 — Benchmark & Evaluation
Status: `PARTIAL`

Shell exists with explicit unavailable state. Real selection/progress/results wait for D4; history/regression waits D5.

## 12. Hardening/evidence

H1 accessibility/responsive · H2 cross-platform runtime matrix · H3 memory lifecycle evidence · H4 documentation/screenshots promotion all remain `PENDING` until their source surfaces are implemented.

Hardware evidence must cover Apple Silicon MLX/MLX-VLM/GGUF, Linux CPU GGUF, supported Linux GPU path, transcription and memory lifecycle where policy permits.

## 13. Critical path

```text
B1 -> B2 -> B3/B4 -> B5 -> B6
 |      |              |
 +------|--------------+-> resource-aware UX/evidence
        |
D1 -> D2 -> D3 -> D4 -> D5
       ^     ^
D3a --+-----+

C1/AC1 -> AC1b -> C2b -> C3/C4

E1 -> E2 -> E3/E4/E5 -> E6
```

Longest risk-bearing chain: **resource observation -> admission -> reclaimable lifecycle -> scheduling/residency -> hardware evidence**. Other lanes continue in parallel around it.

## 14. Active concurrency plan

Run simultaneously:

1. B2 ResourceManager contract.
2. B1b macOS observer.
3. C2b capability registry/API wiring.
4. D2a metric adapter.
5. E3a/E4a source-backed UI composition.
6. D4a test-set/scorer schema.
7. AC1b request-route wiring with exclusive `server.py` ownership.

Merge contract-first branches before consumers where possible. Validate cumulative state with a living-plan integration PR after the wave.

## 15. Merge-conflict minimization

- AC1b alone owns broad `server.py` request edits.
- B2/B1b stay in resource modules.
- C2b owns registry/capability metadata, not the request route.
- D2 adapters own observability translation, not UI rendering.
- E3/E4 frontend modules consume existing APIs and explicit unavailable states.
- D4a remains independent of runtime execution.
- status docs update on integration after coherent slices, not on every feature branch.

## 16. Plan maintenance

After every integrated coherent slice:

1. update task status/dependencies here;
2. update [`current-state.md`](current-state.md);
3. update affected workstream tracker;
4. leave target specs stable unless intended behavior changes;
5. keep evidence in PR/tests/evidence records rather than turning this roadmap into a changelog.

The roadmap is stale whenever merged reality changes a task state/dependency and this file is not updated in the same integration cycle.

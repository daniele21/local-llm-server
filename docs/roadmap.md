# Control-plane and UX/UI roadmap

Status: active
Document type: roadmap
Owner: repository
Canonical scope: roadmap.repository
Read when: selecting the next capability milestone, understanding dependencies or parallelizing implementation
Last reviewed: 2026-08-15

This roadmap tracks capability milestones, hard dependencies and parallel delivery lanes for the Local LLM Server repositioning and UX/UI evolution. Integrated truth and the immediate implementation block belong in [`current-state.md`](current-state.md).

## 1. Delivery objective

Move from the current multi-backend local model server toward a **resource-aware, observable local AI control plane and evaluation harness** with a coherent product experience for text, vision and audio.

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
| M1 — Trustworthy foundation | PARTIAL | A1/A3/F1 done; A2/C1 request-path integration and E1 screen adoption remain |
| M2 — Resource-aware runtime | IN_PROGRESS | Batch 2 begins with B1; ResourceManager/reclamation/zero-resident remain |
| M3 — Multi-task control plane | IN_PROGRESS | canonical task vocabulary exists; C2 capability model starts next |
| M4 — Evidence-grade observability | READY | D1 metric vocabulary and D3 artifact identity can start independently |
| M5 — Redesigned control-plane UX | IN_PROGRESS | design-system foundation exists; E2 shell starts next |
| M6 — Benchmark & Evaluation harness | PENDING | reproducible test sets/runs/comparisons tied to exact runtime identity |
| M7 — Product-grade release candidate | PENDING | completion policy satisfied on representative macOS/Linux hardware |

## 4. Dependency graph

```text
Batch 1 integrated foundation

A1 DONE ──────────────┐
A3 DONE               │
F1 DONE               │
A2 PARTIAL ─┐         │
C1 PARTIAL ─┴─> AC1 request-path integration
E1 PARTIAL ─────> E2 shell/navigation
                     
A1 ─────────────> B1 Resource observation ─> B2 ResourceManager
C1 vocabulary ──> C2 Capability model ─────> C3 ASR task/API
C1 lifecycle names -> D1 Metric vocabulary -> D2 normalization
artifact sources ─> D3a Artifact identity ──┐
D1/D2 + hardware profile ───────────────────> D3 runtime fingerprint

B1/B2 ───────────> E3 memory/resource panels
C2 ──────────────> E3/E5 capability-driven UX
D1/D2 ───────────> E4 truthful metrics
D3 ──────────────> E3/E4 fingerprint/evidence

B2 + reclaimable lifecycle -> B5 scheduler -> B6 residency policy
D2 + D3 + B1 -------------> D4 benchmark engine -> E6 Benchmark UX
```

## 5. Batch 1 — Foundation status

Batch 1 was deliberately developed on isolated branches and integrated sequentially behind a blocking CI baseline.

### A1 — Make CI truthful
Status: `DONE`
Dependencies: none

Integrated:

- removed pytest failure suppression;
- Python 3.10/3.11/3.12 deterministic matrix is blocking;
- required Hugging Face test dependency is installed;
- Ruff correctness gate blocks syntax/high-confidence correctness errors;
- legacy style/modernization debt remains visible but is not conflated with the correctness gate;
- current FastAPI route-shape compatibility is covered.

Remaining non-blocking debt:

- broaden Ruff coverage incrementally after pre-existing violations are paid down.

### A2 — Privacy/security defaults
Status: `PARTIAL`
Dependencies: none

Integrated:

- `trust_remote_code=false` default;
- explicit opt-in through config/environment;
- trust decision propagated into MLX tokenizer configuration;
- `allow_remote_media=false` default;
- pure HTTP(S) media policy validator with fail-closed tests;
- deterministic cleanup of temporary WAV files owned by the helper lifecycle.

Remaining gate:

- enforce the media policy in the canonical HTTP request path before backend execution.

### A3 — Remove ClosedRoom-specific registry coupling
Status: `DONE`
Dependencies: none

Integrated:

- removed direct ClosedRoom Application Support reads from core;
- added generic YAML/JSON external registry layers;
- explicit paths or `LOCAL_LLM_REGISTRY_PATHS` provide consumer integration;
- precedence is built-in < external < user;
- missing external layers fail clearly;
- merge behavior is covered by tests.

### C1 — Canonical task/request vocabulary
Status: `PARTIAL`
Dependencies: none

Integrated:

- backend-neutral `TaskType`;
- `InferenceRequest`, `InferenceResult`, generation/output contracts;
- typed termination/error vocabulary;
- compatibility translator from current OpenAI/legacy chat payloads;
- chat, structured generation, vision-language and transcription classification;
- Python 3.10-compatible contract implementation;
- no FastAPI/Pydantic/backend dependency in the core types.

Remaining gate:

- route the existing HTTP execution path through the compatibility translator/canonical request boundary.

### E1 — Design-system tokens and primitives
Status: `PARTIAL`
Dependencies: none

Integrated:

- brand palette and semantic surface tokens;
- dark-first and light semantic variants;
- typography, spacing, radii, control height and focus tokens;
- status semantics not represented by color alone;
- reusable card, button, field, metric, status, empty-state and table primitives;
- reduced-motion foundation;
- stylesheet loaded by the Studio bundle.

Remaining gate:

- migrate the real shell/screens and add visual/accessibility regression evidence.

### F1 — Positioning and information-language contract
Status: `DONE`
Dependencies: target specification

Integrated:

- README/package description aligned to resource-aware local AI control-plane positioning;
- explicit “orchestrates specialist runtimes; does not replace them” statement;
- local-first/not-local-only language;
- current-vs-target capability disclaimer;
- artifact/residency/evidence terminology aligned to the program.

## 6. Batch 2 — Active parallel implementation

Batch 2 starts now. The key rule is **parallelize by ownership boundary, not by task count**.

### AC1 — Canonical request + security enforcement integration
Status: `READY`
Dependencies: A2, C1
Ownership: API/request path; exclusive `server.py` stream

Why it is one stream:

- A2 remote-media enforcement and C1 request translation converge on the same normalization/execution boundary;
- separate branches editing `server.py` would create avoidable conflicts and duplicated validation.

Deliverables:

- translate current `/v1/chat/completions` requests to `InferenceRequest` before execution policy;
- preserve current OpenAI-compatible behavior and response shape;
- apply `validate_media_sources()` before backend invocation;
- resolve `allow_remote_media` from the selected runtime/model configuration;
- map typed invalid request/policy errors to bounded public errors;
- keep request normalization free of backend-specific policy where possible;
- add non-streaming and streaming compatibility tests;
- add explicit HTTP(S)-media rejected/default and opt-in tests.

Exit gate:

- current API compatibility tests pass through the canonical request boundary;
- remote media cannot reach a backend unless explicitly enabled;
- no duplicated request parser becomes a second source of truth.

### B1 — Resource observation contract
Status: `READY`
Dependencies: A1 recommended; satisfied
Ownership: new resource modules, no `server.py` changes in first slice

Deliverables:

- `SystemResourceSnapshot` with timestamp/source/platform metadata;
- host memory fields with unavailable rather than invented zero semantics;
- accelerator/unified-memory fields only where measurable;
- per-runtime `RuntimeResourceProfile` separating configured estimate, observed current and observed peak;
- configured budget/headroom contract;
- pressure classification vocabulary;
- injectable observer interface for deterministic tests;
- platform adapters kept behind the contract.

Exit gate:

- callers can distinguish estimate, measured value and unavailable value structurally;
- no cross-platform metric is fabricated;
- pure contract/tests work on CI without physical hardware.

### C2 — Capability descriptor
Status: `READY`
Dependencies: C1 vocabulary; satisfied
Ownership: core capability/registry validation modules

Deliverables:

- task support set;
- input modality set;
- output modality set;
- feature set such as streaming, thinking, structured output and tool-like extensions only when truly supported;
- deterministic mapping from current registry metadata to capability descriptors;
- validation for inconsistent declarations;
- pre-backend `supports(request)` decision;
- client/API serialization suitable for future UI consumption.

Migration constraint:

- existing `modalities` remains readable during migration;
- new capability metadata must not claim support merely because a backend family could theoretically provide it.

Exit gate:

- representative text, VLM and audio-capable registry entries resolve to deterministic descriptors;
- unsupported task/modalities can be rejected without loading/invoking the backend.

### D1 — Precise metric vocabulary
Status: `READY`
Dependencies: coordinate with C1 lifecycle names; satisfied
Ownership: new observability contract module

Deliverables:

- request admitted/queued/started/first-output/completed/failed/cancelled lifecycle vocabulary;
- queue wait, load, prompt/prefill, TTFT, decode and total duration fields with precise definitions;
- input/output token counts only when token semantics are real;
- separate chunk/event counts from tokens;
- throughput units tied to a measured denominator;
- cache/load classification;
- resource snapshot linkage;
- unavailable/source semantics;
- privacy-safe event fields with no prompt/output persistence requirement.

Exit gate:

- schema makes it impossible to silently label chunks as tokens;
- UI/backend adapters can leave unsupported fields unavailable.

### E2 — New application shell/navigation
Status: `READY`
Dependencies: E1 foundation; satisfied
Ownership: frontend shell/module boundaries

Deliverables:

- control-plane sidebar/top-level information architecture;
- routes/views for Overview, Models & Runtimes, Endpoints, Playground, Benchmark & Evaluation, System and Settings;
- shared loading/empty/unavailable/error patterns;
- existing working Chat/Models/Logs/API functions preserved during migration;
- module boundaries that reduce collisions for later parallel screen work;
- design-system primitives used as the visual source of truth;
- current source-backed values only; future metrics render unavailable/disabled placeholders rather than fake data.

Exit gate:

- all top-level destinations are navigable;
- legacy workflows remain reachable/functional;
- shell does not depend on B1/C2/D1 to render truthfully.

### D3a — Artifact identity foundation
Status: `READY`
Dependencies: none for artifact portion
Ownership: model source/artifact metadata contract

Deliverables:

- stable artifact identity schema;
- local file SHA-256 where a concrete file exists;
- Hugging Face repository/revision/source metadata where available;
- source kind and verification state;
- stable serialization for later runtime fingerprint assembly;
- no expensive hashing performed implicitly on every UI refresh/request;
- explicit unknown/unverified state.

Exit gate:

- two artifact identities compare deterministically;
- identity does not rely on display name alone;
- later D3 can compose backend/config/hardware identity without changing artifact semantics.

## 7. Batch 2 dependency release points

Batch 2 is designed to unlock follow-on work incrementally instead of waiting for the entire batch.

| Contract landed | Newly unblocked work |
| --- | --- |
| AC1 | canonical API policy path; safer C3/C4 endpoint work |
| B1 | B2 ResourceManager; resource evidence adapters; E3c/E4 resource presentation skeleton |
| C2 | C3 transcription API; E3b/E5 task-aware model controls |
| D1 | D2 backend metric adapters; request-lifecycle UI labels |
| E2 | E3a Models inventory, E4a Overview health, Playground/Diagnostics screen slices in parallel |
| D3a | backend/config/hardware fingerprint composition work |

## 8. Batch 3 — Resource lifecycle, task API, metrics and source-backed UX

### B2 — ResourceManager admission
Status: `BLOCKED`
Dependencies: B1

Deliverables:

- load-time reservation;
- budget/headroom check;
- pressure classification;
- typed resource-exhausted decision;
- reservation release/rollback;
- estimate-to-observation reconciliation;
- deterministic races/overcommit tests.

### B3 — Worker ownership and memory reclamation
Status: `PENDING`
Dependencies: lifecycle contract; B1 for measurement/evidence

May begin protocol design after B1 types stabilize and proceed in parallel with B2.

Deliverables:

- worker protocol;
- isolated text runtime path where required for provable reclamation;
- bounded startup/health/drain/terminate;
- no orphan processes;
- repeated unload evidence.

### B4 — Zero-resident runtime manager
Status: `PENDING`
Dependencies: lifecycle semantics; B2 preferred before load-on-demand policy

Deliverables:

- server remains healthy with zero resident models;
- last runtime can unload;
- configured/default artifact identity survives cold state;
- registry, route selection and residency are separate concepts.

State/API work can progress in parallel with B3; automatic cold-load waits for admission/reclamation policy.

### C3 — First-class transcription task/API
Status: `BLOCKED`
Dependencies: AC1, C2

Deliverables:

- `/v1/audio/transcriptions` compatibility surface;
- ASR-specific request/result contract mapping;
- audio-language chat stays separate from transcription;
- efficient local media transfer/cleanup;
- explicit capability rejection.

### D2 — Metric normalization adapters
Status: `BLOCKED`
Dependencies: D1

Parallel adapter slices after D1:

- D2a llama.cpp / llama-server;
- D2b MLX text;
- D2c MLX-VLM;
- D2d ASR after C3.

Exit gate:

- UI/client consumes one metric schema;
- unsupported metrics remain unavailable;
- token/chunk semantics remain truthful.

### E3/E4 early source-backed slices
Status: `BLOCKED`
Dependencies: E2; individual panels additionally depend on B1/C2/D1

Once E2 lands, parallelize:

- E3a registry/default/residency table using current real sources;
- E4a server/runtime health summary using current real sources;
- current endpoint catalog;
- Playground text migration;
- Diagnostics/log migration.

## 9. Batch 4 — Scheduling, residency, fingerprint and evaluation foundation

### B5 — Scheduler, deadlines and cancellation
Status: `PENDING`
Dependencies: C1/AC1, B2, stable lifecycle/worker boundary

Deliverables:

- bounded queue;
- queue state/wait duration;
- deadline expiry;
- cancellation before/during execution;
- client disconnect propagation where supported;
- explicit overload responses;
- backend-native batching remains backend-owned.

### B6 — Residency policy: pin/LRU/TTL
Status: `PENDING`
Dependencies: B2, B3, B4, B5 lease semantics

Deliverables:

- pin/unpin;
- monotonic idle TTL;
- deterministic LRU ordering;
- eviction reason;
- no active-runtime eviction;
- safe no-candidate/resource-exhausted behavior.

### D3 — Runtime fingerprint completion
Status: `PENDING`
Dependencies: D3a plus backend/config/hardware identity; coordinate with D1/D2

Subtasks that can proceed in parallel:

- backend version and resolved-config digest;
- hardware profile;
- artifact identity integration;
- stable fingerprint serialization and comparison.

### D4a — Benchmark/test-set foundation
Status: `READY`
Dependencies: none for schema preparation

Can progress before final benchmark execution engine.

Deliverables:

- versioned test-set interface;
- general-purpose starter dataset design;
- sample-size selection contract;
- scorer interface;
- result/report schema draft;
- deterministic sample IDs and provenance.

### D4 — Benchmark engine v1
Status: `PENDING`
Dependencies: D2, D3; D4a prepared earlier

Deliverables:

- deterministic run manifest;
- cold/warm distinction;
- latency/TTFT/throughput/memory/success metrics;
- task-quality evaluators;
- result persistence with execution identity;
- comparison rules rejecting incompatible run identity.

### D5 — Benchmark history/regression
Status: `PENDING`
Dependencies: D4

Deliverables:

- immutable run history;
- explicit baseline promotion;
- matched-identity regression checks;
- no comparison across incompatible fingerprints.

## 10. Complete product-surface work

### E3 — Models & Runtimes
Status: `PENDING`
Dependencies: E2; split by data contract

Parallel slices:

- E3a registry/residency table — after E2;
- E3b capability details — after C2;
- E3c memory budget/pressure — after B1/B2;
- E3d pin/auto-evict — after B6;
- E3e runtime fingerprint — after D3.

### E4 — Overview and Diagnostics
Status: `PENDING`
Dependencies: E2; split by source

Parallel panels:

- current server/runtime health — after E2;
- resident-model summary — after E2;
- activity/request lifecycle — B5/D1;
- resource pressure — B1/B2;
- truthful latency/throughput — D2;
- fingerprint/evidence — D3.

### E5 — Endpoints/Playground multimodal UX
Status: `PENDING`
Dependencies: E2, C2; ASR portion C3

Deliverables:

- task-aware model selection;
- capability-driven controls;
- text/image/audio inputs only when supported;
- structured-output settings;
- streaming/cancel state;
- runtime/result metadata;
- no fake supported capability.

### E6 — Benchmark & Evaluation
Status: `PENDING`
Dependencies: E1/E2, D4; shell may precede engine

Deliverables:

- model/backend/test-set/sample-size/task selection;
- run progress/status;
- TTFT/tokens/sec/latency/success/memory/cache/load metrics where available;
- comparison table;
- run manifest/fingerprint;
- history/regression after D5;
- confidence/unavailable states rather than marketing conclusions.

## 11. Final hardening

### H1 — Accessibility and responsive web validation
Status: `PENDING`
Dependencies: primary surfaces

Requirements:

- keyboard navigation and deterministic focus;
- semantic labels;
- status not color-only;
- WCAG AA contrast where applicable;
- 200% zoom/readability;
- narrow laptop/tablet widths;
- reduced-motion compatible transitions.

### H2 — Cross-platform runtime matrix
Status: `PENDING`
Dependencies: B3, D2

Representative matrix:

- Apple Silicon macOS: MLX text + MLX-VLM + GGUF;
- Linux CPU: GGUF text;
- Linux NVIDIA where supported/configured;
- one real transcription path;
- concurrent multi-runtime case where admission permits it.

### H3 — Memory lifecycle evidence
Status: `PENDING`
Dependencies: B1-B4

Must record cold baseline, load footprint, inference peak, unload/post-stop footprint, repeated cycles, model switch, cancellation/failure cleanup and later pressure/eviction behavior.

### H4 — Documentation/positioning promotion
Status: `PENDING`
Dependencies: actual shipped capability

README/screenshots/diagrams/examples must be promoted only from integrated behavior and measured evidence.

## 12. Critical path

```text
B1 -> B2 -> B3/B4 -> B5 -> B6
 |      |             |
 |      +------------> resource-aware UX
 +-> D1 -> D2 -> D3 -> D4 -> D5

AC1 -> C2 -> C3

E1 -> E2 -> E3/E4/E5 -> E6
```

The longest risk-bearing chain remains **resource observation -> admission -> reclaimable lifecycle -> scheduler/residency policy -> hardware evidence**. Capability, observability, artifact identity and UX work must run around it rather than wait for it wholesale.

## 13. Recommended concurrency plan

### Active Batch 2 — up to 6 workers

1. AC1 canonical request + media-policy wiring — exclusive API/server ownership.
2. B1 resource observation — new resource modules.
3. C2 capability model — core/registry capability modules.
4. D1 metric vocabulary — observability contracts.
5. E2 shell/navigation — frontend shell/module boundaries.
6. D3a artifact identity — artifact/source metadata contracts.

### Next release wave after first Batch 2 contracts

Up to 6 workers:

1. B2 ResourceManager after B1.
2. B3 worker protocol/reclamation after B1 types.
3. C3 transcription after AC1+C2.
4. D2 adapters split by backend after D1.
5. E3a/E4a source-backed UI after E2.
6. D4a dataset/scorer foundation independently.

## 14. Merge-conflict minimization

- AC1 is the only Batch 2 stream permitted to make broad request-path changes in `server.py`.
- B1, C2, D1 and D3a should start in new narrow modules and expose stable contracts before wiring.
- E2 owns frontend shell/module extraction; later screen branches start from those boundaries rather than all editing one static bundle.
- backend-specific metric adapters sit behind D1 so they can be developed independently.
- status documentation is updated on the integration line after coherent slices land, not separately by every worker.

## 15. Plan maintenance

At the end of every merged coherent slice:

1. update task status here;
2. record changed dependencies discovered during implementation;
3. update [`current-state.md`](current-state.md) with integrated baseline and immediate next block;
4. update affected workstream progress files;
5. leave target specifications unchanged unless intended behavior changed;
6. keep evidence/test links in completion records/PRs rather than turning this roadmap into a changelog.

The roadmap is stale if merged implementation changes task state/dependencies and this file is not updated in the same integration cycle.

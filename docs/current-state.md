# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Read when: determining the integrated baseline, open blockers or immediate next implementation block
Last reviewed: 2026-08-15

This is the operational ledger for the Local LLM Server evolution program. Target behavior belongs in [`implementation-plan.md`](implementation-plan.md); sequencing belongs in [`roadmap.md`](roadmap.md).

## Active direction

Local LLM Server is evolving into a **resource-aware, observable local AI control plane and evaluation harness** for product-grade text, vision and audio workloads. Specialist inference engines retain backend execution ownership.

## Integrated baseline

### Delivery

- pytest is blocking on Python 3.10/3.11/3.12;
- Ruff blocks syntax/high-confidence correctness errors;
- cumulative program PRs validate the integration line;
- CI remains merge evidence, not physical-hardware performance evidence.

### Canonical request and privacy foundation

Integrated:

- backend-neutral task/request/result/error contracts;
- compatibility translation from current OpenAI/legacy request shapes;
- `request_pipeline.py` canonicalization, modality policy and fail-closed HTTP(S) media validation;
- `trust_remote_code=false` and `allow_remote_media=false` defaults;
- deterministic temporary WAV cleanup;
- bounded public policy errors;
- core registry no longer reads ClosedRoom-specific state.

Remaining:

- `server.py` still uses its historical duplicate parser. AC1b must make the route call the integrated request pipeline before backend execution.

### Resource observation and admission

Integrated:

- measured/estimated/configured/unavailable resource source semantics;
- `SystemResourceSnapshot`, `RuntimeResourceProfile`, budget/headroom and pressure vocabulary;
- Linux total/available/RSS observation where available;
- macOS total memory from `hw.memsize`;
- macOS reclaimable-memory estimate from measured free/inactive/speculative `vm_stat` pages;
- Apple Silicon accelerator memory remains explicitly unavailable rather than inventing a separate VRAM pool;
- `ResourceManager` reservation ledger with `ADMIT`, `REJECT`, `UNKNOWN` decisions;
- reserved/committed accounting, rollback/release and observed-footprint reconciliation;
- unconfigured budget returns `UNKNOWN` and does not pretend the load was admitted.

Remaining:

- runtime load/reload is not yet wired through ResourceManager;
- observer snapshots are not yet persisted/exposed as product evidence;
- memory reclamation after unload is not demonstrated and remains B3.

### Capabilities

Integrated:

- task/input/output/feature descriptors;
- conservative legacy-registry mapping;
- `supports(request)` decision and consistency validation;
- audio modality alone does not imply first-class transcription;
- capability catalog projection with explicit vs legacy-conservative provenance.

Remaining:

- capability projection is not yet included in the public/admin model listing;
- canonical request execution does not yet reject via the descriptor before backend invocation;
- C3 first-class transcription remains dependency-gated.

### Observability

Integrated:

- precise D1 lifecycle/duration/count/throughput vocabulary;
- token counts and chunk counts are structurally distinct;
- unsupported fields serialize as unavailable rather than zero;
- D2a runtime-status adapter maps only trustworthy `output_chunks` / `chunks_per_second`;
- historical `tokens_generated` / `tokens_per_second` aliases are deliberately ignored by the canonical adapter because they are chunk-backed.

Remaining:

- richer backend adapters for real prompt tokens, output tokens, TTFT, prefill and decode timing;
- product API/UI exposure of canonical metrics;
- removal/deprecation of misleading historical field names after consumers migrate.

### Artifact and execution identity

Integrated:

- path-free artifact source identity;
- explicit verification state and optional local-file SHA-256;
- stable artifact key;
- Hugging Face source/revision metadata without false verification claims.

Remaining D3:

- backend version identity;
- resolved config digest;
- hardware profile;
- final runtime fingerprint composition.

### Evaluation harness foundation

Integrated:

- versioned `TestSet` and stable sample IDs;
- task-typed `EvaluationSample` with provenance/tags;
- deterministic seeded sample selection;
- scorer protocol and score schema;
- run manifest with exact selected sample IDs and optional runtime fingerprint;
- sample result/report schema and exact completeness checks.

Remaining:

- built-in general-purpose starter dataset;
- concrete scorers;
- execution engine after D2/D3 identity is stable;
- history/regression after D4 execution is complete.

### UX/UI

Integrated:

- shared design-system foundation;
- incremental control-plane shell with Overview, Models & Runtimes, Endpoints, Playground, Benchmark & Evaluation, System/Diagnostics and Settings;
- existing real Chat/Models/Logs flows preserved during migration;
- Overview now polls real `/health`, `/status` and `/v1/models` sources;
- server readiness, backend, default route, resident count and active-request values render only when their source exists;
- failed/missing sources render `Unavailable` rather than fake zero/stale data;
- resource pressure remains explicitly unavailable until resource observation is product-exposed.

Remaining:

- Models & Runtimes lifecycle composition beyond the legacy view;
- capability/resource/metric/fingerprint panels as their sources become public;
- Playground/Diagnostics modular migration;
- accessibility and visual-regression evidence.

## Program status

| Task | Status | Integrated outcome | Remaining gate |
| --- | --- | --- | --- |
| A1 truthful CI | DONE | blocking deterministic matrix | broad Ruff debt later |
| A2 privacy defaults | PARTIAL | fail-closed policy + cleanup | route enforcement AC1b |
| A3 consumer decoupling | DONE | generic registry sources | — |
| C1 canonical requests | PARTIAL | contracts + translator + policy adapter | route wiring AC1b |
| E1 design system | PARTIAL | tokens/primitives | screen adoption/evidence |
| F1 positioning | DONE | README/package positioning | — |
| B1 resource observation | PARTIAL | Linux + macOS source adapters | runtime/API wiring + hardware evidence |
| B2 ResourceManager | PARTIAL | reservation/admission accounting | load/reload wiring |
| C2 capabilities | PARTIAL | descriptor + catalog projection | list/API/request wiring |
| D1 metric vocabulary | DONE | canonical truthful schema | — |
| D2 metrics | PARTIAL | runtime chunk adapter | backend timings/tokens + API exposure |
| D3a artifact identity | DONE | stable path-free identity | D3 runtime fingerprint |
| D4a evaluation schema | DONE | test-set/selection/scorer/run contracts | dataset + execution engine |
| E2 shell/navigation | PARTIAL | new IA | full screen migration/evidence |
| E4a Overview | PARTIAL | source-backed health/runtime summary | resources/metrics/fingerprint panels |
| AC1 request/security | PARTIAL | tested request pipeline | replace historical route parser |

## Immediate next parallel wave

Run these streams together with the stated ownership boundaries:

1. **B2b runtime admission wiring** — connect model load/reload reservations to ResourceManager without claiming reclamation.
2. **B3 worker/reclamation protocol** — define isolatable runtime worker lifecycle and evidence hooks; implementation may begin independently from final B2 wiring.
3. **C2c public capability exposure** — add capability projection to model listing/admin sources, still avoiding request-route edits.
4. **D3b execution identity** — backend version + resolved-config digest + hardware profile contract toward runtime fingerprint.
5. **D4b built-in general-purpose test set** — create the first curated local test set and deterministic baseline scorers on top of D4a.
6. **E3a Models & Runtimes source-backed redesign** — consume current registry/residency facts; capability/resource sections stay unavailable until their APIs land.
7. **AC1b route wiring** — exclusive `server.py` ownership; make the existing OpenAI endpoint execute through `request_pipeline.py` and enforce remote-media policy.

### Parallelization constraints

- AC1b exclusively owns broad request-path changes in `server.py`.
- B2b owns runtime admission integration; B3 owns reclamation/worker isolation and must not treat accounting as proof of memory release.
- C2c changes model/catalog presentation, not the inference route.
- D3b remains a pure identity contract first; hashing/version probes must not run implicitly on every request.
- D4b is local harness data/scoring work and must not depend on live runtime execution yet.
- E3a shows only source-backed state and explicit unavailable placeholders.

## Evidence boundary

The current automated suite proves contract behavior. It does **not** prove real Apple unified-memory reclaimability, model unload memory recovery, true backend token throughput or final TTFT. Those remain representative-hardware evidence tasks.

## Update rule

Update this file in the same integration cycle whenever task state, blockers or the next wave changes. Keep it current rather than historical.

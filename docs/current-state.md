# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Read when: determining the integrated baseline, open blockers or immediate next implementation block
Last reviewed: 2026-08-15

This is the operational ledger for the Local LLM Server evolution program. Target behavior belongs in [`implementation-plan.md`](implementation-plan.md); sequencing belongs in [`roadmap.md`](roadmap.md).

## Active direction

Local LLM Server is evolving into a **resource-aware, observable local AI control plane and evaluation harness** for product-grade local inference. Specialist inference engines retain backend execution ownership.

## Integrated baseline

### Delivery and safety

- blocking pytest on Python 3.10/3.11/3.12 plus a Ruff correctness gate;
- fail-closed `trust_remote_code` and remote-media policy foundations;
- deterministic owned temporary-audio cleanup;
- generic external registry integration with no ClosedRoom-specific core dependency;
- supported public Python and CLI server entrypoints now install canonical request-policy middleware before inference.

### Canonical requests and privacy enforcement

Integrated:

- backend-neutral task/request/result/error contracts;
- OpenAI/legacy compatibility translator;
- `request_pipeline.py` canonicalization, modality checking, remote-media policy and bounded public errors;
- request-policy middleware on `/v1/chat/completions` and `/api/v1/chat` for the supported `serve()`, package `run_server()` and `local-llm serve` paths;
- remote HTTP(S) media is rejected before backend invocation by default; tests assert zero backend calls on rejection;
- explicit remote-media opt-in remains compatible;
- the prepared canonical request is attached to request state for subsequent route migration.

Compatibility boundary:

- the historical route still builds backend kwargs with its legacy parser after middleware validation;
- direct use of the legacy module-level `local_llm_server.server:app` does not automatically install the middleware and remains a compatibility/deprecation path rather than the supported product entrypoint.

### Resources and runtime lifecycle

Integrated:

- measured/estimated/configured/unavailable resource semantics;
- Linux memory/RSS and macOS total/reclaimable-memory observation;
- Apple unified memory is not represented as fake separate VRAM;
- budget/headroom/pressure vocabulary;
- `ResourceManager` reservation ledger with `ADMIT`, `REJECT`, `UNKNOWN`;
- model artifact estimates from explicit bytes, registry `size_gb` or concrete local file size;
- `ModelRuntimeManager.load()` reserves before expensive backend load when a ResourceManager and estimate exist;
- successful load commits accounting; failed load rolls back;
- reload preserves old accounting while checking replacement peak overlap and restores the old runtime on rejection/failure;
- unload/shutdown release accounting after engine close;
- runtime status exposes the admission decision/estimate when present;
- worker protocol plus concrete bounded JSON-line subprocess transport with request correlation, health/generate/drain/cancel/stop ownership.

Important boundary:

- normal product entrypoints do not yet construct/configure a ResourceManager from user settings, so resource admission is wired but not yet an always-active product policy;
- estimates are not measured residency;
- subprocess ownership is not proof of host-memory reclamation;
- existing inference engines are not yet routed through the new worker transport;
- representative pre/peak/post-stop memory evidence remains required.

### Capabilities

Integrated:

- task/input/output/feature descriptors and conservative legacy mapping;
- `supports(request)` and consistency validation;
- audio modality alone does not imply first-class transcription;
- capability catalog projection with explicit vs `legacy_conservative` provenance;
- `list_models()` and the admin registry source now expose `capabilities` and `capability_source` while preserving legacy fields.

Open gap:

- live inference currently enforces media/modality compatibility but not the full capability descriptor (`structured_output`, streaming, task eligibility, etc.);
- first-class transcription remains unimplemented.

### Observability

Integrated:

- D1 lifecycle/duration/count/throughput vocabulary with token/chunk separation;
- current runtime chunk counters map only to canonical chunk fields;
- misleading historical chunk-backed token aliases are ignored by the canonical adapter;
- completed OpenAI-compatible responses can contribute real `prompt_tokens` / `completion_tokens` when provided;
- llama.cpp-style `prompt_ms`, `predicted_ms`, `prompt_n`, `predicted_n`, `predicted_per_second` are mapped only when explicitly present;
- completed-response adapters deliberately leave TTFT unavailable;
- complementary token and chunk evidence can be merged without aliasing.

Open gap:

- canonical metrics are not yet attached to live request/status API responses;
- streaming TTFT needs a real first-output timestamp rather than reconstruction;
- backend-specific coverage remains incomplete across MLX/VLM/ASR.

### Artifact and runtime identity

Integrated:

- path-free artifact identity and verification state;
- optional explicit SHA-256 for concrete local files;
- backend identity, allowlisted config digest and hostname-free hardware profile;
- stable privacy-safe runtime fingerprint composition;
- explicit immutable `RuntimeIdentitySnapshot` attachment for one residency period;
- attachment is intentionally controlled rather than recomputed per request/token.

Open gap:

- product lifecycle does not yet automatically capture and expose an identity snapshot after runtime readiness;
- artifact verification/backend version/hardware capture policy still needs a controlled integration point.

### Evaluation harness

Integrated:

- versioned test-set/sample/scorer/run/report contracts;
- deterministic seeded sample selection;
- built-in `general-purpose` v1 set with 20 stable samples covering arithmetic, classification, extraction, instruction following, simple reasoning, structured JSON and formatting;
- deterministic objective scorer with no initial LLM-as-judge dependency;
- backend-neutral `EvaluationExecutor` and `EvaluationRunner`;
- selected samples are translated into canonical deterministic `InferenceRequest` objects, executed, scored and collected into a report;
- one sample failure does not abort the full run;
- test-set identity is validated before sample interpretation;
- supplied runtime fingerprint is carried into sample evidence.

Open gap:

- no executor is yet bound to the resident runtime/server API;
- no benchmark run service/API/persistence yet;
- history/regression and evidence-grade comparison rules remain pending.

### UX/UI

Integrated:

- shared design system and seven-destination control-plane shell;
- existing real Chat/Models/Logs workflows remain available;
- Overview reads real `/health`, `/status`, `/v1/models` and renders source failure as `Unavailable`;
- a dedicated Models & Runtimes control-plane module now combines resident models, runtime state and admin catalog data;
- configured identity, resident/cold state, default route, backend, active requests and capability descriptors are rendered only when sources exist;
- when admin catalog is unavailable the screen degrades explicitly to resident-only mode;
- resource admission and runtime fingerprint sections remain `Unavailable` until public product sources exist.

Open gap:

- resource/metrics/fingerprint panels need API exposure;
- Benchmark & Evaluation has no connected runner workflow yet;
- Playground/Diagnostics modular migration, accessibility and visual-regression evidence remain.

## Program status

| Task | Status | Integrated outcome | Remaining gate |
| --- | --- | --- | --- |
| A1 truthful CI | DONE | blocking deterministic matrix | broad Ruff debt later |
| A2/C1/AC1 | PARTIAL | canonical policy enforced on supported public/CLI entrypoints | retire duplicate parser + legacy direct-app gap; full capability enforcement |
| A3 consumer decoupling | DONE | generic registry sources | — |
| E1 design system | PARTIAL | shared tokens/primitives | screen evidence |
| F1 positioning | DONE | control-plane positioning | — |
| B1 resource observation | PARTIAL | Linux/macOS observers | product API + representative evidence |
| B2 ResourceManager | PARTIAL | real load/reload/unload accounting wiring | product budget configuration + measured reconciliation |
| B3 worker/reclamation | PARTIAL | protocol + concrete subprocess transport | engine integration + reclamation evidence |
| C2 capabilities | PARTIAL | descriptor + public catalog exposure | full pre-backend capability enforcement |
| D1 metrics vocabulary | DONE | truthful canonical schema | — |
| D2 adapters | PARTIAL | real response token/timing adapters where sourced | live request/API integration + TTFT/backends |
| D3 runtime identity | PARTIAL | fingerprint + immutable residency snapshot contract | automatic lifecycle capture/exposure |
| D4 evaluation | PARTIAL | dataset + scorer + executable runner | runtime binding + run service/persistence/history |
| E2 shell/navigation | PARTIAL | new IA | full screen migration/evidence |
| E3a Models & Runtimes | PARTIAL | live source-backed control-plane view | resource/fingerprint/actions integration + UX evidence |
| E4a Overview | PARTIAL | live health/runtime summary | resource/metrics/fingerprint/evaluation panels |

## Immediate next parallel wave

Prioritize **product exposure, evaluation workflow and runtime control**:

1. **B2c resource policy configuration/exposure** — configure optional memory budget/headroom in supported server entrypoints, expose truthful ResourceManager snapshot and admission state, and keep unconfigured policy explicit.
2. **B3c reclamation evidence harness** — bind observers to worker lifecycle checkpoints and produce before-ready/peak/after-stop evidence without automatically declaring PASS.
3. **B4 zero-resident semantics** — separate configured/default identity from residency so the server can remain healthy with no loaded models; automatic cold loading waits for policy/worker readiness.
4. **B5a scheduler foundation** — bounded queue/deadline/cancellation contracts and deterministic tests; backend-native batching remains backend-owned.
5. **C2d request capability enforcement + C3 ASR foundation** — use public descriptors before backend invocation and begin first-class transcription API/adapter now that canonical policy/catalog dependencies exist.
6. **D2c/D3d evidence API** — attach canonical request metrics and runtime identity snapshots to product status/evidence surfaces only when sourced.
7. **D4d evaluation service** — bind `EvaluationRunner` to a resident-runtime executor, persist a run manifest/report, expose built-in test-set selection and sample count.
8. **E4b/E6a UI** — consume resource/metric/fingerprint sources and build the first real Benchmark & Evaluation setup/run/results flow.

### Parallelization constraints

- B2c owns resource configuration/API state; B3c owns reclamation evidence, not admission claims.
- B4 state semantics should avoid broad request-route edits while C2d/C3 own canonical task/API changes.
- D2c/D3d expose canonical producer data; UI must not recompute or infer it.
- D4d comparisons require explicit runtime identity; runs lacking it may execute but are not evidence-grade comparisons.
- E4b/E6a stay source-backed and show `Unavailable`/`Inconclusive` when evidence is missing.

## Evidence boundary

Automated tests establish contract and deterministic workflow correctness. They do **not** prove Apple unified-memory reclamation, actual unload recovery, thermal behavior, streaming TTFT or device-specific token throughput. Representative hardware evidence remains mandatory before those claims become DONE.

## Update rule

Update this file in the same integration cycle whenever task state, blockers or the next wave changes.

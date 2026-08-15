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

- blocking pytest on Python 3.10/3.11/3.12;
- Ruff correctness gate;
- fail-closed `trust_remote_code` and remote-media policy foundations;
- deterministic owned temporary-audio cleanup;
- generic external registry integration with no ClosedRoom-specific core dependency.

### Canonical requests

Integrated:

- backend-neutral task/request/result/error contracts;
- OpenAI/legacy compatibility translator;
- `request_pipeline.py` for canonicalization, modality checking, remote-media policy and bounded public errors.

Open gap:

- `server.py` still uses its historical duplicate parser. AC1b remains the route-level privacy/canonicalization blocker.

### Resources and lifecycle

Integrated:

- measured/estimated/configured/unavailable resource semantics;
- Linux memory/RSS observation;
- macOS total/reclaimable-memory adapter with unified-memory-safe semantics;
- budget/headroom and pressure vocabulary;
- `ResourceManager` reservation ledger with `ADMIT`, `REJECT`, `UNKNOWN`;
- reserve/commit/reconcile/release/rollback accounting;
- worker protocol states/commands and deterministic state-machine validation;
- worker evidence slots for before-start, after-ready, peak and after-stop snapshots.

Important boundary:

- the worker protocol is a contract, not yet a concrete isolated process implementation;
- accounting does not prove memory reclamation;
- load/reload is not yet routed through ResourceManager;
- physical post-stop reclamation evidence is still required.

### Capabilities

Integrated:

- task/input/output/feature descriptors;
- conservative legacy mapping;
- `supports(request)`;
- explicit-vs-legacy capability catalog projection;
- audio modality alone does not imply first-class transcription.

Open gap:

- capability projection is not yet exposed through the model listing/admin source or enforced in the live request route.

### Observability

Integrated:

- exact D1 lifecycle/duration/count/throughput vocabulary;
- token and chunk semantics are separate;
- D2a maps only trustworthy `output_chunks` and `chunks_per_second`;
- historical chunk-backed `tokens_generated` / `tokens_per_second` are ignored by the canonical adapter.

Open gap:

- real backend prompt/output tokens, TTFT, prefill and decode timing remain backend-specific adapter work;
- canonical metrics are not yet exposed through the product API/UI.

### Artifact and runtime identity

Integrated:

- path-free artifact identity and verification state;
- explicit optional SHA-256 for concrete local files;
- backend identity contract;
- allowlisted resolved-config digest excluding paths, URLs, prompts and unrelated private fields;
- hostname-free hardware profile;
- stable runtime fingerprint composition from artifact/backend/config/hardware identity.

Open gap:

- runtime instances and evaluation reports do not yet attach the fingerprint automatically;
- hardware/backend version evidence must be captured at controlled lifecycle points, not per token/request refresh.

### Evaluation harness

Integrated:

- versioned test-set/sample/scorer/run/report contracts;
- deterministic seeded sample selection;
- built-in `general-purpose` v1 dataset with 20 stable samples;
- coverage across arithmetic, classification, extraction, instruction following, simple reasoning, structured JSON and formatting;
- deterministic objective scorer for exact, case-insensitive, contains, word-count, comma-count and JSON checks;
- no LLM-as-judge dependency in the initial deterministic core.

Open gap:

- no live execution engine yet;
- benchmark comparison/history waits for runtime execution identity and richer measured metrics.

### UX/UI

Integrated:

- shared design system;
- control-plane shell with Overview, Models & Runtimes, Endpoints, Playground, Benchmark & Evaluation, System/Diagnostics and Settings;
- existing real Chat/Models/Logs workflows preserved;
- Overview reads real `/health`, `/status`, `/v1/models` sources;
- missing sources render `Unavailable`, not fake zero/stale data.

Open gap:

- E3a Models & Runtimes redesign;
- capability/resource/metric/fingerprint API exposure and panels;
- Playground/Diagnostics modular migration;
- accessibility/visual-regression evidence.

## Program status

| Task | Status | Integrated outcome | Remaining gate |
| --- | --- | --- | --- |
| A1 truthful CI | DONE | blocking deterministic matrix | broad Ruff debt later |
| A2/C1/AC1 | PARTIAL | policy + contracts + request pipeline | AC1b `server.py` wiring |
| A3 consumer decoupling | DONE | generic registry sources | — |
| E1 design system | PARTIAL | shared tokens/primitives | screen evidence |
| F1 positioning | DONE | control-plane positioning | — |
| B1 resource observation | PARTIAL | Linux/macOS observers | product wiring + hardware evidence |
| B2 ResourceManager | PARTIAL | reservation/admission accounting | runtime load/reload wiring |
| B3 worker/reclamation | PARTIAL | protocol + evidence contract | concrete worker + reclamation evidence |
| C2 capabilities | PARTIAL | descriptor + catalog projection | public/request wiring |
| D1 metrics vocabulary | DONE | truthful canonical schema | — |
| D2 adapters | PARTIAL | truthful chunk adapter | real tokens/timings + exposure |
| D3 runtime identity | PARTIAL | artifact/backend/config/hardware fingerprint contracts | lifecycle/evidence attachment |
| D4 evaluation | PARTIAL | schema + 20-sample built-in set + deterministic scorer | execution/history |
| E2 shell/navigation | PARTIAL | new IA | full screen migration |
| E4a Overview | PARTIAL | live source-backed health/runtime summary | richer source panels |

## Immediate next parallel wave

Prioritize **wiring real execution paths**, not more disconnected contracts:

1. **AC1b request-route wiring** — exclusive `server.py` ownership; make `/v1/chat/completions` call `request_pipeline.py` and enforce remote-media policy before backend work.
2. **B2b runtime admission wiring** — reserve/commit/rollback/release around real model load/reload/unload while preserving rollback semantics.
3. **B3b concrete worker transport** — bind the worker protocol to managed process ownership for runtime families where isolation is needed for reclaimability.
4. **C2c public capability exposure** — add capability object/provenance to model catalog/list sources; request enforcement follows AC1b.
5. **D2b backend metric adapters** — add real token/timing fields only where the backend exposes trustworthy measurements.
6. **D3c fingerprint attachment** — attach runtime fingerprint to controlled runtime/evaluation evidence without per-request expensive probing.
7. **D4c evaluation runner** — execute the built-in set through an executor interface, score samples and produce reports tied to supplied runtime fingerprint.
8. **E3a Models & Runtimes redesign** — consume current lifecycle facts and leave not-yet-public capability/resource/fingerprint values unavailable.

### Parallelization constraints

- AC1b is the only broad request-route editor.
- B2b owns load admission; B3b owns process isolation/reclamation.
- C2c owns model/catalog presentation rather than request execution.
- D2b/D3c expose canonical observability/identity contracts; UI consumes them rather than recomputing semantics.
- D4c must require explicit execution identity for evidence-grade comparison.
- E3a remains source-backed and must not infer unsupported values.

## Evidence boundary

Automated tests prove contract and deterministic harness behavior. They do not prove Apple unified-memory reclamation, real unload memory recovery, TTFT or token throughput. Representative hardware evidence remains mandatory.

## Update rule

Update this file in the same integration cycle whenever task state, blockers or the next wave changes.

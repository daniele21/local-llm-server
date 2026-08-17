# Runtime correctness and evidence hardening

Status: active
Owner: local-llm-server
Read when: implementing or coordinating post-smoke-test correctness, evaluation and hardware-evidence hardening

## Goal

Turn the first successful real-device smoke into a trustworthy product baseline by making thinking behavior controllable and non-leaky, structured output deterministic at the API boundary, evaluation use the same canonical request path as interactive inference, artifact identity evidence-grade, and resource/hardware validation repeatable without overstating what CI or one device proves.

## Triggering evidence

The 2026-08-17 Apple Silicon smoke established the following current facts:

- interactive GGUF inference works end-to-end after the text-capability fix;
- streaming works, but reasoning text is exposed even when the UI does not visibly enable thinking;
- JSON requests can end with valid JSON, but reasoning can precede the final structured payload;
- `/v1/runtime/identity` is partial because the concrete GGUF artifact has no verified SHA-256;
- `/api/v1/evidence` records real HTTP streaming TTFT/total while token counts remain unavailable when the streaming backend does not expose them;
- deterministic evaluation executes 10/10 samples but scored 20% on the sampled general-purpose set; that score is not yet suitable for model-quality interpretation because the evaluation path independently reconstructs backend kwargs and does not pin a reasoning policy;
- two reclamation reports produced six complete lifecycle windows, zero lifecycle errors and six `recovery_observed` observations, but review remains `insufficient` solely because verified artifact identity is required;
- resource policy was disabled in that smoke, so admission/accounting enforcement was not exercised.

These observations are evidence for what was executed on that device. They are not a production-safety or cross-device claim.

## Non-goals

- Do not enable automatic pressure eviction in this workstream.
- Do not claim Apple unified-memory reclamation, safe concurrency, thermal safety or production unload safety from the current reports.
- Do not emulate worker streaming by buffering completed output.
- Do not silently repair malformed model JSON into apparently valid output.
- Do not make evaluation results attribution-safe when runtime/request identity is incomplete.
- Do not hash multi-gigabyte model artifacts during ordinary UI refresh or every health request.
- Do not broaden this workstream into a general UI redesign or new model-family integration.

## Invariants

- Missing evidence stays `Unavailable`/`null`; it never becomes a fabricated zero.
- Public evidence must remain path-free, hostname-free and prompt/output-free unless the endpoint explicitly exists to return inference output.
- `thinking_mode=switchable` may be advertised only when the effective backend/template path can actually honor request-level enable/disable semantics.
- `show_thinking=false` is an output-exposure contract, not proof that the model did not internally reason.
- `enable_thinking=false` is an execution-policy request and must not be silently discarded by an adapter that claims switchable support.
- Structured-output requests expose the final structured answer as application content; reasoning must never be mixed into that content.
- Invalid structured output must fail explicitly or remain explicitly invalid; no hidden JSON rewriting.
- Interactive inference and evaluation must converge on the same canonical `InferenceRequest -> PreparedBackendRequest` translation owner.
- Evaluation manifests must record request-level settings that can materially change results.
- Artifact verification must be explicit and bounded; a digest is evidence for the exact file that was hashed.
- Automatic eviction remains disabled regardless of a positive reclamation observation.

## Work graph

| ID | Work | Owns/writes | Depends on | Parallel | State |
| --- | --- | --- | --- | --- | --- |
| RC-0 | Preserve the real-device smoke baseline and regression expectations | tests/docs only; no runtime behavior | — | yes | DONE |
| TH-1 | Define effective thinking contract per backend/template path | `core/capabilities.py`, request/backend contract tests, adapter tests | — | yes | READY |
| TH-2 | Make `llama_cpp` honor switchable thinking instead of dropping the request flag | `engine.py`, backend request/engine tests | TH-1 | yes, with TH-3 | BLOCKED |
| TH-3 | Replace streaming thinking filtering with a chunk-safe reasoning boundary state machine | `server.py` or dedicated output-normalization module + streaming tests | TH-1 | yes, with TH-2 | BLOCKED |
| TH-4 | Make UI controls represent execution vs exposure truthfully | Playground capability/UI assets + tests | TH-1, TH-2 | yes, after contract | BLOCKED |
| SO-1 | Define structured-output final-content contract and typed invalid-output behavior | canonical contracts/request-output tests | TH-1 | yes | READY |
| SO-2 | Enforce reasoning/final separation for non-stream and streaming structured output | response normalization + server tests | TH-2, TH-3, SO-1 | no | BLOCKED |
| EV-1 | Move evaluation execution onto canonical backend preparation | `evaluation_runner.py`, `evaluation_service.py`, `backend_request.py` consumers + tests | TH-1 | yes, with ID-1/RES-1 | READY |
| EV-2 | Add explicit evaluation reasoning policy to run identity/manifest and UI/API | evaluation manifest/service/API/UI + compatibility tests | EV-1, TH-2 | no | BLOCKED |
| EV-3 | Re-run general-purpose `10 samples / seed 0` and compare pre/post behavior | real runtime evidence; no product code unless failure found | SO-2, EV-2 | yes, with HE-2/RES-2 | BLOCKED |
| ID-1 | Design explicit artifact verification receipt/cache contract | artifact identity + CLI contract tests | — | yes | READY |
| ID-2 | Implement `verify-artifact` and optional evidence-run verification | CLI, artifact identity persistence, runtime identity/evidence integration + tests | ID-1 | yes | BLOCKED |
| HE-1 | Make verified artifact identity flow into hardware report/reviewer compatibility | hardware evidence/review tests | ID-2 | no | BLOCKED |
| HE-2 | Repeat two compatible 3-cycle Apple Silicon GGUF reports with verified identity | retained local/release evidence | HE-1 | yes, with EV-3/RES-2 | BLOCKED |
| RES-1 | Add deterministic resource-policy admission/accounting integration coverage | resource policy/runtime/API tests | — | yes | READY |
| RES-2 | Run bounded real-device resource-policy smoke: admit, account, unload/release, reject-before-load | real device evidence | RES-1 | yes, with EV-3/HE-2 | BLOCKED |
| DOC-1 | Reconcile current-state/roadmap/API docs with integrated truth and remove stale duplicate execution claims | `docs/current-state.md`, `docs/roadmap.md`, affected durable docs | all code slices | no | BLOCKED |
| REL-1 | Cumulative green gate and workstream finalization | whole repository validation/evidence review | EV-3, HE-2, RES-2, DOC-1 | no | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

Parallel work must have explicit non-conflicting ownership/write boundaries or a defined integration point.

## Current executable slices

The first implementation wave can start in parallel on four independent boundaries:

- `TH-1` — thinking contract truth;
- `SO-1` — structured-output contract;
- `EV-1` — evaluation canonicalization;
- `ID-1` — artifact verification contract;
- `RES-1` — resource-policy integration coverage.

`TH-2` and `TH-3` must not begin as unrelated fixes before `TH-1` determines what the backend can actually guarantee. `HE-2` must not be repeated until artifact identity is verified, otherwise it only reproduces the known `insufficient: verified_identity_required` result.

## Slice details

### TH-1 — Effective thinking contract

Outcome: capability metadata and request semantics describe behavior the effective backend can prove.

Implementation requirements:

- enumerate `none`, `switchable`, and `always` behavior at the canonical request boundary;
- distinguish **execution control** (`enable_thinking`) from **output exposure** (`show_thinking`);
- prove each backend adapter either forwards the execution control through a supported mechanism or does not advertise switchability;
- ensure aliases (`enable_reasoning`, `show_reasoning`) normalize before backend translation;
- preserve fail-closed behavior for unsupported thinking requests;
- document backend-specific inability as capability evidence, not a best-effort guess.

Acceptance:

- a runtime advertised as `switchable` demonstrably produces different effective backend configuration for `enable_thinking=true` and `false`;
- a backend that cannot honor the flag cannot advertise switchable thinking;
- no adapter silently removes a supported request flag.

Validation:

- `uv run pytest tests/test_capabilities.py tests/test_backend_request.py tests/test_server_multimodel.py -v`
- targeted adapter tests for every changed engine;
- `uv run ruff check src/ tests/ --select E9,F63,F7,F82`

### TH-2 — llama-cpp switchable execution

Outcome: Nemotron `thinking_mode=switchable` behaves as advertised on the direct `llama_cpp` path.

Implementation requirements:

- use the backend-supported template/request mechanism established by TH-1;
- do not forward unknown kwargs blindly into `llama-cpp-python`;
- preserve deterministic cache identity: requests with different thinking policy must never collide;
- preserve current OpenAI-compatible request shape at the public boundary;
- add contract tests proving ON/OFF propagation at the exact engine call boundary.

Acceptance:

- `enable_thinking=false` is visible in the effective backend invocation and is not discarded;
- `enable_thinking=true` remains supported;
- unsupported template/backend combinations fail or downgrade capability explicitly rather than pretending success.

Validation:

- focused engine/backend-request suite;
- real Nemotron smoke with identical prompt under OFF and ON modes after merge.

### TH-3 — Chunk-safe reasoning boundary

Outcome: `show_thinking=false` never leaks reasoning solely because tags are absent, partial or split across stream chunks.

Implementation requirements:

- move filtering into a dedicated incremental parser/state machine instead of ad-hoc per-token string checks;
- cover opening tag present, closing tag present without opening tag, both tags in one chunk, tags split across chunks, text before/after tags, empty deltas and terminal metrics-only chunks;
- bound parser carry-over to the maximum delimiter length plus minimal state;
- never lose final-answer characters at chunk boundaries;
- keep raw/internal reasoning unavailable to normal output when hidden;
- preserve metrics collection on the original backend stream.

Acceptance:

- aggregate client content with `show_thinking=false` contains only the final answer for all supported delimiter chunkings;
- `show_thinking=true` preserves the exposed reasoning behavior intentionally;
- terminal usage/timing events still reach telemetry even when they contain no text.

Validation:

- table-driven streaming tests with adversarial chunk boundaries;
- existing streaming metrics suite remains green.

### TH-4 — UI truthfulness

Outcome: Playground controls make it clear whether the user is toggling model execution reasoning or only reasoning visibility.

Implementation requirements:

- separate `Enable thinking` and `Show thinking` when both are supported;
- hide/disable controls from server-owned capability metadata, never named-model allowlists;
- do not show `Enable thinking` for `none` or unproven backend support;
- ensure an unchecked control sends an explicit `false` where execution semantics require it instead of omitting the field and falling back to runtime default `true`;
- retain accessible labels, keyboard behavior and focus states.

Acceptance:

- Nemotron OFF sends `enable_thinking=false`;
- Nemotron ON sends `enable_thinking=true`;
- exposure choice is independent and correctly reflected in `show_thinking`.

Validation:

- UI asset regression tests + JS syntax test;
- manual browser network inspection on the real server.

### SO-1 — Structured-output contract

Outcome: the API has one explicit rule for reasoning-capable JSON generation.

Decision to encode:

- `response_format={"type":"json_object"}` applies to the **final application answer**, not to hidden reasoning;
- the final application content must parse as JSON;
- reasoning may be retained only in a separately typed/internal field where the endpoint contract permits it, never prefixed/suffixed to `message.content`;
- invalid final JSON is a typed invalid-model-output condition; no silent repair or regex extraction that changes model meaning.

Acceptance:

- a successful structured completion's exposed `message.content` is parseable JSON;
- a malformed final answer is distinguishable from transport/backend failure;
- non-structured chat behavior is unchanged.

Validation:

- canonical contract tests for valid JSON, invalid JSON and reasoning+JSON;
- stream aggregation test proves the final aggregate is parseable when successful.

### SO-2 — Structured reasoning separation

Outcome: both interactive and evaluation consumers receive a clean final structured payload.

Implementation requirements:

- share final-answer extraction between streaming and non-streaming paths;
- apply structured validation only after the reasoning boundary has produced final content;
- preserve raw backend evidence privately where needed for debugging without exposing it in public evidence APIs;
- do not count parser/validator behavior as model-quality improvement.

Acceptance:

- the user's previous JSON smoke returns only the JSON application answer when thinking is hidden;
- exact same final-answer normalization is available to Evaluation.

### EV-1 — Canonical evaluation execution

Outcome: Evaluation stops maintaining a second backend-kwargs builder.

Implementation requirements:

- construct canonical `InferenceRequest` for each sample;
- resolve the resident runtime once under the existing lease/lifecycle rules;
- call the same backend preparation owner used by supported interactive inference;
- delete duplicated sampling/penalty/structured-output translation from `ResidentRuntimeExecutor` once parity tests prove equivalence;
- preserve deterministic `temperature=0.0` unless the test-set/sample contract explicitly overrides it;
- preserve usage only when the backend explicitly supplies it.

Acceptance:

- a capture engine sees byte-for-byte/equivalent kwargs from Evaluation and canonical preparation for the same request;
- no evaluation-only alias/default logic remains for fields owned by `PreparedBackendRequest`.

Validation:

- new evaluation/backend parity tests;
- existing evaluation unit/history/custom-set suites remain green.

### EV-2 — Evaluation reasoning policy and identity

Outcome: a benchmark result records whether thinking was ON, OFF or runtime-default so comparisons are reproducible.

Implementation requirements:

- add an explicit reasoning policy to run request/manifest, with a stable serialized representation;
- built-in objective `general-purpose` defaults to `off` unless the test-set contract explicitly requires reasoning;
- always-thinking runtimes must be represented truthfully rather than mislabeled OFF;
- include the effective request profile in comparison compatibility/attribution logic;
- preserve backward read compatibility for existing run JSON by treating absent policy as legacy/unknown rather than guessing;
- expose the effective policy in the Evaluation UI/history.

Acceptance:

- runs with different thinking policy cannot be labeled attribution-safe as if they were identical;
- old reports remain readable but are not upgraded to stronger evidence.

### EV-3 — Pre/post evaluation evidence

Outcome: determine whether the previous 20% score reflected model capability, reasoning/output contamination, or both.

Procedure:

1. run `general-purpose v1.0.0`, `sample_count=10`, `seed=0`, thinking OFF;
2. repeat the same run once to confirm deterministic request identity and stable sample selection;
3. optionally run the exact same workload with thinking ON as a separate, explicitly labeled experiment;
4. compare only compatible runs and inspect every changed scorer outcome;
5. do not conclude that a model is globally better from ten samples.

Acceptance:

- 10/10 transport/inference success or explicit per-sample failures;
- run manifest contains runtime fingerprint when available and explicit reasoning policy;
- any score change can be traced to concrete sample outputs/scorers, not hidden request differences.

### ID-1 — Artifact verification contract

Outcome: a user can explicitly turn an available local artifact into a strong identity input without exposing its path publicly or hashing it on every refresh.

Design requirements:

- introduce an explicit command such as `local-llm verify-artifact <model>`;
- hash the concrete resolved model file with SHA-256 only on explicit verification;
- persist a local verification receipt outside packaged registry data;
- receipt may contain private local path/stat information because it is local state, but no public API/report may expose that path;
- receipt must bind digest to enough local file metadata to detect ordinary replacement and force re-verification;
- evidence-grade runs may offer `--verify-artifact` to recompute the digest before the run, avoiding blind reliance on stale cached receipts;
- a supplied/registry digest must be validated before use;
- directories/multi-file models require a separate deterministic manifest-hash design and must not be falsely treated as a single-file verified artifact.

Acceptance:

- verifying the current Nemotron GGUF produces a 64-char SHA-256 receipt;
- changing the file invalidates ordinary receipt reuse;
- `/v1/runtime/identity` can expose digest/key/fingerprint without local path;
- no background UI refresh triggers a 4+ GB hash.

Validation:

- temporary-file digest/receipt invalidation tests;
- privacy/path-leak tests;
- CLI behavior tests.

### ID-2 / HE-1 — Evidence-grade identity flow

Outcome: the same verified artifact identity reaches runtime identity, worker evidence and review compatibility.

Implementation requirements:

- one canonical artifact verification result feeds runtime/evidence descriptors;
- backend version + artifact digest + effective config + bounded hardware identity produce the fingerprint;
- reviewer refuses to pool reports whose digest/config/environment differs;
- `identity_grade=verified` requires actual strong digest evidence, never filename/size inference.

Acceptance:

- a verified Nemotron hardware report no longer fails review solely for `verified_identity_required`;
- public reports remain privacy-safe.

### HE-2 — Repeat representative hardware evidence

Procedure on the same Mac/config used for the first smoke:

- produce two independent reports of three complete cycles each;
- keep model/backend/config/procedure/environment identical;
- use verified artifact identity;
- run `local-llm evidence-review` with default conservative thresholds;
- retain positive, mixed, negative and inconclusive raw reports; never keep only favorable runs.

Acceptance:

- six complete windows are attempted;
- reviewer output is determined by the actual data;
- `automatic_eviction_recommendation` remains `not_provided` and `production_safety_claim` remains false regardless of observation consistency.

### RES-1 — Resource policy deterministic coverage

Outcome: the resource manager is proven at the product API/runtime boundary, not only as isolated accounting logic.

Cases:

- disabled policy stays `UNKNOWN`/non-enforcing and does not fabricate budget;
- sufficient configured limit admits initial load, creates reservation, commits accounted bytes and reports remaining budget;
- unload releases committed accounting and preserves health/zero-resident behavior;
- insufficient configured limit rejects before expensive backend load;
- reload peak-overlap rejection preserves the existing resident runtime;
- headroom participates in usable budget exactly once.

Acceptance:

- tests assert backend loader is not called after admission rejection;
- `/api/v1/resources` matches internal accounting for each lifecycle transition.

### RES-2 — Bounded real-device resource smoke

Procedure:

1. start with a safe budget comfortably above the Nemotron estimate, e.g. explicit memory limit + headroom;
2. verify `/api/v1/resources` is `configured` and the model becomes committed;
3. run one inference;
4. unload the model and confirm committed/reserved bytes return to zero while `/health` remains green;
5. restart with a deliberately insufficient configured budget that is still safe for the host and verify rejection happens before model load;
6. do not induce OS critical pressure or uncontrolled OOM.

Acceptance:

- admit/account/release/reject behavior matches deterministic tests;
- no automatic eviction occurs.

## Integration points

- **Thinking -> structured output:** SO-2 consumes the reasoning boundary from TH-3; it must not invent a second parser.
- **Thinking -> evaluation:** EV-2 consumes effective thinking semantics from TH-1/TH-2; it must not guess backend support.
- **Canonical request -> evaluation:** EV-1 consumes `PreparedBackendRequest`; evaluation must not own a parallel kwargs schema.
- **Artifact identity -> runtime/evidence:** ID-2 feeds both runtime fingerprints and hardware descriptors; no separate evidence-only digest format.
- **Hardware evidence -> policy:** HE-2 informs future pressure-policy decisions but cannot directly enable automatic eviction.
- **Resource policy -> pressure policy:** RES-2 proves configured accounting only; it is not a pressure/eviction safety test.

## Parallel execution plan

### Wave A — contract and deterministic foundations

Run in parallel:

- `TH-1`
- `SO-1`
- `EV-1`
- `ID-1`
- `RES-1`

Write-conflict note: TH-1 and SO-1 may both touch canonical contract tests; coordinate ownership by keeping TH-1 on capability/request policy and SO-1 on output/result validation. EV-1 owns evaluation modules. ID-1 owns artifact identity/CLI. RES-1 owns resource-policy/runtime integration tests.

### Wave B — implementation

After the relevant Wave A contracts merge:

- `TH-2` and `TH-3` run in parallel;
- `ID-2` runs independently;
- EV-1 can already merge independently if its parity tests do not depend on the final thinking implementation.

### Wave C — convergence

- `TH-4` after TH-2;
- `SO-2` after TH-2 + TH-3 + SO-1;
- `EV-2` after EV-1 + TH-2;
- `HE-1` after ID-2.

### Wave D — representative evidence

Run in parallel on the real device after code convergence:

- `EV-3`
- `HE-2`
- `RES-2`

These produce evidence, not automatic product claims.

### Wave E — closure

- `DOC-1`
- `REL-1`

## Suggested branch / PR boundaries

Keep `dev` as the integration branch. Prefer bounded branches that can be reviewed and merged independently:

- `feat/thinking-contract`
- `fix/llama-cpp-thinking-control`
- `fix/streaming-reasoning-boundary`
- `feat/structured-output-contract`
- `refactor/evaluation-canonical-request`
- `feat/evaluation-reasoning-profile`
- `feat/artifact-verification`
- `test/resource-policy-integration`
- final docs/evidence sync branch

A branch that changes a shared contract must merge before dependent adapter/UI branches are rebased for final validation.

## Cumulative acceptance matrix

| Area | Required evidence before DONE |
| --- | --- |
| Interactive chat | real Nemotron OFF/ON smoke + deterministic adapter tests |
| Hidden reasoning | adversarial chunk-boundary stream tests + manual UI confirmation |
| Structured output | valid JSON final content, typed malformed-output case, stream aggregate test |
| Evaluation | canonical parity tests, explicit reasoning profile, repeat 10-sample seed-0 run |
| Runtime identity | explicit SHA verification, path-free public fingerprint |
| Reclamation | two verified compatible 3-cycle reports + reviewer output, no safety promotion |
| Resource manager | integration tests + real admit/account/release/reject smoke |
| CI | Python 3.10/3.11/3.12 deterministic suite + blocking Ruff correctness gate |
| Docs | current-state, roadmap, API/config docs agree with actual integrated behavior |

## Validation ladder

During each slice use the narrowest relevant test first, then expand before merge:

```bash
uv sync --all-extras
uv run pytest <targeted tests> -v --tb=short
uv run ruff check src/ tests/ --select E9,F63,F7,F82
```

Before a dependent convergence merge:

```bash
uv run pytest tests/ -v --tb=short
```

Representative device checks must be executed outside CI and retained separately from deterministic test results.

## Stop conditions

Stop and surface the issue rather than improvising if:

- the effective backend cannot prove switchable thinking for a runtime currently advertised as switchable;
- structured output would require silent semantic repair to become valid JSON;
- evaluation cannot consume canonical backend preparation without changing supported interactive semantics;
- artifact verification would expose private paths in public API/evidence;
- a resource-policy test would require uncontrolled host memory pressure;
- a hardware report differs in artifact/config/environment and the reviewer would otherwise pool it;
- CI is green but the required claim depends on real-device evidence that has not been run.

## Durable documentation destinations

- `docs/current-state.md`: only current integrated/blocker/next operational truth.
- `docs/roadmap.md`: milestone sequencing after this workstream changes release readiness.
- `docs/runtime-identity-api.md`: verified artifact/fingerprint behavior.
- `docs/http-api-reference.md`: thinking/structured-output public request/response semantics.
- `docs/configuration-reference.md`: new verification/resource controls if user configurable.
- `docs/hardware-evidence-matrix.md`: representative procedure/results references, never invented outcomes.
- tests/contracts: executable truth for request translation, output boundary, identity and accounting.

## Completion

This workstream is complete only when:

1. thinking execution and exposure semantics are truthful and tested;
2. structured output contains only the final structured application answer;
3. evaluation uses canonical backend preparation and records effective reasoning policy;
4. the exact local model artifact can be verified explicitly and fingerprinted without path leakage;
5. the representative Apple Silicon reclamation run is repeated with verified identity and reviewed without safety promotion;
6. configured resource admission/accounting/release/rejection is tested deterministically and on the real device;
7. cumulative CI is green;
8. durable docs agree with the integrated code and retained evidence.

Then update `docs/current-state.md`, transfer durable behavior to the owning docs, and delete this workstream by default. Git history remains the implementation-history source.

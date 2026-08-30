# Runtime ownership and resource governor

Status: active
Owner: runtime-and-platform
Read when: coordinating lifecycle ownership, llama.cpp modernization, memory envelopes, multi-model admission or eviction evidence
Last reviewed: 2026-08-30

## Goal

Evolve Local LLM Server into a resource-safe multi-model control plane without duplicating backend ownership or promoting deterministic tests into hardware reclamation claims.

The control plane remains the canonical owner of residency, admission, lifecycle and resource policy. Backend engines own model execution and backend-native batching/caches. Automatic pressure eviction remains disabled until representative evidence justifies it.

## Invariants

- `STOPPED` is declared only after the owned backend teardown succeeds.
- Resource accounting is released only after the corresponding owner is stopped; failed teardown stays accounted and diagnosable.
- Active runtime leases are never evicted as an admission side effect.
- Configured, resident, default, pinned and failed states remain distinct.
- Multi-model concurrency is bounded by both per-runtime and global resource policy.
- Estimated, configured and observed memory remain distinct; unavailable is never reported as zero.
- llama.cpp/backend versions used for evidence are attributable to an exact executable/package identity.
- Hosted CI does not prove Apple unified-memory reclamation, thermal safety or real-model performance.

## Work graph

| ID | Work | Depends on | State | Exit evidence |
| --- | --- | --- | --- | --- |
| RRG-1 | deterministic runtime ownership and bounded lifecycle | — | DONE | strong remote preflight green on PR #154; teardown/failed-cleanup/reload/shutdown contracts accepted |
| RRG-2 | llama.cpp server modernization and backend identity contract | RRG-1 | DONE | strong remote preflight green on PR #156; attributable v0.3 server adapter/config/identity contracts accepted |
| RRG-3 | resident + transient memory envelope | RRG-1, RRG-2 | DONE | strong remote preflight green on PR #157; shared resident/transient budget, stream/cancel and ASR request accounting accepted |
| RRG-4 | global multi-model execution governor | RRG-3 | DONE | strong remote preflight green on PR #158; global bound, runtime fairness, cancellation/deadline, streaming, ASR and evaluation contracts accepted |
| RRG-5 | representative-device reclamation and pressure policy review | RRG-1..RRG-4 | ACTIVE | deterministic runner/reviewer tooling plus one-command campaign orchestration; still requires two compatible real-Mac reports; automatic eviction stays disabled |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

## RRG-1 — deterministic ownership

Strengthen the existing manager/engine boundary before adding more policy:

- explicit native teardown for in-process llama-cpp-python;
- `DRAINING -> STOPPING -> STOPPED` lifecycle with `FAILED` on teardown failure;
- unload/reload must not remove or replace canonical runtime ownership before teardown succeeds;
- post-load admission failure must close the newly allocated engine before releasing its reservation;
- shutdown drain is bounded; a runtime that still has active leases remains owned/accounted as `FAILED` instead of being torn down concurrently;
- failed teardown remains visible and accounted for retry/diagnostics.

This slice does not claim host-memory reclamation.

## RRG-2 — llama.cpp modernization

Target the latest validated stable llama.cpp server line through an attributable binary identity rather than opportunistically relying on an unknown LM Studio/PATH revision. Add modern server configuration only where Local LLM Server remains the policy owner: context/batch/threads, backend-native parallel slots, KV/cache controls, fit/headroom controls and observability. Do not introduce the upstream multi-model router as a second residency/LRU owner without a separate ADR and comparative evidence.

The current target is the upstream `v0.3.0` stable release, whose published binary build is `b10621` at commit `c1d0e7a004015f23bc0233470b747b596f29b264`. Local LLM Server does not silently download or replace the external specialist runtime. It validates the selected executable, retains exact build/commit identity, uses the modern server profile only at/above that feature floor, and requires an explicit escape hatch for older/unparseable legacy binaries.

Within one managed server runtime, Local LLM Server owns the admitted request count and maps it to llama.cpp `--parallel` slots. llama.cpp owns continuous batching and the runtime-local unified KV/cache implementation. The control plane does not adopt llama.cpp multi-model autoload/router ownership.

## RRG-3 — memory envelope

Replace artifact-size-only admission with an explicit runtime envelope containing model weights, fixed backend overhead, KV/context budget, prompt/cache budget, multimodal projector cost and safety margin. Add separate transient request reservations so two individually safe resident models cannot overcommit memory during simultaneous inference.

Resident runtimes and active requests share the same `ResourceManager` budget; reservation kind identifies ownership but does not create a second pool. A resident total override remains supported for deployments that already have a calibrated estimate. Otherwise the control plane adds only attributable components: configured byte budgets, registry/local artifact size, configured llama-server prompt-cache RAM and local projector size. Missing backend/context/safety evidence remains explicitly unavailable while known components form a lower-bound estimate; `ctx_size` alone is never converted into guessed KV bytes.

Transient request estimates are independently configurable as a total override or as base/input/output/safety components. Queue wait does not reserve transient memory. Once admitted to execution, chat/vision streams hold their reservation through route failure, cancellation or the final body byte; first-class resident ASR uses the same transient owner through backend execution. Supported product policy evidence exposes path-free resident/transient accounting and resident-envelope completeness. None of these configured estimates is a claim about observed RSS, Apple unified memory or accelerator reclamation.

## RRG-4 — global governor

Keep backend-native continuous batching inside each runtime while Local LLM Server owns cross-runtime admission. The governor must bound aggregate compute use, preserve per-runtime scheduler semantics, propagate pre-execution cancellation/deadlines and avoid starvation. Memory remains owned by the shared RRG-3 `ResourceManager`; the governor does not create a second memory pool.

Global execution admission is explicit rather than silently changing server capacity. `LOCAL_LLM_GLOBAL_MAX_RUNNING` and `LOCAL_LLM_GLOBAL_QUEUE_CAPACITY` must be configured together. The existing per-runtime FIFO queue remains independently optional. When both layers are enabled, one pre-execution deadline spans per-runtime and global waits; a request that is only waiting for global capacity does not reserve transient memory.

Fairness is runtime round-robin with FIFO order inside each runtime's global waiters. `max_concurrent_requests` is mirrored only as an eligibility bound so a runtime cannot consume global slots that would immediately block on its final semaphore; the runtime semaphore remains the canonical per-runtime safeguard. Chat/vision, first-class resident ASR and evaluation samples share the same attached governor. Evaluation samples also use the RRG-3 transient reservation before their runtime lease, so benchmarks do not bypass the shared execution or memory owners. Streaming chat/vision retains its global permit through the final body byte. Public scheduler evidence is aggregate and path/content-free. This slice does not claim that an already-running in-process backend can always be interrupted.

## RRG-5 — real environment evidence

The deterministic tooling now includes `scripts/run_device_evidence_campaign.py`, which orchestrates the already-owned TH-E1, EV-3, HE-2 and RES-2 procedures plus repeated RRG-5 in one representative-device command. The orchestrator owns only sequencing, the temporary loopback server lifecycle, per-phase classification and the bounded campaign summary; individual evidence modules and their reviewers remain authoritative for thresholds and semantics. `docs/device-evidence-campaign.md` documents the one-command path, while `docs/device-evidence-runbook.md` remains the manual diagnostic source of truth.

The target procedure must cover:

- two distinct verified model artifacts resident at the same time;
- two cross-runtime HTTP requests admitted concurrently under the RRG-4 global governor;
- exact configured resident/transient accounting peaks from the shared `ResourceManager`, kept semantically separate from OS memory observations;
- macOS available-memory and current-process RSS sampling, plus aggregate RSS for owned backend subprocesses when the engine exposes owned PIDs;
- dry-run pressure-policy evaluation only; no pressure-triggered unload;
- repeated load/infer/unload cycles with zero configured accounting after unload;
- a bounded shutdown while one runtime lease remains active, proving fail-conservative retained ownership/accounting followed by successful shutdown retry;
- two compatible attributable reports and a conservative repetition reviewer that preserves raw post-stop deltas without an automatic-eviction or reclamation-safety recommendation.

The campaign differentiates `PASS`, `FAIL` and `INCONCLUSIVE`: host-memory safety refusals and missing representative preconditions do not become fake product failures, while reached lifecycle/accounting/API invariant violations do. The campaign summary is path/content/PID-free and is persisted after every phase; raw evaluation/server diagnostics remain machine-local evidence and are not meant to be committed wholesale.

The tooling may be merged after deterministic STRONG preflight, but RRG-5 remains `ACTIVE` until the required representative Apple Silicon reports exist. Negative or inconclusive memory behavior remains evidence and cannot be converted into a pass by lowering margins or redefining a zero baseline.

## Closure

Move durable architecture/contracts into their owning documents as each slice lands. Delete this workstream after RRG-1..RRG-5 are either completed or explicitly moved to a replacement tracked plan; Git history retains chronology.

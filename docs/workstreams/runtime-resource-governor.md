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
| RRG-1 | deterministic runtime ownership and bounded lifecycle | — | ACTIVE | teardown/failed-cleanup/reload/shutdown contracts green |
| RRG-2 | llama.cpp server modernization and backend identity contract | RRG-1 | READY | version-attributable server adapter + compatibility tests |
| RRG-3 | resident + transient memory envelope | RRG-1, RRG-2 | READY | deterministic budget arithmetic + request reservation tests |
| RRG-4 | global multi-model execution governor | RRG-3 | READY | fairness/admission/cancellation tests across runtimes |
| RRG-5 | representative-device reclamation and pressure policy review | RRG-1..RRG-4 | BLOCKED | target-hardware evidence; no automatic eviction before acceptance |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

## RRG-1 — deterministic ownership

Strengthen the existing manager/engine boundary before adding more policy:

- explicit native teardown for in-process llama-cpp-python;
- `DRAINING -> STOPPING -> STOPPED` lifecycle with `FAILED` on teardown failure;
- unload/reload must not remove or replace canonical runtime ownership before teardown succeeds;
- post-load admission failure must close the newly allocated engine before releasing its reservation;
- shutdown drain is bounded and backend stop is attempted even when requests fail to drain;
- failed teardown remains visible and accounted for retry/diagnostics.

This slice does not claim host-memory reclamation.

## RRG-2 — llama.cpp modernization

Target the latest validated stable llama.cpp server line through an attributable binary identity rather than opportunistically relying on an unknown LM Studio/PATH revision. Add modern server configuration only where Local LLM Server remains the policy owner: context/batch/threads, backend-native parallel slots, KV/cache controls, fit/headroom controls and observability. Do not introduce the upstream multi-model router as a second residency/LRU owner without a separate ADR and comparative evidence.

## RRG-3 — memory envelope

Replace artifact-size-only admission with an explicit runtime envelope containing model weights, fixed backend overhead, KV/context budget, prompt/cache budget, multimodal projector cost and safety margin. Add separate transient request reservations so two individually safe resident models cannot overcommit memory during simultaneous inference.

## RRG-4 — global governor

Keep backend-native continuous batching inside each runtime while Local LLM Server owns cross-runtime admission. The governor must bound aggregate compute/memory use, preserve per-runtime scheduler semantics, propagate cancellation/deadlines and avoid starvation.

## RRG-5 — real environment evidence

Extend the existing target-Mac campaigns to cover repeated multi-model load/infer/unload, concurrent request pressure, shutdown under load and post-stop memory observations. Negative or inconclusive reclamation evidence remains evidence and cannot be converted into an automatic-eviction pass by loosening thresholds.

## Closure

Move durable architecture/contracts into their owning documents as each slice lands. Delete this workstream after RRG-1..RRG-5 are either completed or explicitly moved to a replacement tracked plan; Git history retains chronology.

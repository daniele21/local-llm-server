# Critical lifecycle failure contracts

Status: active
Owner: runtime-and-platform
Canonical matrix: `.engineering/lifecycle-contracts.json`
Read when: changing startup/admission, request scheduling, cancellation, worker transport or shutdown ownership
Last reviewed: 2026-08-30

## Purpose

L1 requires critical lifecycle behavior to remain explicit across success and failure paths. The repository contains deterministic behavioral tests for the important owners; the machine-readable matrix makes those claims discoverable and prevents a refactor from silently deleting the evidence while normal CI still looks broadly healthy.

`python3 scripts/verify_lifecycle_contracts.py` checks that every contract has a unique ID, a supported lifecycle phase, a concrete `pytest file::function` node and coverage for startup failure, timeout, cancellation, shutdown, process shutdown and dependency failure. Normal CI executes the referenced tests as part of the full test suite.

## Runtime ownership invariant

For a dynamically resident engine, logical state and resource accounting follow backend ownership rather than preceding it:

```text
READY -> DRAINING -> STOPPING -> STOPPED
                    \\-> FAILED
```

`STOPPED` means the owning backend teardown operation completed successfully. The associated resource reservation is released only after that teardown succeeds. A backend close failure therefore keeps the runtime tracked as `FAILED` and keeps its reservation accounted so teardown can be retried or diagnosed.

A failed load/reload that already allocated a backend follows the same rule. If cleanup of the unpublished engine fails, the manager retains an internal cleanup owner and its reservation until shutdown/retry succeeds rather than fabricating a free-resource state.

Shutdown drain is bounded. If an active lease does not drain within the configured shutdown timeout, that runtime remains owned as `FAILED`; the manager does not concurrently tear down an in-use in-process engine and does not report it as stopped.

## Covered invariants

The current matrix establishes, at deterministic boundaries:

- resource admission rejects before backend allocation when capacity cannot be satisfied;
- backend initialization failure rolls back provisional resource accounting;
- unload stops an owned engine and only then releases committed accounting;
- failed backend teardown retains runtime ownership and resource accounting until retry;
- bounded shutdown does not fabricate `STOPPED` for a runtime whose active lease did not drain;
- queue timeout does not enter the backend route;
- queued cancellation does not consume a future runtime slot;
- active cancellation does not free capacity before the running owner releases it;
- streaming request ownership is retained until iterator completion and then pruned;
- application shutdown notification precedes Uvicorn exit and is idempotent;
- malformed worker protocol responses cannot leave the owned transport falsely ready;
- worker stop clears the owned process handle.

## In-process llama.cpp boundary

`LlamaCppEngine.close()` explicitly delegates to `llama-cpp-python`'s native `Llama.close()` owner. This closes the library-owned model/context resources deterministically at the Python/backend boundary. It is intentionally not promoted into a host-memory or Apple unified-memory reclamation claim; representative-device evidence remains the owner for that observation.

## Non-claims

This matrix does not promote worker-backed streaming/cancellation to a supported product capability. Explicit backend close does not establish RSS/unified-memory return-to-baseline. It does not establish hardware reclamation success and does not justify automatic pressure eviction. Those claims remain governed by their explicit capability flags and representative-device evidence.

## Change rule

When a critical lifecycle owner changes, update the behavior test first or alongside the implementation, then update the matrix only if ownership/claim semantics changed. Do not point a contract at a weak existence test merely to satisfy the validator; the referenced test must prove the stated cleanup/recovery invariant.

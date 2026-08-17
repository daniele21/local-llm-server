# Critical lifecycle failure contracts

Status: active
Owner: runtime-and-platform
Canonical matrix: `.engineering/lifecycle-contracts.json`
Read when: changing startup/admission, request scheduling, cancellation, worker transport or shutdown ownership
Last reviewed: 2026-08-17

## Purpose

L1 requires critical lifecycle behavior to remain explicit across success and failure paths. The repository already contains deterministic behavioral tests for the important owners; the machine-readable matrix makes those claims discoverable and prevents a refactor from silently deleting the evidence while normal CI still looks broadly healthy.

`python3 scripts/verify_lifecycle_contracts.py` checks that every contract has a unique ID, a supported lifecycle phase, a concrete `pytest file::function` node and coverage for startup failure, timeout, cancellation, shutdown, process shutdown and dependency failure. Normal CI executes the referenced tests as part of the full test suite.

## Covered invariants

The current matrix establishes, at deterministic boundaries:

- resource admission rejects before backend allocation when capacity cannot be satisfied;
- backend initialization failure rolls back provisional resource accounting;
- unload stops an owned engine and releases committed accounting;
- queue timeout does not enter the backend route;
- queued cancellation does not consume a future runtime slot;
- active cancellation does not free capacity before the running owner releases it;
- streaming request ownership is retained until iterator completion and then pruned;
- application shutdown notification precedes Uvicorn exit and is idempotent;
- malformed worker protocol responses cannot leave the owned transport falsely ready;
- worker stop clears the owned process handle.

## Non-claims

This matrix does not promote worker-backed streaming/cancellation to a supported product capability. It does not establish hardware reclamation success and does not justify automatic pressure eviction. Those claims remain governed by their explicit capability flags and representative-device evidence.

## Change rule

When a critical lifecycle owner changes, update the behavior test first or alongside the implementation, then update the matrix only if ownership/claim semantics changed. Do not point a contract at a weak existence test merely to satisfy the validator; the referenced test must prove the stated cleanup/recovery invariant.

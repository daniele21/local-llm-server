# Fault-injection contract

Status: active
Owner: runtime-and-platform
Canonical scope: current.fault-injection
Last reviewed: 2026-08-17

L2 requires important lifecycle failures to have explicit injected evidence and a recovery invariant. `.engineering/fault-injection.json` maps each fault to an exact pytest node; `scripts/verify_fault_injection.py` fails when a required domain or concrete test disappears.

Covered domains are resource admission, worker lifecycle, persisted-state integrity, pressure policy, request admission and request lifecycle. The evidence includes backend-load rollback, rejected reload overlap, failed worker prepare/exercise cleanup, tampered restore refusal, pressure hysteresis/unknown evidence, queued timeout and streaming disconnect lease release.

This matrix composes existing behavioral tests rather than duplicating their implementation. It does not claim representative-hardware pressure eviction safety, worker streaming cancellation support or native-memory reclamation after every injected failure.

Shared Repository Health integration remains L2-10.

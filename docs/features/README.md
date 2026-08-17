# Feature documentation

Status: active
Document type: documentation-governance
Owner: repository
Canonical scope: documentation.feature-routing
Read when: deciding where durable product behavior without a better API/operations owner should live
Last reviewed: 2026-08-17

This directory contains independently readable **current feature behavior** that deserves a durable owner but does not belong more naturally in an API reference, configuration guide, security policy or architecture document.

Feature documents describe what the integrated product does, boundaries/non-goals and evidence classes. They do not track branch/PR progress.

Use `docs/workstreams/` only for active bounded implementation coordination. When a workstream is complete, move any still-useful behavior/decision to the appropriate durable owner and delete the workstream by default.

Current feature documents:

- [`product-acceptance.md`](product-acceptance.md) — deterministic Studio/product browser acceptance and its boundary relative to real-runtime/device evidence.

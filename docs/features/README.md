# Feature documentation

Status: active
Document type: documentation-governance
Owner: repository
Canonical scope: documentation.feature-routing
Read when: deciding where durable product behavior without a better API/operations owner should live
Last reviewed: 2026-08-30

This directory contains independently readable **current feature behavior** that deserves a durable owner but does not belong more naturally in an API reference, configuration guide, security policy or architecture document.

Feature documents describe what the integrated product does, boundaries/non-goals and evidence classes. They do not track branch/PR progress.

When a change alters durable behavior already described by a feature document, update that owner in the same change. Create a new feature document only when the behavior is non-obvious, independently useful and not sufficiently discoverable from public contracts, operational references, tests, code or architecture. Do not create one file per small feature.

Use `docs/workstreams/` only for active bounded implementation coordination. When a workstream is complete, move any still-useful behavior/decision to the appropriate durable owner and delete the workstream by default.

Current feature documents:

- [`product-acceptance.md`](product-acceptance.md) — deterministic Studio/product browser acceptance and its boundary relative to real-runtime/device evidence.

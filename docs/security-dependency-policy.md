# Dependency and supply-chain security policy

Status: active
Owner: repository engineering
Read when: changing dependencies, security workflows or vulnerability exceptions
Last reviewed: 2026-08-17

## Scope

This policy covers Python runtime dependencies from `uv.lock` and Node tooling from `package-lock.json`. It complements `SECURITY.md`; it does not replace runtime trust-boundary policy.

## Blocking audit

`.github/workflows/security.yml` runs on pull requests, pushes to canonical branches, manual dispatch and weekly schedule.

Python runtime dependencies are exported from the committed `uv.lock` with local project packages omitted, then audited with the exactly pinned `pip-audit 2.10.1`. The audit runs with dependency resolution disabled so the security result describes the committed dependency graph rather than a newly solved graph.

Node dependencies are installed with `npm ci` and fail at `high` or `critical` advisory severity through `npm audit --audit-level=high`.

## Vulnerability handling

The default policy is **no ignored vulnerability IDs**. A blocking advisory is resolved by upgrading/replacing/removing the dependency or by narrowing/removing the affected feature.

A temporary exception is allowed only when all of the following are recorded in the same change that introduces the ignore:

- vulnerability/advisory ID;
- affected package/version and reachable product surface;
- why remediation is not currently possible;
- compensating control;
- owner;
- review/expiry date;
- tracking issue or workstream reference.

Exceptions must be time-bounded. An undocumented or non-expiring ignore is not acceptable.

## Dependency updates

Automated dependency update proposals are enabled for Python and npm manifests. Updates remain normal reviewed changes and must pass CI, Repository Health and Security Audit. Automated update tooling must not bypass lockfile review or runtime/backend evidence requirements.

## What this audit does not prove

Known-vulnerability auditing does not prove a package is non-malicious, does not statically analyze project code and does not prove native/shared-library security below the Python package metadata boundary. Backend/runtime and model-source trust decisions remain governed by `SECURITY.md` and representative runtime validation.

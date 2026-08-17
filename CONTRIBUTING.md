# Contributing

## Change scope

Prefer the smallest coherent change that preserves repository invariants. Inspect the owning boundary, direct consumers and tests before changing shared contracts. Use a workstream only when dependency/state coordination adds real value.

## Canonical commands

`.engineering/commands.json` is the canonical repository-level mapping for `setup`, `doctor`, `dev`, `check`, `test`, `e2e`, `build`, `smoke`, `package`, `stop` and `clean`. Keep native tooling behind those intents; do not add undocumented parallel command paths.

## Validation

Run the narrowest useful checks while iterating, then the required gates for the changed blast radius. Do not suppress failures or weaken a gate simply to make a change green.

Repository health:

```bash
python3 scripts/verify_repository.py
python3 scripts/verify_operations.py
python3 scripts/verify_docs.py
python3 scripts/verify_agent_context.py
```

Use `.engineering/commands.json` for actual project `check`/`test`/`e2e`/`build`/`smoke` commands.

`test`, browser `e2e`, real-runtime smoke and representative-device evidence are deliberately different evidence classes. Hosted CI must not be described as proof of real model quality, Apple Silicon memory behavior, throughput, thermal behavior or reclamation.

When E2E runs, verify cleanup of project-owned server/listener/browser/temp/evaluation state. Failure traces/screenshots/logs must remain bounded and privacy-safe.

When build/runtime/package behavior changes, validate applicable operating invariants: unique build identity, immutable promoted artifacts, manifest/checksum/build delta, bounded retention, graceful stop and zero project-owned residue.

## Dependencies and architecture

Use committed dependency state in CI. Avoid dynamic dependency versions and speculative abstractions. New dependencies must have a concrete owner/problem and must not duplicate an existing source of truth.

Preserve Local LLM Server's backend-neutral product contracts. Do not leak backend-specific assumptions into application-facing APIs when they belong in adapters/capability metadata.

## Pull requests

Keep PRs focused. Describe what changed, why, user/developer impact, invariants/risks, lifecycle implications and exact validation executed. Distinguish deterministic tests, E2E, smoke/manual and device/hardware evidence.

Canonical development/release branches should use pull requests and required checks. External branch-protection state that has not been verified must be recorded as pending rather than assumed.

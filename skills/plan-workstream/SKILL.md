# plan-workstream

Use when a change needs explicit dependency/state coordination across multiple slices or owners. Do not create a workstream for a small local change.

1. Read `AGENTS.md`, `docs/current-state.md` and `docs/workstreams/README.md`.
2. Identify the canonical owner, invariants, shared files and evidence boundary.
3. Define bounded slices with IDs, dependencies, allowed parallel lanes, owned paths, acceptance and validation.
4. Keep one active plan for the workstream; do not create separate progress/status files.
5. Mark hardware/external configuration evidence pending unless actually verified.
6. Prefer branches/PRs that align with non-conflicting ownership boundaries.
7. On completion, transfer durable truth to its canonical owner and use `finalize-workstream`.

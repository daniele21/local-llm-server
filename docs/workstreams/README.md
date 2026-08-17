# Active workstreams

This directory contains only substantial active work that needs explicit dependency, ownership and state coordination.

Use the `repo-template-sw` lifecycle:

- one workstream file owns both plan and progress;
- use only `READY`, `ACTIVE`, `BLOCKED`, `DONE` for executable slices;
- parallel work must have explicit non-conflicting write boundaries or a defined integration point;
- durable architecture/feature behavior belongs in its owning documentation and executable tests, not permanently in the workstream plan;
- when all acceptance criteria are satisfied, transfer durable truth, update `docs/current-state.md`, and delete the completed workstream by default.

Do not create separate plan/progress/status files for the same workstream. Git history owns implementation history.

## Active

- [`runtime-correctness-evidence-hardening.md`](runtime-correctness-evidence-hardening.md) — thinking/structured-output correctness, evaluation canonicalization, verified artifact identity, resource-policy validation and representative hardware evidence.
- [`repo-template-sw-adoption.md`](repo-template-sw-adoption.md) — baseline metadata, canonical commands, agent routing, reproducible CI, artifact lifecycle, zero-residue E2E and documentation/security governance.

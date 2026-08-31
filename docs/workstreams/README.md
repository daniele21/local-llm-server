# Active workstreams

This directory contains only substantial active work that needs explicit dependency, ownership and state coordination.

Use the `repo-template-sw` lifecycle:

- one workstream file owns both plan and progress;
- use only `READY`, `ACTIVE`, `BLOCKED`, `DONE` for executable slices;
- parallel work must have explicit non-conflicting write boundaries or a defined integration point;
- durable behavior belongs in owning docs/tests, not permanently in workstream plans;
- when acceptance is satisfied, transfer durable truth, update `docs/current-state.md`, and delete the completed workstream by default.

Do not create separate plan/progress/status files for the same workstream. Git history owns implementation history.

## Active

No active workstreams. Full L2 repository, representative-hardware and bounded human product-experience evidence are accepted for the current candidate; future workstreams should be opened only for new bounded capability or evidence objectives.

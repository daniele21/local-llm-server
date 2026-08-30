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

- [`api-blackbox-e2e-hardening.md`](api-blackbox-e2e-hardening.md) — external application-to-HTTP acceptance coverage and exact-head validation.
- [`runtime-resource-governor.md`](runtime-resource-governor.md) — deterministic backend ownership, llama.cpp modernization, memory envelopes, global multi-model admission and representative pressure/reclamation evidence.
- [`runtime-correctness-evidence-hardening.md`](runtime-correctness-evidence-hardening.md) — thinking/structured-output correctness, evaluation canonicalization, verified artifact identity, resource-policy validation and representative hardware evidence.
- [`l2-reference-grade.md`](l2-reference-grade.md) — repository-side L2 is accepted; full engineering L2 remains gated by retained representative Apple Silicon/model/backend evidence.
- [`v040-product-ui-l2.md`](v040-product-ui-l2.md) — explicit `repo-template-sw 0.4.0` migration, `product-ui` L2 guardrails, design-system drift control and real manual product-experience evidence boundary.

# finalize-workstream

Use when every slice in an active workstream is complete or explicitly dispositioned.

1. Verify executable acceptance and required evidence; do not upgrade pending hardware/external checks.
2. Assess documentation impact from the final observable behavior using `docs/README.md` when ownership is unclear.
3. Transfer durable current truth to the appropriate owner: project purpose/audience/outcome -> README identity; setup/run/configuration/public usage/examples -> README usage; architecture -> `docs/architecture.md`; API/config/runtime behavior -> its existing operational reference; durable non-obvious feature behavior -> existing/new `docs/features/` owner; security/trust/data lifecycle -> security/architecture/feature owner; material rationale -> ADR; executable invariants -> tests/tooling.
4. Treat README identity and usage independently. Do not rewrite stable mission/positioning because implementation or commands changed; do update usage when the old path becomes incomplete, wrong or misleading.
5. Keep `docs/current-state.md` short and update only the affected operational truth.
6. Remove the workstream from `docs/workstreams/README.md`.
7. Delete the completed workstream file by default. Archive only for an independent audit/regulatory/release-history reason.
8. Search for stale links, setup/run/configuration examples and existing feature docs affected by the completed behavior; update them before claiming documentation completion.
9. Run documentation/context/repository validators after the transfer.
10. Let Git history preserve implementation chronology instead of keeping duplicate completed plans.

Completion requires that a future maintainer can understand current behavior without the plan and that a new user/developer can follow the current documented usage path. Existing feature docs must agree with the implementation they describe.

# finalize-workstream

Use when every slice in an active workstream is complete or explicitly dispositioned.

1. Verify executable acceptance and required evidence; do not upgrade pending hardware/external checks.
2. Move durable current behavior to the owning architecture/API/feature/security/operations document.
3. Keep `docs/current-state.md` short and update only the affected operational truth.
4. Remove the workstream from `docs/workstreams/README.md`.
5. Delete the completed workstream file by default. Archive only for an independent audit/regulatory/release-history reason.
6. Run documentation/context/repository validators after the transfer.
7. Let Git history preserve implementation chronology instead of keeping duplicate completed plans.

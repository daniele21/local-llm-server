# structured-change

Use for meaningful changes to shared product/runtime/data contracts.

Before editing:

1. Read the owning implementation, direct consumers, fakes and nearby tests.
2. State the contract/invariant being changed and the smallest coherent scope.
3. Identify compatibility, resource, cleanup, privacy and evidence implications.
4. Avoid speculative abstractions and backend-specific leakage into public contracts.

After editing:

1. Re-read the changed owner and callers for contract drift.
2. Add or update deterministic tests at the lowest sufficient boundary.
3. Escalate to E2E only when a complete assembled workflow claim is affected.
4. Use representative-device evidence only for hardware-dependent claims.
5. Update only the canonical durable document whose current behavior or decision changed.

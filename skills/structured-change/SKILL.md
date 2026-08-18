# structured-change

Use for meaningful changes to shared product/runtime/data contracts and user-facing experience.

Before editing:

1. Read the owning implementation, direct consumers, fakes and nearby tests.
2. State the contract/invariant being changed and the smallest coherent scope.
3. Identify compatibility, resource, cleanup, privacy and evidence implications.
4. Avoid speculative abstractions and backend-specific leakage into public contracts.
5. When `product-ui` is adopted and the UI is affected, read `design/ux-contract.json`, `design/brand-kit.json` and the canonical design/component owner before adding a visual or interaction pattern.
6. For meaningful UI changes, evaluate the user task model, primary action hierarchy, progressive disclosure/cognitive load, critical states, recovery, accessibility, adaptive layout and evidence impact—not visual appearance alone.

After editing:

1. Re-read the changed owner and callers for contract drift.
2. Add or update deterministic tests at the lowest sufficient boundary.
3. Escalate to E2E only when a complete assembled workflow claim is affected; preserve bounded identity-bearing evidence and zero residue.
4. For UI changes, reuse the canonical semantic component/token owner and run product-experience/drift checks; do not create a parallel design system for convenience.
5. Use representative-device or representative-user/manual evidence only for claims that actually require it; unavailable evidence stays pending.
6. Update only the canonical durable document/design contract whose current behavior or decision changed.

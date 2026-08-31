# structured-change

Use for meaningful changes to shared product/runtime/data contracts, operational behavior and user-facing experience.

Before editing:

1. Read the owning implementation, direct consumers, fakes and nearby tests; identify one canonical owner.
2. State the invariant being changed and the smallest coherent scope. Resolve material product/contract ambiguity from repository evidence or the user instead of silently guessing.
3. Identify compatibility, resource, cleanup, privacy, persistence and evidence implications. No unbounded queue/cache/resource path and no cleanup without proven ownership.
4. Read `.engineering/commands.json` when setup/runtime/build/validation/package/cleanup can change; preserve canonical commands, artifact identity, immutable promotion and zero-residue lifecycle semantics.
5. Read `.engineering/e2e.json` when a complete workflow or environment-dependent claim can change. Do not promote fake/Linux/emulated evidence into Apple Silicon/model/hardware evidence.
6. When `product-ui` is adopted, read `design/ux-contract.json` and `design/brand-kit.json`. For meaningful UI work use `design-product-experience`: user outcome -> task model -> IA/journey -> hierarchy -> disclosure/defaults -> states/recovery -> adaptive/accessibility -> components -> motion -> polish -> evidence.
7. Avoid speculative abstractions, backend-specific leakage into public contracts and new visual/component patterns when an existing semantic owner can be extended.

After editing:

1. Re-read owner and direct consumers for contract drift; verify failure, cancellation, shutdown, restart and partial-initialization paths where material.
2. Add deterministic evidence at the lowest sufficient boundary, then use `validate-change` to expand by blast radius.
3. Use E2E only when the assembled outcome is part of the claim; select the cheapest sufficient declared environment and retain residual real-environment gaps explicitly.
4. Never delegate an automatable deterministic gate to the user merely because the current agent lacks the toolchain; `preflight-change` must classify it `REMOTE_AUTOMATED` and route repository automation.
5. Use representative-device/manual evidence only for claims that truly depend on hardware, protected authority or human judgment; unavailable evidence remains `PENDING`.
6. Update only the canonical durable document/design contract whose current truth changed.
7. Before publishing, run `preflight-change`: refresh target base, review the full diff, select the validation profile, classify executors, and require exact-head evidence.

# review-reference-quality

Use when adopting a template/reference implementation or comparing architecture/product quality against an external baseline.

1. Identify the exact reference source/version and applicable profiles.
2. Classify each relevant practice as `KEEP`, `ADAPT`, `ADD` or `N/A`; never copy placeholders or weaker defaults over stronger project behavior.
3. Verify reference claims against executable project behavior before declaring compliance.
4. Prefer project-native commands/frameworks over cosmetic uniformity.
5. Keep product semantics, privacy/evidence boundaries and hardware claims unchanged unless the change explicitly versions them.
6. When `product-ui` is adopted, inspect the actual UI plus `design/ux-contract.json` and `design/brand-kit.json`; assess task model, hierarchy/progressive disclosure, critical states/feedback/recovery, accessibility, adaptive behavior, design-system ownership and critical-journey evidence rather than grading screenshots alone.
7. Distinguish deterministic UI/E2E/accessibility evidence from manual assistive-technology and representative-user usability evidence. Missing human/device evidence remains pending, not passing.
8. Do not recommend a new design system or UI framework when the established semantic tokens/components can own the requirement; actively flag duplicated design ownership/drift.
9. Record unresolved gaps in the active workstream rather than hiding them behind placeholder commands or optimistic metadata.
10. Treat external repository settings/branch protection as pending unless authenticated state was inspected.

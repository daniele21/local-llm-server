# design-product-experience

Use for meaningful Local LLM Studio UX/UI changes. Keep local visual-only token/style edits proportional.

The decision order is mandatory for structural work:

`user outcome -> task model -> information architecture/critical journey -> information/action hierarchy -> progressive disclosure/defaults -> interactions/states/feedback/recovery -> adaptive/platform behavior -> accessibility -> design system/components -> motion -> visual polish/graphics -> validation`

1. Identify the technical user, job/decision and successful outcome before choosing components or layout.
2. Keep backend/runtime concepts hidden unless they create real value for this expert-facing product. Distinguish configured model, available artifact, resident runtime and route/default state truthfully.
3. Define the smallest coherent journey: entry -> decision -> action -> feedback -> outcome -> recovery/next step. Preserve context across control-plane surfaces.
4. Establish primary information/action first; keep destructive actions distinct and advanced diagnostics progressively disclosed.
5. Design reachable loading/empty/error/disabled/warning/partial states and actionable recovery before polish.
6. Preserve keyboard/focus semantics, non-color status meaning, text scaling, responsive priority and global reduced-motion behavior.
7. Reuse `src/local_llm_server/static/design-system.css` semantic tokens/components before creating new visual ownership.
8. Motion must serve feedback, continuity, state transition, progress, attention, hierarchy or meaningful completion; frequent technical interactions stay restrained.
9. Graphics are functional before decorative and must never be required to operate the product.
10. Map critical journeys to `.engineering/e2e.json`; deterministic browser E2E proves assembled orchestration, while Apple Silicon/model/backend/performance claims remain separate real-environment evidence.

Durable experience truth belongs in `design/ux-contract.json`, `design/brand-kit.json`, the canonical UI source or an owning feature document—not in permanent per-change design plans.

# Korgis brand and product-language guidelines

Status: active
Document type: design-guideline
Owner: web-product-and-docs
Canonical scope: design.brand
Read when: changing product positioning, visual identity, UI tokens, screenshots or user-facing terminology
Last reviewed: 2026-08-31

## 1. Brand role

**Korgis** is the user-facing brand for the local-first AI control-plane product implemented in this repository.

The bundled browser control plane now ships under the **Korgis** identity. The technical repository/package identity remains **Local LLM Server**. **Local LLM Studio** is a historical legacy UI name and must not be presented as the current product surface.

Korgis should feel:

- technical without being intimidating;
- privacy-conscious without fear-based messaging;
- operational and evidence-driven;
- modular and backend-neutral;
- precise about limitations;
- calm under high information density;
- ready to be embedded into real applications and use cases.

It should not feel like:

- a generic chatbot;
- a consumer AI assistant brand;
- a crypto/cyberpunk dashboard;
- an “AI magic” product;
- an imitation of a specific model provider or cloud console.

## 2. Brand hierarchy and positioning

### Brand

**Korgis**

### Claim

**Your AI. Local. Ready to use.**

The claim communicates the product outcome: locally controlled AI made available as infrastructure for the user's applications and use cases. It is a positioning line, not a technical guarantee that every model/task is supported.

### Short category

**Local AI control plane**

### Product descriptor

**Local AI runtime platform**

### Primary positioning statement

> Korgis orchestrates text, vision and audio inference on user-owned hardware through one resource-aware and observable control plane, making local AI available to applications through stable interfaces.

### Developer-oriented explanation

> Applications integrate once. Korgis owns model/runtime lifecycle, task capability, resource admission, scheduling and observability across specialist local inference backends.

### Mission statement

> Run suitable AI workloads locally with explicit control over data boundaries, model lifecycle, resources and evidence — while making that local capability practical to consume from real applications and use cases.

## 3. Naming and migration rules

Use consistently:

- **Korgis** — user-facing product brand and bundled browser control-plane name;
- **Your AI. Local. Ready to use.** — approved claim;
- **Local LLM Server** — repository, package and technical implementation identity until an explicit technical rename is approved;
- **Local LLM Studio** — historical legacy browser UI name only; do not use it for the current surface;
- **model artifact** — file/snapshot identity on storage;
- **runtime** — loaded execution owner/backend instance;
- **resident** — model resources actively loaded/owned;
- **cold** — artifact available but not resident;
- **default route** — model selected when request omits explicit model, not necessarily resident;
- **task** — chat, structured generation, vision-language, transcription, etc.;
- **capability** — supported task/input/output/feature declaration;
- **resource budget** — configured control-plane memory/resource allowance;
- **observed footprint** — measured resource use;
- **estimated footprint** — planning value, explicitly not measured;
- **runtime fingerprint** — reproducibility identity for artifact/backend/config/hardware.

Do not mechanically replace technical identifiers, package names, CLI commands, environment variables or API contracts with `Korgis`. A product-brand rollout and a technical rename are separate changes.

Avoid using these as synonyms:

- downloaded ≠ installed/available ≠ resident;
- selected/default ≠ loaded;
- model ≠ runtime;
- chunk ≠ token;
- audio transcription ≠ audio-language reasoning;
- memory estimate ≠ observed memory.

## 4. Messaging pillars

### Ready for applications

Preferred language:

- local AI available to your applications;
- one stable application-facing layer;
- integrate once across supported local runtimes;
- ready for real use cases;
- explicit task/capability boundaries.

Avoid implying that every model, modality or application is supported automatically.

### Control

Use language around:

- explicit model identity;
- lifecycle/residency;
- resource budgets;
- deterministic routing;
- stable application contracts.

Avoid generic “full control” claims without naming what is controlled.

### Privacy

Preferred:

- local by default;
- user-owned hardware;
- no cloud inference fallback by default;
- remote media/code require explicit policy;
- content excluded from normal telemetry.

Avoid absolute “100% private” claims when optional network/model download behavior exists.

### Observability

Preferred:

- source-backed metrics;
- explicit unavailable states;
- runtime fingerprint;
- evidence/reproducibility;
- queue/resource/lifecycle visibility.

Avoid calling estimated values “measured”.

### Efficiency

Preferred:

- memory-aware residency;
- load/unload;
- backend-native batching/caching;
- scheduler/admission;
- workload-specific benchmarking.

Avoid implying local execution is always cheaper/faster than cloud execution.

### Modularity

Preferred:

- specialist backend adapters;
- text, vision and audio tasks;
- stable control-plane contract;
- backend-neutral application integration.

Avoid claiming universal model support merely because the architecture is extensible.

## 5. Voice and tone

### Preferred

- concise;
- technical but readable;
- declarative;
- explicit about state and uncertainty;
- action-oriented for errors/recommendations.

Examples:

- “Model is available on disk but not resident.”
- “Load requires an estimated 4.8 GB; 3.6 GB remain in the configured AI budget.”
- “TTFT unavailable: this backend does not expose a compatible timing source.”
- “Remote media is disabled by local privacy policy.”

### Avoid

- “AI magic”;
- “blazing fast” without measurement;
- “unlimited”;
- “secure/private by definition”;
- anthropomorphic assistant language in control-plane surfaces;
- raw Python/backend exception dumps as primary user-facing errors.

## 6. Logo system

### Approved concept: Runtime Layers

The Korgis mark is composed of three separated geometric runtime layers:

- the **Electric Blue top layer** is the active application/control-plane entry layer and contains the central diamond cutout;
- the **Teal middle layer** represents orchestration and the modular runtime layer;
- the **Graphite bottom layer** represents the local infrastructure/resource foundation.

The stacked construction expresses local runtime composition, isolation and readiness without using a brain, robot, sparkle, vendor mark or generic neural-network motif.

The mark must remain recognizable at compact sidebar/favicon scale. Do not redraw generated irregularities, change layer order, close the central cutout, distort proportions or introduce vendor-specific symbols.

### Canonical source assets

All approved brand sources live under `design/brand/logo/`:

| Role | Asset |
| --- | --- |
| Mark only | `korgis-mark.png` |
| Primary horizontal / transparent | `korgis-horizontal.png` |
| Horizontal on light background | `korgis-horizontal-light.png` |
| Horizontal + claim on light background | `korgis-horizontal-claim-light.png` |
| Monochrome dark | `korgis-monochrome-dark.png` |
| Reversed dark-background lockup | `korgis-reversed-dark.png` |
| App icon / favicon source | `korgis-app-icon.png` |

`design/brand-kit.json` is the machine-readable owner for these roles. Runtime copies under `src/local_llm_server/static/` must retain byte identity with their corresponding canonical source asset unless a documented derived export is intentionally produced.

### Variant usage

- Use **`korgis-horizontal.png`** as the default wordmark where transparency is useful.
- Use **`korgis-horizontal-light.png`** on controlled light-neutral surfaces when a baked light background is acceptable.
- Use **`korgis-reversed-dark.png`** on dark presentation/marketing surfaces.
- Use **`korgis-monochrome-dark.png`** when brand color cannot be reproduced or color is intentionally suppressed.
- Use **`korgis-mark.png`** for compact navigation, avatars and mark-only placements. The current browser sidebar uses this compact role.
- Use **`korgis-app-icon.png`** as the app-icon/favicon source. A future packaging/performance slice may add derived 16/32/other exports; derived assets must remain traceable to this source rather than being redrawn independently.
- Use the claim lockup only where the logo has enough size to keep the claim legible. Do not put the claim into favicons, tiny navigation marks or dense controls.

Keep clear space around a lockup at least comparable to one visible layer thickness. Never stretch, rotate, add glow, recolor individual layers outside the approved variants, or put the colored mark on a background that destroys contrast.

## 7. Color system

Reference palette:

| Token | Hex | Role |
| --- | --- | --- |
| Graphite | `#0E1117` | primary dark canvas / infrastructure layer |
| Slate | `#1F2937` | elevated dark surfaces / secondary structure |
| Electric Blue | `#2563EB` | primary action and top logo layer |
| Teal | `#14B8A6` | healthy resource/observability accent and middle logo layer |
| Violet | `#8B5CF6` | benchmark/reasoning/secondary data accent |
| Light Neutral | `#F5F7FA` | light surface/reference background |

Semantic colors remain separate from brand accents so status meaning stays stable if brand colors evolve.

Suggested semantic roles:

- success/healthy: accessible green distinct from teal decorative data accent;
- warning/pressure: amber;
- destructive/error: red;
- unavailable/disabled: neutral gray;
- info/loading: electric blue.

Rules:

- status is never communicated only by color;
- chart series remain distinguishable with labels/legend and accessible contrast;
- gradients are limited to identity/primary emphasis, not used as a substitute for hierarchy.

## 8. Typography

Reference direction:

- headings/navigation: **Inter** or equivalent highly legible UI sans-serif;
- body/data labels: **IBM Plex Sans** or equivalent technical UI sans-serif;
- code/IDs/hashes: **IBM Plex Mono**, **JetBrains Mono** or equivalent monospaced face.

Implementation must use web-safe/licensable distribution rather than embedding unauthorized font binaries.

Hierarchy target:

- brand wordmark is an asset and must not be approximated by arbitrary runtime typography when the lockup is intended;
- page title: strong, compact, not marketing-sized;
- section heading: semibold;
- body: high legibility at dense dashboard scale;
- captions/metadata: never below accessible/readable product size merely to fit more data.

## 9. Spacing and shape

- base spacing grid: 4/8 px increments;
- standard control/card radius: restrained 8–12 px range;
- larger panels may use 12–16 px where it improves grouping;
- avoid excessive pill-shaped containers for ordinary data;
- dense tables use consistent row height and alignment;
- visual grouping should come primarily from spacing, contrast and typography rather than heavy borders.

## 10. Iconography

Target style:

- monoline/geometric;
- consistent stroke weight;
- rounded joins/caps where appropriate;
- simple model/task abstractions;
- no vendor logo required for basic task recognition.

Core concepts requiring stable icons:

- Overview;
- Models;
- Runtime/residency;
- Endpoints/API;
- Chat;
- Vision;
- Audio/transcription;
- Benchmark;
- Resources/memory;
- System/health;
- Logs/evidence;
- Settings/privacy.

## 11. Component visual language

### Cards

Use for one coherent summary or control group. Avoid nesting multiple unrelated mini-dashboards merely to maximize visual density.

### Status pills

Use short status text + icon/dot. Do not use pills for every tag/value.

### Tables

Preferred for model inventories and benchmark comparisons. Key identity remains left aligned; numeric performance/resource columns align consistently for scanning.

### Charts

Use only when a time series/distribution/comparison adds information over a number and textual summary. Do not add decorative sparklines to unavailable or low-sample data.

### Detail drawer

Appropriate for model/runtime details when the user should retain table context. Use a full route if the detail becomes a complex workflow.

## 12. Dark/light strategy

Dark mode is the primary reference for runtime control and operations because it supports dense technical panels and current product direction.

Light mode remains first-class for:

- benchmark/evaluation reports;
- documentation/examples;
- users with light-system preference;
- accessibility requirements.

The two themes share semantic tokens and component hierarchy; light mode is not a separately designed product.

## 13. Screenshot and marketing rules

A screenshot used in README/portfolio must:

- come from a real implemented screen;
- identify demo/test data as such when not live;
- avoid presenting target mockup numbers as product evidence;
- avoid exposing private local paths, tokens, prompts or sensitive media;
- prefer one clear product question per screenshot.

Generated concept mockups are design references only until implemented. Brand rollout claims must refer to the checked-in runtime surface and its validated exact head, not merely to canonical source assets.

## 14. Rollout boundary

The **Korgis browser rollout is implemented**. The app bootstrap in `src/local_llm_server/static/config.js` applies the canonical Korgis mark, app icon/favicon, product name, descriptor and metadata before the application, i18n and control-plane boot sequence. `src/local_llm_server/static/brand.css` maps the legacy shell variables onto the shared design-system tokens and removes the old decorative glow treatment. Routed titles and both language resources preserve Korgis.

The static Korgis assets used by the runtime live under `src/local_llm_server/static/` and are byte-identical copies of the approved sources where no derived export is declared.

The product/technical boundary remains explicit:

- **Korgis** is the current browser control-plane/product identity;
- package names, CLI commands, API identifiers, environment variables and repository identity remain **Local LLM Server**;
- **Local LLM Studio** is historical terminology and must not be presented as the current browser product;
- `index.html` currently retains pre-rollout literals only as non-canonical parser/bootstrap fallback markup. `config.js` replaces those literals synchronously before application boot; this retained fallback is explicitly documented in `design/brand-kit.json` and is not a second supported brand identity;
- future work may remove that fallback when the legacy HTML shell is retired, but it must not change the user-visible identity back to Local LLM Studio.

## 15. Brand acceptance criteria

Brand implementation is acceptable when:

- Korgis, the claim and the technical `Local LLM Server` identity are used according to the boundary above;
- README, web UI and docs use the same category/descriptor vocabulary for migrated surfaces;
- navigation and component tokens derive from one design system;
- status semantics are consistent across screens;
- logo/assets are reproducible, role-specific and vendor-independent;
- dark/light themes meet contrast requirements;
- model/resource claims use truthful terminology;
- current capability and roadmap language are not conflated;
- real product screenshots replace concept mockups before release positioning is promoted;
- legacy bootstrap literals are either removed or explicitly retained as non-canonical fallback by contract and cannot override the Korgis runtime identity.

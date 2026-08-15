# Local LLM Server brand and product-language guidelines

Status: active
Document type: design-guideline
Owner: web-product-and-docs
Canonical scope: design.brand
Read when: changing product positioning, visual identity, UI tokens, screenshots or user-facing terminology
Last reviewed: 2026-08-15

## 1. Brand role

Local LLM Server is the infrastructure/control-plane product in the local-first AI stack.

It should feel:

- technical without being intimidating;
- privacy-conscious without fear-based messaging;
- operational and evidence-driven;
- modular and backend-neutral;
- precise about limitations;
- calm under high information density.

It should not feel like:

- a generic chatbot;
- a consumer AI assistant brand;
- a crypto/cyberpunk dashboard;
- an “AI magic” product;
- an imitation of a specific model provider or cloud console.

## 2. Positioning hierarchy

### Short category

**Local AI control plane**

### Product descriptor

**Private local AI orchestration**

### Primary positioning statement

> Local LLM Server orchestrates text, vision and audio inference on user-owned hardware through one resource-aware and observable control plane.

### Developer-oriented explanation

> Applications integrate once. Local LLM Server owns model/runtime lifecycle, task capability, resource admission, scheduling and observability across specialist local inference backends.

### Mission statement

> Run suitable AI workloads locally with explicit control over data boundaries, model lifecycle, resources and evidence — while keeping future external execution an explicit architectural choice rather than a hidden dependency.

## 3. Messaging pillars

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

## 4. Naming and terminology

Use consistently:

- **Local LLM Server** — product/repository name;
- **Local LLM Studio** — bundled web control-plane UI, if this name is retained;
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

Avoid using these as synonyms:

- downloaded ≠ installed/available ≠ resident;
- selected/default ≠ loaded;
- model ≠ runtime;
- chunk ≠ token;
- audio transcription ≠ audio-language reasoning;
- memory estimate ≠ observed memory.

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

## 6. Logo direction

Target symbol language:

- geometric;
- modular;
- inspired by routing, stacked runtime layers, local nodes or memory blocks;
- recognizable at small sidebar/favicon size;
- independent from any model-vendor mark.

The current target mockup uses a geometric cube/layer/network motif. Final vector production should preserve the abstract infrastructure meaning rather than reproduce generated-image irregularities literally.

Required logo variants when assets are implemented:

- mark only;
- horizontal wordmark;
- dark-background variant;
- light-background variant;
- monochrome variant;
- favicon/app icon.

## 7. Color system

Reference palette from the approved visual direction:

| Token | Hex | Role |
| --- | --- | --- |
| Graphite | `#0E1117` | primary dark canvas |
| Slate | `#1F2937` | elevated dark surfaces / secondary structure |
| Electric Blue | `#2563EB` | primary action, navigation, active identity |
| Teal | `#14B8A6` | healthy resource/observability accent |
| Violet | `#8B5CF6` | benchmark/reasoning/secondary data accent |
| Light Neutral | `#F5F7FA` | light surface/reference background |

Semantic colors should be defined separately from brand accents so status meaning remains stable if brand colors evolve.

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

Generated concept mockups are design references only until implemented. They must not be labelled as current product screenshots.

## 14. Brand acceptance criteria

Brand implementation is acceptable when:

- README, web UI and docs use the same category/descriptor vocabulary;
- navigation and component tokens derive from one design system;
- status semantics are consistent across screens;
- logo/assets are reproducible and vendor-independent;
- dark/light themes meet contrast requirements;
- model/resource claims use truthful terminology;
- current capability and roadmap language are not conflated;
- real product screenshots replace concept mockups before release positioning is promoted.

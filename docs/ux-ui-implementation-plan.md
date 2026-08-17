# Local LLM Server UX/UI target specification

Status: active
Document type: target-specification
Owner: web-product
Canonical scope: target.web-ux
Read when: changing Local LLM Studio navigation, screen behavior, information architecture, visual semantics or UX acceptance criteria
Last reviewed: 2026-08-15

## Purpose

This document defines the target product behavior and acceptance criteria for the Local LLM Server web/control-plane UI. Current implementation status belongs in [`ux-ui-implementation-progress.md`](ux-ui-implementation-progress.md) and repository-wide reality in [`current-state.md`](current-state.md).

The redesign must make the control-plane value obvious: the UI is not primarily a chat demo. It is the operational surface for local model residency, capabilities, resource use, task execution, observability and evidence-based evaluation.

## Product experience principles

1. **Source-backed over illustrative.** Runtime, memory, latency, throughput and capability values are real or explicitly unavailable.
2. **State before action.** The user can understand what is installed, resident, busy, pressured or unsupported before triggering work.
3. **Lifecycle is explicit.** Downloaded, cold, loading, resident, draining, stopped and failed are visually distinct.
4. **Task capability is explicit.** Text, image and audio inputs appear only for models/tasks that support them.
5. **Local privacy is visible but not theatrical.** Local/network/media policies are understandable without repeated marketing banners.
6. **Operational density with calm hierarchy.** This is a developer control plane: information-rich, not decorative.
7. **Evidence over claims.** Metrics show source, timing and unavailable states; benchmark comparisons include run identity.
8. **Destructive actions are unambiguous.** Unload memory and remove artifact are never conflated.

## Brand anchor

The visual/product-language contract is owned by [`brand-guidelines.md`](brand-guidelines.md).

Working descriptor:

> **Private local AI orchestration**

Long positioning:

> Local LLM Server orchestrates text, vision and audio runtimes on user-owned hardware through one resource-aware and observable control plane.

## Information architecture

Primary navigation:

1. **Overview**
2. **Models & Runtimes**
3. **Endpoints**
4. **Playground**
5. **Benchmark & Evaluation**
6. **System**
7. **Settings**

Optional advanced subroutes may include Logs, Evidence/Reports and Hardware, but they should be reachable from the owning top-level surface rather than multiplying navigation prematurely.

### Navigation rules

- navigation does not start inference, load a model or run diagnostics implicitly;
- the current route remains stable across ordinary refreshes;
- deep links to model/run details use stable opaque identifiers, not filesystem paths;
- a selected model in a table does not become the default runtime merely by opening details;
- destructive actions require explicit user intent and confirmation where impact is not trivially reversible.

## Global shell

Target shell:

- left navigation rail/sidebar;
- product identity at top;
- server state and local endpoint identity visible but secondary;
- responsive content workspace;
- global status area for actionable degraded state;
- theme support with dark mode as primary control-plane reference and a coherent light mode for data/report surfaces.

Global status vocabulary:

- Healthy / Ready;
- Loading;
- Resident;
- Cold;
- Draining;
- Stopped;
- Warning / Pressure;
- Error;
- Unavailable / Not measured.

Status must use text/icon semantics in addition to color.

## Screen 1 — Overview

### User question

> Is the local AI control plane healthy, what is running, and is anything under resource pressure?

### Required top summary

- resident model count;
- active/queued request count;
- request latency summary only when measured from a truthful metric source;
- current AI/system memory summary;
- global health state.

### System health panel

Source-backed rows may include:

- CPU;
- RAM/unified memory;
- GPU/accelerator when meaningful and available;
- disk/model storage;
- local network activity if supported and relevant.

Rules:

- unsupported hardware readings show unavailable, not zero;
- memory values distinguish system total/available from AI budget and resident model footprint;
- pressure classification links to the reason and affected runtimes.

### Live workload panel

Show:

- request rate or active concurrency;
- success/failure/cancel outcomes;
- queue depth/wait when scheduler exists;
- selectable time window when history exists.

Do not render a live time-series chart until there is a bounded source of real samples.

### Resident models panel

Each row shows, when available:

- display name + registry key;
- task/category icon;
- backend;
- residency state;
- current/observed memory footprint;
- active requests;
- last used;
- quick link to model details.

### Resource pressure card

Appears only for source-backed non-normal pressure.

Must explain:

- pressure level;
- evidence/reason;
- safe user actions, such as unloading an idle model or reducing configured context;
- whether automatic eviction policy is enabled.

It must not recommend an action the runtime cannot currently execute safely.

### Recent activity

Privacy-safe event stream may include:

- model load/unload;
- request completion/failure/cancel;
- benchmark run state;
- resource-pressure transition;
- integrity verification result.

Normal activity does not include prompt, generated text or sensitive media.

### Endpoints & capabilities summary

Summarize available task surfaces such as:

- Chat / structured generation;
- Vision-language;
- Transcription;
- future embeddings if actually implemented.

Display available resident/configured model counts rather than generic checkmarks without data.

### Overview acceptance

- every metric is source-backed or unavailable;
- no composition/refresh side effect starts domain work;
- model/runtime state matches Models & Runtimes;
- pressure state matches ResourceManager/observation source;
- request state matches scheduler/telemetry source;
- a green overview does not hide degraded individual runtime state.

## Screen 2 — Models & Runtimes

### User question

> What models are available, which are resident, what do they support, and what resources do they consume?

This is the primary lifecycle/control screen.

### Upper resource/lifecycle area

#### Runtime lifecycle actions

Actions are capability/state-aware:

- Load;
- Unload;
- Reload;
- Pin / Unpin;
- Set default route;
- later configure automatic eviction policy.

Rules:

- unavailable actions explain why;
- unload is disabled while lifecycle policy says the runtime cannot safely drain, or initiates an explicit drain flow;
- set default does not force load;
- unload does not remove the artifact;
- remove artifact is a separate storage action with separate confirmation.

#### Memory budget visualization

Only authoritative after resource contracts exist.

Show distinct categories:

- system/unified memory total where meaningful;
- configured AI budget;
- safety headroom/reserved;
- observed resident model footprint;
- active/cache/request overhead where measurable;
- available budget;
- overcommit/pressure state.

An estimate uses a visually/semantically distinct label from an observation.

### Model table

Core columns:

- Model;
- Task / input -> output capability;
- Backend;
- Format/quantization;
- Context or relevant capacity;
- Artifact state;
- Runtime/residency state;
- RAM/unified/accelerator footprint when measured;
- Last used;
- Actions.

Filters:

- search;
- task/modality;
- backend;
- lifecycle state;
- pinned only;
- optionally artifact source.

### State model

A model row can represent orthogonal facts:

```text
artifact: missing | available | verified | invalid
runtime: cold | loading | resident | draining | stopped | failed
route: default | non-default
policy: pinned | evictable
```

Do not compress these into one ambiguous status pill.

### Model detail drawer/page

Tabs or sections:

1. Overview
2. Metrics
3. Configuration
4. Logs / events

Overview fields:

- display/model ID and registry key;
- tasks and input/output modalities;
- backend;
- format/quantization;
- context/capacity;
- artifact source;
- immutable revision/hash when available;
- artifact size;
- local availability/verification;
- capabilities;
- current runtime state;
- observed startup/load time;
- observed resident/peak memory;
- runtime fingerprint link once implemented.

### Models acceptance

- no filename is treated as immutable identity;
- artifact availability, default routing and residency remain distinct;
- selected row state survives refresh without changing runtime state;
- load/unload failures return actionable typed state;
- UI never claims memory reclamation solely because the route disappeared;
- cold/zero-resident state is a valid product state.

## Screen 3 — Endpoints

### User question

> Which stable application contracts are available and which models can satisfy them?

Required content:

- endpoint/path;
- task contract;
- accepted input/output types;
- resident/configured compatible models;
- streaming support;
- structured-output/tool support when true;
- authentication/network boundary status if shared mode is enabled;
- copy-ready examples.

The page derives compatibility from the capability registry, not from hardcoded UI model names.

### Endpoint detail

Include:

- request schema summary;
- response/streaming shape;
- capability requirements;
- sample cURL/Python/JavaScript/Swift integration where maintained;
- typed error cases such as unsupported capability, resource exhausted, deadline, cancellation and cold model policy.

## Screen 4 — Playground

### User question

> Can I execute this real task locally with this model/configuration, and what happened?

### Task selector

Available task types are source-backed:

- Chat;
- Structured output;
- Vision-language;
- Transcription.

### Model selector

Filters automatically to models compatible with the selected task, while showing why unavailable resident/configured models do not qualify.

### Inputs

Task-dependent:

- text/messages;
- local image upload;
- local audio upload;
- structured schema/config where supported.

Remote URL input is hidden/disabled by default under local privacy policy.

### Execution states

- idle;
- queued;
- loading/preparing;
- prompt/prefill where meaningful;
- generating/transcribing;
- cancelling;
- completed;
- cancelled;
- failed.

### Result metadata

Expose separately from content:

- model/runtime identity;
- TTFT/latency/throughput only where accurate;
- token counts;
- memory/request peak if captured;
- cache result;
- termination reason;
- fingerprint/run detail link.

### Playground privacy

- input/output remains process/session-memory-only unless the user explicitly exports/copies it;
- normal logs contain request identity/metrics, not content;
- local media lifecycle is visible enough to support trust but does not expose private filesystem paths.

## Screen 5 — Benchmark & Evaluation

### User question

> Which model/runtime is the best fit for this scenario on this machine, and is the comparison reproducible?

This screen is not a generic benchmark leaderboard. It is a workload-specific local evaluation harness.

### Run configuration

Required controls:

- model(s);
- backend/runtime configuration when multiple supported paths exist;
- task/test set;
- sample count;
- seed where relevant;
- cold/warm mode;
- generation preset/config;
- optional quality/performance weighting for presentation only, never altering raw metrics.

### Run state

- created;
- preparing;
- running;
- cancelling;
- completed;
- failed;
- partial/inconclusive where data is insufficient.

### Key metrics

Show only supported metrics:

- TTFT p50/p95;
- output tokens/sec p50/p95;
- total latency p50/p95;
- success/error/cancel rate;
- peak memory;
- model load time;
- prompt/KV-cache hit/reuse where accurately exposed;
- task-quality score with scorer identity.

### Comparison table

Each comparison row includes:

- exact model artifact;
- backend;
- compatible configuration/run identity;
- raw metrics;
- quality metric;
- optional scenario score with visible weights.

Rules:

- refuse or flag comparisons across incompatible run manifests;
- “best” is metric-specific unless a user-defined composite score is used;
- statistical uncertainty/sample size is visible for quality/performance claims;
- unavailable values do not rank as zero.

### Run metadata

Display:

- artifact hash/revision;
- backend/version;
- resolved config digest;
- hardware profile;
- server/harness version;
- dataset/test-set version;
- seed;
- timestamp;
- cold/warm classification.

### Test set management

Target capabilities:

- built-in general-purpose starter set;
- custom user-provided test set;
- sample size in bounded increments/validated ranges;
- versioned dataset identity;
- scorer compatibility;
- local-only storage by default.

### Benchmark acceptance

- no run is considered comparable without stable execution identity;
- partial/failed samples remain visible;
- per-sample results use progressive disclosure for prompt, expected value, model output, scorer details and raw metrics;
- prompt and expected value remain bound to immutable test-set identity; private local history retains model output by default with a per-run opt-out;
- legacy sample context is reconstructed only when test-set version and identity match, while shareable evidence remains content-free by default;
- automatic history refresh preserves the inspected run, expanded samples, focus and scroll orientation;
- benchmark execution cannot silently alter the model/default route for unrelated application traffic without explicit isolation/policy;
- reports distinguish measured facts from interpretation.

## Screen 6 — System / Diagnostics

### User question

> What is the server/runtime environment doing, and where is a problem occurring?

Sections:

- Server health;
- Hardware/resources;
- Runtime processes/workers;
- Request/event timeline;
- Logs;
- Cache state where exposed;
- Artifact verification;
- Evidence/diagnostic export.

Requirements:

- each data source has loading, empty, unavailable, warning and error state;
- diagnostic refresh is observational;
- explicit actions run diagnostics/verification;
- private paths and prompt/output content are excluded from shareable evidence by default.

## Screen 7 — Settings

Groups:

- local server/network boundary;
- model/artifact storage;
- default resource budget/headroom;
- residency/eviction policy after implemented;
- privacy policy such as remote media and remote-code opt-ins;
- theme/accessibility;
- advanced backend paths/binaries;
- build/version metadata.

Settings must not become a parallel source of runtime truth. It configures policy; status remains owned by runtime/observability sources.

## Design system requirements

Canonical visual tokens are in [`brand-guidelines.md`](brand-guidelines.md).

Reusable components should include:

- application shell/navigation;
- page header;
- metric card;
- status pill/icon pair;
- model identity cell;
- lifecycle action group;
- resource budget bar;
- data table;
- detail drawer;
- chart container/legend;
- empty/unavailable/error states;
- confirmation dialog;
- code/integration example;
- progress/run status;
- evidence/fingerprint metadata list.

Repeated patterns are extracted because they represent shared product concepts, not merely because two blocks look similar.

## Responsive behavior

Primary target remains desktop/laptop control-plane use.

Minimum expectations:

- wide desktop: sidebar + multi-column dashboard + optional detail drawer;
- laptop: sidebar + reduced grid columns; detail drawer overlays or narrows main content;
- narrow/tablet: collapsible navigation; data tables support horizontal scrolling or purposeful stacked rows;
- no critical lifecycle action becomes inaccessible below the reference width;
- charts never force unreadably dense labels.

## Accessibility

Required:

- full keyboard navigation for all primary actions;
- visible focus states;
- semantic labels for icon-only actions;
- minimum target sizing appropriate for desktop/touch hybrid use;
- WCAG AA text/status contrast where applicable;
- state not conveyed by color alone;
- prefers-reduced-motion respected;
- readable at 200% zoom without loss of critical controls;
- data visualizations have textual summaries for essential information.

## UX migration strategy

Do not rewrite the entire frontend in one step.

### UX-0 — Design-system and shell

- introduce tokens/components;
- implement target sidebar/navigation shell;
- preserve current chat/config functionality behind routes;
- establish standard unavailable/error/loading states.

### UX-1 — Models & Runtimes first

Reason: it best expresses the new positioning and can progressively integrate new resource/capability contracts.

Sequence:

1. existing registry/resident state table;
2. lifecycle detail drawer;
3. capability descriptors;
4. resource budget/observations;
5. pin/eviction policy;
6. fingerprint/evidence.

### UX-2 — Overview

Build from already-source-backed summaries first, then add scheduler/resource/metric panels as backend contracts land.

### UX-3 — Endpoint/Playground task model

Migrate from chat-centric interface to task-aware controls while retaining existing chat compatibility.

### UX-4 — Benchmark & Evaluation

Implement shell/configuration against stable harness contracts, then add real execution/history/comparison.

### UX-5 — Diagnostics/System and polish

Consolidate logs, resources, hardware, worker state and evidence after their contracts stabilize.

## Test and evidence matrix

### Automated

- component tests for status/lifecycle variants;
- route/navigation tests;
- state contract tests using deterministic source fixtures;
- API/UI contract tests for unavailable and error states;
- screenshot/visual regression for stable reference states;
- keyboard/focus/accessibility checks;
- responsive reference widths;
- no-network tests for default local media behavior where feasible.

### Representative runtime evidence

- real model load/unload reflected correctly;
- memory observations match resource source and reclaim after worker stop where claimed;
- queue/cancel states match scheduler lifecycle;
- text/image/audio capabilities match actual backend success/failure;
- benchmark UI uses real run identity and metrics;
- no illustrative metric remains in production runtime mode.

## UX completion boundary

The UX/UI program is complete only when:

- the new information architecture is implemented;
- primary screens use shared source-backed state;
- Models & Runtimes clearly separates artifact, route and residency state;
- resource-budget UI is backed by actual resource contracts;
- task-aware Playground supports the implemented text/vision/audio boundaries;
- benchmark/evaluation UI is tied to reproducible run identity;
- loading/empty/unavailable/warning/error/success states are covered;
- accessibility and responsive gates are green;
- representative hardware evidence validates lifecycle/resource presentation;
- README/screenshots reflect the real shipped UI rather than target mockups.

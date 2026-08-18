# Documentation map

Status: active
Document type: documentation-governance
Owner: repository
Canonical scope: documentation.routing
Read when: locating the canonical owner of operational, architecture, feature, roadmap, UX/UI or delivery information
Last reviewed: 2026-08-18

Local LLM Server documentation follows progressive disclosure. A fact should have one canonical owner; summaries link to it instead of copying detailed state/checklists.

## Use the server

Read in this order when operating/integrating the product:

1. [`getting-started.md`](getting-started.md) — install, model discovery/download, first server/inference and readiness checks.
2. [`configuration-reference.md`](configuration-reference.md) — CLI/environment/registry precedence and security-sensitive defaults.
3. [`http-api-reference.md`](http-api-reference.md) — supported public/admin endpoints and network/error boundaries.
4. [`runtime-status-reference.md`](runtime-status-reference.md) — mutable runtime telemetry semantics.
5. [`runtime-identity-api.md`](runtime-identity-api.md) — path-free `local-llm-identity-v1` execution identity and evidence rules.
6. [`troubleshooting.md`](troubleshooting.md) — operational/integration diagnosis.

Swagger at `/docs` is the executable schema for the checked-out revision; the references above own cross-endpoint semantics and safe usage.

## Canonical ownership

| Question | Canonical source |
| --- | --- |
| What is the current architecture/trust/resource flow? | [`architecture.md`](architecture.md) |
| What architectural direction/migration remains? | [`architecture-evolution-plan.md`](architecture-evolution-plan.md) |
| What is integrated, blocked or executable next? | [`current-state.md`](current-state.md) |
| What product are we building and why? | [`implementation-plan.md`](implementation-plan.md) |
| Which milestones/dependencies remain? | [`roadmap.md`](roadmap.md) |
| What proves automated Studio/product acceptance? | [`features/product-acceptance.md`](features/product-acceptance.md) and `tests/e2e/README.md` |
| Which active work needs explicit coordination? | [`workstreams/README.md`](workstreams/README.md) |
| Why was a durable architecture choice made? | [`adr/README.md`](adr/README.md) and the applicable ADR |
| What feature behavior lacks a better API/operations owner? | [`features/README.md`](features/README.md) |
| What UX/UI is targeted/integrated? | [`ux-ui-implementation-plan.md`](ux-ui-implementation-plan.md), [`ux-ui-implementation-progress.md`](ux-ui-implementation-progress.md) |
| What brand/visual language applies? | [`brand-guidelines.md`](brand-guidelines.md) plus `../design/brand-kit.json` for machine-readable token routing |
| What product-experience evidence/privacy/manual validation applies? | [`product-experience-validation.md`](product-experience-validation.md) plus `../design/ux-contract.json` |
| What must be true before completion/release? | [`definition-of-done.md`](definition-of-done.md) |

## Architecture vs progress

- [`architecture.md`](architecture.md) describes **current integrated ownership and data/trust/resource flow**.
- [`architecture-evolution-plan.md`](architecture-evolution-plan.md) describes the **target/migration direction** and must not become a progress ledger.
- [`current-state.md`](current-state.md) is the one short repository-level operational ledger.
- [`roadmap.md`](roadmap.md) owns milestone dependencies/sequencing.
- `docs/workstreams/` contains only active bounded plans that need explicit state coordination.

## Durable documentation topology

### Operational references

`getting-started.md`, `configuration-reference.md`, `http-api-reference.md`, `runtime-status-reference.md`, `runtime-identity-api.md` and `troubleshooting.md` track executable user/integration behavior.

### Architecture and decisions

- `architecture.md` — current boundaries/composition/resources/trust/data flow.
- `architecture-evolution-plan.md` — target ownership/migration where the current structure is not yet final.
- `adr/` — accepted decisions whose rationale/tradeoffs remain useful after implementation.

### Features

`features/` owns independently readable current feature behavior that has no better API, configuration, security or architecture owner. It is not a progress archive.

### Active delivery

- `current-state.md` — compact integrated truth and immediate blockers/next work.
- `roadmap.md` — capability milestones/dependencies.
- `workstreams/` — active substantial work only.
- `definition-of-done.md` — completion/evidence/release quality gates.

### Product/design

`implementation-plan.md`, UX/UI plan/progress and `brand-guidelines.md` own product intent and design constraints. `design/ux-contract.json` and `design/brand-kit.json` are the machine-readable `product-ui` contracts; `product-experience-validation.md` owns automated/manual evidence boundaries and privacy-safe usability research.

## Workstream lifecycle

Use a workstream only when multiple slices/dependencies/owners need explicit coordination. One file owns both plan and progress.

When a workstream completes:

1. verify its executable/evidence acceptance;
2. transfer durable behavior/decisions to the appropriate owner (`architecture`, API/operations, `features`, security or ADR);
3. update `current-state.md` only if repository-level operational truth changes;
4. remove the entry from `workstreams/README.md`;
5. delete the completed workstream by default—Git history owns implementation chronology.

Do not keep a completed plan merely as documentation. Archive only for a separate audit/regulatory/release-history requirement.

## Evidence classes

Keep these distinct:

```text
unit / contract / integration tests
browser E2E product acceptance
automated accessibility / adaptive / design-system fitness
manual accessibility / representative-user usability
real-runtime smoke
representative-device hardware evidence
```

A stronger claim requires the applicable evidence class. Hosted CI is not proof of real model quality, memory reclamation, Apple Silicon resource behavior, throughput, thermal stability or representative-user usability.

## Before creating another document

1. Find the canonical owner above.
2. Update that owner when the concern fits.
3. Create a new durable document only for an independently readable concern.
4. Give it Status, Document type, Owner, Canonical scope, Read when and Last reviewed metadata.
5. Link it from this map in the same change.
6. Do not copy detailed status/checklists from another owner.

## Precedence

When sources disagree:

1. executable contracts/tests;
2. accepted durable architecture decisions;
3. focused target specifications;
4. operational references for current invocation/API/serialization behavior;
5. current architecture/product target;
6. current state;
7. roadmap/workstream coordination;
8. README summaries.

Do not silently reconcile a contradiction that changes behavior. Correct the canonical owner and update planning/state only where necessary.

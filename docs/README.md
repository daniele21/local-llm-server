# Documentation map

Status: active
Document type: documentation-governance
Owner: repository
Canonical scope: documentation.routing
Read when: locating the canonical owner of operational, product, roadmap, UX/UI, architecture or delivery information
Last reviewed: 2026-08-15

Local LLM Server documentation follows progressive disclosure. Start from this map, then read only the focused source that owns the question. A fact should have one canonical owner; summaries link to that owner instead of copying detailed status or acceptance criteria.

The documentation model intentionally follows the discipline used by the Android Local LLM Harness: target behavior, current state, roadmap, workstream progress and completion gates are separate concerns.

## Start here if you want to use the server

For operational use, read in this order:

1. [`getting-started.md`](getting-started.md) — install, model discovery/download, first server, first inference and verification checklist.
2. [`configuration-reference.md`](configuration-reference.md) — CLI/environment/registry precedence, defaults and identity-relevant settings.
3. [`http-api-reference.md`](http-api-reference.md) — public/admin endpoints and the semantic split between inference, identity and status.
4. [`runtime-status-reference.md`](runtime-status-reference.md) — `/status` field meaning, polling limitations and Performance Lab telemetry mapping.
5. [`runtime-identity-api.md`](runtime-identity-api.md) — complete `local-llm-identity-v1` payload, privacy and evidence-grade rules.
6. [`troubleshooting.md`](troubleshooting.md) — common startup, routing, backend, identity, telemetry, CORS and Performance Lab integration failures.

Swagger at `/docs` remains the executable request/response schema for the checked-out revision; the operational references above own cross-endpoint semantics and safe usage guidance.

## Canonical sources

| Question | Canonical source |
| --- | --- |
| How do I install, start and verify a first runtime? | [`getting-started.md`](getting-started.md) |
| Which config wins and what are the supported defaults/environment variables? | [`configuration-reference.md`](configuration-reference.md) |
| Which HTTP endpoint should my application/evaluator call? | [`http-api-reference.md`](http-api-reference.md) |
| What does `/status` mean and what must not be inferred from it? | [`runtime-status-reference.md`](runtime-status-reference.md) |
| What does the public runtime identity endpoint expose and what may it never leak? | [`runtime-identity-api.md`](runtime-identity-api.md) |
| How do I diagnose operational/integration failures? | [`troubleshooting.md`](troubleshooting.md) |
| What is integrated, blocked or next? | [`current-state.md`](current-state.md) |
| What product are we building and why? | [`implementation-plan.md`](implementation-plan.md) |
| Which milestones remain and what can run in parallel? | [`roadmap.md`](roadmap.md) |
| What runtime/control-plane architecture is the target? | [`architecture-evolution-plan.md`](architecture-evolution-plan.md) |
| What should the product UX/UI do? | [`ux-ui-implementation-plan.md`](ux-ui-implementation-plan.md) |
| What UX/UI work is actually integrated? | [`ux-ui-implementation-progress.md`](ux-ui-implementation-progress.md) |
| What brand and visual language should be used? | [`brand-guidelines.md`](brand-guidelines.md) |
| What must be true before a milestone is considered complete? | [`definition-of-done.md`](definition-of-done.md) |

## Document lifecycle

- `operational-guide` / `operational-reference`: current install/config/API/output/troubleshooting behavior for users and integrations; must track executable contracts.
- `current-state`: one short operational ledger for the integrated baseline, blockers and immediate next block.
- `target-specification`: intended product behavior, invariants and acceptance criteria. It changes only when the target changes.
- `focused-specification`: independently readable durable behavior for one bounded contract such as public runtime identity.
- `roadmap`: capability milestones, dependencies and parallel work lanes. It is not a branch/commit log.
- `workstream-state`: concise status tracker for one focused workstream.
- `architecture`: durable target boundaries and migration direction.
- `design-guideline`: brand, design-system and product-language constraints.
- `completion-policy`: merge, evidence and release-quality gates.
- completed temporary plans should be archived only after durable behavior has been transferred to the owning specification.

## Living-plan contract

The plan is part of the implementation, not an after-the-fact report.

Every pull request or coherent implementation change that advances this program must update the relevant documentation in the same change when any of the following is true:

1. a task changes status;
2. a dependency is added, removed or discovered;
3. the next executable block changes;
4. scope or acceptance criteria change;
5. a target assumption is disproved by implementation or hardware evidence;
6. a workstream becomes blocked or unblocked;
7. a milestone acquires evidence sufficient to change its completion state;
8. invocation/configuration/API/output behavior changes in a way that affects users or integrations.

At minimum, update:

- the applicable operational reference when current invocation/config/API behavior changes;
- [`current-state.md`](current-state.md) when integrated reality or the immediate next block changes;
- [`roadmap.md`](roadmap.md) when milestone status, dependencies or sequencing change;
- the applicable workstream tracker, currently [`ux-ui-implementation-progress.md`](ux-ui-implementation-progress.md), when that workstream changes;
- the target specification only when intended behavior changes, not merely because implementation progressed.

### Status vocabulary

Use these states consistently:

- `PENDING`: not started.
- `READY`: dependency-complete and safe to start.
- `IN_PROGRESS`: active implementation.
- `PARTIAL`: meaningful implementation exists but acceptance is incomplete.
- `BLOCKED`: cannot progress until an explicit dependency/evidence item is resolved.
- `EVIDENCE`: implementation is integrated; representative runtime/hardware/UX evidence remains.
- `DONE`: implementation and applicable automated acceptance criteria are integrated and required evidence is recorded.
- `DEFERRED`: intentionally outside the active delivery boundary.

Do not mark a task `DONE` because code exists if its stated validation gate is still open.

## Parallel-development rules

The roadmap uses dependency IDs and parallel lanes. Parallel execution is allowed only when ownership boundaries are explicit.

A task may run in parallel when:

- all of its hard dependencies are `DONE` or explicitly declared unnecessary for that slice;
- it does not modify the same unstable contract as another active task without coordination;
- it can be validated independently through a narrow test or review gate;
- it does not require illustrative/fake runtime data to unblock a production UI.

When two tasks share a contract that is still changing, extract or stabilize that contract first rather than merging competing interpretations later.

## Active source index

### Operational use

- [`getting-started.md`](getting-started.md) — clean-checkout-to-first-inference workflow and Performance Lab handoff.
- [`configuration-reference.md`](configuration-reference.md) — supported config precedence, CLI/environment mappings, security-sensitive settings and reproducibility guidance.
- [`http-api-reference.md`](http-api-reference.md) — supported public/control-plane HTTP surfaces, request patterns, error and network boundaries.
- [`runtime-status-reference.md`](runtime-status-reference.md) — dynamic runtime-state semantics, chunk/token distinction and sampling caveats.
- [`runtime-identity-api.md`](runtime-identity-api.md) — `local-llm-identity-v1`, public `GET /v1/runtime/identity`, privacy boundary, evidence-grade semantics and AI Performance Lab consumer mapping.
- [`troubleshooting.md`](troubleshooting.md) — operational diagnosis without weakening privacy/identity/evidence semantics.

### Product and architecture

- [`implementation-plan.md`](implementation-plan.md) — product positioning, target, non-goals and cross-cutting invariants.
- [`architecture-evolution-plan.md`](architecture-evolution-plan.md) — control-plane architecture and technical migration sequence.
- [`roadmap.md`](roadmap.md) — milestones, dependency graph, work lanes and recommended parallel batches.
- [`current-state.md`](current-state.md) — current operational truth and next block.

### UX/UI and brand

- [`ux-ui-implementation-plan.md`](ux-ui-implementation-plan.md) — information architecture, screen behavior, data contracts and acceptance matrix.
- [`ux-ui-implementation-progress.md`](ux-ui-implementation-progress.md) — current UX/UI workstream status only.
- [`brand-guidelines.md`](brand-guidelines.md) — positioning language, visual tokens, component direction and brand constraints.

### Delivery

- [`definition-of-done.md`](definition-of-done.md) — completion gates for code, UX, privacy, observability and evidence.

## Before creating another document

1. Search this map for the owning source.
2. Update the existing canonical owner when the concern fits its scope.
3. Create a new document only for a durable, independently readable concern.
4. Give it Status, Document type, Owner, Canonical scope, Read when and Last reviewed metadata.
5. Link it from this map in the same change.
6. Avoid duplicating detailed checklists or status tables from another canonical source.

## Precedence

When sources disagree, use this order:

1. executable contracts and tests;
2. accepted durable architecture decisions;
3. focused target specifications;
4. operational references for current invocation/API/serialization behavior;
5. repository target overview;
6. current state;
7. roadmap;
8. README summaries and archived material.

Do not silently reconcile a contradiction that changes behavior. Correct the owning source and update the plan state in the same change.
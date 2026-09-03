---
name: plan-workstream
description: Plan substantial Local LLM Server work as observable vertical outcomes with parallel technical subtasks and early convergence rather than stacked publication ceremony.
---

# Plan Workstream

Use a durable workstream only when dependencies, multiple owners or execution environments genuinely require persistent coordination. Prefer slices that unlock an observable user/system outcome; runtime layers, adapters, Studio pieces and test harness changes are subtasks unless independently valuable and mergeable.

Parallel branches may own non-conflicting subtasks, but related work should converge early on a shared feature/integration branch. Stacked PRs are exceptional; sync-only parent/child PRs are a coordination smell.

For each slice record goal/non-goals, owning paths/contracts, dependencies, `READY|ACTIVE|BLOCKED|DONE`, convergence point, iteration checks and integration/release gates. Keep representative Apple Silicon evidence explicit and pending until executed. Update `docs/current-state.md` only for integrated/blocked/next truth, not temporary branch motion. Delete completed workstreams after durable truth moves to canonical owners.

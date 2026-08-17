# Local LLM Server — Coding Agent Guide

This file is the repository-wide navigation layer for coding agents. It owns durable invariants, routing and validation selection. It is not a project-status ledger.

## Read only what the task requires

Always read this guide. Then read only the closest scoped guidance, the canonical owner document for the task, `.engineering/commands.json` when operations are involved, and the owning implementation/direct consumers/tests.

Do not load every roadmap, workstream or evidence document for a local change.

## Repository purpose

Local LLM Server is a local-first AI control plane and evaluation harness. It exposes stable application-facing text, vision and transcription boundaries while specialist inference engines own model execution. The server owns runtime lifecycle, resource admission, scheduling, privacy policy, execution identity, observability and reproducible evaluation. Hardware-dependent claims require retained representative-device evidence.

## Non-negotiable invariants

- Artifact, configured model, resident runtime and default route are distinct states.
- Supported product entrypoints fail closed on unsupported task/modality combinations and remote media unless explicitly enabled.
- Public runtime identity is path-free and must not expose secrets, prompts, outputs or private filesystem locations.
- Measured, estimated, configured and unavailable evidence are never collapsed into one claim.
- Hardware/performance/memory-reclamation claims require representative hardware evidence; deterministic CI is not a substitute.
- Automatic pressure eviction remains disabled until its evidence gate is satisfied.
- Worker streaming/cancellation must not be claimed unless a real incremental/cancellable protocol exists.
- Build version, source identity and unique build identity remain distinct.
- Project-owned processes, listeners, temp files and E2E evidence require explicit ownership and cleanup.

## Ownership and routing

| Change | Start here | Inspect next |
| --- | --- | --- |
| Public request/task/capability contract | `src/local_llm_server/core/` | product composition, adapters, contract tests |
| Runtime/residency/lifecycle | `src/local_llm_server/runtime.py`, `product_runtime_manager.py` | resource/scheduler/eviction code and tests |
| Product HTTP policy | `src/local_llm_server/product_composition.py` | API modules, middleware and product tests |
| Runtime identity/evidence | `src/local_llm_server/runtime_identity*.py` | identity API, verification/evidence tests |
| Evaluation | `src/local_llm_server/evaluation*.py` | control-plane API, Studio UI, evaluation tests |
| Browser product acceptance | `tests/e2e/` | `playwright.config.js`, Studio source, E2E workstream |
| Real-device evidence | `docs/device-evidence-runbook.md` | hardware evidence modules and active correctness workstream |
| Build/release | `deploy.sh`, `release.sh` | release workflow and `.engineering/commands.json` |
| Durable architecture/docs | `docs/README.md` | `docs/current-state.md`, active workstream, owning feature/API docs |

Add scoped `AGENTS.md` only where a subtree has meaningful local hazards or commands.

## Project operating commands

`.engineering/commands.json` is the canonical repository-level routing for `setup`, `doctor`, `dev`, `check`, `test`, `e2e`, `build`, `smoke`, `package`, `stop` and `clean`.

Do not invent a second command path. `test`, `e2e`, `smoke` and representative-device evidence prove different things and must remain distinct.

## Core change workflow

1. Confirm the owning boundary and smallest coherent scope.
2. Use `plan-workstream` only when dependency/state coordination adds value.
3. Use `structured-change` for meaningful changes to shared behavior.
4. Inspect owner, direct consumers, fakes and tests before changing a shared contract.
5. Implement one coherent vertical slice without speculative layers.
6. Use `validate-change` to select the narrowest sufficient validation, then expand by blast radius.
7. Update only the canonical durable document whose behavior or decision changed.
8. Finalize completed workstreams by transferring durable truth and deleting the active plan by default.
9. Inspect the complete diff before publishing.

## Validation routing

Repository-health checks:

```bash
python3 scripts/verify_repository.py
python3 scripts/verify_operations.py
python3 scripts/verify_docs.py
python3 scripts/verify_agent_context.py
```

Use `.engineering/commands.json` for project-specific `check`, `test`, `e2e`, `build` and lifecycle commands.

A missing real-device/hardware run must be reported as pending. E2E traces/screenshots/logs are bounded diagnostic evidence, not durable documentation.

## Documentation lifecycle

- `docs/architecture.md` owns current architecture once installed by the adoption workstream.
- `docs/features/` owns durable feature behavior that needs a dedicated document.
- `docs/adr/` owns accepted architectural decisions.
- `docs/current-state.md` is the single short repository-level operational ledger.
- `docs/workstreams/` contains only active bounded implementation plans.
- Completed plans are deleted after durable behavior/decisions are transferred; Git history owns implementation history.

## Stop conditions

Surface the conflict instead of improvising when a requested change would weaken a durable runtime/privacy/evidence invariant, expose private state, create a second source of truth, bypass canonical validation/lifecycle behavior, delete state without proven ownership, or claim evidence that was not executed.

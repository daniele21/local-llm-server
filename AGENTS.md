# Local LLM Server — Coding Agent Guide

This file is the repository-wide navigation layer for coding agents. It owns durable invariants, routing and validation selection. It is not a project-status ledger.

## Read only what the task requires

Always read this guide. Then read only the closest scoped guidance, the canonical owner document for the task, `.engineering/commands.json` when operations/validation are involved, `.engineering/e2e.json` for complete-workflow or environment-dependent claims, and the owning implementation/direct consumers/tests.

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
- Final target-environment validation confirms residual environment-specific claims; it must not be the first complete-system test when the workflow can be automated earlier.
- Execution capability and environment fidelity are separate: `REMOTE_AUTOMATED` does not upgrade `host_or_fake` evidence into Apple Silicon/target evidence.

## Ownership and routing

| Change | Start here | Inspect next |
| --- | --- | --- |
| Public request/task/capability contract | `src/local_llm_server/core/` | product composition, adapters, contract tests |
| Runtime/residency/lifecycle | `src/local_llm_server/runtime.py`, `product_runtime_manager.py` | resource/scheduler/eviction code and tests |
| Product HTTP policy | `src/local_llm_server/product_composition.py` | API modules, middleware and product tests |
| Runtime identity/evidence | `src/local_llm_server/runtime_identity*.py` | identity API, verification/evidence tests |
| Evaluation | `src/local_llm_server/evaluation*.py` | control-plane API, Studio UI, evaluation tests |
| Browser product acceptance | `tests/e2e/` | `.engineering/e2e.json`, `playwright.config.js`, Studio source |
| Product UX/UI | `design/ux-contract.json` | `design/brand-kit.json`, canonical static UI source, `design-product-experience` |
| Real-device evidence | `docs/device-evidence-runbook.md` | hardware evidence modules and active correctness workstream |
| Build/release | `deploy.sh`, `release.sh` | release workflow and `.engineering/commands.json` |
| Durable architecture/docs | `docs/README.md` | `docs/current-state.md`, active workstream, owning feature/API docs |

Add scoped `AGENTS.md` only where a subtree has meaningful local hazards or commands.

## Project operating and validation contracts

`.engineering/commands.json` is the canonical repository-level routing for `setup`, `doctor`, `dev`, `check`, `test`, `e2e`, `build`, `smoke`, `package`, `stop` and `clean`, plus publication-preflight, execution-capability and blast-radius profile semantics.

`.engineering/e2e.json` owns target environments, automated execution environments, environment fidelity, critical journeys and residual real-environment gaps. `test`, `e2e`, built-surface evidence, `smoke` and representative-device evidence prove different things and must remain distinct.

Use `scripts/select_validation_profile.py` to resolve `auto -> LEAN | SCOPED | STRONG | FULL`. Changes to CI, the selector, global build/dependency/toolchain surfaces or unknown executable paths fail safe to `FULL`.

## Core change workflow

1. Confirm the owning boundary and smallest coherent scope.
2. Use `plan-workstream` only when dependency/state coordination adds value.
3. Use `structured-change` for meaningful changes to shared behavior.
4. For meaningful UX/UI semantics use `design-product-experience` before implementation; structure/hierarchy/recovery precede motion/polish.
5. Inspect owner, direct consumers, fakes and tests before changing a shared contract.
6. Implement one coherent vertical slice without speculative layers.
7. Use `validate-change` to select iterative evidence by blast radius and E2E fidelity.
8. Update only the canonical durable document whose behavior or decision changed.
9. Finalize completed workstreams by transferring durable truth and deleting the active plan by default.
10. Before publication use `preflight-change`: refresh target/base, inspect the full diff, select the validation profile, classify `AGENT_LOCAL`/`REMOTE_AUTOMATED`/`REAL_ENVIRONMENT`, and require exact-head evidence.
11. If deterministic gates are unavailable agent-local, use `remote-preflight` and repository-owned GitHub automation; do not delegate automatable CI work to the user.

## Validation routing

Repository-health checks:

```bash
python3 scripts/verify_repository.py
python3 scripts/verify_operations.py
python3 scripts/verify_e2e.py
python3 scripts/verify_docs.py
python3 scripts/verify_agent_context.py
```

Use `.engineering/commands.json` for project-specific `check`, `test`, `e2e`, `build` and lifecycle commands.

For E2E, report the declared environment ID/fidelity class. A missing real-device/hardware run is `PENDING`, not a failed deterministic CI gate and not an implicit pass. E2E traces/screenshots/logs are bounded diagnostic evidence, not durable documentation.

## Documentation lifecycle

- `docs/architecture.md` owns current architecture.
- `docs/features/` owns durable feature behavior that needs a dedicated document.
- `docs/adr/` owns accepted architectural decisions.
- `docs/current-state.md` is the single short repository-level operational ledger.
- `docs/workstreams/` contains only active bounded implementation plans.
- Completed plans are deleted after durable behavior/decisions are transferred; Git history owns implementation history.

## Stop conditions

Surface the conflict instead of improvising when a requested change would weaken a durable runtime/privacy/evidence invariant, expose private state, create a second source of truth, bypass canonical validation/lifecycle behavior, delete state without proven ownership, claim stronger environment evidence than was executed, or ask the user to run an automatable deterministic gate only because the current agent lacks the toolchain.

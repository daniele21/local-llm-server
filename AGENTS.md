# Local LLM Server — Coding Agent Guide

Repository-wide routing and durable invariants. Detailed architecture/feature truth lives in canonical docs and owning code; this file is not a status diary.

## Read only what the task requires

Always read this guide, then the closest scoped `AGENTS.md`, owning implementation/direct consumers/tests, `.engineering/commands.json` for operations/validation, `.engineering/e2e.json` for complete workflow or environment claims, and `design/*` only for meaningful product UI work. Do not load every roadmap/evidence document for a local edit.

## Repository purpose and invariants

Local LLM Server is a local-first AI control plane/evaluation harness exposing stable text, vision and transcription boundaries while specialist engines own inference. The server owns runtime lifecycle, resource admission/scheduling, privacy policy, execution identity, observability and reproducible evaluation.

Preserve these invariants:
- artifact, configured model, resident runtime and default route are distinct states;
- unsupported task/modality combinations and remote media fail closed unless explicitly enabled;
- public runtime identity is path-free and excludes secrets/prompts/outputs/private paths;
- measured/estimated/configured/unavailable evidence remain distinct;
- hardware, performance and reclamation claims require representative Apple Silicon evidence;
- pressure eviction stays disabled until its evidence gate is satisfied;
- streaming/cancellation claims require real incremental/cancellable protocol support;
- build version, source revision and unique build identity remain distinct;
- project-owned processes/listeners/temp state/evidence have explicit bounded lifecycle and cleanup;
- deterministic CI does not become target-hardware evidence.

## Ownership routing

| Change | Start here | Inspect next |
| --- | --- | --- |
| Public task/capability contract | `src/local_llm_server/core/` | composition, adapters, contract tests |
| Runtime/residency/lifecycle | runtime/product runtime owners | resource/scheduler/eviction tests |
| Product HTTP policy | `src/local_llm_server/product_composition.py` | API/middleware/product tests |
| Runtime identity/evidence | `runtime_identity*` | identity API/evidence tests |
| Evaluation | `evaluation*` | API, Studio, evaluation tests |
| Browser acceptance | `tests/e2e/` | `.engineering/e2e.json`, Studio source |
| UX/UI | `design/ux-contract.json` | brand kit/static UI/design skill |
| Real-device evidence | `docs/device-evidence-runbook.md` | hardware evidence owners |
| Build/release | `deploy.sh`, `release.sh` | commands/workflows |
| Durable docs | `docs/README.md` | owning architecture/feature/current-state doc |

## Delivery and validation model

Korgis follows repo-template-sw **0.9.2**. Delivery stage and validation depth are independent:

- `ITERATION`: default while implementation is changing. Use focused owner-local checks. No exact-head/full-diff/doc-freshness ceremony, package smoke, broad Playwright, L1/L2 fitness or remote preflight merely because those gates exist.
- `INTEGRATION` (`PR -> dev`): coherent observable outcome ready to converge. Refresh base/head/diff/docs and run required automated risk gates, including affected deterministic Studio/API E2E. Required Apple Silicon evidence is explicit but non-blocking and deferred to release.
- `RELEASE` (`dev -> main`): FULL plus release-critical package/E2E/security/L1-L2 and every applicable required residual real-environment confirmation.

`scripts/select_validation_profile.py` reports `risk_dimensions -> required_gates -> LEAN|SCOPED|STRONG|FULL`. Profiles are shorthand; concrete gates are authoritative. Selector/global workflow/dependency machinery changes fail safe FULL.

Automatic PR execution is owned by `.github/workflows/ci.yml`. Repository Health is a cheap structural guard. Package smoke and security have dedicated manual/scheduled workflows but are automatic PR gates only through `ci.yml`, avoiding duplicate pipelines.

Successful integration evidence is reusable when head/source tree, target/base, gates/profile and relevant E2E claim are equivalent. A squash/rebase merge into `dev` may reuse evidence only when repository automation proves identical source tree and the same validated target/base. Direct pushes without equivalent evidence validate normally.

## E2E and UI evidence

`.engineering/e2e.json` separates executor capability from environment fidelity and uses `ASSERTIONS`, `SCREENSHOTS`, `FULL_MEDIA` by risk. UI existence alone does not force video; a material UI/UX integration journey does.

- status/navigation and stable evaluation review: screenshots;
- chat progress/failure/recovery and runtime residency/lifecycle visibility: full media;
- external application API and cleanup contracts: assertions;
- real model/backend/memory/thermal behavior remains representative/target Apple Silicon evidence and gates release, not entry into `dev`.

Never upgrade hosted deterministic evidence into real-device claims. A real runtime smoke may be used early for diagnosis, but it is not the standard integration gate.

## Change workflow

1. Find one canonical owner; inspect consumers/fakes/tests before shared-contract edits.
2. Prefer one observable vertical outcome; technical layers are subtasks unless independently valuable.
3. Parallelize non-conflicting subtasks, then converge early. Stacked publication is exceptional; sync-only PRs are a smell.
4. During iteration use `validate-change` and the cheapest falsifying checks.
5. When the outcome is integration-ready, make affected durable docs current and use `preflight-change`.
6. Reuse equivalent evidence before triggering remote work; `remote-preflight` runs only missing/stale/insufficient deterministic gates.
7. Diagnose failures by owner/root cause; never weaken a legitimate gate for green CI.
8. Update `docs/current-state.md` only for integrated/blocked/next truth; delete completed workstreams after durable truth moves to canonical owners.

## Stop conditions

Surface conflicts instead of improvising if a request would weaken runtime/privacy/evidence invariants, expose private state, create duplicate ownership, bypass cleanup/migration/validation/doc freshness, overclaim environment evidence, mutate successful artifacts, or delegate an automatable deterministic gate to the user only because the current agent lacks tooling.
# API Black-box E2E Hardening

Status: active
Last reviewed: 2026-08-30
Owner: runtime-and-platform
Read when: implementing or coordinating external application-to-HTTP product acceptance coverage

## Goal

Prove representative public Local LLM Server contracts from the perspective of an external local application over the real loopback HTTP socket, while keeping browser E2E focused on user journeys and lower-level fault tests focused on internal invariants.

## Non-goals

- Treat the deterministic fixture as production llama.cpp/MLX or Apple Silicon evidence.
- Duplicate every unit/integration/fault-injection branch at the E2E level.
- Claim real-model performance, quality, native memory reclamation, thermals or cancellation semantics from hosted CI.
- Add a second process/lifecycle owner for API tests.

## Invariants

- API black-box tests do not call product handlers, services or runtime-manager methods directly.
- The existing `fixture_runner.py` remains the sole process, listener, temporary-root and cleanup owner.
- Public identity remains path-free and prompts/reasoning/private filesystem data do not enter CI failure artifacts.
- Unsupported task/modality and remote-media behavior fail closed.
- Automatic residency eviction remains disabled; preview evidence is not a reclamation claim.
- Mutable E2E state is reset within the run-owned root so one journey cannot contaminate another.
- Representative backend/hardware claims remain REAL_ENVIRONMENT evidence.

## Work graph

| ID | Work | Owns/writes | Depends on | Parallel | State |
| --- | --- | --- | --- | --- | --- |
| APIE2E-1 | Reuse deterministic runner and extend fixture tasks/fault probes | `tests/e2e/fixture_server.py` | — | yes | DONE |
| APIE2E-2 | Add external HTTP black-box contract matrix | `tests/e2e/api_blackbox.spec.js` | APIE2E-1 | no | DONE |
| APIE2E-3 | Preserve browser/visual isolation and run-owned cleanup | `tests/e2e/*` fixture/test state | APIE2E-2 | no | DONE |
| APIE2E-4 | Declare E2E fidelity/critical-journey contract and durable docs | `.engineering/e2e.json`, `tests/e2e/README.md`, `docs/current-state.md` | APIE2E-2 | yes | ACTIVE |
| APIE2E-5 | STRONG exact-head remote preflight and merge | PR/CI evidence | APIE2E-3, APIE2E-4 | no | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

## Current executable slice

`APIE2E-4`

Acceptance:

- Repository contracts describe a direct external API-consumer E2E journey separately from browser UX journeys.
- The documented matrix matches executable black-box coverage and explicitly preserves host/fake limitations.
- Mutable custom evaluation state is cleaned before later browser/visual assertions.

Validation:

- repository selector with `profile=auto` must select at least `STRONG`;
- canonical Repository Health contracts must pass;
- `npm run test:e2e && python tests/e2e/verify_residue.py` must pass through REMOTE_AUTOMATED CI on the final exact HEAD;
- Python 3.10/3.11/3.12, Ruff, Security and Package Install Smoke must remain green.

## Integration points

- `.engineering/e2e.json` owns the fidelity claim and critical journey.
- `tests/e2e/api_blackbox.spec.js` is executable assembled-boundary evidence.
- `.engineering/fault-injection.json` remains the owner for lower-level deterministic fault coverage not worth duplicating at E2E.
- representative Apple Silicon evidence remains the owner for production backend, memory, performance and thermal claims.

## Durable documentation destinations

- `docs/current-state.md`: integrated API-consumer E2E truth and remaining REAL_ENVIRONMENT gaps.
- `.engineering/e2e.json`: execution environment fidelity and critical journey.
- `tests/e2e/README.md`: executable test lanes, fixture probes, cleanup and privacy behavior.

## Completion

The workstream is complete only when the final exact HEAD is STRONG-validated, the PR is merged without base staleness and post-merge deterministic evidence is green. At completion, fold the durable result into `docs/current-state.md` and delete this workstream file by default.

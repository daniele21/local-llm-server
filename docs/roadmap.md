# Control-plane roadmap

Status: active
Owner: repository
Read when: selecting the next capability milestone or understanding release dependencies
Last reviewed: 2026-08-17

This file owns milestone sequencing only. Detailed active implementation planning and progress belong in `docs/workstreams/`; integrated/blocker/next truth belongs in `docs/current-state.md`.

## Objective

Evolve Local LLM Server into a **resource-aware, observable control plane for product-grade local AI inference** while specialist engines retain backend execution ownership.

The product loop remains:

`Build -> Run locally -> Observe -> Measure -> Compare -> Improve`

## Milestone summary

| Milestone | State | Remaining release outcome |
| --- | --- | --- |
| M0 Documentation governance | PARTIAL | converge active planning on workstreams/current-state and retire duplicated status ledgers as touched |
| M1 Trustworthy request/runtime foundation | PARTIAL | truthful thinking/structured-output semantics and remaining legacy direct-app boundary cleanup |
| M2 Resource-aware runtime | PARTIAL | real configured admission/accounting smoke, representative lifecycle evidence, later pressure-policy decision |
| M3 Multi-task control plane | PARTIAL | broader specialist backend/device evidence beyond current text/vision/audio contracts |
| M4 Evidence-grade observability | PARTIAL | verified artifact identity workflow plus wider representative runtime/device evidence |
| M5 Control-plane UX | EVIDENCE | current correctness fixes plus manual contrast/zoom/destructive-action/visual evidence |
| M6 Evaluation harness | PARTIAL | canonical request-path convergence, explicit request profile/reasoning identity, richer workload families later |
| M7 Product-grade candidate | BLOCKED | M1/M2/M4/M5/M6 evidence gates, cumulative smoke and release review |

## Active implementation workstream

The current executable plan is:

- [`runtime-correctness-evidence-hardening`](workstreams/runtime-correctness-evidence-hardening.md)

It was opened after the first representative Apple Silicon smoke exposed correctness/evidence gaps in switchable thinking, reasoning-output separation, evaluation request parity, artifact verification and real resource-policy validation.

Do not duplicate those task states in this roadmap. The workstream owns its work graph, dependencies, parallelization, acceptance and validation until completion.

## Dependency release points

| Completion | Unlocks |
| --- | --- |
| truthful backend thinking contract + implementation | reliable Playground ON/OFF semantics, structured reasoning separation, reproducible evaluation reasoning profiles |
| structured-output final-content contract | strict JSON consumers and objective structured-generation scoring without reasoning contamination |
| Evaluation canonical request convergence | trustworthy parity between interactive inference and benchmark execution |
| explicit verified artifact identity | evidence-grade runtime fingerprinting and verified hardware-report compatibility |
| verified compatible hardware reports | stronger descriptive reclamation evidence; **not** automatic-eviction authorization |
| real resource-policy admit/account/release/reject smoke | confidence in configured lifecycle accounting; **not** pressure-safety evidence |
| manual UX/accessibility evidence | primary control-plane UX eligible for DONE review |
| all above + cumulative CI/smoke | M7 release-candidate review |

## Product-grade candidate gate

Promotion toward `main` requires all applicable items below to agree with the exact candidate head:

1. blocking deterministic CI green on the integration head;
2. no known P0/P1 regression in supported product entrypoints;
3. thinking execution/exposure semantics truthful for advertised capabilities;
4. structured-output success returns clean final application content and malformed output fails explicitly rather than being silently repaired;
5. Evaluation uses canonical backend preparation and records request settings that can materially alter results;
6. release/evidence runs identify exact artifact/backend/config/environment strongly enough for the claim being made;
7. representative task/backend/device smoke retained where compatible hardware exists;
8. configured resource admission/accounting behavior validated without inducing uncontrolled memory pressure;
9. manual accessibility/responsive/destructive-action review for primary UX;
10. README/API/config/evidence documentation aligned with actual supported behavior;
11. experimental/evidence-pending claims remain explicit;
12. automatic pressure eviction remains disabled unless a later dedicated evidence/policy decision explicitly changes that boundary.

## Later milestones outside the active workstream

The following remain valid future work but should not distract from the current correctness tranche:

- decide whether worker subprocess isolation must support true incremental interactive streaming and cancellation; never emulate streaming with buffered completed output;
- broaden ASR/VLM/backend/device evidence;
- richer evaluation workloads, explicit cold/warm experiment orchestration and longer benchmark suites;
- stable visual-regression fixtures and representative real-runtime documentation screenshots;
- formalize eventual compatibility/deprecation policy for direct module-level `server:app` use;
- evaluate pressure-driven automatic residency actions only after representative evidence and an explicit policy decision.

## Evidence boundary

Automated tests establish deterministic contracts and make representative testing reproducible. CI does **not** prove Apple unified-memory reclamation, actual unload recovery, thermal behavior, safe concurrency, device throughput or safe automatic pressure eviction.

Positive real-device observations are descriptive evidence. They do not become production-safety claims unless a later explicitly defined evidence gate supports that claim.

## Maintenance rule

- update this roadmap only when milestone/release sequencing changes;
- update `docs/current-state.md` when the integrated baseline, blockers or next executable step changes;
- update the active workstream after every coherent implementation/evidence slice;
- when the workstream completes, transfer durable behavior/decisions to owning docs/tests, update current state/roadmap, and delete the completed workstream by default.

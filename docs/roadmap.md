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
| M0 Documentation governance | PARTIAL | finish durable-doc reconciliation after representative evidence and retire the completed active workstream |
| M1 Trustworthy request/runtime foundation | EVIDENCE | representative real thinking ON/OFF confirmation on the converged target runtime; no known contract implementation blocker |
| M2 Resource-aware runtime | EVIDENCE | real bounded admit/account/release/reject smoke, verified lifecycle evidence, later explicit pressure-policy decision |
| M3 Multi-task control plane | PARTIAL | broader specialist backend/device evidence beyond current text/vision/audio contracts |
| M4 Evidence-grade observability | EVIDENCE | run verified compatible representative hardware reports; artifact verification/identity flow is integrated |
| M5 Control-plane UX | EVIDENCE | manual contrast/zoom/destructive-action/visual evidence on the converged UI |
| M6 Evaluation harness | EVIDENCE | repeat the exact post-convergence 10-sample/seed-0 workload and retain compatible run evidence; canonical request/reasoning identity is integrated |
| M7 Product-grade candidate | BLOCKED | M1/M2/M4/M5/M6 evidence gates, cumulative smoke and release review |

## Active workstream

The current executable plan is:

- [`runtime-correctness-evidence-hardening`](workstreams/runtime-correctness-evidence-hardening.md)
- [`device-evidence-runbook`](device-evidence-runbook.md)

The original correctness tranche is integrated. The active workstream is now in its representative-device evidence wave: `TH-E1`, `EV-3`, `HE-2` and `RES-2` can proceed independently at the evidence level, while heavy model executions on one Mac must be serialized when they compete for the same residency/memory.

Do not duplicate those task states in this roadmap. The workstream owns its work graph, acceptance and evidence status until completion.

## Dependency release points

| Completion | Unlocks |
| --- | --- |
| representative real thinking ON/OFF evidence | M1 evidence review for the advertised switchable target runtime |
| repeated compatible post-convergence Evaluation runs | M6 evidence review and trustworthy pre/post comparison under explicit reasoning policy |
| verified compatible hardware reports | stronger descriptive reclamation evidence; **not** automatic-eviction authorization |
| real resource-policy admit/account/release/reject smoke | confidence in configured lifecycle accounting; **not** pressure-safety evidence |
| manual UX/accessibility evidence | primary control-plane UX eligible for DONE review |
| all above + durable-doc reconciliation + cumulative CI/smoke | M7 release-candidate review |

## Product-grade candidate gate

Promotion toward `main` requires all applicable items below to agree with the exact candidate head:

1. blocking deterministic CI green on the integration head;
2. no known P0/P1 regression in supported product entrypoints;
3. thinking execution/exposure semantics truthful for advertised capabilities and representative target-runtime evidence retained;
4. structured-output success returns clean final application content and malformed output fails explicitly rather than being silently repaired;
5. Evaluation uses canonical backend preparation, records materially relevant request settings and has representative repeated-run evidence;
6. release/evidence runs identify exact artifact/backend/config/environment strongly enough for the claim being made;
7. representative task/backend/device smoke retained where compatible hardware exists;
8. configured resource admission/accounting behavior validated without inducing uncontrolled memory pressure;
9. manual accessibility/responsive/destructive-action review for primary UX;
10. README/API/config/evidence documentation aligned with actual supported behavior and observed evidence;
11. experimental/evidence-pending claims remain explicit;
12. automatic pressure eviction remains disabled unless a later dedicated evidence/policy decision explicitly changes that boundary.

## Later milestones outside the active workstream

The following remain valid future work but should not distract from the current evidence tranche:

- decide whether worker subprocess isolation must support true incremental interactive streaming and cancellation; never emulate streaming with buffered completed output;
- broaden ASR/VLM/backend/device evidence;
- richer evaluation workloads, explicit cold/warm experiment orchestration and longer benchmark suites;
- stable visual-regression fixtures and representative real-runtime documentation screenshots;
- formalize eventual compatibility/deprecation policy for direct module-level `server:app` use;
- evaluate pressure-driven automatic residency actions only after representative evidence and an explicit policy decision.

## Evidence boundary

Automated tests establish deterministic contracts and make representative testing reproducible. CI does **not** prove Apple unified-memory reclamation, actual unload recovery, thermal behavior, safe concurrency, device throughput or safe automatic pressure eviction.

Positive real-device observations are descriptive evidence. Negative, mixed and inconclusive evidence must also be retained. One representative device does not establish a cross-device or production-safety claim.

## Maintenance rule

- update this roadmap only when milestone/release sequencing changes;
- update `docs/current-state.md` when the integrated baseline, blockers or next executable step changes;
- update the active workstream after every coherent implementation/evidence slice;
- when the workstream completes, transfer durable behavior/decisions to owning docs/tests, update current state/roadmap, and delete the completed workstream by default.

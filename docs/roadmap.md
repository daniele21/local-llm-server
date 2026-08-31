# Control-plane roadmap

Status: active
Owner: repository
Read when: selecting the next capability milestone or understanding release dependencies
Last reviewed: 2026-08-31

This file owns milestone sequencing only. Detailed active implementation planning and progress belong in `docs/workstreams/`; integrated/blocker/next truth belongs in `docs/current-state.md`.

## Objective

Evolve Local LLM Server into a **resource-aware, observable control plane for product-grade local AI inference** while specialist engines retain backend execution ownership.

The product loop remains:

`Build -> Run locally -> Observe -> Measure -> Compare -> Improve`

## Milestone summary

| Milestone | State | Remaining release outcome |
| --- | --- | --- |
| M0 Documentation governance | DONE | representative-device truth reconciled and completed runtime workstreams retired |
| M1 Trustworthy request/runtime foundation | DONE | representative thinking OFF/ON-hidden evidence accepted on the target Mac |
| M2 Resource-aware runtime | DONE | bounded resource smoke and repeated two-resident lifecycle/accounting evidence accepted; automatic pressure eviction remains a separate future policy decision |
| M3 Multi-task control plane | PARTIAL | broaden specialist backend/device evidence beyond current text/vision/audio contracts where product scope requires it |
| M4 Evidence-grade observability | DONE | verified compatible representative hardware evidence accepted without promoting memory deltas into safety claims |
| M5 Control-plane UX | DONE | bounded manual accessibility and representative-user usability evidence accepted on the tested product revision |
| M6 Evaluation harness | DONE | repeated compatible post-convergence 10-sample/seed-0 reasoning-OFF evidence accepted |
| M7 Product-grade candidate | READY | final exact-head FULL publication preflight and promotion to `main` |

## Active workstreams

There are no active L2 completion workstreams. The hardware/runtime and human product-evidence tranches are complete; `docs/device-evidence-runbook.md` and `docs/product-experience-validation.md` remain the durable procedures for reproducing or extending those evidence classes.

## Accepted release dependencies

The 2026-08-31 representative Mac evidence accepted the following release dependencies:

- real thinking OFF/ON-hidden behavior for the exercised target runtime;
- repeated compatible evaluation under exact post-convergence workload identity;
- verified compatible reclamation observations under the conservative no-safety-promotion contract;
- bounded resource-policy admit/account/release/reject behavior;
- repeated two-model residency, concurrent execution accounting, cleanup and shutdown-under-load ownership.

The 2026-08-31 bounded product-experience evidence accepted:

- the six required manual accessibility checks with no blocking finding;
- the four required representative-user usability journeys with no high/critical finding.

Those results remain scoped to the tested source revision and exercised environment. They do **not** authorize automatic pressure eviction or establish cross-device thermal/performance/production-safety claims.

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

All evidence-dependent items above are satisfied for the current candidate scope. Promotion still requires the final FULL deterministic preflight on the exact publication head/merge result.

## Later milestones outside the active workstream

The following remain valid future work:

- decide whether worker subprocess isolation must support true incremental interactive streaming and cancellation; never emulate streaming with buffered completed output;
- broaden ASR/VLM/backend/device evidence where supported-product scope requires it;
- richer evaluation workloads, explicit cold/warm experiment orchestration and longer benchmark suites;
- stable visual-regression fixtures and representative real-runtime documentation screenshots;
- formalize eventual compatibility/deprecation policy for direct module-level `server:app` use;
- evaluate pressure-driven automatic residency actions only after a separate representative evidence and policy decision.

## Evidence boundary

Automated tests establish deterministic contracts and make representative testing reproducible. The accepted Apple Silicon campaigns prove only the procedures and environment actually exercised. They do not prove cross-device unified-memory reclamation, thermal behavior, universal safe concurrency, device throughput or safe automatic pressure eviction.

Positive real-device observations are descriptive evidence. Negative, mixed and inconclusive evidence must also be retained. One representative device does not establish a cross-device or production-safety claim.

## Maintenance rule

- update this roadmap only when milestone/release sequencing changes;
- update `docs/current-state.md` when the integrated baseline, blockers or next executable step changes;
- update active workstreams after every coherent implementation/evidence slice;
- when a workstream completes, transfer durable behavior/decisions to owning docs/tests, update current state/roadmap, and delete the completed workstream by default.

# Architecture fitness contract

Status: active
Owner: runtime-and-platform
Canonical scope: current.architecture.fitness
Last reviewed: 2026-08-17

The L2 architecture policy protects a small set of dependency and ownership invariants derived from `docs/architecture.md`. The machine-readable source is `.engineering/architecture-policy.json`; `scripts/verify_architecture.py` evaluates the Python AST.

Protected boundaries:

- `core/` remains backend-neutral and independent from HTTP, runtime orchestration and backend libraries.
- resource admission, scheduling, residency eviction and pressure policy remain below HTTP and CLI composition.
- low-level engine/resource policy may be assembled by product composition but does not depend back on product/API composition roots.
- every critical boundary declared by the policy has one existing canonical owner path.

The policy intentionally does not freeze every current import. Transitional compatibility ownership stays governed by `docs/architecture.md` and the architecture evolution plan.

Run `python3 scripts/verify_architecture.py` to validate the contract. Shared Repository Health wiring is deferred to the L2 integration slice.

# Repeatability and cleanliness contract

Status: active
Owner: repository-engineering
Canonical scope: current.repeatability
Last reviewed: 2026-08-17

L2 repeatability reuses existing owned lifecycle evidence instead of creating another orchestrator. `.engineering/repeatability-contracts.json` ties development, test, E2E, build, smoke and runtime claims to concrete pytest functions or permanent workflow steps.

Key evidence includes three successive canonical builds with retention/failure cleanup, frozen clean-checkout tests, five sequential owned E2E temp-root lifecycles, blocking post-browser zero-residue verification, fresh-install smoke cleanup and repeated worker ready/exercise/stop cycles.

The contract verifies project-owned cleanliness only. It does not claim that repeated hosted runs prove representative hardware stability, that project cleanup owns external model caches, or that repeated worker cycles prove native-memory reclamation.

Run `python3 scripts/verify_repeatability_contracts.py`. Shared Repository Health wiring remains L2-10.

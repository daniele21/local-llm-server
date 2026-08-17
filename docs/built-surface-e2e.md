# Built/installed surface E2E

Status: active
Owner: repository-engineering
Canonical scope: current.built-surface-e2e
Last reviewed: 2026-08-17

L2 package validation now goes beyond import/CLI smoke. `scripts/smoke_installed_artifact.py` creates a fresh lock-backed environment, installs the produced wheel, verifies metadata/package data, and then launches `scripts/installed_surface_journey.py` with that fresh environment's Python.

The journey asserts `local_llm_server` is imported from the installed environment rather than the source checkout, assembles the real HTTP application/runtime manager from the wheel, and uses a deterministic local engine. It proves health before the journey, an expected `model_not_resident` failure, a successful retry against a valid resident runtime, health after recovery, and no retained evaluation state.

No model is downloaded and the result does not claim a native backend works, that synthetic-engine performance represents inference, or that hosted Linux proves macOS runtime behavior. Prompt/output/private paths are not retained as evidence.

`.engineering/built-surface-e2e.json` and `scripts/verify_built_surface_e2e.py` keep the workflow/runner/privacy/recovery wiring explicit. The existing Package Install Smoke workflow executes the real installed-surface journey on every PR/push.

# Browser E2E tests

This suite runs Chromium against the shipped FastAPI application and Studio assets. A deterministic in-process fake inference engine is resident behind the real product HTTP stack, so the tests cover browser -> UI JavaScript -> HTTP -> runtime/middleware contracts without downloading or loading a model.

The mandatory PR gate covers product journeys that unit tests alone cannot prove:

- control-plane keyboard navigation;
- explicit thinking ON/OFF and hidden-reasoning behavior;
- structured JSON separation from hidden reasoning;
- typed API error rendering;
- general-purpose evaluation request/reasoning policy;
- public `/v1/models`, `/v1/runtime/identity` and `/status` coherence;
- explicit multi-model routing from the Playground;
- visible `/status` polling while a request is genuinely generating;
- recovery of the next inference after a failed request.

The fixture keeps two deterministic resident runtimes: the default returns `42` and the alternate runtime returns `84`. A special `[slow-status]` prompt only delays fixture chunks long enough for the browser's status polling loop to observe `generating`; it is not a performance benchmark.

The suite is intentionally **not** hardware evidence. Real-device thinking behavior, memory reclamation and resource-policy validation still require the representative Mac/model evidence runbook. A bounded automated preflight for an already running real runtime lives in [`../real_runtime/README.md`](../real_runtime/README.md).

## Run-owned lifecycle

Every fixture process creates an isolated temporary root with a random run identity and ownership marker. Evaluation persistence is scoped under that root. Cleanup refuses to remove a directory unless the marker proves that the current fixture owns it.

The application shutdown hook cleans the run root during normal shutdown. The fixture process repeats the cleanup in a `finally` path to cover interruption and partial initialization, then verifies that the run root is gone and the loopback listener is no longer reachable. Uvicorn graceful shutdown is bounded to five seconds.

`tests/e2e/verify_residue.py` is the independent post-run check. It fails when port `8765` is still open or any marked `local-llm-e2e-*` temporary root remains. The shared CI workflow runs this verifier with `if: always()` after Playwright, so residue is checked even when the browser assertions fail.

## Failure evidence

Playwright traces are retained only on failure and screenshots are captured only on failure. Video is not part of the current evidence contract. CI uploads browser failure evidence only on failure and retains it for seven days. Deterministic fixture content must remain synthetic and must not ingest user model files, prompts, outputs or private evaluation corpora.

## Local execution

The canonical setup and E2E intents are owned by `.engineering/commands.json`. For a browser-only local run after the Python development environment is ready:

```bash
npm ci --ignore-scripts --no-audit --no-fund
npm audit --audit-level=high
npx playwright install chromium
npm run test:e2e
python tests/e2e/verify_residue.py
```

On Ubuntu CI, Chromium is installed with `npx playwright install --with-deps chromium`. Python dependencies come from committed `uv.lock`; Node dependencies come from committed `package-lock.json`.

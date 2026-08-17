# Browser E2E tests

This suite runs Chromium against the shipped FastAPI application and Studio assets.
A deterministic in-process fake inference engine is resident behind the real product
HTTP stack, so the tests cover browser -> UI JavaScript -> HTTP -> runtime/middleware
contracts without downloading or loading a model.

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

The fixture keeps two deterministic resident runtimes: the default returns `42` and the
alternate runtime returns `84`. A special `[slow-status]` prompt only delays fixture chunks
long enough for the browser's status polling loop to observe `generating`; it is not a
performance benchmark.

The suite is intentionally **not** hardware evidence. Real-device thinking behavior,
memory reclamation and resource-policy validation still require the representative
Mac/model evidence runbook. A bounded automated preflight for an already running real
runtime lives in [`../real_runtime/README.md`](../real_runtime/README.md).

Run from the repository root:

```bash
python -m pip install --upgrade pip
pip install -e . --no-deps
pip install pyyaml fastapi uvicorn python-multipart httpx huggingface-hub
npm ci --ignore-scripts --no-audit --no-fund
npm audit --audit-level=high
npx playwright install chromium
npm run test:e2e
```

The committed lockfile makes the Node dependency graph reproducible. The CI job rejects
high-severity npm advisories, uses `npx playwright install --with-deps chromium` on Ubuntu
and retains Playwright traces/screenshots only when the browser gate fails.

# Browser E2E tests

This suite runs Chromium against the shipped FastAPI application and Studio assets.
A deterministic in-process fake inference engine is resident behind the real product
HTTP stack, so the tests cover browser -> UI JavaScript -> HTTP -> runtime/middleware
contracts without downloading or loading a model.

The suite is intentionally **not** hardware evidence. Real-device thinking behavior,
memory reclamation and resource-policy validation still require the representative
Mac/model evidence runbook.

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

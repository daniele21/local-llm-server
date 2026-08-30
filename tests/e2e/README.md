# Deterministic product E2E tests

This suite starts the shipped FastAPI application through the repository-owned E2E runner and exercises it over a real loopback HTTP socket. A deterministic in-process inference fixture sits behind the real product HTTP, middleware, task-policy, runtime-management and evaluation boundaries, so hosted CI can prove assembled software behavior without downloading production models.

The mandatory gate has two complementary lanes:

1. **Browser product journeys** use Chromium to cover user-visible control-plane behavior.
2. **API black-box journeys** use an external HTTP client context with no DOM access to cover how another application integrates with Local LLM Server.

The API lane is intentionally black-box with respect to product internals: requests travel through `127.0.0.1:8765` into the real FastAPI stack and assertions are made from HTTP responses and public state surfaces. It does not call route handlers or runtime-manager methods directly.

## Covered assembled journeys

The browser lane covers behavior that unit tests alone cannot prove, including:

- route navigation, refresh and browser-history behavior;
- task-first Playground model selection;
- explicit thinking ON/OFF and hidden-reasoning behavior;
- structured JSON separation from hidden reasoning;
- typed API error rendering and recovery;
- evaluation setup, result evidence and repeatable history;
- model/runtime lifecycle controls and deep-linked detail;
- visible `/status` polling while a request is genuinely generating;
- targeted perceptual fingerprints for stabilized Overview and Evaluation surfaces.

The direct API black-box lane covers representative application-consumer contracts, including:

- `/health`, `/v1/models`, `/v1/runtime/identity` and `/status` coherence and path-free public identity;
- default and explicit multi-model routing;
- default-route mutation through the admin HTTP contract and subsequent model-omitted inference;
- deterministic concurrent execution on two different resident runtimes through the socket boundary;
- unknown model and malformed request failures followed by a healthy next request;
- fail-closed task/modality behavior, compatible local vision input and remote-media rejection;
- SSE streaming with hidden reasoning removed before bytes cross the HTTP boundary;
- a backend-originated failure produced inside the server stack followed by successful recovery;
- multipart transcription with explicit transcription capability enforcement;
- residency pinning and eviction preview with `automatic=false` and no reclamation claim;
- resource, scheduler, policy and evidence admin surfaces without E2E-root or reasoning leakage;
- built-in evaluation discovery/execution;
- custom evaluation upload, duplicate rejection, discovery and execution through the public admin API.

Internal combinatorial fault coverage remains at the lowest sufficient test level. For example, reservation rollback, queue timeout, pressure hysteresis, persistence tampering and stream-disconnect lease release are owned by the deterministic backend/fault-injection tests referenced from `.engineering/fault-injection.json`. The black-box suite adds representative assembled-boundary evidence; it does not duplicate every internal branch.

## Deterministic fixture

The fixture keeps two resident runtime identities so browser visual contracts remain stable:

- `e2e-switchable` / `org/e2e-switchable` returns `42` and is the default text runtime;
- `e2e-alt` / `org/e2e-alt` returns `84` and deterministically exposes chat, vision-language and transcription tasks.

A few reserved fixture prompts are test probes rather than product features:

- `[slow-status]` delays fixture streaming just long enough for browser status polling to observe `generating`;
- `[backend-error]` raises inside the deterministic engine so the API black-box lane can prove a server-originated failure and recovery;
- `[parallel-probe]` synchronizes the two deterministic engines with a barrier, proving cross-runtime overlap without timing thresholds.

These probes are not performance measurements and never justify latency, throughput, memory or backend-compatibility claims.

Mutable custom evaluation state is reset by a fixture-only, schema-hidden endpoint after the black-box import test. The reset is constrained to the evaluation test-set directory beneath the run-owned E2E root, preventing one journey from contaminating later browser or visual evidence.

## What hosted E2E does not prove

The deterministic suite is intentionally **not** hardware evidence. It does not:

- load a production model;
- execute production llama.cpp or MLX backend processes on Apple Silicon;
- prove native allocation reclamation or unified-memory pressure behavior;
- prove real backend cancellation semantics beyond the contracts implemented by the fixture;
- prove production latency, throughput, output quality, thermals or power behavior.

Those claims remain owned by representative Apple Silicon evidence and the device-evidence runbook. A bounded automated preflight for an already running real runtime lives in [`../real_runtime/README.md`](../real_runtime/README.md).

## Run-owned lifecycle

`fixture_runner.py` is the process-level owner that Playwright starts. It creates the isolated temporary root and random run identity, writes the ownership marker, then starts `fixture_server.py` as its child with that exact identity/root in the environment. The server validates the marker before using the evaluation subdirectory; it does not invent or discover another workspace.

Playwright tracks the runner directly (`exec python tests/e2e/fixture_runner.py`) and requests graceful `SIGTERM` shutdown. The runner forwards shutdown to Uvicorn, waits for the child, removes only the root whose marker proves ownership, then verifies both the root and loopback listener are gone before exiting. Child shutdown and Playwright escalation are both bounded.

`tests/e2e/verify_residue.py` is an independent post-run verifier. It never deletes residue. It allows only a bounded shutdown-completion window and then fails if port `8765` or any marked `local-llm-e2e-*` root remains. The shared CI workflow runs it with `if: always()` after Playwright, so residue is checked even when browser or API assertions fail.

## Failure evidence

Local developer runs may retain failure traces/screenshots for debugging. CI intentionally does **not** publish those rich artifacts because rendered content, stack traces and absolute paths can cross the privacy boundary.

On CI failure Playwright writes a JSON reporter file locally. `prepare_failure_evidence.py` reduces it to an allow-listed `e2e-failure-evidence/manifest.json` containing only run/source identity, relative E2E test file, test title, status and duration. Error text, stdout/stderr, screenshots, traces, video, page content and absolute paths are excluded. The bundle is uploaded only on failure with run/attempt identity in the artifact name and seven-day retention.

The deterministic fixture remains synthetic and must not ingest user model files, prompts, outputs or private evaluation corpora.

## Local execution

The canonical setup and E2E intents are owned by `.engineering/commands.json`. For a local E2E run after the Python development environment is ready:

```bash
npm ci --ignore-scripts --no-audit --no-fund
npm audit --audit-level=high
npx playwright install chromium
npm run test:e2e
python tests/e2e/verify_residue.py
```

On Ubuntu CI, Chromium is installed with `npx playwright install --with-deps chromium`. Python dependencies come from committed `uv.lock`; Node dependencies come from committed `package-lock.json`.

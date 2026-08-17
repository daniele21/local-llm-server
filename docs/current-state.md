# Current repository state

Status: active
Owner: repository
Read when: understanding what is integrated, blocked or executable next
Last reviewed: 2026-08-17

Keep this file operational and small. Detailed active implementation planning belongs in `docs/workstreams/`; durable behavior belongs in the owning API/config/architecture/evidence documentation.

## Current milestone

Harden the first real-device control-plane baseline so interactive inference, thinking/structured output, evaluation, artifact identity and resource evidence are truthful and reproducible before broader release claims.

## Active workstreams

| Workstream | Current executable slices | State | Blocker |
| --- | --- | --- | --- |
| [`runtime-correctness-evidence-hardening`](workstreams/runtime-correctness-evidence-hardening.md) | `TH-1`, `SO-1`, `EV-1`, `ID-1`, `RES-1` | ACTIVE | dependent slices wait on contract foundations; representative evidence waits on integrated code |

## Integrated baseline

- `dev` is the integration branch for the current product baseline.
- The 2026-08-17 text-only capability regression is fixed: built-in text runtimes resolve to explicit `modalities=["text"]` and structured API errors no longer render as `[object Object]` in the Playground.
- CI for that fix passed Ruff plus the deterministic suite on Python 3.10/3.11/3.12; the Python 3.11 job executed 435 passing tests.
- Real Apple Silicon smoke confirms the GGUF Nemotron runtime loads and interactive streaming inference completes end-to-end.
- Public runtime identity is path-free and reports backend/config/hardware evidence, but the tested GGUF remains partial/exploratory because no verified artifact SHA-256 is attached.
- `/api/v1/evidence` truthfully records HTTP streaming TTFT/total and leaves token counts unavailable when the stream does not expose them.
- Evaluation successfully executed 10/10 selected `general-purpose v1.0.0` samples at seed 0, but the observed 20% score is not yet suitable for model-quality attribution because Evaluation still owns a parallel backend-kwargs path and does not explicitly identify reasoning policy.
- Two Apple Silicon worker-reclamation reports produced six complete lifecycle windows, zero lifecycle errors and six `recovery_observed` observations. The conservative reviewer correctly remains `insufficient` because verified artifact identity is required; it provides no automatic-eviction recommendation or production-safety claim.
- Resource admission/accounting exists, but the real smoke used the default disabled resource policy, so enforcing admit/account/release/reject behavior remains to be exercised on-device.
- Automatic pressure eviction remains disabled. Worker streaming/cancellation remains explicitly unsupported rather than emulated.

## Repository blockers

- `llama_cpp` currently drops `enable_thinking` while Nemotron is advertised as `thinking_mode=switchable`; backend capability and request semantics are therefore not yet aligned.
- Streaming hidden-reasoning filtering is not robust to outputs that emit a closing reasoning delimiter without an opening delimiter, or delimiters split across chunks.
- Structured JSON output can be preceded by exposed reasoning, so the final application-content contract is not yet clean enough for strict API consumers.
- Evaluation reconstructs backend kwargs independently instead of consuming the canonical prepared-backend request path.
- Evaluation run identity does not yet record an explicit effective thinking/reasoning profile.
- Artifact verification is explicit in low-level helpers but there is no product workflow/CLI receipt that makes the exact local GGUF evidence-grade without path leakage.
- The current Apple Silicon reclamation reports are observational and exploratory; verified identity and broader representative coverage are still required before stronger claims.
- ResourceManager product enforcement has not yet been exercised in the real-device smoke.
- Manual accessibility/visual evidence and broader backend/device evidence remain release-candidate gates outside the immediate correctness workstream.

## Next

Run the first workstream wave in parallel with non-conflicting ownership:

- `TH-1` — define effective thinking contract per backend/template path;
- `SO-1` — define structured final-output/invalid-output contract;
- `EV-1` — move Evaluation onto canonical backend preparation;
- `ID-1` — design explicit artifact verification receipt/cache semantics;
- `RES-1` — add product-boundary resource admission/accounting integration coverage.

Do not repeat hardware reclamation solely to reproduce the known exploratory result. Repeat representative reports only after verified artifact identity reaches the evidence descriptor.

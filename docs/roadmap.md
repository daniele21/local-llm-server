# Control-plane and UX/UI roadmap

Status: active
Document type: roadmap
Owner: repository
Canonical scope: roadmap.repository
Read when: selecting the next capability milestone, understanding dependencies or parallelizing implementation
Last reviewed: 2026-08-15

Integrated truth belongs in [`current-state.md`](current-state.md). This file owns sequencing and dependency release points.

## Objective

Evolve Local LLM Server into a **resource-aware, observable local AI control plane and evaluation harness** while specialist runtimes retain backend execution ownership.

## Milestone summary

| Milestone | Status | Remaining outcome |
| --- | --- | --- |
| M0 documentation governance | DONE | keep plan synchronized |
| M1 trustworthy foundation | PARTIAL | AC1b route wiring + UX evidence |
| M2 resource-aware runtime | PARTIAL | admission wiring, concrete worker/reclamation, zero-resident, scheduler, eviction |
| M3 multi-task control plane | PARTIAL | public capability exposure, ASR/task routing |
| M4 evidence-grade observability | PARTIAL | richer metrics + fingerprint attachment/evidence |
| M5 control-plane UX | PARTIAL | Models/Playground/Diagnostics/data panels |
| M6 evaluation harness | PARTIAL | execution engine + history/regression |
| M7 product-grade candidate | BLOCKED | representative hardware/release evidence |

## Done foundations

- **A1 CI** — blocking deterministic Python 3.10/3.11/3.12 tests and Ruff correctness gate.
- **A3 decoupling** — no ClosedRoom-specific core registry dependency.
- **F1 positioning** — control-plane product language with current-vs-target separation.
- **D1 metrics vocabulary** — truthful token/chunk/duration/throughput semantics.
- **D3a artifact identity** — path-free artifact source/verification identity.
- **D4a evaluation schema** — versioned test sets, deterministic selection, scorer/run/report contracts.
- **D4b built-in dataset** — 20-sample deterministic general-purpose v1 set and objective scorer.

## Active foundations

### A2/C1/AC1 — PARTIAL

Fail-closed policy, canonical request contracts, compatibility translator and tested request pipeline exist. **AC1b** must make the live FastAPI route use them.

### B1 resources — PARTIAL

Linux and macOS observation contracts exist. Apple unified memory is not represented as separate VRAM. Runtime/API exposure and hardware evidence remain.

### B2 ResourceManager — PARTIAL

Reservation/admission accounting exists. **B2b** must wire real load/reload/unload lifecycle.

### B3 worker/reclamation — PARTIAL

Worker commands/states, deterministic lifecycle and pre/peak/post-stop evidence slots exist. **B3b** must bind them to concrete managed worker ownership and real reclamation evidence.

### C2 capabilities — PARTIAL

Descriptor, conservative migration, `supports(request)` and catalog projection exist. **C2c** must expose them publicly; request enforcement follows AC1b.

### D2 metrics — PARTIAL

Current trustworthy chunk metrics map to D1 without masquerading as tokens. Real backend token/timing adapters and API exposure remain.

### D3 runtime identity — PARTIAL

Artifact + backend + allowlisted config digest + hostname-free hardware profile compose a stable privacy-safe fingerprint. **D3c** must attach it to runtime/evaluation evidence.

### E1/E2/E4a UX — PARTIAL

Design system, seven-destination shell and live source-backed Overview exist. Models/Playground/Diagnostics and richer data panels remain.

## Immediate parallel wave 4

### AC1b — Live request-path wiring
Status: `READY`
Ownership: exclusive broad `server.py` request edits

- replace historical duplicate normalization with `prepare_chat_request()`;
- reject remote HTTP(S) media before backend invocation by default;
- preserve explicit opt-in, streaming, sampling and thinking behavior;
- map typed policy/request errors to bounded HTTP details;
- keep OpenAI compatibility tests green.

### B2b — Runtime admission wiring
Status: `READY`
Ownership: runtime load lifecycle

- reserve before expensive load;
- commit after successful load;
- rollback failed load/reload;
- release accounting on unload;
- preserve current reload rollback semantics;
- keep accounting distinct from reclamation proof.

### B3b — Concrete worker transport
Status: `READY`
Ownership: worker/process lifecycle

- bind B3 protocol to managed process transport where isolation is justified;
- bounded startup/health/drain/terminate;
- no orphan processes;
- capture before-ready/peak/after-stop evidence;
- do not promote reclaimability until representative evidence exists.

### C2c — Public capability exposure
Status: `READY`
Ownership: model/catalog presentation

- include capability object and provenance in list/catalog sources;
- preserve backward-compatible fields;
- no backend load/inference required;
- expose unsupported/unknown honestly.

### D2b — Backend metric adapters
Status: `READY`
Ownership: backend -> canonical metrics

Parallelize by backend after adapter interface:

- llama.cpp / llama-server;
- MLX text;
- MLX-VLM;
- ASR after C3.

Only map token counts, TTFT, prefill/decode durations and token throughput when the backend source is semantically trustworthy.

### D3c — Fingerprint attachment
Status: `READY`
Ownership: runtime/evidence integration

- compute/cache identity at controlled model/runtime preparation points;
- attach fingerprint to evaluation/run evidence;
- never hash/probe per token;
- no prompts, output, private paths or signed URLs.

### D4c — Evaluation runner
Status: `READY`
Dependencies: D4a/D4b; evidence-grade comparisons also need D2/D3 identity

- executor protocol;
- execute selected samples;
- deterministic objective scoring;
- collect per-sample result/error/metrics;
- produce complete report tied to explicit runtime fingerprint;
- do not compare incompatible/missing execution identity as evidence-grade runs.

### E3a — Models & Runtimes redesign
Status: `READY`
Ownership: frontend Models module

Show current real facts only:

- configured model identity;
- resident vs non-resident;
- default route separately;
- backend/runtime state/active work;
- current load/activate/unload controls;
- unavailable capability/resource/fingerprint sections until their sources are public.

## Dependency release points

| Completion | Unlocks |
| --- | --- |
| AC1b | route-level privacy completion; C3/C4 execution integration |
| B2b | resource-aware load policy; scheduler/residency work |
| B3b + evidence | credible reclaimability; stronger zero-resident/eviction guarantees |
| C2c | capability UI and C3 eligibility |
| D2b + D3c | evidence-grade evaluation metrics/fingerprint |
| D4c | Evaluation UI run/progress/results |
| E3a | screen-level accessibility/visual-regression work |

## Later runtime work

- **B4 zero-resident semantics** — healthy server with zero resident runtimes; configured/default/resident states separate.
- **B5 scheduler/deadlines/cancellation** — bounded queue, deadline expiry, cancellation, overload semantics.
- **B6 pin/LRU/TTL** — deterministic residency policy with no active-runtime eviction.

## Multi-task work

- **C3 transcription** — blocked by AC1b + C2c; ASR remains distinct from audio-language chat.
- **C4 task-aware routing** — no silent incompatible model substitution.

## Evaluation/UX completion

- D4 execution -> D5 immutable history/matched-fingerprint regression.
- E4 Overview/Diagnostics gains resource, exact performance and fingerprint panels only from canonical sources.
- E5 Playground becomes capability-aware; ASR after C3.
- E6 Benchmark & Evaluation connects D4c, then D5 history.

## Evidence boundary

Automated tests prove contract behavior, not real unified-memory reclamation, unload recovery, TTFT or token throughput. Representative hardware evidence remains a release gate.

## Active concurrency plan

Run AC1b, B2b, B3b, C2c, D2b, D3c, D4c and E3a in parallel **only where ownership does not overlap**. AC1b retains exclusive broad `server.py` request ownership. Merge narrow producer contracts before consumers and finish each wave with a cumulative living-plan validation PR.

## Plan maintenance

After every coherent merge wave update this roadmap, [`current-state.md`](current-state.md) and affected progress trackers. Target specifications change only when intended behavior changes.

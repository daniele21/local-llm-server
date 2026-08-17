# Runtime correctness and evidence hardening

Status: active — evidence wave
Owner: local-llm-server
Read when: coordinating the remaining representative-device evidence and release gate
Last reviewed: 2026-08-17

## Goal

Close the correctness/evidence gap exposed by the first Apple Silicon smoke without promoting deterministic CI or one-device observations into broader safety claims.

The code-convergence portion is now integrated in `dev`. The remaining work is representative-device evidence, durable documentation reconciliation and the cumulative release gate.

## Evidence boundary

- Missing evidence stays `Unavailable`/`null`; it never becomes a fabricated zero.
- Public evidence remains path-free, hostname-free and prompt/output-free unless an inference endpoint explicitly returns output.
- `enable_thinking` controls execution policy where the backend advertises switchability; `show_thinking` controls exposure only.
- Structured-output success means the final application content itself is valid structured output after reasoning separation. No silent repair.
- Evaluation comparisons are attribution-safe only when dataset selection, runtime identity and effective reasoning profile are compatible.
- Artifact verification is explicit and bound to the exact local file receipt.
- Reclamation observations are descriptive evidence, not automatic-eviction or production-safety authorization.
- Automatic pressure eviction remains disabled throughout this workstream.

## Work graph

| ID | Work | Depends on | State | Integrated / next evidence |
| --- | --- | --- | --- | --- |
| RC-0 | Preserve the first real-device smoke as historical baseline | — | DONE | regression baseline retained |
| LC-1 | Correct graceful shutdown ordering for long-lived ASGI streams | — | DONE | PR #101 |
| TH-1 | Effective `none / switchable / always` thinking contract | — | DONE | PR #95 |
| TH-2 | Real request-level `llama_cpp` thinking control | TH-1 | DONE | PR #102 |
| TH-3 | Chunk-safe streamed reasoning boundary | TH-1 | DONE | PR #104 |
| TH-4 | Separate execution vs exposure controls in Playground | TH-2 | DONE | PR #110 |
| TH-E1 | Representative Nemotron ON/OFF smoke on the converged runtime | TH-2, TH-3, TH-4 | READY | run on target Mac |
| SO-1 | Strict structured-output contract and typed invalid output | TH-1 | DONE | PR #100 |
| SO-2 | Reasoning/final separation before structured validation, including Evaluation | TH-2, TH-3, SO-1 | DONE | PR #111 |
| EV-1 | Evaluation uses canonical backend preparation | TH-1 | DONE | PR #100 |
| EV-2 | Persist requested/effective reasoning policy in runs/history/UI | EV-1, TH-2 | DONE | PR #108 |
| EV-3 | Repeat `general-purpose v1.0.0`, 10 samples, seed 0 on converged runtime | SO-2, EV-2 | READY | run OFF twice; optional ON separately |
| ID-1 | Explicit single-file artifact verification receipt contract | — | DONE | PR #100 |
| ID-2 | Persist receipt + `local-llm verify-artifact` | ID-1 | DONE | PR #103 |
| HE-1 | Feed the same verified identity into hardware evidence/review | ID-2 | DONE | PR #107 |
| HE-2 | Two compatible 3-cycle Apple Silicon reclamation reports with verified identity | HE-1 | READY | run + conservative review on target Mac |
| RES-1 | Deterministic resource admission/accounting integration coverage | — | DONE | PR #100 |
| RES-2 | Bounded real-device admit/account/release/reject smoke | RES-1 | ACTIVE | runner merged in PR #105; physical run pending |
| DOC-1 | Reconcile current state and durable public docs with integrated/evidence truth | code convergence | ACTIVE | this evidence-wave sync starts it; final reconciliation follows device runs |
| REL-1 | Cumulative green gate and workstream finalization | TH-E1, EV-3, HE-2, RES-2, DOC-1 | BLOCKED | wait for retained device evidence |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

## Integrated correctness baseline

The current converged `dev` contains:

- truthful thinking capability semantics and real `llama_cpp` request-level ON/OFF propagation;
- chunk-safe reasoning parsing at the client output boundary;
- independent Playground controls for execution (`Enable thinking`) and rendering (`Show thinking`);
- strict structured-output validation after reasoning/final separation for non-streaming and SSE responses;
- the same final-output normalization inside backend-neutral Evaluation before scoring;
- canonical Evaluation request preparation plus persisted requested/effective reasoning profiles;
- explicit artifact verification receipts reused by runtime identity and hardware evidence without public path leakage;
- deterministic ResourceManager product-lifecycle coverage and a bounded macOS smoke runner;
- graceful Uvicorn shutdown notification before long-lived response drain.

PR #111 validated this composition with Ruff and the full Python 3.10/3.11/3.12 matrix. The Python 3.11 job executed 518 passing tests.

## Wave D — representative device evidence

The following four workstreams are logically parallel. On a single Mac, serialize executions that compete for the same model residency or memory budget. Do not run multiple heavy model loads concurrently merely to make the plan physically parallel.

Use [`../device-evidence-runbook.md`](../device-evidence-runbook.md) as the executable procedure.

### TH-E1 — real thinking ON/OFF

Run the same model and prompt under explicit OFF and ON on the direct `llama_cpp` path.

Acceptance:

- both requests reach the target runtime successfully or fail with explicit typed errors;
- OFF is sent as an explicit execution policy, not omission/runtime default;
- ON is sent explicitly;
- `show_thinking=false` does not expose reasoning in normal client content;
- `show_thinking=true` remains an exposure choice and does not substitute for execution control;
- observations are retained as representative-device evidence, not a universal model-family guarantee.

### EV-3 — post-convergence evaluation

Procedure:

1. verify the artifact first so the runtime can attach strong identity where supported;
2. run `general-purpose v1.0.0`, `sample_count=10`, `seed=0`, `reasoning_policy=off`;
3. repeat the exact same OFF run once;
4. confirm identical dataset identity/sample selection and compatible runtime/reasoning identity;
5. optionally run the same workload with `reasoning_policy=on` as a separate experiment;
6. inspect changed sample/scorer outcomes; do not generalize a ten-sample score to global model quality.

Acceptance:

- every selected sample has success or an explicit per-sample failure;
- manifests record reasoning profile and runtime fingerprint when the evidence prerequisites are present;
- repeated OFF runs are comparable without hidden request differences.

### HE-2 — verified reclamation evidence

Produce two independent reports with three cycles each using the same exact artifact, backend, runtime config, hardware/environment and procedure, then run the conservative reviewer.

Acceptance:

- six complete lifecycle windows are attempted;
- identity is verified from the ID-2 receipt, not inferred from filename/size;
- incompatible reports are not pooled;
- positive, mixed, negative or inconclusive observations are retained as observed;
- `automatic_eviction_recommendation` remains absent/not provided and no production-safety claim is made.

### RES-2 — bounded resource smoke

Use the merged `resource_policy_smoke` runner. It must:

- require measured macOS available memory before load;
- admit under a deliberately safe configured budget;
- expose committed accounting after load;
- complete one real inference;
- unload and return reserved/committed accounting to zero while product health is green/cold;
- reject a budget one byte below the same pre-load estimate before backend construction;
- never create artificial memory pressure, trigger OOM or exercise automatic eviction.

Acceptance is the retained path/prompt-free JSON report produced by the real Mac run.

## Wave E — closure

After all Wave D evidence exists:

1. update `docs/current-state.md` with observed results, not expected outcomes;
2. reconcile `docs/roadmap.md`, HTTP/config/runtime-identity and hardware-evidence docs where behavior/evidence changed;
3. retain evidence references without embedding private local paths;
4. run the cumulative deterministic CI gate again if any product/doc-test code changes;
5. evaluate REL-1 strictly against the completion gate below;
6. delete this workstream by default after durable truth has moved to owning docs. Git history remains implementation history.

## Stop conditions

Stop and surface the result instead of improvising if:

- the real target model/template cannot honor explicit ON/OFF despite the advertised switchable contract;
- structured output needs semantic repair to become valid JSON;
- a verification receipt is stale or points to a changed artifact;
- HE-2 reports differ in artifact/config/environment and would otherwise be pooled;
- the Mac does not have the safety margin required by the bounded resource runner;
- a claim depends on device behavior that was not actually executed;
- evidence is negative or inconclusive: retain it rather than rerunning until a favorable result appears.

## Completion gate

This workstream is DONE only when all are true:

1. TH-E1 has representative real ON/OFF evidence on the converged runtime;
2. EV-3 has two comparable OFF runs for the exact 10-sample/seed-0 workload, with any optional ON run separately identified;
3. HE-2 has two compatible verified 3-cycle reports plus conservative reviewer output;
4. RES-2 has a real bounded admit/account/release/reject report;
5. automatic eviction remains disabled and no one-device result is promoted to a production-safety/cross-device claim;
6. durable docs match the integrated behavior and retained evidence;
7. the final deterministic CI gate is green.

# Runtime correctness and evidence hardening

Status: active — representative-device evidence pending
Owner: local-llm-server
Read when: coordinating the remaining target-Mac evidence and final runtime gate
Last reviewed: 2026-08-18

## Goal

Close the remaining real-device correctness/evidence gap without promoting hosted CI or one-device observations into broader safety/model claims. Code convergence and the deterministic L2 evidence bridge are accepted; only physical evidence, observed-result reconciliation and finalization remain.

## Evidence boundary

- Missing evidence stays unavailable; it never becomes a fabricated zero or pass.
- `enable_thinking` controls execution where supported; `show_thinking` controls exposure only.
- Structured-output success means final application content is valid after reasoning separation; no silent repair.
- Evaluation comparisons require compatible dataset selection, runtime identity and reasoning profile.
- Artifact verification binds evidence to the exact local file receipt.
- Reclamation remains descriptive; it never authorizes automatic eviction or production safety.
- Private model paths, prompts and outputs are not retained in the bounded L2 summary.
- Automatic pressure eviction remains disabled throughout this workstream.

## Work graph

| ID | Work | Depends on | State | Integrated / next evidence |
| --- | --- | --- | --- | --- |
| RC-0 | preserve first real-device smoke baseline | — | DONE | historical baseline retained |
| LC-1 | graceful shutdown ordering for long-lived ASGI streams | — | DONE | PR #101 |
| TH-1..TH-4 | thinking semantics, backend control, boundary parser and UI separation | — | DONE | PRs #95/#102/#104/#110 |
| SO-1..SO-2 | strict structured output after reasoning/final separation | TH | DONE | PRs #100/#111 |
| EV-1..EV-2 | canonical evaluation preparation + persisted reasoning identity | TH | DONE | PRs #100/#108 |
| ID-1..ID-2 | exact artifact verification receipt + CLI/store | — | DONE | PRs #100/#103 |
| HE-1 | verified identity flows into hardware evidence/review | ID-2 | DONE | PR #107 |
| RES-1 | deterministic resource admission/accounting coverage | — | DONE | PR #100 |
| BRIDGE-1 | privacy-safe thinking capture + full device bundle validator | convergence | DONE | accepted on `de899cc945e1d1c735a2ded91c5da717ce0fe2b0` |
| TH-E1 | target-Mac explicit thinking OFF/ON-hidden campaign | BRIDGE-1 | READY | produce `thinking-campaign.json` |
| EV-3 | two comparable OFF evaluation runs | BRIDGE-1 | READY | exact 10-sample/seed-0 workload |
| HE-2 | two compatible verified 3-cycle reclamation reports | BRIDGE-1 | READY | run + conservative review |
| RES-2 | bounded real-device admit/account/release/reject smoke | BRIDGE-1 | READY | physical run pending |
| DOC-1 | reconcile durable docs with observed results | Wave D | BLOCKED | wait for physical evidence |
| REL-1 | cumulative green gate + finalization | TH-E1, EV-3, HE-2, RES-2, DOC-1 | BLOCKED | wait for validated bundle |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

## Accepted deterministic bridge

The accepted bridge is repository tooling, not physical evidence:

```text
python -m local_llm_server.l2_evidence_bridge capture-thinking
python -m local_llm_server.l2_evidence_bridge validate-hardware-bundle
```

`docs/device-evidence-runbook.md` owns the exact commands and safety margins. `.engineering/l2-evidence-bridge.json` owns the machine-readable minimum bundle. Repository Health blocks on `scripts/verify_l2_evidence_bridge.py` so procedures, product-ui privacy policy, templates and validator commands cannot drift silently.

The bundle validator requires:

- TH-E1 explicit OFF and ON-hidden successful application responses without normal-content reasoning boundaries;
- EV-3 two complete `general-purpose v1.0.0`, `sample_count=10`, `seed=0`, reasoning-OFF reports that are attribution-safe comparable evidence;
- HE-2 two compatible verified reports with at least six complete error-free windows, plus stored review matching a conservative recomputation;
- RES-2 successful safe admission/inference, positive resident accounting, zero accounting after unload, green/cold health and insufficient-budget rejection before backend construction;
- `automatic_eviction_exercised=false` and no production-safety/automatic-eviction promotion.

A non-zero validation result is an incomplete/incompatible evidence result, not permission to loosen thresholds.

## Wave D — representative Mac

The four campaigns are logically parallel but heavy executions on one Mac should be serialized.

### TH-E1 — thinking execution/exposure

Use the packaged `capture-thinking` procedure on the same verified resident runtime. It internally sends the same deterministic workload under explicit OFF and ON-hidden policies and retains only bounded identity/policy/outcome metadata. It does not write prompt, model output or raw response.

Acceptance is a complete `thinking-campaign.json`, not a universal model-family claim.

### EV-3 — evaluation repeatability

Run the exact OFF workload twice using the same verified runtime:

- `general-purpose` v1.0.0;
- 10 samples;
- seed 0;
- explicit reasoning `off`.

Every selected sample must succeed or carry an explicit typed failure. The bundle validator uses the canonical evaluation comparison logic and requires identical selection plus compatible runtime/reasoning identity. Optional ON evaluation is a separate descriptive experiment.

### HE-2 — Apple Silicon reclamation

Produce two independent 3-cycle reports using the same exact artifact, backend, config, hardware/environment and procedure. Run the conservative reviewer. The bundle validator then recomputes that review from the raw reports rather than trusting the stored result.

Positive, mixed, negative and inconclusive observations remain as observed. A negative device result is not a failed software-test result and must not be rerun merely to manufacture favorable evidence.

### RES-2 — bounded resource-policy smoke

Run the macOS safety-gated smoke with measured available memory and conservative host headroom. It must exercise safe admission, one inference, accounting while resident, full accounting release and a one-byte-below-estimate rejection before backend construction. Do not lower safety margins merely to force execution.

## Closure

After all source evidence exists:

1. run `validate-hardware-bundle` and retain the bounded summary;
2. reconcile `docs/current-state.md` and relevant runtime/evidence docs with observed results only;
3. do not commit private source evidence wholesale;
4. keep automatic eviction disabled unless a separate later policy decision is justified by broader evidence;
5. rerun the deterministic repository gate after evidence-ledger/doc changes;
6. finalize/delete this workstream only after durable truth has moved to owning docs.

## Stop conditions

Stop and surface the real result if the target model cannot honor the advertised thinking contract, a receipt is stale, reports are incompatible, the Mac lacks the safety margin, structured output needs repair, a claim depends on unexecuted device behavior, or evidence is negative/inconclusive. Never alter evidence or thresholds solely to obtain a favorable gate.

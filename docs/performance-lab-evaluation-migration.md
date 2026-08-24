# Performance Lab evaluation migration

Status: active transition
Owner: Local LLM Server / Performance Lab integration
Last reviewed: 2026-08-24

## Decision

Long-term benchmark/evaluation product ownership belongs to `daniele21/performance-lab`.

Local LLM Server remains the serving/runtime control plane. It owns resident model lifecycle, request execution, capability truth, public runtime identity, provider-observed metrics, resource admission/reclamation and hardware/runtime correctness evidence.

The existing Local LLM Server evaluation subsystem is transitional and receives no new product scope. It is retained only while the current evidence wave and migration gates require it.

## Keep in Local LLM Server

These runtime/provider responsibilities are not migration candidates:

- `/v1/models` and `/v1/chat/completions`;
- resident runtime loading/routing/leases and task/capability validation;
- `/v1/runtime/identity` and `local-llm-identity-v1` evidence;
- `/status` and completion/streaming/runtime metrics;
- hardware/resource/admission/reclamation evidence and bounded real-device runners;
- backend-specific thinking/reasoning capability resolution and output normalization required for truthful serving behavior.

Performance Lab may consume these surfaces, but preserves their provider provenance rather than re-owning them.

## Transition out of Local LLM Server

After replacement evidence, these become redundant here:

- `evaluation.py` sample/test-set/score/run-manifest contracts;
- `evaluation_builtin.py` generic evaluation content/scoring;
- `evaluation_testsets.py` custom evaluation data store/upload contract;
- evaluation-specific runner/service orchestration;
- local evaluation report persistence, history and baseline/candidate comparison;
- `/api/v1/evaluation/*` run/test-set/history surfaces;
- Studio Benchmark & Evaluation / evaluation-history surfaces;
- evaluation-only tests after their production owner disappears;
- legacy root `test_inference.py`, `inference_test_config.json` and `inference_results_report.json` after final archive/consumer review.

## Frozen migration dependency

Do **not** remove or semantically change `general-purpose@1.0.0` before EV-3 completes:

```text
general-purpose v1.0.0
sample_count = 10
seed = 0
reasoning = off
2 comparable retained runs
```

Those runs must be produced on the converged real-device runtime. Historical pre-convergence runs are not substitutes.

## MIG-002 continuity policy: legacy stays legacy

The initial migration deliberately chooses **historical-only Local LLM Server evidence** instead of importing old evaluation JSON into Performance Lab.

- Existing and EV-3 reports remain immutable LLS evidence under the contracts that produced them.
- After cutover, all new benchmark/evaluation evidence is created and stored by Performance Lab.
- Performance Lab's `general-diagnostic-starter` is a different experiment from `general-purpose@1.0.0`; neither is relabeled to make history look continuous.
- No cross-product baseline/candidate comparison is claimed unless a future explicit compatibility protocol proves it valid.
- A one-time legacy importer is out of scope unless a concrete archival/query requirement later justifies it.
- Root `inference_results_report.json` is legacy output, not canonical current evaluation history and not an import source for Performance Lab.

This avoids creating a second compatibility layer solely for cosmetic continuity.

## Replacement policy: user outcome, not feature-for-feature cloning

Performance Lab already replaces the core user outcome: evaluate an external inference endpoint with versioned evidence, inspect immutable results and compare compatible runs.

Legacy mechanics are migrated only when a retained consumer needs them:

- custom expectation keys `exact`, `exact_ci`, `contains`, `word_count`, `comma_count` and `json` are not a requirement to preserve the old upload schema. A real required workload should be expressed through Performance Lab's native dataset/evaluator contracts;
- evaluation-specific requested/effective thinking policy is not automatically copied into Performance Lab. Thinking capability remains LLS runtime truth; a PL integration control is added only if a real replacement use case requires it;
- `general-purpose@1.0.0` mixes request/task semantics that are not identical to Performance Lab's current generic chat orchestrator. Exact replay is therefore an optional legacy compatibility feature, not a migration prerequisite.

## Repository-known consumers

The repository proves the following consumers of the evaluation subsystem:

- `static/control-plane-evaluation.js` directly calls test-set list/import and evaluation-run endpoints and renders the current result;
- `static/control-plane-evaluation-history.js` directly calls history list/detail/compare endpoints;
- evaluation API/service/history/UI tests cover those same owners;
- the active real-device evidence workflow requires EV-3 on `general-purpose@1.0.0`.

No additional external consumer can be established from repository contents. That is not proof that external scripts do not exist, so route removal still requires visible deprecation/replacement messaging and a release boundary.

## Cutover sequence

1. **Retain EV-3.** Finish the two required post-convergence real-device legacy runs.
2. **Prove the replacement.** Run Performance Lab against the same real LLS serving product with `/v1/runtime/identity` required and `/status` sampled; retain the PL fingerprint and `.plab.zip`.
3. **Redirect Studio/users.** Replace Benchmark & Evaluation navigation/copy with the supported Performance Lab workflow before disabling evaluation run/write behavior.
4. **Freeze legacy history.** At cutover, stop creating new LLS evaluation evidence. Retained reports remain historical artifacts under their existing identities.
5. **Disable/remove redundant evaluation.** Remove evaluation run/test-set/history product paths and their tests only after known consumers are redirected.
6. **Run cross-repository smoke.** Verify `/v1/models`, `/v1/chat/completions`, `/v1/runtime/identity`, `/status`, resource/reclamation behavior and Performance Lab evaluation all remain correct.

## Removal gate

Redundant evaluation code may be removed only after all are true:

- EV-3 evidence is retained;
- Performance Lab representative real-runtime evidence is retained;
- Studio/users have a replacement path;
- legacy history is frozen under the historical-only policy;
- no repository-known consumer still requires evaluation run/write routes;
- cross-repository smoke is green on a real runtime;
- serving, identity, telemetry, resource and hardware-evidence behavior remains unchanged.

Until then, evaluation is a bounded compatibility/evidence surface and should not gain new product scope.

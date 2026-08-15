# Runtime status reference

Status: active
Document type: operational-reference
Owner: runtime observability
Canonical scope: operations.runtime-status
Read when: consuming `/status`, correlating runtime activity with inference, or integrating AI Performance Lab telemetry
Last reviewed: 2026-08-15

`GET /status` is the dynamic operational surface for resident runtimes. It is intentionally separate from `GET /v1/runtime/identity`, which describes stable execution identity that can be frozen before an evaluation run.

## Identity, status and evidence are different

Use the three surfaces for different questions:

| Question | Surface |
| --- | --- |
| What models are resident? | `/v1/models` |
| What exact model/runtime/config/hardware identity is active? | `/v1/runtime/identity` |
| What is the runtime doing right now? | `/status` |
| What broader privacy-safe resource/task evidence is available? | `/api/v1/evidence` when admin API is enabled |

Do not use a mutable `/status` sample as a substitute for the execution fingerprint. Do not use static identity as a substitute for load/phase telemetry.

## Multi-runtime shape

The supported multi-runtime status response exposes a top-level default route and a map of resident runtime state:

```json
{
  "default_model": "nemotron-nano-4b-q8",
  "models": {
    "nemotron-nano-4b-q8": {
      "model": "nemotron-nano-4b-q8",
      "backend": "llama_cpp",
      "loaded_at": 1786800000.0,
      "state": "ready",
      "active_requests": 1,
      "max_concurrent_requests": 1,
      "phase": "generating",
      "output_chunks": 12,
      "output_characters": 640,
      "chunks_per_second": 18.4
    }
  }
}
```

Consumers should tolerate additive fields. A metric absent from a runtime should remain unavailable rather than being treated as zero.

## Field semantics

| Field | Meaning | Stability |
| --- | --- | --- |
| `default_model` | current default resident route when one exists | mutable routing state |
| `models` | resident runtime states keyed by server/runtime key | mutable residency state |
| `model` | model identifier associated with that runtime | descriptive; use identity endpoint for canonical fingerprinting |
| `backend` | active backend label | descriptive; use identity endpoint for versioned runtime identity |
| `loaded_at` | runtime load timestamp when available | runtime-instance metadata |
| `state` | lifecycle/readiness state | mutable |
| `active_requests` | currently active requests | instantaneous counter |
| `max_concurrent_requests` | effective per-runtime concurrency cap | configuration/reporting state |
| `phase` | current observed inference phase | instantaneous state |
| `output_chunks` | observed output chunks for the tracked active request/state | runtime observational counter |
| `output_characters` | observed output characters | runtime observational counter |
| `chunks_per_second` | runtime-observed chunk emission rate | sampled runtime metric |

Common phase values include states such as `idle`, `prompt_eval` and `generating` where the backend exposes that distinction. Consumers must not require every backend to report every phase.

## Chunks are not tokens

`chunks_per_second` is deliberately named for its measurement source. A transport/runtime chunk can contain zero, one or multiple model tokens depending on the backend and buffering behavior.

Never relabel:

```text
chunks_per_second -> tokens_per_second
```

Token throughput should be computed only when token counts and timing boundaries are actually observable from the inference/runtime evidence path.

## Sampling limitations

`/status` is a point-in-time observation. Polling it cannot guarantee observation of short phases that occur between samples. Therefore:

- phase ratios are sampling-dependent;
- peaks can be missed between polls;
- very short requests may appear entirely idle to a slow collector;
- comparing two runs requires the same sampling protocol/interval if sampled status metrics matter.

For a 50 ms client poll, a 10 ms prefill phase may legitimately never appear in samples.

## AI Performance Lab mapping

Performance Lab's `local-llm-server-status-v1` collector currently consumes selected fields to produce runtime-provenance measurements such as:

- status sample count and sample errors;
- observed sampling duration;
- peak active requests;
- active/generating/prompt-eval sample ratios;
- peak observed chunks per second;
- peak observed output chunks/characters;
- reported maximum concurrency.

The collector does not promote `backend`, `model`, `loaded_at` or `state` into canonical execution identity. Identity comes from the separate `local-llm-identity-v1` contract.

## `unknown`, `unavailable`, zero and idle

These states are not interchangeable:

- `0` means an observed numerical zero;
- `idle` is an observed runtime phase/state;
- a missing field means the backend/server did not provide that evidence;
- `null` may represent explicitly unknown/not observed data depending on the field contract.

Client UIs and evaluators should preserve this distinction. Fabricating zero from absence creates false performance/resource claims.

## When to prefer another endpoint

If you need a comparison identity such as quantization, artifact hash, runtime version or configuration digest, use `/v1/runtime/identity`.

If you need host/resource policy and administrative evidence, use the corresponding `/api/v1/*` evidence/resource endpoints when enabled.

If you need model output, token usage or TTFT at the application boundary, use `/v1/chat/completions` and its streaming/usage semantics rather than trying to reconstruct them from `/status`.
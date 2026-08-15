# Public runtime identity API

Status: active specification  
Protocol: `local-llm-identity-v1`  
Endpoint: `GET /v1/runtime/identity`

Local LLM Server is the source of truth for the model artifact and serving runtime that are actually resident. The public identity endpoint exposes that information to external evaluation systems such as AI Performance Lab without exposing model paths, download URLs, credentials, prompts, outputs, hostnames, or mutable request counters.

The identity API is separate from `/status`: `/status` is dynamic operational telemetry, while `/v1/runtime/identity` describes the stable execution identity that should be frozen before an evaluation run.

## Response contract

```json
{
  "protocol_version": "local-llm-identity-v1",
  "server": {
    "name": "local-llm-server",
    "version": "0.3.8"
  },
  "default_model": "nemotron-nano-4b",
  "models": {
    "nemotron-nano-4b": {
      "model": {
        "id": "nvidia/nemotron-3-nano-4b",
        "revision": null,
        "artifact_digest": null,
        "artifact_key": null,
        "quantization": "Q4_K_M",
        "verification": "available_unverified"
      },
      "runtime": {
        "name": "llama_cpp",
        "version": "0.3.x",
        "implementation": "...",
        "config_digest": "<sha256>",
        "config": {
          "backend": "llama_cpp",
          "ctx_size": 36466,
          "n_threads": 8
        },
        "fingerprint": null,
        "captured_at": null,
        "evidence_grade": "partial"
      },
      "hardware": {
        "system": "darwin",
        "machine": "arm64",
        "processor": null,
        "logical_cpus": 10,
        "total_memory_bytes": null,
        "accelerator": null,
        "extra": {}
      }
    }
  }
}
```

## Evidence rules

- `model.id` is the effective resident model ID.
- `model.revision` is emitted only when explicitly known.
- `model.artifact_digest` is emitted only from a valid explicit SHA-256 pin and uses the `sha256:<hex>` form.
- `model.quantization` is explicit metadata from resolved configuration/registry. It is never inferred by consumers from a filename.
- `runtime.name` is the effective backend.
- `runtime.version` is resolved from the backend package, an explicit backend version, or the supported backend-specific probe. Unknown stays `null`.
- `runtime.config` contains only the same allowlisted non-sensitive effective settings covered by `runtime.config_digest`.
- `runtime.fingerprint` and `captured_at` are present only when the existing evidence-grade runtime fingerprint was successfully captured.
- `hardware` intentionally excludes hostname or other direct machine identifiers.

`evidence_grade=verified` means the existing runtime fingerprint capture had both a verified artifact SHA-256 and a resolved backend version. A resident runtime may still expose useful partial identity when that stronger evidence is unavailable.

## Privacy boundary

The serialized contract must not contain:

- `model_path`, `mmproj_path`, local directories or private absolute paths;
- download URLs or repository credentials;
- API keys, authorization headers or environment-variable values;
- prompts, model output, thinking traces or cached inference content;
- hostname or user identity;
- dynamic request counters (those belong to `/status`).

## Consumer mapping

AI Performance Lab maps the protocol into its immutable `ExecutionFingerprint`:

- model ID/revision/digest/quantization -> `ModelIdentity`;
- backend name/version/config digest -> `RuntimeIdentity`;
- machine/CPU/accelerator/memory/OS -> `HardwareIdentity`.

The protocol is optional. OpenAI-compatible inference remains independently usable when this endpoint is absent.

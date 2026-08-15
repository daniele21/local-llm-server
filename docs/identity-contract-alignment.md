# AI Performance Lab identity alignment

Local LLM Server produces `local-llm-identity-v1` at `GET /v1/runtime/identity`.
AI Performance Lab task `INT-002` consumes the same protocol and maps its stable fields into the evaluation `ExecutionFingerprint`.

The two repositories intentionally keep separate responsibilities:

- Local LLM Server owns discovery of the resident model, backend, safe effective runtime configuration and local hardware profile.
- AI Performance Lab owns validation, fingerprint mapping, comparison semantics, benchmark execution and evidence persistence.
- The OpenAI-compatible inference API and `/status` telemetry remain independent contracts.
- Missing identity evidence remains missing; neither side infers quantization, revisions, hashes or runtime versions from suggestive filenames or labels.

Any incompatible wire-format change requires a new protocol version rather than silent mutation of `local-llm-identity-v1`.

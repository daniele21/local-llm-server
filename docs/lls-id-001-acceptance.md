# LLS-ID-001 — Public execution identity producer

Status: implementation validation

## Acceptance criteria

- expose `GET /v1/runtime/identity` on the supported public product stack;
- identify the wire protocol as `local-llm-identity-v1`;
- reuse existing artifact/backend/config/hardware identity primitives rather than duplicating inference logic;
- expose explicit quantization metadata without filename inference;
- expose a safe effective runtime-config payload and its matching digest;
- preserve unknown revision/hash/backend-version values rather than fabricating them;
- distinguish partial from verified runtime fingerprint evidence;
- never serialize private model paths, download URLs, credentials, prompts, outputs, hostnames or dynamic request counters;
- support multiple resident runtimes and identify the resident default;
- deterministic tests cover privacy, partial/verified identity and multi-runtime behavior;
- producer documentation stays aligned with AI Performance Lab `INT-002`.

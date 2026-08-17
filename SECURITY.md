# Security policy

## Reporting a vulnerability

Report security issues privately through GitHub's security-advisory/private vulnerability reporting flow for this repository when available. If that flow is unavailable, contact the repository owner privately through GitHub before publishing exploit details.

Do not open a public issue containing credentials, private user data, reproducible exploit payloads, private model paths or other information that would increase exploitation risk before a remediation path is agreed.

## Supported versions

Security fixes are developed on the current development line and released from the current supported `0.4.x` product line. Older development snapshots, archived branches and historical artifacts are not supported security baselines unless a release note explicitly says otherwise.

## Trust model

Local LLM Server is local-first infrastructure. The default product trust boundary is the local machine and loopback interface.

- The normal server bind default is loopback. Binding beyond loopback is an explicit operator decision and requires an explicit trusted-network/authentication boundary outside the default product assumptions.
- Local inference must not silently fall back to remote execution.
- Remote HTTP(S) media is rejected unless explicitly enabled by policy.
- Remote model code/trust is an explicit configuration decision; it is never inferred merely because a model requires it.
- Model artifacts, inference engines and optional backend packages are executable/data inputs with their own supply-chain and parser risk. Operators should obtain them from trusted sources and verify artifacts when integrity matters.
- Administrative APIs are disabled by default and should not be exposed to untrusted networks.

## Sensitive data boundaries

Prompts, model outputs, uploaded media, transcripts, evaluation samples and local model paths can contain sensitive information. The product therefore follows these defaults:

- application-facing runtime identity is path-free and must not expose credentials, prompts, outputs, hostnames or private filesystem locations;
- normal logs and telemetry must avoid raw prompt/output/media content unless a user explicitly enables a diagnostic path that documents the exposure;
- deterministic browser fixtures use synthetic content and must not ingest user model files or personal evaluation corpora;
- failure screenshots, traces, logs and other E2E evidence are bounded diagnostic artifacts rather than durable repository documentation;
- hardware/evaluation evidence must retain only the information required to support the stated claim, and must preserve the existing distinction between public-safe identity and local/private evidence;
- secrets, API keys, tokens, signing material and private credentials must never be committed to the repository or bundled into build artifacts.

## Data lifecycle

Project-owned temporary and generated state must have an explicit owner and cleanup boundary.

- Runtime/E2E temporary directories are run-scoped where practical and must be cleaned on success, failure, timeout, cancellation, interrupt and partial initialization.
- Cleanup must verify ownership before deleting state; broad deletion of user-controlled directories is not an acceptable cleanup strategy.
- Successful cleanup should verify that project-owned child processes/listeners and run-owned temporary state no longer remain.
- Evaluation and hardware-evidence files are retained only when deliberately selected as evidence. The active repo-template adoption workstream does not treat the existing local `evidence/` tree as automatically publishable or disposable.
- Build outputs are generated artifacts. They must not contain secrets/private paths and are governed by the artifact lifecycle in `.engineering/commands.json`.
- Model caches/downloads are user-owned durable data unless a command explicitly states that it owns and removes them; generic repository `clean` must not delete user model caches.

## Security-sensitive changes

Changes affecting any of the following require focused tests and review of trust/data boundaries:

- bind address, CORS, authentication or administrative API exposure;
- remote media, downloads, remote code or model-loading trust;
- filesystem paths, uploads, archives or temporary-file handling;
- subprocess creation, signals, shutdown or cleanup ownership;
- public runtime identity, logs, telemetry or evidence serialization;
- dependency resolution, release artifacts, checksums, tags or provenance;
- deletion, retention or migration of user/evaluation/evidence data.

Do not weaken a security gate merely to make CI pass. If representative-device behavior or an external GitHub/release configuration has not been verified, record it as pending instead of making a stronger claim.

## Dependency and release hygiene

- Python and Node dependency state used by CI should be committed and reproducible.
- Security-relevant dependency updates should preserve deterministic tests and browser acceptance.
- Successful release artifacts must be immutable, identifiable by source revision/build identity and accompanied by the checksums/manifest required by the repository operating contract.
- Release tags must not be force-moved after publication.

This policy describes the intended security boundary of the supported product. More detailed runtime behavior remains owned by the relevant architecture/API/evidence documentation and executable tests.
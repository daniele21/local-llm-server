# Persisted state compatibility and recovery

Status: active
Owner: repository engineering
Read when: changing evaluation persistence, custom test sets, artifact verification receipts or recovery behavior
Last reviewed: 2026-08-17

## Owned state

The bounded recovery surface contains only small JSON state owned by Local LLM Server:

- evaluation reports from the configured evaluation root;
- custom test sets under its `test_sets/` child;
- artifact-verification receipts from the configured local receipt root.

Model weights/download caches, Hugging Face/LM Studio state, build artifacts, logs, temporary files and arbitrary user paths are **not** backup categories and are never recursively copied by the state archive.

## Compatibility

The state archive itself is schema version `1` and uses exact category names. Custom test sets already use their own schema version `1`.

Pre-L1 evaluation reports and artifact-verification receipts are explicit legacy schema `0` shapes because they were persisted without a schema field. The recovery reader intentionally supports them. Evaluation report schema `1` is the same compatible report body with an explicit top-level version reserved for future writers. Artifact receipt schema `1` may wrap the legacy private receipt payload under `receipt`.

Unknown future schema versions fail closed. Readers do not silently rewrite legacy state merely because it was read. Any future incompatible schema must add an explicit migration/compatibility path and tests before release.

## Export

Run:

```bash
python -m local_llm_server.state_backup export --output ~/local-llm-state.json
```

Optional `--evaluation-dir` and `--verification-dir` override the product defaults for migration/testing.

Export enumerates only allow-listed `*.json` files in the owned category roots, validates every payload, canonicalizes it, records SHA-256 and writes the archive atomically. File count, entry size and total archive size are bounded. An invalid owned JSON file fails the export rather than being silently omitted.

Because evaluation reports can intentionally retain prompts/expected/output content, **the archive may contain sensitive user content**. It remains local and is never uploaded automatically. Protect/delete it according to the same policy as the source state.

## Restore

Run into an empty/new state location first when recovering manually:

```bash
python -m local_llm_server.state_backup restore --input ~/local-llm-state.json
```

Restore validates the complete archive before creating directories or writing files: archive/category schema, safe basename, duplicates, size limits, checksum and category-specific payload semantics. Traversal/absolute paths are rejected.

Existing target files fail the restore by default. `--replace` is an explicit operator decision; unrelated files are never deleted. Restored files are staged as owned temporary files and promoted with `os.replace` only after archive validation.

## Recovery procedure

1. Stop the server before restoring shared state.
2. Keep the original state directories unchanged until archive validation succeeds.
3. Prefer restoring into fresh directories and point the server to them with configuration overrides for verification.
4. Start the server and inspect evaluation/test-set/verification behavior.
5. Only after verification retire the old state.

Do not use a generic `clean` command as recovery. Generic cleanup must not delete durable evaluation or verification data.

## Release rule

A release that changes one of these persisted formats must retain backward compatibility or provide an explicit migration path. Irreversible changes require release notes and a pre-migration export. Downgrades must never destructively reinterpret unknown future state.

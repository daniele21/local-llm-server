# Release, rollback and recovery runbook

Status: active
Owner: repository engineering
Read when: preparing, publishing, verifying or recovering a Local LLM Server release
Last reviewed: 2026-08-17

## Release invariants

- Product version, build ID and source revision are different identities.
- Existing tags and GitHub Releases are immutable. Never force-move a release tag or replace assets in an existing release.
- A release is published only after deterministic tests, staged artifact validation and fresh-install wheel smoke succeed.
- A release failure before GitHub Release creation leaves no published release to repair in place; fix the source/workflow and create a new version/tag.
- Model weights, local caches, evaluation data and verification receipts are not release assets.

## Preflight

1. Start from a clean `main` checkout containing the intended integrated changes.
2. Run canonical setup/check/test/E2E/build gates and review any representative-device evidence required by the claims in the release notes.
3. Confirm `VERSION`, `pyproject.toml` and `uv.lock` are coherent.
4. Confirm no target tag already exists locally or remotely.
5. Review `CHANGELOG.md`, migration/compatibility notes and known limitations.

`release.sh` performs the clean-main check, patch version bump, local immutable build, deterministic tests, version/lock commit, immutable annotated tag creation and non-force push.

## Automated publication gate

The tag-triggered `Release` workflow:

1. verifies tag/version identity;
2. synchronizes the committed lock-backed build toolchain;
3. builds wheel/sdist into staging and promotes only validated output;
4. creates a **fresh temporary environment**, installs exact locked runtime dependencies except the intentionally hosted-CI-excluded native `llama-cpp-python`, installs the built wheel, runs `local-llm --help`, verifies installed version/entry point and required package data;
5. copies manifest, checksum inventory and build delta into the release handoff;
6. refuses to replace an existing GitHub Release;
7. creates the immutable GitHub Release.

A native-backend/model smoke remains a representative-runtime evidence gate when the release claim depends on it; package smoke is not relabelled backend evidence.

## Post-publish verification

After GitHub Release creation:

- verify the expected version/tag and release assets are present;
- verify `SHA256SUMS` matches the attached bundle/metadata it covers;
- inspect `build-manifest.json` for expected source revision/channel/variant;
- inspect `BUILD_CHANGELOG.md` for unexpected dependency/toolchain/config changes;
- when a runtime-specific claim is made, link the exact retained real-runtime/hardware evidence used for that claim.

Do not edit a published release to hide an observed problem. Add an explicit note only when needed to warn consumers while a corrective release is prepared.

## Rollback semantics

A rollback never rewrites history.

### Consumer rollback

When the previous immutable release is still safe/compatible, direct consumers back to that existing version/tag and state the compatibility/data implications. This changes the selected version, not the old release artifact.

### Corrective release

When code/config/migration behavior must change, fix forward on source and publish a **new patch/minor version**. The corrective release records the bad version, impact, remediation and any state-recovery steps.

### Release withdrawal

If a release should no longer be recommended, mark it clearly as affected/deprecated in communication and point to the safe version. Do not delete or silently replace the evidence unless a security incident requires restricted handling; preserve enough audit history to explain what shipped.

## Recovery from publication failures

- **Build/package/fresh-install failure:** no release is published; repair source/tooling and create a new tag/version after normal review.
- **Handoff artifact failure:** no GitHub Release is created because publication depends on the build job; rerun only when the exact tag/source is unchanged and the failure was infrastructure-only. If source must change, create a new version/tag.
- **GitHub Release creation failure with tag already pushed:** do not move the tag. If retrying the exact workflow would publish the exact already-verified source/assets, a workflow retry is allowed. If any source/build input changes, publish a new version/tag instead.
- **Bad release discovered after publication:** choose consumer rollback or corrective release; never replace tag/assets in place.

## Persisted-state compatibility

Before a release changes a persisted schema or data contract, the corresponding migration/backward-compatibility and recovery tests must already be integrated. Release notes state any minimum compatible version or irreversible migration. Destructive automatic downgrade is not permitted.

## Evidence to retain

Durable release storage owns published artifacts, manifest/checksums and build delta. CI handoff/debug artifacts remain bounded temporary evidence. Representative runtime/hardware evidence is retained under its own identity/runbook rather than copied into release binaries.

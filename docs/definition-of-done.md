# Definition of done

Status: active
Document type: completion-policy
Owner: repository
Canonical scope: delivery.completion
Read when: deciding whether a task, milestone, UX surface or release-quality claim is complete
Last reviewed: 2026-08-15

This policy prevents “code exists” from being confused with “product behavior is complete”. A roadmap item may be marked `DONE` only when the applicable gates below are satisfied.

## 1. Completion levels

### Implementation complete

The intended code path exists and narrow deterministic tests pass.

This is insufficient for `DONE` when the task also requires integration, UX, security or hardware evidence.

### Integration complete

The behavior is connected to its real owner/consumer, repository-wide compatibility checks pass and no duplicate temporary architecture remains without an explicit removal plan.

### Evidence complete

Claims that depend on real inference engines, operating-system resource behavior or user-visible runtime state have representative evidence.

### Product complete

Implementation, integration, evidence, UX/accessibility and documentation gates are satisfied for the stated milestone.

## 2. Universal merge gate

Every coherent change must satisfy:

- tests covering the changed owner and direct consumers;
- lint/format/static checks applicable to changed code;
- no intentionally suppressed failing test gate;
- `git diff --check` equivalent cleanliness where available;
- no new secret, model binary, private user path or sensitive runtime content committed;
- public errors/logs remain bounded and privacy-safe;
- affected plan/current-state/workstream documentation updated in the same integration change;
- no target document updated merely to make implementation look complete.

## 3. Runtime/lifecycle gate

Changes to model/runtime lifecycle are complete only when:

- state transitions are explicit and deterministic;
- success, failure, cancellation and shutdown paths are tested;
- active leases cannot be invalidated by unload/eviction;
- startup failure cleans owned partial state;
- bounded shutdown behavior is specified and tested;
- no child process is orphaned after normal or failed shutdown;
- zero-resident behavior remains valid once introduced;
- unload never implies artifact deletion;
- any automatic eviction reason is observable.

For memory reclamation claims, representative hardware evidence is mandatory.

## 4. Resource-management gate

ResourceManager/residency policy work is complete only when:

- estimates and observations are separate fields/types;
- unavailable values remain unavailable rather than becoming zero;
- budget/headroom arithmetic is deterministic and unit-tested;
- concurrent load reservation prevents known overcommit races;
- explicit resource exhaustion is returned before relying on OOM as normal control flow;
- active/pinned runtime protections are tested;
- pressure transitions have deterministic semantics;
- representative hardware validates resource readings and post-unload behavior.

## 5. API/capability gate

A task/capability/API change is complete only when:

- capability metadata has one canonical owner;
- unsupported combinations fail before backend execution;
- public request/response behavior has compatibility tests;
- backend-specific details do not leak into core contracts unnecessarily;
- task-specific endpoint behavior does not duplicate runtime policy;
- streaming/cancellation/error semantics are covered where applicable;
- OpenAPI/client examples match real behavior.

## 6. Audio/media gate

Audio/image work is complete only when:

- allowed media types/size limits are explicit;
- remote media behavior is policy-controlled and disabled by default unless the product target changes;
- owned temporary media is cleaned after success/failure/cancellation;
- sensitive media paths/payloads do not appear in normal logs;
- large media paths avoid unreasonable duplicate buffering where a safer streaming/multipart path is available;
- ASR/transcription behavior is not misrepresented as generic audio-chat capability.

## 7. Security/privacy gate

Security/privacy-sensitive work is complete only when:

- local loopback behavior remains the default;
- network sharing is explicit;
- remote code execution/trust is opt-in and documented;
- no silent cloud inference fallback exists;
- model/source integrity checks fail closed where implemented;
- telemetry excludes prompt/output/media content by default;
- shareable reports exclude private paths, tokens and sensitive local metadata;
- negative/fail-closed tests exist for important policy defaults.

## 8. Observability gate

A metric/event is production-ready only when:

- its name matches what is actually measured;
- units are explicit;
- source/backend semantics are documented;
- unavailable source data remains unavailable;
- aggregation window/percentile semantics are clear;
- request correlation is privacy-safe;
- prompt/output content is not required for normal operational telemetry;
- UI labels use the canonical metric vocabulary.

A chunk counter cannot be labelled token count or tokens/second.

## 9. Artifact/fingerprint gate

Artifact identity work is complete only when:

- immutable identity does not depend on display name or local path;
- SHA/revision/source semantics are defined;
- incomplete/unverified state is explicit;
- config digest serialization is deterministic;
- backend/server versions are captured where required;
- hardware profile semantics are bounded;
- a stored benchmark/result can resolve the identity required for reproduction;
- incompatible fingerprints are not silently compared as equivalent runs.

## 10. Benchmark/evaluation gate

A benchmark capability is complete only when:

- test set identity/version is durable;
- sample selection is reproducible or explicitly random with recorded seed;
- failed/cancelled/inconclusive samples remain represented;
- cold/warm mode is explicit;
- performance metrics use canonical semantics;
- quality scorer identity/configuration is recorded;
- model artifact/backend/config/hardware/run identity is persisted;
- comparison rejects or visibly flags incompatible identities;
- benchmark execution does not silently disturb unrelated production/runtime state;
- reports separate measured facts from composite interpretation.

## 11. UX/UI screen gate

A primary screen is `DONE` only when:

- it uses real shared source-backed state;
- loading, empty, unavailable, warning, error and success states are handled where applicable;
- no illustrative mockup metric appears as live product state;
- user actions are state-aware and have deterministic feedback;
- destructive operations communicate impact and require appropriate confirmation;
- navigation/refresh does not trigger domain work unexpectedly;
- component/state tests cover major variants;
- keyboard navigation and visible focus work;
- semantic labels exist for icon-only controls;
- status is not conveyed by color alone;
- reference responsive widths and 200% zoom remain usable;
- representative runtime behavior is reflected correctly for screens that claim runtime/resource state.

## 12. Design-system/brand gate

Brand/design work is complete only when:

- tokens have a single implementation owner;
- product language follows [`brand-guidelines.md`](brand-guidelines.md);
- light/dark semantics are consistent;
- colors meet applicable contrast requirements;
- reusable components encode real shared concepts;
- target/generated mockups are not presented as shipped screenshots;
- final logo/assets are reproducible, vendor-independent and available in required variants;
- screenshots used publicly come from real implemented states.

## 13. Documentation gate

A milestone that changes product behavior is not complete until:

- [`current-state.md`](current-state.md) reflects integrated reality;
- [`roadmap.md`](roadmap.md) status/dependencies are updated;
- affected focused workstream tracker is updated;
- target specs reflect any intentional behavior change;
- README/API examples are updated if the public contract changed;
- stale or contradictory duplicated claims are removed;
- measured evidence is labelled with hardware/runtime identity.

## 14. Hardware evidence gate

Representative hardware evidence is required before finalizing claims about:

- memory residency/reclamation;
- unified-memory/GPU footprint;
- safe model concurrency;
- performance/throughput/TTFT;
- thermal behavior;
- auto-eviction under pressure;
- backend/runtime stability during repeated lifecycle operations.

At minimum, evidence records:

- OS + version;
- CPU/GPU/device profile;
- physical/unified memory;
- exact artifact fingerprint;
- backend/runtime version;
- resolved configuration;
- test procedure/version;
- raw/derived result reference;
- known limitations.

CI/mock/emulator evidence may establish deterministic correctness but must not be relabelled as representative hardware performance evidence.

## 15. Release-candidate gate for this program

The control-plane/UX repositioning program may be called product-grade/release-candidate only when:

- CI fails on real regressions;
- core infrastructure is consumer-agnostic;
- local privacy defaults are hardened;
- canonical tasks/capabilities exist for implemented text/vision/audio paths;
- resource admission exists and memory lifecycle has representative evidence;
- zero-resident state and bounded shutdown work;
- scheduler/cancellation/overload semantics are explicit;
- metrics are truthful across supported backends;
- artifact/runtime fingerprint supports reproducible evaluation;
- redesigned primary UX surfaces meet their source-backed acceptance criteria;
- benchmark/evaluation workflow produces reproducible comparisons;
- accessibility/responsive gates pass;
- README/portfolio positioning matches shipped reality.

Until all applicable gates are satisfied, documentation should use precise qualifiers such as `planned`, `partial`, `evidence pending` or `experimental` rather than collapsing them into a generic “supported”.

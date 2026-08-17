# L1 production readiness

Status: active
Owner: repository engineering
Read when: coordinating `repo-template-sw 0.3.0` L1 adoption
Last reviewed: 2026-08-17

## Goal

Raise Local LLM Server from the repository-side L0 baseline to a truthful L1 production-ready engineering baseline without weakening local-first privacy, resource, evidence or artifact invariants.

Canonical branch protection is an owner-deferred exception and is not part of this workstream. Hardware-dependent claims remain owned by `runtime-correctness-evidence-hardening.md` and are not fabricated in hosted CI.

## Work graph

| ID | Work | Depends on | State |
| --- | --- | --- | --- |
| L1-01 | target L1 + gap map + parallel plan | — | DONE |
| L1-02 | supply-chain security and dependency audit gate | L1-01 | DONE |
| L1-03 | persisted-state schema, compatibility, export/restore/recovery | L1-01 | DONE |
| L1-04 | critical failure/cancellation/shutdown/recovery contract matrix | L1-01 | DONE |
| L1-05 | performance/resource budget contract and validation | L1-01 | DONE |
| L1-06 | release/rollback/recovery runbook + fresh-install artifact smoke | L1-01 | DONE |
| L1-07 | identity-bearing privacy-safe E2E failure evidence | L1-01 | DONE |
| L1-08 | shared integration, Repository Health convergence and L1 acceptance | L1-02..L1-07 | ACTIVE |
| L1-09 | transfer durable truth and delete completed workstream | L1-08 | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

## Completed L1 capabilities

### Supply-chain security

- Python runtime dependencies are exported from committed `uv.lock` and audited without re-resolution.
- Node tooling uses the committed npm lock and blocking high/critical audit policy.
- audit tooling is pinned and runs on PR/push, schedule and manual dispatch;
- FastAPI/Starlette were remediated to non-vulnerable locked versions;
- the remaining transitive `diskcache` advisory has an explicit owner, reachability statement, compensating controls, review date and hard expiry rather than an unbounded ignore;
- Dependabot proposes bounded weekly Python/npm updates.

### Persisted-state recovery

- state export is restricted to server-owned JSON: evaluation reports, custom test sets and artifact-verification receipts;
- model weights, caches, logs, artifacts and arbitrary paths are excluded;
- archive/schema/category/checksum/path/size validation completes before restore writes;
- unknown future schemas fail closed and pre-L1 report/receipt shapes remain readable;
- overwrite is explicit and unrelated state is never deleted.

### Lifecycle recovery contracts

- `.engineering/lifecycle-contracts.json` maps critical startup failure, timeout, cancellation, cleanup, shutdown and dependency-failure claims to exact pytest node IDs;
- the zero-dependency validator fails when evidence disappears or required lifecycle phases are no longer represented;
- unsupported worker streaming/cancellation, hardware reclamation and automatic pressure eviction remain explicit non-claims.

### Performance/resource budgets

- deterministic operational limits are machine-readable and validator-enforced;
- hardware-dependent TTFT/throughput/memory observations are kept separate from hosted-CI limits;
- budget units, owners, applicability and boundedness are validated rather than inferred from observed metrics.

### Release operations

- immutable release and rollback semantics are documented;
- rollback uses a prior immutable release or a new corrective release and never rewrites tags/assets;
- the produced wheel is installed into a fresh environment and CLI/package-data smoke-tested;
- artifact staging, checksums, build identity, failure-before-promote and retention remain permanently exercised.

### E2E evidence

- browser failure evidence is identity-bearing and collision-safe by run/attempt/source identity;
- retained files are allow-listed and privacy checked rather than uploading raw traces/page content by default;
- zero-residue process/listener/temp-root verification remains a blocking post-Playwright gate.

## L1-08 integration acceptance

The six implementation lanes were independently validated and progressively rebased/merged onto `dev`. L1-08 now integrates the specialist fitness functions into the canonical Repository Health entrypoint:

- `scripts/verify_performance_budgets.py`;
- `scripts/verify_lifecycle_contracts.py`;
- `scripts/verify_security_exceptions.py`.

For target level L1/L2, `scripts/verify_repository.py` invokes all three. The combined exact head must pass:

- normal CI: lint, Python 3.10/3.11/3.12 and Playwright E2E;
- Repository Health including the three L1 specialist fitness functions;
- artifact lifecycle through the canonical build command;
- Security Audit;
- Package Install Smoke;
- E2E zero-residue verification.

Only after all workflows are green on one exact head may L1-08 be marked DONE.

## L1-09 finalization

After L1-08 succeeds:

1. record the exact validated L1 revision in `.engineering/baseline.json`;
2. move stable operational truth into `docs/current-state.md` and the durable references that already own each capability;
3. remove this completed workstream according to the repository delete-by-default documentation policy;
4. remove its entry from `docs/workstreams/README.md`;
5. run the complete repository validation again after deletion.

## Accepted deviations and external evidence

- canonical GitHub branch protection is explicitly owner-deferred and excluded from this adoption scope;
- real-runtime/model smoke and representative Apple Silicon memory/performance/reclamation evidence remain owned by the runtime-correctness workstream;
- absence of representative hardware evidence constrains only the corresponding hardware/runtime claims, not deterministic repository/build/security/recovery evidence.

## Stop conditions

- a change expands cloud/network trust implicitly;
- recovery can delete model caches or arbitrary user state;
- vulnerability ignores become undocumented or non-expiring;
- a performance budget manufactures hardware claims in hosted CI;
- rollback mutates an existing tag/release;
- E2E evidence retains prompt/output/media/private-path content by default.

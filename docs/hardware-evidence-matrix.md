# Representative hardware evidence matrix

Status: active
Document type: evidence-procedure
Owner: repository
Canonical scope: evidence.hardware
Read when: executing or reviewing hardware-dependent claims for runtime lifecycle, memory recovery or pressure policy
Last reviewed: 2026-08-15

This document turns the hardware gate into a repeatable evidence procedure. It does **not** contain benchmark results and must not be used to imply that memory reclamation or automatic eviction is already proven.

Canonical status lives in [`current-state.md`](current-state.md). Completion criteria live in [`definition-of-done.md`](definition-of-done.md).

## 1. Evidence goal

The minimum objective is to answer, for an exact runtime identity on an exact software/hardware environment:

- can the isolated worker repeatedly start, become ready, complete one bounded inference and stop without lifecycle errors?
- what host available-memory change is observed across `before_start -> after_stop`?
- what child-process RSS is observed while the worker is alive at `after_ready` and `peak` when the OS exposes it?
- are repeated observations compatible and consistent enough to describe, without converting them into a production-safety verdict?

The procedure must **not** answer by assumption:

- that process exit equals reclaimed unified memory;
- that a positive delta once is a PASS;
- that a compatible report group authorizes automatic eviction;
- that CPU/GPU/thermal behavior on one device generalizes to another device;
- that missing RSS/available-memory fields equal zero.

## 2. Minimum repeated-run rule

For one matrix cell, collect at least:

- **2 independent report files**;
- **3 complete lifecycle cycles per report**;
- therefore at least **6 complete cycles** before the default reviewer can describe a repeated pattern;
- zero lifecycle-error cycles for the default review gate;
- zero inconclusive cycles for a conclusive repeated pattern;
- verified artifact/backend identity when available;
- complete environment identity: OS family, OS release, machine architecture and Python version.

These defaults match `local-llm evidence-review` and may be tightened for release review.

## 3. Minimum representative matrix

Do not claim a cell is tested until the actual report paths and review output exist.

| Cell | Platform class | Backend | Workload | Minimum evidence | Status |
| --- | --- | --- | --- | --- | --- |
| H3-MAC-MLX-TEXT | Apple Silicon macOS | `mlx` | bounded text completion | 2 reports x 3 cycles | PENDING REAL DEVICE |
| H3-MAC-GGUF-TEXT | Apple Silicon macOS | `llama_cpp` | bounded text completion | 2 reports x 3 cycles | PENDING REAL DEVICE |
| H3-LINUX-GGUF-CPU | Linux x86_64/arm64 | `llama_cpp` CPU path | bounded text completion | 2 reports x 3 cycles | PENDING REAL DEVICE |

Additional cells are valuable only when the project can actually execute them with trustworthy identity/evidence. Add rather than silently substituting:

- Linux GPU-offloaded GGUF;
- `llama_server` text/multimodal subprocess lifecycle;
- MLX-VLM lifecycle;
- first-class ASR lifecycle once the worker protocol owns a transcription command rather than generic completed chat.

## 4. Cell identity record

Before running a cell, record the following in the evidence index or PR/release note:

| Field | Required | Source |
| --- | --- | --- |
| Cell ID | yes | this matrix |
| anonymized device label | yes | operator-defined, e.g. `mac-m2-16g-a` |
| OS family + release | yes | evidence JSON `environment` |
| architecture | yes | evidence JSON `environment.machine` |
| Python version | yes | evidence JSON `environment.python_version` |
| physical/unified memory | yes when observable | report descriptor/resource preflight |
| backend | yes | report descriptor |
| backend version | yes for verified identity | report descriptor |
| exact artifact SHA-256 | yes for verified identity | report descriptor |
| deterministic config digest | yes | report descriptor |
| accelerator label | recommended | `--accelerator` / report descriptor |
| procedure name | yes | `worker_reclamation_v1` |
| max tokens | yes | report procedure |
| settle-after-stop interval | yes | report procedure |
| raw report paths | yes | retained files |
| review output path | yes after review | retained file |
| limitations/notes | yes | operator note |

Do not put hostname, username, prompt text, generated text or private model paths into the shared evidence index.

## 5. Run procedure

### 5.1 Preflight

Use a clean working tree/revision and record the commit SHA separately from the evidence JSON.

Confirm the exact artifact is already available when possible:

```bash
local-llm models
```

Prefer `--no-download` during repeated evidence runs so network/download behavior does not contaminate lifecycle observations.

Do not close unrelated applications solely to manufacture a positive memory delta; instead note meaningful background-load differences between runs.

### 5.2 First report

Example:

```bash
local-llm evidence-reclamation \
  --model <registry-model-key> \
  --backend <backend> \
  --cycles 3 \
  --max-tokens 32 \
  --settle-seconds 2 \
  --accelerator <bounded-device-label> \
  --no-download \
  --output evidence/<cell-id>/run-01.json
```

The workload prompt is local input only. The generated JSON records `prompt_recorded=false` and `output_recorded=false`.

### 5.3 Independent repeated report

Run a second independent invocation rather than increasing only the cycle count in one process invocation:

```bash
local-llm evidence-reclamation \
  --model <registry-model-key> \
  --backend <backend> \
  --cycles 3 \
  --max-tokens 32 \
  --settle-seconds 2 \
  --accelerator <bounded-device-label> \
  --no-download \
  --output evidence/<cell-id>/run-02.json
```

A third report is recommended when the first two differ materially or when available-memory observations are noisy.

## 6. Review procedure

Review only reports intended to represent the **same** artifact/backend/config/hardware/environment/procedure cell:

```bash
local-llm evidence-review \
  evidence/<cell-id>/run-01.json \
  evidence/<cell-id>/run-02.json \
  --output evidence/<cell-id>/review.json
```

Default review requirements are intentionally conservative:

- minimum 2 reports;
- minimum 6 complete cycles;
- verified runtime identity;
- complete environment identity;
- no lifecycle-error cycles;
- no inconclusive cycles for a conclusive consistency state;
- exact compatibility of procedure/runtime/hardware/environment keys.

Possible descriptive review states include:

- `insufficient`;
- `incompatible`;
- `mixed`;
- `consistent_recovery_observed`;
- `consistent_no_recovery_observed`.

Even `consistent_recovery_observed` remains an **observation summary**, not an automatic-eviction recommendation or production-safety claim.

## 7. Pressure-policy dry run

After the runtime/lifecycle evidence path is healthy on a device, the admin API can sample current host pressure without unloading anything:

```bash
curl -X POST \
  http://127.0.0.1:1235/api/v1/residency/pressure/evaluate
```

Expected response boundaries:

- `mode = dry_run`;
- `action_executed = false`;
- `evaluation.automatic_eviction_enabled = false`;
- candidates, when present, are policy candidates only;
- no memory-reclamation claim is emitted.

Do **not** intentionally drive a development machine toward uncontrolled OOM merely to obtain a `critical` sample. Pressure-transition testing belongs in controlled/reproducible conditions before any production automation decision.

## 8. Evidence interpretation rules

### Acceptable statement

> On device/environment X, for exact artifact/backend/config Y, N compatible complete worker cycles produced a repeated `recovery_observed` pattern under procedure Z. Automatic eviction remains disabled pending broader review.

### Unacceptable statements

- “Unload definitely frees all model memory.”
- “LRU eviction is safe on every Apple Silicon device.”
- “The process exited, therefore unified memory was reclaimed.”
- “One positive run proves automatic eviction is production-ready.”
- “Unavailable RSS means zero RSS.”

## 9. Escalation conditions

A matrix cell remains evidence-pending when any of these apply:

- artifact SHA or backend version cannot be verified;
- environment identity is incomplete;
- repeated reports are incompatible;
- lifecycle errors occur;
- observations are inconclusive/mixed;
- resource fields needed for the intended claim are unavailable;
- the procedure changed between reports;
- background conditions changed enough to undermine comparability.

In those cases, preserve the raw reports and limitations rather than deleting negative or inconclusive evidence.

## 10. Release evidence index template

Fill this table only with retained artifacts; do not pre-fill outcomes.

| Cell | Device label | Commit | Artifact SHA | Backend/version | Environment | Raw reports | Review | Limitation summary | Release claim |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H3-MAC-MLX-TEXT | — | — | — | — | — | — | — | not executed | evidence pending |
| H3-MAC-GGUF-TEXT | — | — | — | — | — | — | — | not executed | evidence pending |
| H3-LINUX-GGUF-CPU | — | — | — | — | — | — | — | not executed | evidence pending |

## 11. Gate to automatic pressure eviction

No review state in this document automatically unlocks B6 automatic eviction.

A separate review must still establish:

1. representative coverage is sufficient for the intended supported platform set;
2. lifecycle errors and mixed/inconclusive recovery patterns are understood;
3. pressure sampling cadence/source is stable;
4. pinned, active and resident-default protections remain intact under real pressure;
5. dry-run candidate behavior is observable and bounded;
6. automatic mode, if ever enabled, is explicit opt-in and reversible;
7. public documentation still distinguishes policy success from memory-reclamation evidence.

Until those conditions are met, **automatic pressure eviction remains disabled**.

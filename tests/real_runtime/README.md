# Real-runtime smoke

This directory contains bounded automated checks for an **already running real Local LLM Server**.
They are deliberately separate from the deterministic PR gate because they require a real model,
backend and device.

The smoke verifies the public product path without persisting prompt or model-output content:

```text
/health
/v1/models
/v1/runtime/identity
/status
/v1/chat/completions
```

Run it on the target machine after starting the intended runtime:

```bash
python tests/real_runtime/smoke_runtime.py \
  --base-url http://127.0.0.1:1235 \
  --model <runtime-key-or-model-id>
```

If the default runtime is unambiguous, `--model` may be omitted.

A successful report records only bounded metadata such as selected runtime/model identity, identity
evidence grade, runtime version, status phase, response length and whether token usage was observed.
It does **not** print or retain the prompt or generated answer.

This smoke is a preflight, not representative performance evidence. The device-evidence runbook still
owns real thinking, evaluation, reclamation and resource-policy evidence. Do not run those heavier
slices concurrently when they would compete for the same model residency or memory budget.

# repo-template-sw 0.4.0 product-ui L2 migration

Status: active — real-human evidence pending
Owner: repository engineering + web product
Read when: coordinating the remaining `product-ui` L2 evidence
Last reviewed: 2026-08-18

## Goal

Complete the two real-human evidence tasks required after the already accepted `repo-template-sw 0.4.0` product-ui repository guardrails, without replacing the code-first design system or fabricating usability/accessibility evidence.

The separate full-engineering-L2 representative-hardware gate remains owned by `l2-reference-grade.md` + `runtime-correctness-evidence-hardening.md`.

## Work graph

| ID | Work | Depends on | State |
| --- | --- | --- | --- |
| PX4-01..PX4-08 | 0.4.0 contracts, guardrails, CI integration and repository acceptance | — | DONE |
| PX4-BRIDGE | bounded templates + human-evidence validator | PX4-08 | DONE |
| PX4-09 | execute and retain bounded manual accessibility review | PX4-BRIDGE | READY |
| PX4-10 | execute and retain bounded representative-user usability session | PX4-BRIDGE | READY |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

PX4-09 and PX4-10 are independent and may proceed in parallel. They require actual human interaction with a built product surface and cannot be satisfied by hosted CI.

## Accepted repository guardrails

Product-ui repository guardrails were accepted on exact head `89d360698234016ddfe1f3fff0bacbc4f9bb7852`. They cover task/state/accessibility/adaptive contracts, brand/design-system ownership, critical-journey mapping, privacy-safe research policy and significant-UX-change review.

The deterministic human-evidence bridge was accepted on `de899cc945e1d1c735a2ded91c5da717ce0fe2b0`. It adds:

- `docs/evidence-templates/manual-accessibility.example.json`;
- `docs/evidence-templates/representative-usability.example.json`;
- `python -m local_llm_server.l2_evidence_bridge validate-product-ui`;
- machine checks that reject example identifiers, missing required checks/journeys, non-allow-listed usability fields and observations that appear to contain private paths/email/secret-like values;
- separate `evidence_present`, `acceptance_ready` and `blocking_findings` states;
- `baseline_mutated=false` so evidence review never silently promotes the maturity claim.

The example templates are deliberately **not evidence** and are rejected as completion inputs until copied, bound to an exact source revision and populated from a real session.

## PX4-09 — manual accessibility

Execute the protocol in `docs/product-experience-validation.md` on a built surface and record all six required checks:

- keyboard primary shell;
- focus order and visibility;
- accessibility tree or screen reader;
- zoom/text scaling;
- reduced motion;
- error/loading/empty/disabled states.

A required `fail` or `inconclusive` result is blocking until the underlying issue is understood/resolved and a justified follow-up review is executed. The evidence must remain bounded and sanitized.

Only after real evidence exists and the validator reports acceptance-ready may `.engineering/product-ui-l2.json` move `manual_accessibility_status` away from `pending` through an explicit repository change.

## PX4-10 — representative-user usability

Use non-sensitive demo/test data and record the four minimum journeys:

- `control-plane-status-and-navigation`;
- `chat-inference-and-recovery`;
- `advanced-control-discovery`;
- `evidence-interpretation`.

Only the allow-listed fields in `.engineering/product-ui-l2.json` may be retained. Raw prompts, outputs, uploaded media, private paths and machine identity are forbidden by default. High/critical findings are blocking; lower-severity findings remain evidence requiring product judgment rather than silent dismissal.

Only after real evidence exists and the validator reports acceptance-ready may `representative_user_usability_status` move away from `pending` through an explicit repository change.

## Validation

After both real evidence files exist:

```bash
python -m local_llm_server.l2_evidence_bridge validate-product-ui \
  --accessibility /path/to/manual-accessibility.json \
  --usability /path/to/representative-usability.json \
  --output /path/to/product-ui-evidence-summary.json
```

Exit code `0` means the bounded evidence meets the validator's acceptance-readiness contract. Exit code `2` means validly incomplete/not ready; it is not permission to edit observations merely to obtain green.

## Completion boundary

Repository-side **0.4.0 product-ui guardrails and the deterministic human-evidence bridge are accepted**. Full `product-ui` L2 is not evidence-complete while PX4-09 or PX4-10 remains open.

Do not mark manual evidence complete unless it was actually executed; do not add surveillance telemetry, retain raw product content, treat automated accessibility checks as human evidence, or rerun a negative session solely to manufacture a favorable result.

# <WORKSTREAM_TITLE>

Status: active
Owner: <DOMAIN_OR_REPOSITORY>
Read when: implementing or coordinating <WORKSTREAM_SCOPE>

## Goal

<ONE_CLEAR_OUTCOME>

## Non-goals

- <EXPLICITLY_EXCLUDED_SCOPE>

## Invariants

- <INVARIANT_THAT_MUST_REMAIN_TRUE>

## Work graph

| ID | Work | Owns/writes | Depends on | Parallel | State |
| --- | --- | --- | --- | --- | --- |
| WS-1 | <bounded slice> | <paths/boundary> | — | yes | READY |
| WS-2 | <bounded slice> | <paths/boundary> | WS-1 | no | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

Parallel work must have explicit non-conflicting ownership/write boundaries or a defined integration point.

## Current executable slice

`WS-1`

Acceptance:

- <observable acceptance criterion>

Validation:

- `<targeted command or evidence>`

## Integration points

- <contract/merge point between parallel slices>

## Durable documentation destinations

- `docs/current-state.md`: repository-level integrated/blocker/next truth
- `docs/architecture*.md`: only if architecture/ownership changes
- feature/API/config docs: only durable current behavior
- tests/contracts: executable truth

## Completion

The workstream is complete only when applicable code, integration, failure/resource behavior, validation/evidence and durable docs agree. Then update `docs/current-state.md` and delete this file by default.

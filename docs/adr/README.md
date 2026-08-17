# Architecture decision records

Status: active
Document type: documentation-governance
Owner: runtime-and-platform
Canonical scope: documentation.adr-routing
Read when: deciding whether an architectural choice needs a durable rationale record
Last reviewed: 2026-08-17

Use this directory for **accepted durable decisions** whose alternatives, tradeoffs or migration consequences remain useful after implementation.

Create an ADR when a decision materially constrains future architecture and cannot be understood from current behavior alone—for example a process-ownership boundary, a public compatibility rule, an artifact identity scheme or a security/trust choice with meaningful rejected alternatives.

Do not create ADRs for routine implementation details, workstream status, temporary experiments or facts already owned by an API/feature/operations document.

Recommended shape:

```text
# ADR-NNN — title
Status: accepted | superseded
Date: YYYY-MM-DD
Context
Decision
Consequences
Alternatives considered
References
```

`docs/architecture.md` owns the current architecture. An ADR explains **why** a durable choice was made; it does not become a duplicate current-state specification. Superseded ADRs may remain when their historical rationale is still useful, but must link to the replacement decision.

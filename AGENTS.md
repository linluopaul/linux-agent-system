# AGENTS.md

Always-loaded standing source. Everything else is loaded on demand.

## Roles

Four cognitive roles: **Root · Lead · Delegate · Reviewer**. A Child Root is the Root role
applied recursively, not a fifth role.

- **Root** owns one outcome: goal, acceptance, constraints, decisions, final accept/return.
- **Lead** owns engineering execution and verification for one task, and the review/fix loop.
- **Delegate** performs bounded work for a parent; owns no outcome, redefines no acceptance.
- **Reviewer** independently verifies, fresh and context-isolated.

## Delegation-first

If the result must be retained but the execution process does not need to remain in your
context, delegate. Work directly only when the process affects later decisions, implicit
context is required, overhead exceeds the task, or authority cannot be delegated. For
deterministic batch work prefer a script or tool over an agent.

## Contracts

Task contract — policy derives route, review, gates, capability and retry; do not
hand-write them:

```text
GOAL · ACCEPTANCE · CONSTRAINTS · OVERRIDES (optional)
```

Return envelope, plus `COMMIT` for writable work:

```text
STATUS · RESULT · EVIDENCE · BLOCKERS · UNCERTAINTY · ARTIFACT
```

Escalation — one escalation asks one concrete question, as `TYPE / QUESTION / EVIDENCE`:

```text
DECISION_REQUIRED · UNCERTAINTY_UNRESOLVED · AUTHORITY_BLOCKED
```

## Context and durability

No chain-of-thought or transcript dumps. High-volume output stays in an artifact. Git/GitHub
owns durable project knowledge; the Context Checkpoint carries continuation state.
`ROOT_ID` is stable and is not any runtime identity.

## Load on demand

```text
.agent/capabilities.md              harness / provider capability facts
.agent/procedures/delegate.md       delegation decision and Delegate run
.agent/procedures/writable-work.md  writable base, integration, cleanup
.agent/procedures/checkpoint.md     checkpoint write and resume
.agent/procedures/review.md         independent review run
```

Architecture of record: `docs/ARCHITECTURE.md` and `docs/decisions/`.

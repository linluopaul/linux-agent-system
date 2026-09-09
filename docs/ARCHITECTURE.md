# Linux Agent System — Architecture (V4)

Current architecture only. This document defines the cognitive responsibility structure and
the boundaries around it. It is not a runtime manual, a roadmap, a project-state record, a
historical narrative, or a provider preference table.

Decision of record: `docs/decisions/ADR-008-v4-cognitive-architecture-and-herdr-runtime.md`.

## 1. System boundary

```text
                         HUMAN
                           │
                           ▼
                         ROOT
              owns outcome / acceptance / decisions
                    │              │
                    ▼              ▼
                  LEAD         CHILD ROOT
        implementation / verification   │
             │          │               └─ recursively the same structure
             ▼          ▼
         DELEGATE    REVIEWER
```

There are **exactly four cognitive roles**: Root, Lead, Delegate, Reviewer. Human authority
sits outside and above them. A **Child Root is the Root role applied recursively**, not a
fifth role.

## 2. Responsibility

**Root** owns exactly one outcome: requirement clarification, goal, acceptance and
constraints, architecture and boundary decisions, decomposition into Lead tasks or Child
Roots, and the final accept / return / escalate decision.

**Lead** owns engineering execution and verification for one assigned task: implementation,
debugging, tests, the review/fix loop when review is required, the decision whether to work
directly or delegate, and normal cleanup of the runtime children it creates.

**Delegate** performs bounded execution and context offload. It produces a result for its
parent. It does not own the parent outcome and does not redefine acceptance.

**Reviewer** performs fresh, independent verification.

## 3. Child Root criterion

```text
bounded result, no outcome of its own                        → Delegate
engineering/research task with Root-provided acceptance      → Lead task
owns its own outcome and acceptance,
  and may own multiple Lead tasks and/or review cycles       → Child Root
```

Classification is by responsibility, never by task size, duration or lifecycle length.

## 4. Delegation-first

When a result must be retained but the execution process does not need to remain in the
parent context, delegation is the default.

The parent performs the work directly only when:

1. the execution process materially affects later parent decisions;
2. continuous access to implicit parent context is required;
3. delegation overhead exceeds the size of the task;
4. the required authority cannot be delegated.

For deterministic batch work, prefer a script, tool or engine over an LLM Agent.

A harness-native subagent is preferred where it is adequate for the task and sufficiently
traceable. An external Herdr Delegate is retained for cross-provider execution, a
specialized or domestic model unreachable from the parent harness, a data source the parent
harness cannot reach, an independent runtime, or stronger isolation or traceability.

## 5. Stable identity

```text
ROOT_ID     stable, immutable architectural identity
TREE_PATH   mutable human-readable hierarchy / presentation
```

`ROOT_ID` is assigned once and never changes. It is **not** a Herdr session, workspace, tab,
pane or process identity, not a harness identity, and not any human-visible label. All of
those may change while `ROOT_ID` does not.

## 6. Minimal Task Contract

```text
GOAL
ACCEPTANCE
CONSTRAINTS
OVERRIDES   (optional; only when deviating from defaults)
```

Policy derives execution route, whether review is required, review route, human gates,
capability envelope and retry budget. No normal task requires a Human or a Root to carry a
large hand-written packet of execution metadata.

## 7. Communication contract

Default return:

```text
STATUS
RESULT
EVIDENCE
BLOCKERS
UNCERTAINTY
ARTIFACT
```

Writable work adds `COMMIT`.

Raw execution process, transcripts and high-volume tool output are never promoted into the
parent context. They stay in artifacts; the parent receives decision-relevant result,
evidence, uncertainty and artifact pointers. Uncertainty is stated explicitly whenever the
evidence is insufficient for a stronger decision.

## 8. Escalation

Exactly three semantic types:

```text
DECISION_REQUIRED
UNCERTAINTY_UNRESOLVED
AUTHORITY_BLOCKED
```

Format:

```text
TYPE
QUESTION
EVIDENCE
```

One escalation asks one concrete question.

## 9. Review

Independent review is performed by a **fresh, context-isolated Reviewer**.

The Reviewer receives only the minimal review material: goal, acceptance, the result or diff
or commit, verification evidence, and the relevant constraints and material selected by Root
or policy. It does not receive Root advocacy for the implementation, implementer
chain-of-thought, or irrelevant transcripts.

The Reviewer returns a concise verdict, an artifact pointer, and integrity evidence. The
original verdict is preserved independently: the Lead may respond to findings but may not
rewrite, suppress or redefine the verdict, and the Root must be able to recover the original
verdict without the Lead as sole transport.

The Lead owns the review/fix loop. The retry budget belongs to policy.

Context isolation between roles is **contractual** and is sufficient by default. An
operating-system or filesystem sandbox is introduced only if future evidence justifies it.

## 10. Context continuation

Three layers, and no more:

```text
current working context   harness-native context and compaction
session continuity        Context Checkpoint
durable project knowledge Git / GitHub  (authoritative)
```

There is no Memory Agent. The Context Checkpoint has exactly ten fields:

```text
ROOT_ID
CHECKPOINT_GENERATION / TIMESTAMP
GOAL
ACCEPTANCE
CURRENT_STATE
DECISIONS_MADE
OPEN_QUESTIONS / BLOCKERS
ACTIVE_CHILD_ROOTS / LEADS
IMPORTANT_EVIDENCE_POINTERS
NEXT_ACTION
```

No eleventh field is added. Each `ACCEPTANCE` criterion carries its current status and an
evidence pointer, so a resuming Root can determine acceptance coverage.

A fresh session or carrier resumes with the same `ROOT_ID`, the latest checkpoint, and
Git/GitHub durable state as needed.

## 11. Herdr boundary

Herdr is the cross-harness **runtime substrate**. It provides session and workspace
lifecycle, runtime launch, worktree lifecycle, human-visible runtime labels, cross-harness
observability, and resource cleanup.

Herdr is not a cognitive Agent and not a reasoning supervisor. Its workspace, tab, pane,
session and process objects are implementation details, never cognitive roles. Command
syntax and label conventions belong to procedures and runtime conventions, not here.

## 12. Lifecycle

Whoever creates a direct child runtime resource owns its normal lifecycle and cleanup; the
parent verifies final state.

`resources_clean` is determined by post-condition verification, not by a cleanup command's
return value. A dirty worktree must not be silently discarded. `resources_clean: false`
prevents normal final acceptance until cleanup succeeds or exceptional recovery is
explicitly handled.

## 13. Policy boundary

Policy owns routing, the review requirement, the review route, human gates, the capability
envelope and the retry budget. A mandatory safeguard may be strengthened by Root or Human,
but never silently weakened.

No role is permanently bound to a harness, model or provider. Current preferences are
resolved through policy and profile resolution, and are not architectural identity.

## 14. Git and GitHub

Git and GitHub hold the authoritative durable project knowledge: code, docs, ADRs,
tests/evals, commits, pull requests and durable outcomes.

GitHub is **not** a mandatory task entry point, and GitHub Issue or Kanban state is not
architectural task state. Task entry is a Human surface, and may in future be provided by a
dashboard or router outside this role model. Individual projects may still use Issues, but
nothing in this architecture depends on them.

## 15. Thin Controller

A Thin Controller performs deterministic enforcement only. Introduce it only when a
deterministic rule is repeatedly violated at real cost or risk, or when a single violation
would carry unacceptable cost or risk. It never becomes a reasoning supervisor.

## 16. Project Control Plane boundary

A Project Control Plane may exist as operational software **outside** the V4 cognitive role
model. It may provide a dashboard, a project registry, a router, profiles, trace,
maintenance, backup, and Root Carrier switching. `PROJECT_ID` belongs to that operational
layer.

It introduces no Meta Root, Supervisor, Project Manager Agent, Router Root, Memory Agent,
Backup Agent, Trace Agent or Runtime Adapter. Its own architecture is not reproduced here.

## 17. Root Carrier

The runtime carrier of a Root — harness, model, reasoning effort, session and workspace —
may change without creating a new Root. `ROOT_ID` remains stable across the change.

Before switching carriers, active direct children, worktrees and outstanding review state
must be reconciled. A switch must not silently orphan runtime resources. The switch
procedure itself belongs to runtime procedure, not to this document.

## 18. Architectural placement test

A concept belongs in the top-level architecture **only if it changes the distribution of
responsibility among Human / Root / Lead / Delegate / Reviewer.**

Otherwise it belongs in one of:

```text
Policy
Herdr / runtime implementation
Skill / Procedure / Runbook
tests
tooling
Project Control Plane
```

This is the guardrail that prevents the architecture from re-expanding into the layered,
runtime-entangled form it previously had.

## 19. Not part of the current architecture

The following are retired as current claims. They remain in ADRs and `docs/HISTORY.md` as
historical record, and must not be reintroduced here:

- an Orca execution and review plane, and its Run / Task / Dispatch topology;
- `Worker` and `Platform Steward` as cognitive roles;
- a large hand-written execution packet as the Root-to-Lead interface;
- the numbered closed re-entry condition list;
- a Memory Agent, a Summarizer Agent, or a Hermes-style Supervisor;
- GitHub Issues as the mandatory task carrier;
- any special topology placing the Root outside the runtime;
- provider or model preference treated as architectural identity.

## 20. Procedures

Operational detail is loaded on demand, one procedure at a time:

```text
.agent/capabilities.md              harness and provider capability facts
.agent/procedures/delegate.md       delegation decision and Delegate run
.agent/procedures/writable-work.md  writable base, integration, cleanup
.agent/procedures/checkpoint.md     checkpoint write and resume
.agent/procedures/review.md         independent review run
```

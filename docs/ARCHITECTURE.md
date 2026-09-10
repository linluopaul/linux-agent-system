# Linux Agent System — Architecture (V4)

Current cognitive responsibilities and boundaries. Operational procedures, policy, project
state, roadmap and historical narrative have separate canonical homes.

Decision of record: `docs/decisions/ADR-008-v4-cognitive-architecture-and-herdr-runtime.md`.

## 1. System boundary

Human authority sits above exactly four cognitive roles: Root, Lead, Delegate, Reviewer.
Root assigns Lead tasks or Child Roots; Leads may use Delegates and Reviewers.
A Child Root is the Root role applied recursively, not a fifth role.

## 2. Responsibility

**Root** owns one outcome: goal, acceptance, constraints, decisions, decomposition into
Lead tasks or Child Roots, and final accept / return / escalate.

**Lead** owns engineering execution and verification for one task: implementation, debugging,
tests, the review/fix loop, direct/delegated execution and cleanup of its runtime children.

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

Direct execution is reserved for decision-relevant process, essential implicit context,
excessive delegation overhead, or nondelegable authority. Deterministic batch work prefers
scripts, tools or engines over LLM Agents.

Native subagents are preferred when adequate and traceable. External Herdr Delegates serve
cross-provider or otherwise unavailable capabilities, independent runtimes, and stronger
isolation or traceability. Selection and execution belong to
`.agent/procedures/delegate.md`.

## 5. Stable identity

`ROOT_ID` is stable, immutable architectural identity.
`TREE_PATH` is mutable human-readable hierarchy / presentation.

`ROOT_ID` is assigned once and never changes. Runtime session/workspace/tab/pane/process,
harness and human-visible label identities may change independently; none is `ROOT_ID`.

## 6. Minimal Task Contract

```text
GOAL
ACCEPTANCE
CONSTRAINTS
OVERRIDES   (optional; only when deviating from defaults)
```

Policy derives execution route, whether review is required, review route, human gates,
capability envelope and retry budget; normal tasks do not carry hand-written execution packets.

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

Execution process, transcripts and high-volume output stay in artifacts. Parent context
receives decision-relevant results, evidence, uncertainty and pointers, never reasoning
dumps. Uncertainty is explicit whenever evidence is insufficient for a stronger decision.

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

Review context is minimal and excludes implementation advocacy and irrelevant execution
history. The original verdict must remain independently recoverable by Root; Lead may
respond to findings but cannot rewrite, suppress or redefine that verdict.

Lead owns the review/fix loop. Policy owns whether review is required, eligible review
routing and the retry budget. `.agent/procedures/review.md` owns the review material,
artifact and integrity procedure.

Context isolation is contractual and sufficient by default. Stronger operating-system or
filesystem sandboxing requires evidence of need.

## 10. Context continuation

Three layers, and no more:

```text
current working context   harness-native context and compaction
session continuity        Context Checkpoint
durable project knowledge Git / GitHub  (authoritative)
```

Context Checkpoint is session-independent continuation state, not a competing knowledge
store. Its fixed architectural contract has exactly ten fields, including acceptance
coverage with status and evidence. The schema and operational instructions belong to
`.agent/procedures/checkpoint.md`; no eleventh field is added.

A fresh session or carrier resumes with the same `ROOT_ID`, the latest checkpoint, and
Git/GitHub durable state as needed. Continuation never requires conversation transfer.

## 11. Herdr boundary

Herdr is the cross-harness runtime substrate: session/workspace lifecycle, runtime launch,
worktrees, human-visible labels, observability and resource cleanup.

Herdr is not a cognitive Agent and not a reasoning supervisor. Its objects are implementation
details, never cognitive roles. Commands and labels belong to procedures/runtime conventions.

## 12. Writable work and lifecycle

Writable delegated work preserves immutable base/provenance, protected checkout isolation
and Lead-owned verified integration. Orchestration lineage is not Git ancestry.
`.agent/procedures/writable-work.md` owns the checks and integration/cleanup procedure.

Whoever creates a direct child runtime resource owns its normal lifecycle and cleanup; the
parent verifies final state.

`resources_clean` is determined by post-condition verification, not by a cleanup command's
return value. A dirty worktree must not be silently discarded. `resources_clean: false`
prevents normal final acceptance until cleanup succeeds or exceptional recovery is
explicitly handled.

## 13. Policy boundary

`.agent/policy.yaml` owns routing, the review requirement, the review route, human gates,
the capability envelope, retry budget and efficiency/reasoning constraints. A mandatory
safeguard may be strengthened by Root or Human, but never silently weakened.

No role is permanently bound to a harness, model or provider. Current preferences are
resolved through policy and profile resolution, and are not architectural identity.
Capability facts live in `.agent/capabilities.md`; load these and procedures only as needed.

## 14. Git and GitHub

Git and GitHub hold the authoritative durable project knowledge: code, docs, ADRs,
tests/evals, commits, pull requests and durable outcomes.

GitHub is not a mandatory task entry point; GitHub Issue or Kanban state is not architectural
task state. Task entry is a Human surface, optionally through a future dashboard/router.
Projects may use Issues without making the architecture depend on them.

## 15. Thin Controller

A Thin Controller performs deterministic enforcement only. Introduce it only when a
deterministic rule is repeatedly violated at real cost or risk, or when a single violation
would carry unacceptable cost or risk. It never becomes a reasoning supervisor.

## 16. Project Control Plane boundary

A Project Control Plane may exist as operational software **outside** the V4 cognitive role
model: dashboard, registry, router, profiles, trace, maintenance, backup and Root Carrier
switching. `PROJECT_ID` belongs to that operational layer.

It introduces no Meta Root, Supervisor, Project Manager Agent, Router Root, Memory Agent,
Backup Agent, Trace Agent or Runtime Adapter. Its own architecture is not reproduced here.

## 17. Root Carrier

The runtime carrier of a Root — harness, model, reasoning effort, session and workspace —
may change without creating a new Root. `ROOT_ID` remains stable across the change.

Before switching carriers, active direct children, worktrees and outstanding review state
must be reconciled. A switch must not silently orphan resources; its procedure belongs to runtime.

## 18. Architectural placement test

A concept belongs in the top-level architecture only if it changes responsibility among
Human / Root / Lead / Delegate / Reviewer. Otherwise it belongs in policy, Herdr/runtime,
a skill/procedure/runbook, tests, tooling or the Project Control Plane.

## 19. Historical boundary

The following are retired, not current claims: Orca execution/review topology; Worker and
Platform Steward cognitive roles; giant Execution Packets; the six-condition Root re-entry
mechanism; Memory/Summarizer Agents and Hermes-style Supervisors; mandatory GitHub
Issue/Kanban task state; and a special topology placing Root outside the runtime.
Historical decisions remain in `docs/decisions/` and `docs/HISTORY.md`.

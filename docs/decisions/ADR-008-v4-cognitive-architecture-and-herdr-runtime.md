# ADR-008: V4 Cognitive Architecture and Herdr Runtime

- Status: Accepted
- Date: 2026-09-08
- Scope: The V4 cognitive role model, stable Root identity, the cross-harness runtime
  substrate, the task/communication/escalation contracts, review and lifecycle ownership,
  and the boundary between cognitive roles and operational software

> Supersession note: this ADR supersedes ADR-001's Orca-first execution-plane decision and
> partially supersedes ADR-003 where that record defines Worker as a role or mandates
> Worker/Orca-specific topology. ADR-001 through ADR-007 are retained unchanged as
> historical decision records. See "Relationship to existing ADRs" below.

## Context

The v3 architecture named Orca as the execution and review plane (ADR-001) and treated
Herdr as optional infrastructure. Over v3 the top-level architecture accumulated
runtime-specific vocabulary — Run, Task, Dispatch, coordinator terminal, worker lifecycle —
so that replaceable runtime mechanics became architecture roles. The same rules were
restated across `AGENTS.md`, `.agent/roles/*`, `.agent/policies/*` and runbooks, and that
duplication drifted.

V4 was designed to remove runtime mechanics from the top-level architecture and to shrink
the always-loaded instruction surface. Before adopting it, a nine-test validation
(S1–S9) exercised the load-bearing assumptions against Herdr 0.8.2 directly rather than
accepting them on design intent. Results: S1 established that Herdr continuity has two
distinct tiers; S2 that a stable human-visible naming mechanism exists; S3 that writable
worktree isolation and cleanup work and that cleanup safely refuses a dirty worktree;
S5 that a parent can decide correctly on compressed returns without ingesting child
execution output; S6 that a fresh, different-provider reviewer's verdict can be preserved
independently of the implementer; S7 that a genuinely fresh session continues from a
checkpoint under a stable identity while every runtime identifier changes; S8 that a ~46
line standing instruction card is sufficient for a Lead to understand its authority and to
choose delegation on its own; S9 that the Child Root criterion classifies real work
unambiguously. S4 (ordinary human-approval side effects) was inconclusive and is recorded
as an open item, not as a validated assumption.

This ADR records the decisions those results support.

## Decision

### 1. Exactly four cognitive roles

The V4 cognitive architecture has exactly four roles:

```text
Root      owns one outcome
Lead      owns engineering execution for one task
Delegate  bounded execution; produces a result for a parent; owns no outcome
Reviewer  fresh, context-isolated independent verification
```

A Delegate does not own the parent outcome and does not redefine acceptance. Human authority
sits outside and above this set. No fifth cognitive role is introduced.

### 2. Child Root is a recursive Root

A Child Root is the Root role applied recursively, not a fifth role. Create one only when
the work both owns its own outcome and acceptance, and may own multiple Lead tasks and/or
review cycles. Otherwise prefer a Lead task or a Delegate. Classification is decided by
outcome and acceptance ownership, never by task size, duration or lifecycle length.

### 3. Root identity is stable and runtime-independent

Two distinct concepts are carried separately:

```text
ROOT_ID     stable, immutable architectural identity
TREE_PATH   mutable human-readable hierarchy / presentation  (1, 1.2, 1.2.1)
```

`ROOT_ID` is assigned once at Root creation and never changes for the lifetime of that Root.
`TREE_PATH` may change freely; it is presentation, not identity.

`ROOT_ID` is **not** a Herdr session identity, workspace identity, tab or pane identity,
terminal identity, operating-system process identity, harness or harness-session identity,
or any human-visible label. All of those may change while `ROOT_ID` does not.

### 4. Herdr is the V4 runtime substrate

Herdr is the cross-harness runtime substrate for V4. It provides the persistent Root
workspace/session, temporary Lead / Delegate / Reviewer agents, worktree isolation,
human-visible naming, start/wait/stop, and resource lifecycle. Herdr workspace, tab, pane,
session and process objects are implementation details of that substrate and are never
cognitive roles. Concrete label formats and runtime command sequences belong to runtime
procedure, not to this ADR.

### 5. Delegation-first

**When a result must be retained but the execution process does not need to remain in the
parent context, Root and Lead default to Delegate / sub-agent execution.**

The parent performs the work directly only when:

- the execution process materially affects later parent decisions;
- continuous access to implicit parent context is required;
- delegation overhead exceeds the size of the task; or
- the required authority cannot be delegated.

Upward promotion carries only decision-relevant result, evidence, uncertainty and artifact
pointers — never the execution process itself.

For deterministic batch work, prefer a script, tool or engine over an LLM Agent.

### 6. Harness-native subagents are preferred where adequate

Where a harness-native subagent is adequate for the work and sufficiently traceable, it is
the preferred Delegate implementation. Native execution avoids a separate runtime object
and its lifecycle cost.

### 7. Herdr external Delegates remain available

An external Herdr Delegate remains the correct choice when the work requires any of:

- cross-provider execution;
- a specialized or domestic model not reachable from the parent harness;
- access to a data source the parent harness cannot reach;
- an independent runtime;
- stronger isolation or traceability than a native subagent provides.

Neither form is a permanent binding. The choice is made per task by the delegating role.

### 8. Context model

Three layers, and no more:

```text
current working context   harness-native context and compaction
session continuity        Context Checkpoint
durable project knowledge Git / GitHub  (authoritative)
```

There is no Memory Agent and no dedicated memory subsystem. A third durable knowledge store
is not introduced.

The Root Context Checkpoint has exactly ten fields:

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

No eleventh field is added.

`ACCEPTANCE` carries more than the criteria themselves: each criterion must record its
current status and an evidence pointer or summary, so that a resuming Root can determine
acceptance coverage — which criteria are discharged, which remain open, and on what basis:

```text
ACCEPTANCE

A1 <criterion>
STATUS: PASS
EVIDENCE: <pointer or short summary>

A2 <criterion>
STATUS: OPEN
EVIDENCE: <what is still missing>
```

The checkpoint carries session-independent transient state only. It never carries
conversation transcript, chain-of-thought, routine tool history, Delegate execution process,
full Reviewer transcript, or durable material already promoted to Git/GitHub.

A new harness or session resumes with the same `ROOT_ID`, the latest checkpoint, and
Git/GitHub durable state as needed.

### 9. Minimal Task Contract

The normal interface from Root to execution is:

```text
GOAL
ACCEPTANCE
CONSTRAINTS
OVERRIDES   (optional; only when deviating from defaults)
```

No normal task requires a Root or a Human to hand-write routing, risk packet fields, retry
budget, model identifiers, review route, or runtime lifecycle metadata. Policy derives
execution metadata such as execution route, whether review is required, review route, human
gate required, capability envelope and retry budget. Mandatory safeguards may be
strengthened by Root or Human but never silently weakened.

### 10. Communication and escalation

The default return envelope is:

```text
STATUS
RESULT
EVIDENCE
BLOCKERS
UNCERTAINTY
ARTIFACT
```

`COMMIT` is added for writable work. Large or high-volume output goes to an artifact; the
parent receives a compressed result; evidence remains independently checkable; uncertainty
must be explicit whenever the evidence is insufficient for a stronger decision. No routine
tool narration, no transcript dumps, no reasoning dumps.

Do not add further protocol fields to express evidence sufficiency. `EVIDENCE`,
`UNCERTAINTY` and `ARTIFACT` are sufficient, and sufficiency is a property of the decision
being made rather than of the envelope.

Escalation uses exactly three semantic types:

```text
DECISION_REQUIRED
UNCERTAINTY_UNRESOLVED
AUTHORITY_BLOCKED
```

Escalation format:

```text
TYPE
QUESTION
EVIDENCE
```

One escalation asks one concrete question. This replaces the v3 numbered closed re-entry
list.

### 11. Reviewer independence and verdict preservation

Independent review is performed by a fresh, context-isolated Reviewer that receives only
the Root- or policy-fixed minimal review material: goal, acceptance, the implementation
result or diff, verification evidence, and the relevant constraints. It never receives Root
private reasoning, the Root's advocacy for the work, implementer chain-of-thought, or
unnecessary execution transcripts.

The Reviewer writes its verdict to an independently preserved artifact and returns:

```text
concise verdict
+ artifact pointer
+ integrity evidence / hash
```

The Root can recover the original verdict artifact directly, without the Lead as transport.
The Lead may respond to findings but may never rewrite, suppress or redefine the verdict.
Reading the Reviewer's terminal is debug evidence only and is not the preservation
mechanism.

V4 requires **contractual context isolation**, not operating-system or filesystem
sandboxing. Stronger sandboxing is added only if real evidence shows it is necessary.

### 12. The Lead owns the engineering review/fix loop

The Lead arranges the required review and owns the review/fix loop within the policy-derived
budget. The Root rules on the final result, not on each cycle.

### 13. Runtime object lifecycle

Whoever creates a direct child runtime resource owns its normal lifecycle and cleanup; the
parent verifies final state. Every completed branch of work reports:

```text
resources_clean: true | false
```

`resources_clean` is established from observable post-conditions, never inferred solely from
a cleanup command's return value. A dirty worktree must be explicitly resolved before normal
removal; normal cleanup must not silently discard uncommitted work; forced removal is not
routine authority.

`resources_clean: false` prevents normal final acceptance until cleanup succeeds or
exceptional recovery is explicitly handled.

### 14. Thin Controller

A Thin Controller is not built by default. Deterministic automation is introduced only when
a deterministic rule is repeatedly violated at real cost or risk, or when a single violation
would carry unacceptable cost or risk. The Thin Controller never becomes a reasoning
Supervisor.

### 15. Project Control Plane boundary

A Project Control Plane may exist as operational software outside the cognitive role model.
It may provide dashboard and visibility, a project registry, routing and profile resolution,
trace, maintenance, backup, and Root Carrier management.

Operational identities belong to it, not to the cognitive architecture — including
`PROJECT_ID`, Root Carrier state, capability and profile resolution, unified event trace,
and backup state.

It is not an Agent, and it introduces none of the following:

```text
Meta Root
Supervisor
Project Manager Agent
Router Root
Memory Agent
Backup Agent
Trace Agent
Runtime Adapter
```

None of these is a V4 cognitive role. The Project Control Plane never owns a project
outcome, never interprets results in place of a Root, and never becomes a memory owner or a
competing source of project truth.

### 16. The Root Carrier is replaceable

The runtime carrier of a Root — its harness, model, reasoning configuration, session and
workspace — may be replaced **without creating a new Root**, while `ROOT_ID` remains stable.
Continuity across a carrier change is provided by the Context Checkpoint plus durable
Git/GitHub state, never by conversation transfer.

Before switching carriers, active direct children, worktrees and outstanding review state
must be reconciled. Carrier switching must not silently orphan runtime resources.

The concrete switch procedure belongs to the Project Control Plane and to runtime
procedure, not to this ADR.

### 17. Architectural placement test

A new concept belongs in the V4 top-level cognitive architecture **only if it changes the
distribution of responsibility among Human / Root / Lead / Delegate / Reviewer.**

Otherwise it belongs in one of:

```text
Policy
Herdr / runtime implementation
Skill / Runbook
tests
tooling
Project Control Plane
```

This is the guardrail against V4 re-expanding into V3-style complexity, and it applies to
every future proposal to extend this architecture — including proposals originating in the
Project Control Plane.

## Relationship to existing ADRs

ADR-001 through ADR-007 are preserved unchanged by this ADR. Their text remains the
historical record of the decisions taken at the time.

**ADR-001 — Orca-First Execution and Collaboration Plane: SUPERSEDED by ADR-008** for the
Orca-first execution-plane decision. Orca is no longer the execution and review plane;
Herdr is the V4 runtime substrate. ADR-001's body is not rewritten and must not be edited
to suggest that Herdr was always intended.

**ADR-003 — Lead-Worker Git Integration Contract v1: PARTIALLY SUPERSEDED.** Superseded
where it defines `Worker` as a role or mandates Worker- or Orca-specific topology; V4 has no
Worker role, and bounded execution is performed by a Delegate. The surviving principles
remain in force and are carried into V4: writable delegated work starts from an explicit,
immutable base commit; the delegated result is an immutable, verified unit; integration is
performed deliberately by the Lead with recorded provenance; and orchestration lineage is
never treated as proof of Git ancestry.

**ADR-004 — Role / Harness / Model / Capability Separation: REMAINS VALID.** The separation
of role from harness from model from capability is preserved by V4 and is the reason a
Delegate may be either harness-native or an external Herdr runtime without changing the role
model. No role is permanently bound to a harness, model or provider.

**ADR-005 — Instruction Diet and Adaptive Premium Reasoning: REMAINS VALID, STRENGTHENED.**
V4 validation (S8) demonstrated that a single short always-loaded instruction source plus
load-on-demand procedures was sufficient for a role to understand its authority, choose
delegation, verify a delegate's findings, escalate correctly, and clean up its own child
resource. The instruction-diet principle is retained and tightened.

**ADR-006 — Hermes Supervisor retirement: REMAINS VALID.** Hermes stays retired. ADR-008
does not revive Hermes or introduce any other Supervisor. The operational concerns that
once motivated a Supervisor are addressed, where justified, by non-agent operational
software under §15 — never by recombining them into a long-lived reasoning agent.

**ADR-007 — Review/Fix Loop Ownership Moves to the Execution Lead: REMAINS VALID.** The
Lead-owned review/fix loop is carried into V4 unchanged in substance (§12). Only the
surrounding vocabulary changes: the v3 numbered re-entry condition is replaced by the three
escalation types in §10.

**ADR-002 — Cognitive and Engineering Control Planes: NO SUPERSESSION STATUS ASSIGNED
HERE.** This ADR deliberately assigns no final status to ADR-002. Its central separation
survives in V4 and is expressed by the role model: cognitive outcome ownership maps to
**Root**, and engineering execution maps to **Lead**. Whether any specific mechanic in
ADR-002 is superseded is left to be decided against its live text rather than asserted here.

## Consequences

The following become true, and are the work that follows this decision — none of it is
performed by this ADR:

- normative architecture, instruction, policy, runbook and test surfaces still describe an
  Orca-first execution plane and must be migrated;
- `Worker` and `Platform Steward` cease to be roles, and their routing and capability
  entries must be removed with them;
- the always-loaded instruction surface must contract rather than absorb V4 additively;
- tests that assert Herdr is non-default, or that pin prose by string, must be rewritten
  around V4 structure;
- Orca-specific runtime units and runbooks must be retired or archived;
- historical documents keep their Orca references; only current normative claims change.

Accepting this ADR does not authorize any of those edits. Each is gated by its own
migration phase.

## Open items

Recorded so they are not mistaken for validated decisions:

- ordinary human-approval side effects on runtime ownership, identity and cleanup remain
  unestablished (S4 was inconclusive); no V4 rule depends on them;
- Herdr provides no structured agent-to-parent return channel; compressed returns and
  verdicts currently travel as artifacts, which is an implementation gap, not an
  architecture gap;
- Herdr server restart and cold-recovery behavior is unverified.

Remaining runtime-level observations are recorded in the V4 validation report and are not
architecture items.

## Verification

This decision is verifiable against the S1–S9 validation results:

| Decision | Validated by |
|---|---|
| §1, §2 four roles and recursive Child Root | S9 |
| §3, §16 stable `ROOT_ID` across changed runtime identity | S7 |
| §4 Herdr as runtime substrate; two-tier continuity | S1 |
| §4 human-visible naming on operator-owned labels | S2 |
| §5–§7 delegation with process kept out of parent context | S5, S8 |
| §8 checkpoint-based continuation without transcript | S7 |
| §9, §10 minimal contract, envelope and escalation types | S5, S6, S8 |
| §11 fresh reviewer, minimal material, preserved verdict | S6 |
| §13 writable isolation, cleanup, `resources_clean` | S3 |
| §14, §15 no supervisor introduced | ADR-006 retained |

§17 is a design guardrail rather than an empirically tested claim; it is adopted to prevent
recurrence of the v3 complexity growth described in Context.

`terminal_title` is agent-owned and volatile and is never a naming carrier (S2). Agent
names are technical slugs; human-visible identity lives on operator-owned labels.

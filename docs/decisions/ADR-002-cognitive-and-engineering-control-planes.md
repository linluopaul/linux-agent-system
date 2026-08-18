# ADR-002: Cognitive and Engineering Control Planes

- Status: Accepted
- Date: 2026-08-18
- Scope: Agent role authority, provider preferences, execution packets and review context

## Context

ADR-001 made Orca the primary execution and collaboration plane and recorded Codex as the
then-current Root preference. That role preference concentrates problem definition and the
implementation edit/verify/fix loop in one session, makes premium judgment usage harder to
bound, and does not distinguish a delegating engineering lead from an ordinary Worker.

The system needs one Root to remain accountable for each outcome while a separate,
first-class role owns autonomous engineering delivery. Its workflow should make normal
execution usage substantially exceed Root usage—currently expected to map mostly to Codex
and Claude respectively—and preserve meaningful independent review across replaceable
providers.

## Decision

Adopt two control planes:

- **Root / Cognitive Control Plane**, with Claude preferred, owns requirement clarification,
  goal definition, reconnaissance strategy, architecture planning, acceptance criteria,
  constraints/non-goals, risk classification, Execution Packet creation, ambiguity
  resolution, escalation handling and final outcome accountability.
- **Execution Lead / Engineering Control Plane**, with Codex preferred, owns implementation
  planning, repository investigation, coding, debugging, tests and verification, iterative
  fixes, and the decision to solve directly, use provider-internal subagents or dispatch an
  Execution Worker.
- **Execution Worker**, with DeepSeek preferred, performs well-scoped implementation,
  search, test generation and mechanical refactoring, normally under the Execution Lead.
  A Worker has no delegation authority.

One Root still owns one task outcome. The Execution Lead receives bounded execution
authority through a supervised Orca Dispatch; it does not receive outcome ownership and is
not a full-handoff recipient.

## Execution Packet and Re-entry

The Execution Packet is the Root's primary work product and sole normal interface to the
Execution Lead. It contains the goal, background/problem statement, objective acceptance
criteria, constraints/non-goals, risk, decided architecture, delegated open questions,
reconnaissance strategy, required tests/evals, required evidence, worktree/base commit,
budget/human gates, escalation contract and expected report format.

The packet's escalation contract may narrow the standing closed list but may not extend or
redefine it.

Root re-entry is a closed list:

1. architecture materially changes
2. acceptance criteria are ambiguous
3. difficult diagnosis remains unresolved
4. HIGH-risk independent review is required
5. deterministic verification cannot resolve uncertainty
6. execution is blocked by something outside the Execution Lead's authority—a protected
   human gate, a missing authorization or credential, an exhausted budget or concurrency
   limit, an unavailable required dependency, or acceptance criteria that are infeasible
   or mutually contradictory

Everything else—including routine implementation decisions, test failures, refactors,
tooling problems and local design—is owned by the Execution Lead.

Condition 6 is an authority escalation, not a cognitive re-entry. The Root routes it to a
human gate or amends the packet without taking over implementation. If unresolved, the
Lead settles `worker_done --outcome failed` with the blocker and the Root promotes the
durable task to GitHub Blocked / Needs-Human.

## Orca Run Topology

The Root-owned Run contains the parent Task and Execution Lead Dispatch and remains bound
to the Root terminal. A Lead that dispatches Workers creates a separate Lead-owned Run
with `run-create`, records the parent Task and Dispatch IDs in its objective and evidence,
and never calls `run-use` on the Root-owned Run. Worker questions terminate at the Lead;
the Lead settles/releases every sub-dispatch before its parent `worker_done`, and the Root
receives compressed evidence rather than Worker transcripts.

## Cost and Review Structure

Root reconnaissance is bounded to what is required to specify the packet. The Root does
not run the implementation edit/verify/fix loop. One Execution Packet is the default;
iterative fixes remain inside the Execution Lead's dispatch. The Lead reports compressed
evidence rather than full transcripts or reasoning dumps. The Root uses long
`check --wait` windows; frequent polling, terminal reading and step-by-step direction are
the Root-micromanagement anti-pattern. Escalations are bounded question/decision exchanges
and never transfer the implementation loop back to the Root.

These are workflow rules intended to produce execution-heavy usage, not an automated
enforcement claim. V0 manually records `root_vs_execution_usage_share`; the Platform
Steward evaluates the rolling window until Controller automation exists.

Independent review means fresh-session context independence. The Reviewer receives the
original task, acceptance criteria, diff/commit, verification evidence, relevant docs and
risk, but not Root private reasoning/transcripts, Execution Packet rationale or a
Root-authored defense. A Root session never reviews its own work. For HIGH-risk work, the
reviewer provider must differ from the implementer provider when a capable alternative
exists; otherwise a human-visible waiver must accept the residual same-provider
correlation risk.

## Provider Preferences

Preferences remain replaceable policy, never permanent bindings:

- Claude: Root / Cognitive Control Plane
- Codex: Execution Lead / Engineering Control Plane
- DeepSeek: well-scoped Execution Worker
- Claude, then Codex: fresh-session independent review
- provider different from implementer: HIGH-risk review
- any capable provider: fallback based on evidence, availability, independence and budget

## Relationship to ADR-001

This ADR supersedes **only** ADR-001's provider-role preferences. ADR-001 remains Accepted,
and all of its decisions that make Orca the primary ADE/worktree/collaboration/orchestration
plane remain in force. The thin Python Controller still must not duplicate Orca's worktree,
terminal, messaging or dispatch lifecycle. GitHub remains the durable system of record.
Herdr remains optional future infrastructure only for explicitly approved detached or
persistent terminal workloads, never the default or a silent fallback.

## Consequences

Benefits:

- cognitive judgment and engineering execution have explicit authority boundaries
- the Execution Lead can delegate without turning every engineering choice into Root work
- the manually recorded usage metric makes Root-heavy drift observable in V0
- reviewer context isolation is explicit even when Root and Reviewer share a provider

Costs and residual risks:

- Execution Packets must be objective enough for autonomous execution
- closed-list escalations require disciplined boundary enforcement
- same-provider review can still have model-level correlated blind spots
- Orca task/dispatch settlement remains necessary for supervised ownership tracking

If an Execution Lead fails mid-flight, the Root owns parent-Dispatch recovery and
replacement while preserving the worktree and uncommitted work. After the prior terminal
is proven inactive and ownership is reassigned, a replacement Execution Lead—not the
Root—owns the resumed edit/verify loop.

## Verification

Repository policy tests assert provider ordering, the Execution Lead role, the closed six
re-entry list, Execution Packet fields, fresh-session review independence and the preserved
Orca/Controller/Herdr boundaries.

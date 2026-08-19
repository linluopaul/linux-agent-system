# AGENTS.md

Always-loaded invariant layer. Detailed procedures live in the referenced policies, Skills
and runbooks; do not restate them here.

## Project Purpose

This repository defines and operates a durable multi-agent development system on Linux:
GitHub as the durable system of record; Orca as the primary agent development environment and execution plane;
Orca-managed Git worktrees for task isolation; Orca CLI
and Orchestration for agent launch, collaboration and completion tracking; Claude, Codex,
DeepSeek and future providers as replaceable agent models; a thin Python Controller for
deterministic policy and external-system coordination; tests and evals as the primary
verification mechanism; and multiple Linux nodes without sharing writable working
directories. **Herdr is not the default** execution plane. Models, harnesses and machines may
change; project knowledge, task state, quality rules and Git history must remain portable.

## Source of Truth

When sources disagree: (1) executable tests and evals, (2) code, schema and configuration,
(3) architecture and project documentation, (4) comments and conversational context.
Important project knowledge must not live only inside an agent session.

## Repository Map

`docs/` (rationale, ADRs, runbooks), `.agent/roles/` (role authority), `.agent/harnesses/`
(harness behavior), `.agent/providers/` (pools), `.agent/policies/` (routing, risk, retry,
capabilities, efficiency), `.agent/skills/` (load-on-demand procedures), `.agent/runs/`
(telemetry), `controller/`, `src/`, `tests/`, `evals/`, `infra/`, `data/`.

## Single normative source per rule

One authoritative source; references elsewhere, never a verbatim second copy: routing →
`routing.yaml`; risk/review/gates → `risk.yaml`; review-cycle budget → `retry.yaml`;
efficiency → `efficiency.yaml`; capabilities → `capabilities.yaml`; writable delegation →
`.agent/skills/orca-writable-delegation/SKILL.md`; role authority → `.agent/roles/`; harness
behavior → `.agent/harnesses/`. Prefer a short reference over restating a rule; do not create
indirection so extreme that an agent must open many files to learn one basic rule.

## Agent Autonomy

One Root Agent owns one task outcome. The Root / **Cognitive Control Plane** owns requirement clarification, goal definition,
reconnaissance strategy, architecture planning, acceptance criteria, constraints and
non-goals, risk classification, Execution Packet creation, ambiguity resolution, escalation
handling, and the final outcome. The Root selects the Execution Lead harness class per task
and records it in the packet. The Execution Lead / **Engineering Control Plane** receives
bounded authority through a supervised Orca Dispatch and owns implementation, debugging,
tests/verification, iterative fixes, and the solve-directly / subagent / Worker-delegation
decision. Its distinguishing property is **delegation authority** — Workers may not
delegate. Give the Lead outcomes, constraints and acceptance criteria, not a prescribed
reasoning process.

## Execution Packet and Escalation

The Execution Packet is the Root's primary work product and the sole normal interface from
Root to Execution Lead. It splits into **CORE** (always required) and **CONDITIONAL**
(required only when the task uses that feature; conditionality is not optionality).

CORE: `GOAL`, `BACKGROUND / PROBLEM STATEMENT`, `ACCEPTANCE CRITERIA`,
`CONSTRAINTS / NON-GOALS`, `RISK: LOW | MEDIUM | HIGH`, `ARCHITECTURE DECISIONS`,
`OPEN QUESTIONS DELEGATED`, `RECONNAISSANCE STRATEGY`, `REQUIRED TESTS / EVALS`,
`VERIFICATION EVIDENCE REQUIRED`, `EXECUTION HARNESS`, `MODEL POLICY`,
`CAPABILITY PROFILE`, `EFFICIENCY PROFILE`, `CONTEXT BUDGET`, `OUTPUT MODE`,
`SESSION POLICY`, `COMPACTION POLICY`, `EXECUTION / RETRY BUDGET`, `ESCALATION THRESHOLD`,
`BUDGET / HUMAN GATES`, `ESCALATION CONTRACT`, `EXPECTED REPORT FORMAT`.

CONDITIONAL — when writable delegation is used, the writable block is mandatory:
`WORKTREE / BASE COMMIT`, `LEAD BRANCH`, `INTEGRATION_BASE_SHA`,
`ALLOWED CHANGED PATHS / SCOPE`, `VERIFICATION REQUIREMENTS`, `RESULT MODE`; an
independent-review and premium budget envelope under `MODEL POLICY` / `BUDGET / HUMAN GATES`;
specialized `CAPABILITY PROFILE` grants (`.agent/policies/capabilities.yaml`); and
remote/system-operation fields.

Git field semantics: `WORKTREE / BASE COMMIT` = placement plus **source ref**;
`LEAD BRANCH` = **target branch**; `INTEGRATION_BASE_SHA` = immutable commit the Lead
must exactly match before any tracked edit; `ALLOWED CHANGED PATHS / SCOPE` = **path
boundary**; `VERIFICATION REQUIREMENTS` = base, ancestry, scope, **integrated-state**
gates; `RESULT MODE` = **immutable unit**.

Agent-to-agent reports use the terse `STATUS / CHANGED / VERIFY / COMMIT / BLOCKERS /
UNCERTAINTY / NEXT` block and never narrate routine tool usage, except clarity overrides
(architecture, acceptance, security, destructive ops, human approvals, ambiguity, HIGH-risk
findings). The `ESCALATION CONTRACT` may narrow the standing conditions below for a task but
may never extend or redefine this closed list. The Execution Lead re-engages the Root only
when one of these six conditions applies:

1. architecture materially changes
2. acceptance criteria are ambiguous
3. difficult diagnosis remains unresolved
4. HIGH-risk independent review is required
5. deterministic verification cannot resolve uncertainty
6. execution is blocked by something outside the Execution Lead's authority—a protected
   human gate, a missing authorization or credential, an exhausted budget or concurrency
   limit, an unavailable required dependency, or acceptance criteria that are infeasible
   or mutually contradictory

This is a closed Root re-entry list; routine choices, test failures, refactors, tooling
problems and local detail stay with the Execution Lead. This is the single canonical full
wording — role files reference it, never copy it. Condition 6 is an authority escalation,
not a cognitive re-entry: the Root routes it to the human gate or amends the packet. If
unresolved, the Lead sends `worker_done --outcome failed` and the Root promotes the task to
GitHub Blocked / Needs-Human.

## Delegation

The Execution Lead delegates when work is independently specifiable, parallelizable,
execution-heavy, high-context or benefits from an independent opinion. Workers get bounded
scope, return concise evidence, and never delegate further or expand architecture.

## Runtime and Controller Boundaries

Use Orca for worktree creation/tracking, launching agent terminals locally or on remote
environments, structured messaging/dispatch/completion tracking, and worktree/terminal
status; use version-matched Orca guides before automating Orca commands. Do not duplicate Orca's deterministic worktree,
terminal, messaging or dispatch lifecycle inside the Python
Controller; the Controller focuses on GitHub task polling, risk and budget policy, node scheduling,
deterministic tests and evals, metrics, human gates, and backup/recovery. If an
Execution Lead fails mid-flight, preserve the worktree and uncommitted changes; the Root
owns parent-Dispatch recovery and reassigns a replacement Execution Lead that resumes the
loop — it never takes the loop over. Herdr is not the default execution plane.

## Risk and Verification

Tasks are LOW, MEDIUM or HIGH; `risk.yaml` is the sole authority for whether independent
review is required. HIGH-risk work requires independent verification. Never claim a test or
evaluation passed unless it was actually executed; do not weaken tests to make them pass;
prefer executable verification over prose review. Review independence means fresh-session context independence
— the reviewer runs in its own worktree/terminal with no Root context
and never receives the Root's private reasoning, Execution Packet rationale, implementer
reasoning, or the Root's defense. A Root session must never review its own work; any session
carrying Root context is not independent. For HIGH-risk work the reviewer's provider MUST
differ from the implementer's provider when a capable alternative is available; otherwise a
human-visible waiver accepting residual same-provider correlation risk must be recorded
before completion.

## Git Rules

Use one active task per branch/worktree; never modify another agent's active worktree.
Declare an immutable `integration_base_sha` on every writable delegation and load
`.agent/skills/orca-writable-delegation/SKILL.md` before performing it. Every supervised
writable dispatch launches through `orca orchestration worker-start` from an explicit base
with a proven pre-dispatch `HEAD == integration_base_sha`; the Worker is verify-only and
returns an immutable ordered linear commit list; Orca parent/child lineage is orchestration
provenance, not proof of Git ancestry; integration is `git cherry-pick -x` with recorded SHA
mappings and `worker-release` before delivery acknowledgment. Do not share one writable
working directory between Linux nodes; cross-machine sync uses Git branches/commits/pushes/
fetches/PRs. Secrets must never be committed; large market datasets must not be stored
in Git.

## Cost and Efficiency

Use the cheapest capable resource; prefer deterministic tools, scripts, tests and evals over
model calls; reserve premium agents for ambiguity, architecture, difficult diagnosis,
conflict resolution and high-risk independent review. Routing is role → harness →
model/provider pool; harnesses and pools are preferences, never permanent bindings; Pi is a
harness with a runtime-selected model, never a fixed model. Reasoning effort is not a
token-savings lever: low-cost pools keep high or provider-recommended effort; premium
model/reasoning effort is **adaptive**
within the Root-defined envelope, never hard-coded HIGH (`efficiency.yaml`). The
implementation edit/verify/fix loop stays with the Execution Lead; the Root supervises with
long `check --wait` windows and compressed evidence. **Root micromanagement** — frequent
polling or step-by-step direction — is the anti-pattern; normal execution volume exceeds
Root reasoning volume.

## Efficiency Principles

1. Never fabricate paths, commands, versions, signatures, test results or evidence.
2. Do not present materially unverified claims as fact; name the assumption and how to
   verify it.
3. "Done" requires actual verification.
4. Do not re-read unchanged in-context files without reason.
5. Store distilled conclusions, not raw transcripts.
6. Prefer existing Skills, tools and CLIs over hand-rolled equivalents.
7. Surgical diffs; no unrelated refactors.
8. Repeated failure triggers diagnosis/escalation, not blind repetition.
9. Routine execution is silent; communicate at meaningful boundaries.
10. Context is scarce; durable artifacts survive sessions.

## Human Gates

Agents must not independently relax production trading permissions; destructive
data-access restrictions; secret or credential protections; HIGH-risk independent-review
requirements; order or capital safety guardrails; maximum budget or concurrency limits;
production deployment gates; or minimum backup-retention requirements. Agents may propose
changes through issues or pull requests.

## Knowledge Management

Use `AGENTS.md` for long-lived rules, `docs/` for durable knowledge, ADRs for decisions,
GitHub Issues for task-specific memory, `.agent/runs/` for telemetry, tests/evals for
verifiable rules, Skills for repeated workflows, and Controller code for automation. Do not
use complete chat transcripts as default future context.

## Definition of Done

A task is complete only when acceptance criteria are satisfied; required tests and evals
were executed and passed; required documentation is updated; there is no known blocking
regression; required independent verification is complete; unresolved uncertainty is
explicitly reported; meaningful changes are committed; and task state is synchronized with
the project system of record.
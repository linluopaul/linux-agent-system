# AGENTS.md

## Project Purpose

This repository defines and operates a durable multi-agent development
system on Linux.

The system is designed around:

- GitHub as the durable system of record
- Herdr as the execution and communication plane
- Claude, Codex, DeepSeek and future providers as replaceable agents
- Python Controller as a deterministic control plane
- independent worktrees for concurrent tasks
- tests and evals as the primary verification mechanism
- multiple Linux nodes without sharing writable working directories

Models, harnesses and machines may change.
Project knowledge, task state, quality rules and Git history must remain
portable.

## Source of Truth

Use the following priority when sources disagree:

1. executable tests and evals
2. code, schema and configuration
3. architecture and project documentation
4. comments and conversational context

Important project knowledge must not exist only inside an agent session.

## Repository Map

- `docs/` — architecture, decisions and runbooks
- `.agent/providers/` — provider-specific guidance
- `.agent/roles/` — role-specific guidance
- `.agent/policies/` — routing, risk and retry policies
- `.agent/skills/` — reusable agent workflows
- `.agent/runs/` — runtime telemetry and task artifacts
- `controller/` — deterministic Python controller
- `src/` — product/application source code
- `tests/` — automated tests
- `evals/` — behavioral and high-risk evaluations
- `infra/` — bootstrap, systemd and node infrastructure
- `data/` — local datasets; large data must not be committed to Git

## Agent Autonomy

One Root Agent owns one task outcome.

The Root Agent may dynamically decide whether to:

- solve the task directly
- investigate first
- delegate work
- parallelize independent work
- request independent review
- escalate to another provider

Do not create agents merely to satisfy a fixed workflow.

Give agents outcomes, constraints and acceptance criteria rather than
a manually prescribed reasoning process.

## Delegation

Prefer delegation when work:

- can be independently specified
- can run in parallel
- produces large amounts of intermediate context
- is execution-heavy or repetitive
- benefits from an independent opinion

Avoid delegation when coordination and handoff cost exceeds the likely
benefit.

## Cost Policy

Use the cheapest capable resource.

Prefer deterministic tools, scripts, tests and evals over model calls.

Reserve premium agents for:

- ambiguity
- architecture
- difficult diagnosis
- conflict resolution
- high-risk independent verification

Provider roles are preferences, not permanent bindings.

## Risk

Tasks are classified as LOW, MEDIUM or HIGH.

HIGH risk includes, but is not limited to:

- financial calculations
- market-data transformations
- adjustment-factor logic
- backtesting
- look-ahead-sensitive logic
- trading signals
- position and risk calculations
- order execution
- authentication and authorization
- destructive migrations
- Controller security and safety policies

HIGH-risk changes require independent verification.

## Verification

Never claim that a test or evaluation passed unless it was actually
executed.

Do not weaken tests merely to make them pass.

Prefer executable verification over prose review whenever possible.

Independent reviewers should receive the original task, acceptance
criteria, relevant diff or commit, tests and necessary documentation.

Do not automatically provide the implementer's full reasoning to an
independent reviewer.

## Git Rules

Use one active task per branch/worktree.

Do not modify another agent's active worktree.

Do not share one writable Git working directory between Linux nodes.

Cross-machine synchronization must use Git branches, commits, pushes,
fetches, pull requests or explicit artifacts.

Secrets must never be committed.

Large market datasets must not be stored directly in Git.

## Human Gates

Agents must not independently relax:

- production trading permissions
- destructive data-access restrictions
- secret or credential protections
- HIGH-risk independent-review requirements
- order or capital safety guardrails
- maximum budget or concurrency limits
- production deployment gates
- minimum backup-retention requirements

Agents may propose changes through issues or pull requests.

## Knowledge Management

Use:

- `AGENTS.md` for long-lived behavioral rules
- `docs/` for durable project knowledge
- ADRs for architectural decisions
- GitHub Issues for task-specific memory
- `.agent/runs/` for runtime telemetry
- tests/evals for objectively verifiable rules
- Skills for repeated workflows
- Controller code for deterministic automation

Do not use complete chat transcripts as default future context.

## Definition of Done

A task is complete only when:

1. acceptance criteria are satisfied
2. required tests and evals were executed and passed
3. required documentation is updated
4. there is no known blocking regression
5. required independent verification is complete
6. unresolved uncertainty is explicitly reported
7. meaningful changes are committed
8. task state is synchronized with the project system of record

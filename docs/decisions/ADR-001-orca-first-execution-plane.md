# ADR-001: Orca-First Execution and Collaboration Plane

- Status: Accepted
- Date: 2026-08-18
- Scope: Multi-agent development runtime and Controller boundary

## Context

The initial architecture made Herdr the default execution and communication plane and gave
the future Python Controller responsibility for worktree creation, agent launch, runtime
monitoring and task completion tracking.

The installed Orca runtime already supplies deterministic, versioned interfaces for the
agent development environment, Git-worktree isolation, terminals, local and configured
remote execution, structured messaging, task dispatch and worker completion. Reimplementing
those capabilities in the Controller would create two competing lifecycle authorities.

The durable project invariants remain valid: GitHub is the system of record, every outcome
has one Root, Workers and Reviewers remain dynamic roles, risk is LOW/MEDIUM/HIGH, HIGH-risk
work requires independent review, and project memory lives in repository artifacts rather
than a provider session.

## Decision

Orca is the primary:

- agent development environment
- Git-worktree isolation layer
- agent collaboration plane
- agent launch and terminal interface
- local and SSH/connected-environment execution layer
- multi-agent orchestration and completion-tracking mechanism

GitHub remains the durable system of record. Orca runtime state is operational state, not a
replacement for issues, Kanban, commits, pull requests, tests, evals, docs or ADRs.

The Python Controller will not implement a parallel worktree/terminal/message/dispatch
scheduler. It will focus on:

- GitHub task polling, claiming and state synchronization
- risk, budget, retry and provider policy
- node eligibility, capacity and scheduling
- deterministic tests and evals
- metrics and audit summaries
- protected human gates
- backup and recovery policy

Where the Controller needs an execution effect, it delegates that effect to the
version-matched Orca CLI/Orchestration contract and records only the policy decision and
durable outcome.

Herdr is optional infrastructure, not a default fallback. It may be introduced for a future
workload that explicitly requires detached or persistent long-running terminal sessions.
Such a workload must define ownership, state promotion and recovery boundaries so it does
not compete with Orca orchestration or GitHub.

Provider preferences become:

- Codex: default Root
- DeepSeek: preferred low-cost Worker for well-scoped implementation, search and testing
- Claude: preferred premium specialist for architecture, difficult diagnosis, ambiguity
  resolution and independent HIGH-risk review

These are routing preferences, never permanent provider-role bindings.

## Consequences

Benefits:

- one deterministic authority for worktree, terminal and dispatch lifecycle
- less Controller code and fewer split-brain failure modes
- consistent local and remote agent operation
- version-matched operational guidance from the installed Orca runtime
- provider choices remain replaceable and policy-driven

Costs and constraints:

- Orca runtime availability is required for the primary interactive workflow
- structured collaboration requires Orca's Orchestration experimental feature to be
  enabled on each participating installation
- exact CLI grammar must be loaded from the installed skills rather than copied from stale
  documentation
- multi-node/SSH behavior must be validated against real saved environments and repository
  availability
- Herdr-specific persistent workloads need a future, explicit adapter and decision record

When Orca is unavailable, the safe default is to preserve Git state and pause new
supervised multi-agent work until the runtime is restored. An explicitly authorized
emergency manual mode may use one Root in one existing worktree, but it cannot claim Orca
Dispatch provenance and must promote all durable state to GitHub. Herdr is not an automatic
fallback.

`.agent/policies/risk.yaml` is authoritative for whether independent review or a human
gate is required. `.agent/policies/routing.yaml` selects providers after those
requirements are known.

## Verification

The repository policy tests assert the primary runtime boundary, provider ordering and
HIGH-risk review requirement. Manual validation must also exercise Orca worktree creation,
agent launch, supervised review completion and Git synchronization before Controller
automation is implemented.

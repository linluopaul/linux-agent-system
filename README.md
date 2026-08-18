# Linux Agent System

A portable, Orca-first multi-agent development system for Linux.

## Core Architecture

- GitHub — durable system of record for code, issues, Kanban, reviews and history
- Orca — primary ADE, Git-worktree isolation layer, agent collaboration plane,
  terminal/launch interface, local or SSH execution layer, and orchestration mechanism
- Codex / DeepSeek / Claude — replaceable providers with task-specific preferences
- Root / Cognitive Control Plane — defines the problem, architecture, acceptance and risk
- Execution Lead / Engineering Control Plane — autonomously delivers the bounded work
- Python Controller — future thin policy and external-system coordination plane
- Tests and evals — primary verification mechanism
- Multiple Linux nodes — independent clones and worktrees synchronized through Git
- Herdr — optional future infrastructure for workloads that specifically need detached or
  persistent long-running terminal sessions

## Provider Preferences

Provider roles remain replaceable rather than permanently bound:

- Claude is preferred for Root / Cognitive Control Plane work.
- Codex is preferred for the first-class Execution Lead / Engineering Control Plane role.
- DeepSeek is the preferred low-cost Execution Worker for well-scoped implementation,
  search, test generation and mechanical refactoring, normally dispatched by the
  Execution Lead.
- Independent review uses a fresh, context-isolated session; Claude is preferred, followed
  by Codex. HIGH-risk review uses a provider different from the implementer when a capable
  alternative exists, or records a human-visible residual-risk waiver.

Capability, availability, risk and budget can override these preferences.

The Root produces one bounded Execution Packet and supervises through Orca without running
the edit/verify/fix loop. The Execution Lead owns that loop, chooses any Worker delegation,
and returns compressed verification evidence. These workflow rules are intended to keep
normal execution usage substantially above Root usage; V0 records the ratio manually, and
the current Claude/Codex mapping is a preference rather than the invariant.

## Runtime Boundaries

Orca owns deterministic worktree creation, agent terminal launch, messaging, dispatch and
completion tracking. The future Controller should use Orca's interfaces instead of
reimplementing those functions.

The Controller remains responsible for GitHub task polling and state synchronization,
risk/budget policy, node scheduling, deterministic tests and evals, metrics, human gates,
and backup/recovery.

GitHub remains authoritative. Orca session state and `.agent/runs/` telemetry are useful
runtime records, but durable decisions and task outcomes must be promoted to issues,
commits, pull requests, docs, tests or evals.

## Current Stage

The project is in manual Orca-first workflow validation. Controller automation will be
added only after the worktree, launch, collaboration, review and multi-node workflows have
been exercised on real tasks.

See:

- `docs/ARCHITECTURE.md` — system architecture
- `docs/decisions/ADR-001-orca-first-execution-plane.md` — architecture decision
- `docs/decisions/ADR-002-cognitive-and-engineering-control-planes.md` — role-plane decision
- `docs/runbooks/ORCA_WORKFLOW.md` — current operational workflow

## Repository Structure

- `AGENTS.md` — universal agent rules
- `CLAUDE.md` — Claude Code adapter
- `.agent/providers/` — provider-specific guidance
- `.agent/roles/` — Root, Execution Lead, Worker, Reviewer and Platform Steward roles
- `.agent/policies/` — routing, risk and retry policies
- `docs/` — architecture, decisions and runbooks
- `controller/` — future thin Python Controller
- `tests/` — automated tests
- `evals/` — behavioral and high-risk evaluations
- `infra/` — bootstrap and node infrastructure
- `data/` — local datasets, not stored directly in Git

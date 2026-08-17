# Linux Agent System

A portable, Orca-first multi-agent development system for Linux.

## Core Architecture

- GitHub — durable system of record for code, issues, Kanban, reviews and history
- Orca — primary ADE, Git-worktree isolation layer, agent collaboration plane,
  terminal/launch interface, local or SSH execution layer, and orchestration mechanism
- Codex / DeepSeek / Claude — replaceable providers with task-specific preferences
- Python Controller — future thin policy and external-system coordination plane
- Tests and evals — primary verification mechanism
- Multiple Linux nodes — independent clones and worktrees synchronized through Git
- Herdr — optional future infrastructure for workloads that specifically need detached or
  persistent long-running terminal sessions

## Provider Preferences

Provider roles remain replaceable rather than permanently bound:

- Codex is the default Root.
- DeepSeek is the preferred low-cost Worker for well-scoped implementation, search and
  testing.
- Claude is the premium specialist for architecture consultation, difficult diagnosis,
  ambiguity resolution and independent HIGH-risk review.

Capability, availability, risk and budget can override these preferences.

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
- `docs/runbooks/ORCA_WORKFLOW.md` — current operational workflow

## Repository Structure

- `AGENTS.md` — universal agent rules
- `CLAUDE.md` — Claude Code adapter
- `.agent/providers/` — provider-specific guidance
- `.agent/roles/` — Root, Worker, Reviewer and Platform Steward roles
- `.agent/policies/` — routing, risk and retry policies
- `docs/` — architecture, decisions and runbooks
- `controller/` — future thin Python Controller
- `tests/` — automated tests
- `evals/` — behavioral and high-risk evaluations
- `infra/` — bootstrap and node infrastructure
- `data/` — local datasets, not stored directly in Git

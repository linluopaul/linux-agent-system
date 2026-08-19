# Linux Agent System

A portable, Orca-first multi-agent development system for Linux.

## Core Architecture

- GitHub — durable system of record for code, issues, Kanban, reviews and history
- Orca — primary ADE, Git-worktree isolation layer, agent collaboration plane,
  terminal/launch interface, local or SSH execution layer, and orchestration mechanism
- Pi / Claude Code / Codex CLI — replaceable harnesses; Pi has a runtime-selected
  model/provider pool and is never a fixed model
- Root / Cognitive Control Plane — defines the problem, architecture, acceptance and risk
- Execution Lead / Engineering Control Plane — autonomously delivers the bounded work;
  the Root selects Pi Standard/Fast by default and Codex Premium for difficult work
- Python Controller — future thin policy and external-system coordination plane
- Tests and evals — primary verification mechanism
- Multiple Linux nodes — independent clones and worktrees synchronized through Git
- Herdr — optional future infrastructure for workloads that specifically need detached or
  persistent long-running terminal sessions

## Harness and Model-Pool Preferences

Harnesses and model/provider pools remain replaceable rather than permanently bound. Pi is a
harness with a runtime-selected model and is never a fixed model. Routing is
`role -> harness class -> model/provider pool` (see `.agent/policies/routing.yaml`):

- The Root selects the Execution Lead harness per task. Pi Standard/Fast is the default for
  well-scoped, lower-complexity, LOW/MEDIUM work; Codex Premium is the escalation for
  difficult engineering reasoning, complex repository investigation, difficult debugging,
  HIGH-risk or cross-module implementation.
- A high-capability pool (for example Claude) is preferred for Root / Cognitive Control
  Plane work.
- A low-cost pool (for example DeepSeek, MiniMax or Kimi) is preferred for well-scoped
  Execution Worker work; the Worker role is not bound to any one pool.
- Independent review uses a fresh, context-isolated session; a capable pool is preferred,
  followed by another. HIGH-risk review uses a pool different from the implementer's when a
  capable alternative exists, or records a human-visible residual-risk waiver.

Capability, availability, risk and budget can override these preferences.

The Root produces one bounded Execution Packet and supervises through Orca without running
the edit/verify/fix loop. The Execution Lead owns that loop, chooses any Worker delegation,
and returns compressed terse verification evidence. These workflow rules keep execution
volume above Root reasoning volume and low-cost execution above premium execution; the
execution-cost metrics (`execution_vs_root_usage_share`, `premium_vs_low_cost_execution_share`,
`context_and_output_cost_per_successful_task`) record the ratio manually in V0, and the
current harness/pool mapping is a preference rather than the invariant.

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
- `.agent/harnesses/` — harness class profiles (pi, claude-code, codex-cli)
- `.agent/providers/` — model/provider-pool profiles
- `.agent/roles/` — Root, Execution Lead, Worker, Reviewer and Platform Steward roles
- `.agent/policies/` — routing, risk, retry, capabilities and efficiency policies
- `docs/` — architecture, decisions and runbooks
- `controller/` — future thin Python Controller
- `tests/` — automated tests
- `evals/` — behavioral and high-risk evaluations
- `infra/` — bootstrap and node infrastructure
- `data/` — local datasets, not stored directly in Git

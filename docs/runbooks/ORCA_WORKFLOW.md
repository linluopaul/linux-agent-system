# Orca-First Task Workflow

This runbook describes the repository's manual first version. Orca command grammar changes
between releases, so the installed skills are authoritative.

## 1. Resolve and Inspect the Runtime

Choose one CLI executable for the whole session:

1. Use `ORCA_CLI_COMMAND` when Orca exported it.
2. In an Orca development checkout with `ORCA_DEV_REPO_ROOT`, use `orca-dev`.
3. On Linux outside an Orca-managed terminal, use `orca-ide`.
4. Otherwise, from an Orca-managed terminal, use `orca`.

Do not run bare `orca` from an ordinary Linux shell because it may resolve to the GNOME
screen reader.

Before operating runtime state, replace `ORCA` below with the selected executable and run:

```text
ORCA skills get orca-cli
ORCA skills get orchestration
ORCA status --json
```

Read both complete guides. Do not guess subcommands or flags from memory. Confirm the
runtime is reachable and, before relying on structured coordination, confirm the
Orchestration experimental feature is enabled in Orca Settings > Experimental on every
participating installation.

## 2. Prepare the Durable Task Packet

The GitHub Issue or equivalent durable task record should contain:

```text
GOAL
ACCEPTANCE CRITERIA
CONSTRAINTS / NON-GOALS
RISK: LOW | MEDIUM | HIGH
BUDGET / HUMAN GATES
RELEVANT DOCS
REQUIRED TESTS / EVALS
BASE REF
```

The Controller may poll, claim, classify policy and choose an eligible node. GitHub remains
authoritative for task state.

## 3. Create or Select the Root Workspace

Codex is the default Root preference. Use an Orca-managed worktree for each writable task.
Choose worktree lineage separately from the Git base:

- use a child worktree for work stacked on or dependent on the active task
- use a top-level worktree for an independent task
- never share one writable checkout across nodes

Use Orca's agent-first worktree creation when a new Root is needed and follow the current
guide's setup policy. Do not replace it with raw `git worktree` plus an ad hoc PTY.

## 4. Delegate Supervised Work

When the Root must receive and integrate a result, use Orca Orchestration:

```text
run-create
task-create
worker-start
check --wait
process every message in the Delivery
worker-release OR worker-start --terminal <handle> for immediate reuse
check --ack <delivery_id> --wait
```

A coordinator `check` replays the same oldest Delivery until its `delivery_id` is
acknowledged. Process every message and decide each settled terminal's next owner before
acknowledging. A wait timeout or `{count:0}` is a liveness checkpoint, not a Worker
failure; keep waiting while the Dispatch is healthy.

Create independent tasks before starting parallel Workers. Prefer DeepSeek for well-scoped
implementation, search and testing when a configured DeepSeek launcher is available. Agent
IDs are installation-specific; inspect the runtime rather than guessing an ID.

Use a fresh Claude agent for architecture consultation, difficult diagnosis, ambiguity
resolution and independent HIGH-risk review. A Reviewer gets the original task, acceptance
criteria, relevant diff or commit, test/check results and necessary docs, but not the
implementer's private reasoning.

A valid supervised Worker or Reviewer must settle its dispatch with exactly one
`worker_done`. After accepting completion, the Root either reuses the exact worker for an
immediate follow-up or releases it through Orchestration.

Use ordinary Orca worktree/terminal prompt delivery only for a genuine ownership handoff
where the original Root will stop monitoring. Do not mix that flow with tracked dispatch
lifecycle.

## 5. Local and Remote Execution

Orca is the primary local and connected-environment/SSH execution layer. The Controller
selects an eligible node from policy and capacity; Orca performs the actual worktree,
terminal and agent lifecycle.

For a remote supervised Worker, use the current guide's `worker-start --on
<saved-environment>` form. Remote `current` and `new-child` are invalid: use an exact
discovered remote worktree selector, or `new-top-level` with an explicit remote repository
selector. The authoritative Run and Task remain on the coordinator runtime. Do not repeat
`--on` on follow-up commands; later communication routes by Dispatch ID.

Each Linux node uses its own clone and writable worktrees. Cross-node synchronization uses
branches, commits, pushes, fetches, pull requests or explicit artifacts—not NFS or a shared
writable directory.

## 6. Runtime-Unavailable Degraded Mode

If Orca is unavailable, do not silently switch the task to Herdr or claim Orca
Orchestration provenance. Preserve existing files and Git state, stop starting new
supervised multi-agent work, and restore the selected Orca runtime first.

Emergency manual work requires explicit human authorization. It is limited to one Root in
one existing worktree with ordinary Git and provider CLI commands, no parallel dispatch or
completion-tracking claims, and mandatory promotion of commands, commits, verification and
remaining uncertainty to GitHub. Resume the Orca-first workflow at a stable commit. Herdr
still requires its own workload decision and is never the automatic fallback.

## 7. Verify and Complete

The Root:

1. runs required tests and evals
2. records exact commands and results
3. obtains required independent review
4. resolves blocking findings
5. commits meaningful changes
6. updates the GitHub Issue/Kanban and durable documentation
7. reports remaining uncertainty

Do not claim a test passed unless it was executed. Do not merge or push unless the task
explicitly authorizes it.

## 8. Optional Herdr Use

Herdr is not the default ADE, worktree layer, communication plane or orchestrator. Consider
it only for a future workload with a concrete requirement for detached or persistent
long-running terminal sessions.

Before introducing it, document:

- why Orca's normal terminal lifecycle is insufficient
- which system owns process and completion state
- how durable outcomes are promoted to GitHub
- how failure, restart and cleanup avoid split-brain orchestration
- who approved any affected human gate

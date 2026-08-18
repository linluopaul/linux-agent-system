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

## 2. Prepare the Execution Packet

The Root / Cognitive Control Plane is preferably Claude. It performs bounded
reconnaissance—only enough reading to specify the work correctly—and produces one
Execution Packet as the sole normal Root-to-Execution-Lead interface:

```text
GOAL
BACKGROUND / PROBLEM STATEMENT
ACCEPTANCE CRITERIA          (objective and checkable)
CONSTRAINTS / NON-GOALS
RISK: LOW | MEDIUM | HIGH
ARCHITECTURE DECISIONS
OPEN QUESTIONS DELEGATED
RECONNAISSANCE STRATEGY
REQUIRED TESTS / EVALS
VERIFICATION EVIDENCE REQUIRED
WORKTREE / BASE COMMIT
BUDGET / HUMAN GATES
ESCALATION CONTRACT
EXPECTED REPORT FORMAT
```

The Controller may poll, claim, classify policy and choose an eligible node. GitHub remains
authoritative for task state. Reading the entire codebase to prepare the packet is an
anti-pattern; repository investigation belongs to the Execution Lead.

## 3. Create or Select the Root Workspace

Claude is the preferred Root provider. Use an Orca-managed workspace for the Root and an
Orca-managed worktree for each writable task. Choose worktree lineage separately from the
Git base:

- use a child worktree for work stacked on or dependent on the active task
- use a top-level worktree for an independent task
- never share one writable checkout across nodes

Use Orca's agent-first worktree creation when a new Root is needed and follow the current
guide's setup policy. Do not replace it with raw `git worktree` plus an ad hoc PTY.

## 4. Dispatch the Execution Lead

Codex is the preferred first-class Execution Lead / Engineering Control Plane. The Root
uses Orca Orchestration to delegate bounded execution authority without transferring
outcome ownership:

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
acknowledging. A wait timeout or `{count:0}` is a liveness checkpoint, not an Execution
Lead or Worker failure; keep waiting while the Dispatch is healthy.

The Root sends the Execution Packet once by default, then supervises with long
`check --wait` windows. Frequent status polling, terminal reading or step-by-step
direction is the **Root micromanagement** anti-pattern. The Root never takes over the
implementation edit/verify/fix loop; the Execution Lead keeps iterative fixes inside its
dispatch and reports compressed evidence rather than transcripts or reasoning dumps.

The Execution Lead owns implementation planning, repository investigation, coding,
debugging, tests/verification, iterative fixes and the delegation decision. It may solve
directly, use provider-internal subagents, or create and settle Orca sub-dispatches.
Prefer DeepSeek for well-scoped implementation, search, test generation and mechanical
refactoring when a configured launcher is available. An Execution Worker has no delegation
authority and routes routine questions to the Lead, not the Root. Agent IDs are
installation-specific; inspect the runtime rather than guessing an ID.

The Execution Lead re-engages the Root only when:

1. architecture materially changes
2. acceptance criteria are ambiguous
3. difficult diagnosis remains unresolved
4. HIGH-risk independent review is required
5. deterministic verification cannot resolve uncertainty

This is a closed list. Each escalation is one specific question followed by one specific
decision; routine implementation choices, failing tests, refactors, tooling problems and
local design remain with the Lead.

Independent review uses a fresh session in its own worktree or terminal with no Root
context or history. Give the Reviewer the original task, acceptance criteria, relevant
diff or commit, verification evidence, necessary docs and risk level, but not the Root's
private reasoning/transcript, Execution Packet rationale or Root-authored defense. A Root
session never reviews its own work. Same-provider review retains correlated-blind-spot
risk; for a HIGH-risk Claude-authored Root architecture design, prefer or add Codex and
record the residual risk.

A valid supervised Execution Lead, Worker or Reviewer settles its dispatch with exactly
one `worker_done`. After accepting completion, its coordinator either reuses the exact
agent for an immediate follow-up or releases it through Orchestration.

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

The Execution Lead:

1. runs required tests and evals
2. records exact commands and results
3. iterates through failures and creates a reviewable meaningful commit
4. invokes the closed HIGH-risk-review re-entry condition when applicable
5. resolves returned findings, re-verifies and creates the final meaningful commit
6. returns compressed evidence: files, commands, results, findings and uncertainty

The Root:

1. handles only closed-list escalations
2. obtains required fresh-session independent review of the reviewable commit
3. provides bounded review decisions/findings while the Lead retains its active
   implementation loop
4. confirms acceptance and unresolved uncertainty
5. updates the GitHub Issue/Kanban and durable documentation

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

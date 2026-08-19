# AGENTS.md

## Project Purpose

This repository defines and operates a durable multi-agent development
system on Linux.

The system is designed around:

- GitHub as the durable system of record
- Orca as the primary agent development environment and execution plane
- Orca-managed Git worktrees for task isolation
- Orca CLI and Orchestration for agent launch, collaboration and completion tracking
- Claude, Codex, DeepSeek and future providers as replaceable agents
- a thin Python Controller for deterministic policy and external-system coordination
- Herdr as optional infrastructure for workloads that specifically require detached or
  persistent long-running terminal sessions
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
- `.agent/harnesses/` — harness class profiles (pi, claude-code, codex-cli)
- `.agent/providers/` — model/provider-pool profiles
- `.agent/roles/` — role-specific guidance
- `.agent/policies/` — routing, risk, retry, capabilities and efficiency policies
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

The Root is the Cognitive Control Plane. It owns requirement clarification, goal
definition, reconnaissance strategy, architecture planning, acceptance criteria,
constraints and non-goals, risk classification, Execution Packet creation, ambiguity
resolution and escalation handling. It remains accountable for the final outcome.

The Execution Lead is the Engineering Control Plane. The Root delegates bounded execution
authority to it through a supervised Orca Dispatch without transferring outcome ownership.
The Execution Lead owns implementation planning, repository investigation, coding,
debugging, tests and verification, iterative fixes, and the decision to solve directly,
use provider-internal subagents, or dispatch an Execution Worker.

The Execution Lead is a first-class role, not an ordinary Worker. Its distinguishing
property is delegation authority: an Execution Lead may decompose work and dispatch
Workers; a Worker may not. Do not create agents merely to satisfy a fixed workflow.

Give the Execution Lead outcomes, constraints and acceptance criteria rather than a
manually prescribed reasoning process. It executes autonomously until acceptance criteria
are met or a closed escalation condition applies.

## Execution Packet and Escalation

The Execution Packet is the Root's primary work product and the sole normal interface from
Root to Execution Lead. It contains:

```text
GOAL
BACKGROUND / PROBLEM STATEMENT
ACCEPTANCE CRITERIA
CONSTRAINTS / NON-GOALS
RISK: LOW | MEDIUM | HIGH
ARCHITECTURE DECISIONS
OPEN QUESTIONS DELEGATED
RECONNAISSANCE STRATEGY
REQUIRED TESTS / EVALS
VERIFICATION EVIDENCE REQUIRED
WORKTREE / BASE COMMIT
LEAD BRANCH
INTEGRATION_BASE_SHA
ALLOWED CHANGED PATHS / SCOPE
VERIFICATION REQUIREMENTS
RESULT MODE
EXECUTION HARNESS
MODEL POLICY
CAPABILITY PROFILE
EFFICIENCY PROFILE
CONTEXT BUDGET
OUTPUT MODE
SESSION POLICY
COMPACTION POLICY
EXECUTION / RETRY BUDGET
ESCALATION THRESHOLD
BUDGET / HUMAN GATES
ESCALATION CONTRACT
EXPECTED REPORT FORMAT
```

The packet fields are distinct: `WORKTREE / BASE COMMIT` identifies placement and the
source ref used to create it; `LEAD BRANCH` is the target branch;
`INTEGRATION_BASE_SHA` is the immutable commit that the Lead worktree must exactly match
before any tracked-file modification; `ALLOWED CHANGED PATHS / SCOPE` is the path boundary;
`VERIFICATION REQUIREMENTS` defines base, ancestry, scope and integrated-state gates beyond
the named tests/evals; and `RESULT MODE` defines the immutable unit returned to the Root.
`VERIFICATION EVIDENCE REQUIRED` defines which commands, results, SHA mappings and
uncertainty the Lead must retain.

The packet's `ESCALATION CONTRACT` may narrow the standing conditions below for a task,
but it may never extend or redefine this closed list.

Agent-to-agent reports use the terse `STATUS / CHANGED / VERIFY / COMMIT / BLOCKERS /
UNCERTAINTY / NEXT` block and never narrate routine tool usage
(`.agent/policies/efficiency.yaml`). Terse reporting must not apply to architecture
decisions, acceptance criteria, security warnings, destructive operations, human approval
requests, unresolved ambiguity or HIGH-risk findings; human-facing communication stays
concise but normal prose. The Root selects the Execution Lead harness class and the
capability profile per task; assignments declare only task-relevant capabilities
(`.agent/policies/capabilities.yaml`).

The Execution Lead re-engages the Root only when one of these six conditions applies:

1. architecture materially changes
2. acceptance criteria are ambiguous
3. difficult diagnosis remains unresolved
4. HIGH-risk independent review is required
5. deterministic verification cannot resolve uncertainty
6. execution is blocked by something outside the Execution Lead's authority—a protected
   human gate, a missing authorization or credential, an exhausted budget or concurrency
   limit, an unavailable required dependency, or acceptance criteria that are infeasible
   or mutually contradictory

This is a closed Root re-entry list. Routine implementation choices, test failures,
refactors, tooling problems and local design details remain with the Execution Lead.
Condition 6 is an authority escalation, not a cognitive re-entry: the Root routes it to
the human gate or amends the Execution Packet and does not take over the implementation
loop. If the blocker cannot be resolved, the Lead sends `worker_done --outcome failed`
with the blocker, and the Root promotes the task to GitHub Blocked / Needs-Human.

## Delegation

The Execution Lead decides whether to delegate. Prefer an Execution Worker when work:

- can be independently specified
- can run in parallel
- produces large amounts of intermediate context
- is execution-heavy or repetitive
- benefits from an independent opinion

Avoid delegation when coordination and handoff cost exceeds the likely
benefit.

Execution Workers are normally dispatched by the Execution Lead. They receive bounded
scope and return concise evidence; they do not delegate further or expand architecture.

## Cost Policy

Use the cheapest capable resource.

Prefer deterministic tools, scripts, tests and evals over model calls.

Reserve premium agents for:

- ambiguity
- architecture
- difficult diagnosis
- conflict resolution
- high-risk independent verification

Routing is role to harness class to model/provider pool; harnesses and model/provider
pools are preferences, never permanent bindings. Pi is a harness with a runtime-selected
model, never a fixed model. The Root selects the Execution Lead harness per task. The
default is the Pi Standard/Fast Lead for well-scoped, lower-complexity, LOW/MEDIUM work;
the Codex Premium Lead is the escalation for difficult engineering reasoning, complex
repository investigation, difficult debugging, HIGH-risk or cross-module implementation,
and when cheaper execution proves insufficient.

The default model/provider-pool preferences are:

- a high-capability pool (for example Claude) for Root / Cognitive Control Plane work
- a low-cost pool (for example DeepSeek) for well-scoped Execution Worker implementation,
  search, test generation and mechanical refactoring (the Worker role is not bound to any
  one pool)
- a low-cost pool (for example volcengine-ark-coding-plan, falling back to DeepSeek) for
  the Pi Standard/Fast Execution Lead
- a capable pool, then another capable pool (for example Claude, then Codex), for
  fresh-session independent review
- a pool different from the implementer's pool for HIGH-risk review

Availability, capability, budget and task evidence may justify another harness or pool.

Reasoning/thinking effort is not a token-savings lever: low-cost pools keep high or
provider-recommended effort, and savings come from routing and context discipline only.

Efficiency and terse reporting are native principles defined in
`.agent/policies/efficiency.yaml`; never narrate routine tool usage. Efficiency targets
never weaken acceptance criteria, HIGH-risk safeguards, independence or human gates — see
`.agent/policies/risk.yaml`.

Normal execution volume should substantially exceed Root reasoning volume, and low-cost
execution volume should exceed premium execution volume. The following workflow
rules are intended to produce that role-first asymmetry, which the execution-cost metrics
`execution_vs_root_usage_share` and `premium_vs_low_cost_execution_share` verify once
usage is collected:

- Root reconnaissance is bounded to what is needed to specify the work correctly; reading
  the whole codebase to prepare a packet is an anti-pattern.
- The Root does not run the implementation edit/verify/fix loop; the Execution Lead owns
  that loop.
- The default is one Execution Packet per task. Iterative fixes remain inside the
  Execution Lead's dispatch.
- The Execution Lead reports compressed evidence—files changed, commands, results,
  findings and uncertainty—rather than transcripts or reasoning dumps.
- The Root supervises with long `check --wait` windows. Frequent status polling, terminal
  reading or step-by-step direction is the **Root micromanagement** anti-pattern.
- Escalations are bounded exchanges: one specific question and one specific decision, not
  a transfer of the implementation loop to the Root.

## Runtime and Controller Boundaries

Use Orca as the default interface for:

- creating and tracking task worktrees
- launching agent terminals locally or on configured remote environments
- structured agent messaging, dispatch and completion tracking
- worktree and terminal status

Use the version-matched Orca guides exposed by the installed CLI before automating Orca
commands. Select one executable for the session in this order: `ORCA_CLI_COMMAND` when
exported; `orca-dev` in a development checkout exposing `ORCA_DEV_REPO_ROOT`; `orca-ide`
on Linux outside an Orca-managed terminal; otherwise `orca` inside an Orca-managed
terminal. Reuse that executable for every later Orca command.

Do not duplicate Orca's deterministic worktree, terminal, messaging or dispatch lifecycle
inside the Python Controller. The Controller should focus on GitHub task polling and state
synchronization, risk and budget policy, node scheduling, deterministic tests and evals,
metrics, human gates, and backup/recovery.

Herdr is not the default execution or communication plane. Use it only when a future
workload has an explicit requirement for detached or persistent long-running terminal
sessions that Orca is not intended to own.

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

Review independence means fresh-session context independence. The reviewer runs in its
own worktree or terminal with no Root session context or history. It receives the original
task, acceptance criteria, relevant diff or commit, verification evidence, required docs
and risk level, but not the Root's private reasoning or transcript, Execution Packet
rationale, implementer reasoning, or the Root's defense of its design.

A Root session must never review its own work, and any session carrying the Root's context
is not independent. For HIGH-risk work, the reviewer's provider MUST differ from the
implementer's provider when a capable alternative is available. If none is available, a
human-visible task record MUST contain an explicit waiver accepting the residual
same-provider correlation risk before completion.

## Git Rules

Use one active task per branch/worktree.

Do not modify another agent's active worktree.

Every writable Root-to-Execution-Lead packet and Execution Lead-to-Worker dispatch must
declare an immutable `integration_base_sha`. The Root aligns the Lead worktree when it is
created; the Lead similarly aligns a fresh Worker worktree from an explicit base ref before
dispatch. An existing worktree may be reused only when it is clean and already at the
declared base, or when the guarded runbook procedure proves there are no commits ahead and
creates a fresh Worker branch without repointing an existing result branch.

Every supervised writable Root-to-Execution-Lead dispatch MUST be launched through
`orca orchestration worker-start`; low-level `worktree create` plus
`orchestration dispatch --inject` does not register the Lead in Orca's `worker-*` lifecycle
registry, so the Root cannot settle it with `worker-release`.

Every supervised writable Worker MUST be launched through
`orca orchestration worker-start`. The launch MUST explicitly select the required Git base
using the installed version's supported mechanism, currently
`--base-branch <integration_base_ref>`; confirm that mechanism against the version-matched
installed Orca guide before dispatch. For supervised writable Workers, the Execution Lead
MUST NOT use `worktree create` plus `orchestration dispatch --inject` as the launch path;
that low-level path may create a dispatch visible to `dispatch-show` without registering
the Worker in Orca's `worker-*` lifecycle registry, so `worker-release` cannot settle it.

When `worker-start` targets `current`, an existing worktree, or `--terminal <handle>`, the
installed CLI rejects `--base-branch`; explicit base selection is satisfied only by the
guarded pre-dispatch HEAD equality proof recorded in the assignment. `--retry-of
<dispatch_id>` does not inherit placement: repeat the intended `--on`/`--worktree` and
`--agent`/`--terminal` choices, and either repeat
`--base-branch <integration_base_ref>` for a new worktree or rerun and record the guarded
equality proof for reuse.

The mandatory writable-Worker lifecycle is:

```text
Lead creates Worker through `worker-start` with explicit base
  → Worker verifies `HEAD == integration_base_sha` before tracked edits
  → Worker implements / verifies / commits
  → immutable result packet
  → `worker_done`
  → Lead validates result
  → Lead cherry-picks ordered commits
  → Lead verifies integrated state
  → `worker-release` succeeds
  → result delivery acknowledged
  → Worker branch/worktree retained or removed per settlement policy
```

Settlement MUST include successful `worker-release` before result-delivery acknowledgment
and before the Worker branch/worktree is retained or removed according to settlement
policy.
Orca replays an unacknowledged Delivery, so the writable Worker terminal MUST be
successfully released before the batch is acknowledged.

Before any tracked-file modification, the Worker is verify-only: its working tree must be
clean, the base must exist locally and `git rev-parse HEAD` must exactly equal
`git rev-parse <integration_base_sha>^{commit}`. If the base cannot be obtained, or if
the base exists but HEAD is not exactly equal, stop and escalate to the Lead instead of
using a guessed base. The Worker must not use `git reset --hard`, `git checkout -B`
or any ref-repointing command to self-align. Preserve every existing commit and redispatch
from a safe worktree; inability to do so maps to closed re-entry condition 6. Orca
parent/child lineage is orchestration provenance, not proof of Git ancestry.

V1 accepts only an immutable ordered linear Git commit list from a Worker. The Worker and
Lead both require no merge commit in `integration_base_sha..worker_head_sha`. No
uncommitted working-tree result is accepted.

The V1 integration operation is `git cherry-pick -x` of each ordered commit into the
Execution Lead branch. Before release, anchor `worker_head_sha` under
`refs/worker-results/<worker_task_id>`; after each successful pick, record the
`worker_commit_sha → integrated_commit_sha` mapping. Do not merge the Worker branch,
reset the Lead branch to Worker HEAD, fast-forward the Lead branch, or infer integration
from Orca lineage.

The Execution Lead owns integration conflicts. The Worker must never modify the Lead
worktree; the Lead may resolve a cherry-pick conflict only within the Execution Packet,
otherwise it must run `git cherry-pick --abort` and use condition 6 for a packet
amendment or redispatch. For a `now empty` pick, deterministically prove the content is
already present, record `worker_commit_sha → ALREADY_PRESENT@<lead_head_sha>` and its
reason, then run `git cherry-pick --skip`; never use `--allow-empty`. If proof is
impossible, abort and use condition 5. Rerun required verification after every resolution
or skip.

The Lead serializes parallel Worker integration, cherry-picks later results onto the new
Lead HEAD and runs integrated-state verification after each result. Verification failure
stays with the Lead unless it reaches closed condition 3, 5 or 6; evidence that a documented
acceptance assumption is false maps to condition 2 or 6.

The Worker worktree/branch must not be deleted until integration succeeds or the Execution
Lead explicitly rejects the result. Agent/terminal release precedes result-delivery
acknowledgment and follows Lead-side anchoring of the immutable commit result, but its Git
objects, branch and anchor must remain recoverable until settlement. Delete temporary
local/remote result refs only after durable SHA mappings and verification evidence are
recorded.

If an Execution Lead fails mid-flight, the Root owns parent-Dispatch lifecycle recovery
and replacement, but it does not enter the failed Lead's edit/verify loop. Preserve the
worktree and uncommitted changes; after Orca proves the prior terminal inactive and
ownership is explicitly reassigned, a replacement Execution Lead owns that worktree or a
conflict-free recovery worktree and resumes the loop.

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

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

The Root / Cognitive Control Plane runs in a capable harness/pool (for example Pi with a
high-capability pool, or Claude Code). It performs bounded
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

Field semantics are mandatory:

- `WORKTREE / BASE COMMIT` is Orca placement plus the source ref used to create it.
- `LEAD BRANCH` is the target branch.
- `INTEGRATION_BASE_SHA` is the immutable commit the Lead worktree must exactly equal
  before any tracked-file modification.
- `ALLOWED CHANGED PATHS / SCOPE` is the path boundary.
- `REQUIRED TESTS / EVALS` names commands/suites;
  `VERIFICATION REQUIREMENTS` adds base, ancestry, scope and integrated-state gates; and
  `VERIFICATION EVIDENCE REQUIRED` names outputs, mappings and uncertainty to retain.
- `RESULT MODE` is the immutable unit returned to the Root; V1 writable Git work uses an
  ordered linear Git commit list.

The Lead must run this gate before its first tracked-file edit:

```text
test -z "$(git status --porcelain)"
git cat-file -e <integration_base_sha>^{commit}
test "$(git rev-parse HEAD)" = "$(git rev-parse <integration_base_sha>^{commit})"
```

A missing base or mismatch stops the Lead under condition 6; the Root amends placement/base
or redispatches without taking over the edit/verify/fix loop.

The packet's `ESCALATION CONTRACT` may narrow the standing six-condition list but may not
extend or redefine it.

The Controller may poll, claim, classify policy and choose an eligible node. GitHub remains
authoritative for task state. Reading the entire codebase to prepare the packet is an
anti-pattern; repository investigation belongs to the Execution Lead.

## 3. Create or Select the Root Workspace

The Root runs in a capable harness/pool and selects the Execution Lead harness class per
task (Pi Standard/Fast is the default for LOW/MEDIUM); for difficult engineering the Root
may escalate to the Codex Premium Lead. Use an Orca-managed workspace for the Root and an
Orca-managed worktree for each writable task. Choose worktree lineage separately from the
Git base:

- use a child worktree for work stacked on or dependent on the active task
- use a top-level worktree for an independent task
- never share one writable checkout across nodes

Use Orca's agent-first worktree creation when a new Root is needed and follow the current
guide's setup policy. Do not replace it with raw `git worktree` plus an ad hoc PTY.

## 4. Dispatch the Execution Lead

The Root dispatches an Execution Lead through Orca Orchestration. The default is the **Pi
Standard/Fast Lead** (pi harness + low-cost pool); for difficult engineering reasoning,
complex repository investigation, difficult debugging, HIGH-risk or cross-module
implementation the Root selects the **Codex Premium Lead**. The chosen EXECUTION HARNESS
is recorded in the Execution Packet. Harness choice never bypasses
`orca orchestration worker-start`.

Every supervised writable Root-to-Execution-Lead dispatch MUST be launched through
`orca orchestration worker-start`; low-level `worktree create` plus
`orchestration dispatch --inject` does not register the Lead in Orca's `worker-*` lifecycle
registry, so the Root cannot settle it with `worker-release`.

```text
Root terminal:
ORCA orchestration run-create --objective "<task outcome>" --json
ORCA orchestration task-create --spec "<Execution Packet>" --json
ORCA orchestration worker-start --task <parent_task_id> \
  --worktree new-child --name <lead_name> \
  --base-branch <integration_base_ref> --agent <agent_id> --setup run --json
ORCA orchestration check --wait ... --json
process every message in the Delivery
ORCA orchestration worker-release --dispatch <lead_dispatch_id> --json
# or, for immediate reuse:
ORCA orchestration worker-start --task <followup_task_id> --terminal <handle> --json
ORCA orchestration check --ack <delivery_id> --wait --json
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
Prefer a low-cost pool (e.g. DeepSeek) for well-scoped implementation, search, test
generation and mechanical refactoring when a configured launcher is available; the Worker
role is not bound to any one pool. An Execution Worker has no delegation
authority and routes routine questions to the Lead, not the Root. Agent IDs are
installation-specific; inspect the runtime rather than guessing an ID.

Run coordinator binding is per-terminal. A dispatched Lead cannot create a Task in the
Root-owned Run and must never call `run-use` on that Run. For sub-dispatches, run the
installed and verified grammar from the Execution Lead terminal:

```text
ORCA orchestration run-create --objective \
  "Execution sub-run for parent Task <task_id>, Dispatch <dispatch_id>" --json
ORCA orchestration task-create --run <lead_run_id> --spec "<bounded worker task>" --json
ORCA orchestration worker-start --task <worker_task_id> \
  --worktree new-child --name <worker_name> \
  --base-branch <integration_base_ref> --agent <agent_id> --setup run --json
ORCA orchestration check --wait --types worker_done,escalation,question ... --json
ORCA orchestration worker-release --dispatch <worker_dispatch_id> --json
ORCA orchestration check --ack <delivery_id> ... --json
```

The Lead owns that separate Lead-owned Run and its inbox. Put the parent Task ID and
parent Dispatch ID in the objective and final evidence; settle/release every Worker before
parent `worker_done`. Worker questions terminate at the Lead, and the Root receives only
compressed Worker evidence.

### 4.1 Writable Worker Git Integration Contract v1

Use this procedure for every writable Execution Lead → Worker dispatch. Orca
parent/child lineage is orchestration provenance, not proof of Git ancestry; never rely on
the repository default base for a nested writable Worker.

Every supervised writable Worker MUST be launched through
`orca orchestration worker-start`. The launch MUST explicitly select the required Git base
using the installed version's supported mechanism, currently
`--base-branch <integration_base_ref>`; confirm that mechanism against the version-matched
installed Orca guide before dispatch. For supervised writable Workers, the Execution Lead
MUST NOT use `worktree create` plus `orchestration dispatch --inject` as the launch path;
that low-level path may create a dispatch visible to `dispatch-show` without registering
the Worker in Orca's `worker-*` lifecycle registry, so `worker-release` cannot settle it.

The Lead first confirms a clean Lead worktree, records `git rev-parse HEAD` as immutable
`integration_base_sha`, and puts this complete assignment in the Worker Task:

```text
GOAL
CONTEXT
LEAD BRANCH
INTEGRATION_BASE_SHA
ALLOWED CHANGED PATHS / SCOPE
CONSTRAINTS
VERIFICATION REQUIREMENTS
RESULT MODE: ORDERED LINEAR GIT COMMIT LIST
EXPECTED OUTPUT
ACCEPTANCE
```

Make the exact base explicit when creating a local Worker worktree. After confirming the
installed guide supports the current `--base-branch` mechanism, use the composed supervised
launch path:

```text
test -z "$(git status --porcelain)"
git rev-parse HEAD
git branch worker-base/<worker_task_id> <integration_base_sha>
ORCA orchestration worker-start --task <worker_task_id> \
  --worktree new-child --name <worker_name> \
  --base-branch <integration_base_ref> --agent <agent_id> --setup run --json
```

Set `<integration_base_ref>` to the verified `worker-base/<worker_task_id>` ref (or another
explicit ref resolving to `integration_base_sha`). Read the `worker-start` receipt and use
its exact worktree, terminal and Dispatch identifiers. Omission of the base is not allowed.

When `worker-start` targets `current`, an existing worktree, or `--terminal <handle>`, the
installed CLI rejects `--base-branch`; explicit base selection is satisfied only by the
guarded pre-dispatch HEAD equality proof recorded in the assignment. `--retry-of
<dispatch_id>` does not inherit placement: repeat the intended `--on`/`--worktree` and
`--agent`/`--terminal` choices, and either repeat
`--base-branch <integration_base_ref>` for a new worktree or rerun and record the guarded
equality proof for reuse.

Alignment is owned by the Lead, not the Worker. The recipe above is the fresh-worktree
path. To consider an existing worktree, the Lead runs the following **before dispatch**:

```text
test -z "$(git status --porcelain)"
git cat-file -e <integration_base_sha>^{commit}
git rev-parse HEAD
git rev-parse <integration_base_sha>^{commit}
test -z "$(git rev-list <integration_base_sha>..HEAD)"
test -z "$(git for-each-ref --format='%(refname)' refs/heads/<fresh_worker_branch>)"
git checkout -b <fresh_worker_branch> <integration_base_sha>
test "$(git rev-parse HEAD)" = "$(git rev-parse <integration_base_sha>^{commit})"
```

If HEAD already equals the base, reuse needs no checkout. If it differs, the first
`rev-list` test must prove the current HEAD has no commits outside the declared base, and
the second test must prove the new branch name is unused. If either fails, stop, preserve
all refs/commits and redispatch from a fresh explicitly based worktree; if resources or
authority prevent that, use condition 6. Never use `git reset --hard` or
`git checkout -B` to repoint an existing result branch.

Before any tracked-file modification, the Worker runs:

```text
test -z "$(git status --porcelain)"
git cat-file -e <integration_base_sha>^{commit}
git rev-parse HEAD
git rev-parse <integration_base_sha>^{commit}
test "$(git rev-parse HEAD)" = "$(git rev-parse <integration_base_sha>^{commit})"
```

The final equality is mandatory and the Worker is verify-only. If `cat-file` fails, stop
and report “base not obtainable” to the Lead; inability to obtain it maps to condition 6.
If the base exists but equality fails, stop and report “HEAD not aligned”; do not
self-align. The Lead either uses the guarded path above or redispatches a fresh worktree.
If it cannot safely align without discarding commits, that separate blocker maps to
condition 6. No tracked-file edit may occur on a guessed or mismatched base.

After implementation and required verification, the Worker creates commits and captures
the immutable result:

```text
git status --short
git diff --check
<required verification commands>
git add <allowed paths>
git commit -m "<message>"
test -z "$(git rev-list --merges <integration_base_sha>..HEAD)"
git rev-parse HEAD
git rev-list --reverse <integration_base_sha>..HEAD
git diff --name-only <integration_base_sha>..HEAD
```

The Worker sends `worker_done` with a result packet containing
`integration_base_sha`, `worker_head_sha`, the ordered linear commit SHA list, changed paths,
verification commands/results and unresolved uncertainty. No uncommitted working-tree
result is accepted.

Before integration, the Lead obtains the exact Worker objects without changing the Lead
branch, then runs:

```text
test -z "$(git status --porcelain)"
git cat-file -e <integration_base_sha>^{commit}
git cat-file -e <worker_head_sha>^{commit}
git rev-parse <integration_base_sha>^{commit}
git rev-parse <expected_integration_base_sha>^{commit}
git merge-base --is-ancestor <integration_base_sha> <worker_head_sha>
git rev-list --reverse <integration_base_sha>..<worker_head_sha>
test -z "$(git rev-list --merges <integration_base_sha>..<worker_head_sha>)"
git diff --name-only <integration_base_sha>..<worker_head_sha>
git diff --check <integration_base_sha>..<worker_head_sha>
git diff <integration_base_sha>..<worker_head_sha>
```

The two base resolutions must be equal; the `rev-list --reverse` output must exactly
match the returned ordered list, and the `rev-list --merges` assertion must succeed.
The Lead checks every changed path against the authorized scope and rejects unexpected
files. After retaining this evidence, anchor the immutable result before any terminal
release:

```text
git update-ref refs/worker-results/<worker_task_id> <worker_head_sha>
```

V1 has exactly one integration operation, run one Worker commit at a time:

```text
git cherry-pick -x <worker_commit_sha_1>
git rev-parse HEAD
# record <worker_commit_sha_1> -> <integrated_commit_sha_1>
git cherry-pick -x <worker_commit_sha_2>
git rev-parse HEAD
# record <worker_commit_sha_2> -> <integrated_commit_sha_2>
<required verification commands>
```

The `-x` trailer preserves source provenance in each integrated commit; the explicit
worker-to-integrated SHA pairs are required integration evidence.

Do not merge the Worker branch, reset the Lead branch to Worker HEAD, fast-forward the
Lead branch, take over the Worker branch, or infer integration from Orca lineage. The
Execution Lead owns integration conflicts. The Worker never modifies the Lead worktree.
For a conflict that is clearly within the Execution Packet, the Lead records and resolves:

```text
git status --short
git add <resolved allowed paths>
git cherry-pick --continue
<required verification commands>
```

Otherwise run `git cherry-pick --abort` and use condition 6 for a packet amendment or
redispatch. If Git instead reports that the current pick is `now empty`, do not treat
it as a conflict and never use `--allow-empty`. Prove the content is already present:

```text
git show --stat --patch <worker_commit_sha>
git diff --cached --quiet
<targeted verification proving the Worker change is present>
# record <worker_commit_sha> -> ALREADY_PRESENT@<lead_head_sha> plus reason
git cherry-pick --skip
<required verification commands>
```

If deterministic verification cannot prove the content is present, run
`git cherry-pick --abort` and use condition 5. Required verification is rerun and
recorded after every conflict resolution or empty-pick skip.

Worker and Lead lifecycle ordering is:

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

Worker worktree/branch must not be deleted until integration succeeds or the Execution
Lead explicitly rejects the result. After the immutable result arrives, the Lead first
creates the `refs/worker-results/<worker_task_id>` anchor. After validation, integration,
integrated-state verification and before Delivery acknowledgment, `worker-release` must
succeed. Worker branch, Git objects and anchor stay recoverable until settlement. A valid
`worker_done` is not itself Git acceptance.

After success or explicit rejection, and only after SHA mappings plus verification evidence
are durable, clean applicable temporary refs:

```text
git update-ref -d refs/worker-results/<worker_task_id>
git update-ref -d refs/heads/worker-base/<worker_task_id>
git push <remote> --delete worker-base/<worker_task_id> worker-result/<worker_task_id>
```

For parallel Workers, validate each result independently and serialize integration. Apply
each later ordered commit list onto the new Lead HEAD and run integrated-state verification
after every result. A textual clean apply followed by verification failure remains in the
Lead fix loop unless diagnosis, deterministic uncertainty or scope requires condition 3,
5 or 6. `Semantic interaction` means verification passed but evidence shows a documented
acceptance assumption is false; use condition 2 for ambiguity or condition 6 for packet
amendment/redispatch.

These Git stop points do not add escalation conditions. Base/ref unavailable, unsafe
alignment, conflict outside the packet and remote authorization/resource blockers map to
condition 6; an unprovable empty pick maps to condition 5; parallel findings map only to
condition 2, 3, 5 or 6 as defined above. A safe routine redispatch stays with the Lead.
The Root amends authority/scope or routes a human gate and never takes over the Git
integration loop.

The Execution Lead re-engages the Root only when:

1. architecture materially changes
2. acceptance criteria are ambiguous
3. difficult diagnosis remains unresolved
4. HIGH-risk independent review is required
5. deterministic verification cannot resolve uncertainty
6. execution is blocked by something outside the Execution Lead's authority—a protected
   human gate, a missing authorization or credential, an exhausted budget or concurrency
   limit, an unavailable required dependency, or acceptance criteria that are infeasible
   or mutually contradictory

This is a closed list. Each escalation is one specific question followed by one specific
decision; routine implementation choices, failing tests, refactors, tooling problems and
local design remain with the Lead.

Condition 6 is an authority escalation, not a cognitive re-entry. The Root routes it to
the human gate or amends the packet without taking over implementation. If unresolved, the
Lead sends `worker_done --outcome failed` with the blocker and the Root moves the GitHub
task to Blocked / Needs-Human.

Independent review uses a fresh session in its own worktree or terminal with no Root
context or history. Give the Reviewer the original task, acceptance criteria, relevant
diff or commit, verification evidence, necessary docs and risk level, but not the Root's
private reasoning/transcript, Execution Packet rationale or Root-authored defense. A Root
session never reviews its own work. For HIGH-risk work, choose a provider different from
the implementer when a capable alternative exists; otherwise require a human-visible
waiver accepting residual same-provider correlation risk.

A valid supervised Execution Lead, Worker or Reviewer settles its dispatch with exactly
one `worker_done`. After accepting completion, its coordinator either reuses the exact
agent for an immediate follow-up or releases it through Orchestration.

If a Lead fails mid-flight, the Root owns parent-Dispatch lifecycle recovery and
replacement. Preserve the worktree and uncommitted changes; do not let the Root edit them.
After Orca proves the prior terminal inactive and ownership is reassigned, a replacement
Execution Lead reuses the preserved worktree or resumes from the last commit/preserved
artifact in a conflict-free worktree and owns the edit/verify loop.

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

When the Worker does not share the Lead's Git object database, make the immutable base
reachable through an explicit fetchable Git ref before dispatch, then exchange only refs:

```text
# Lead-side publication
git push <remote> <integration_base_sha>:refs/heads/worker-base/<worker_task_id>

# Composed supervised launch after publication
ORCA orchestration worker-start --task <worker_task_id> \
  --on <saved-environment> --worktree new-top-level \
  --repo <exact_remote_repo_selector> --name <worker_name> \
  --base-branch <integration_base_ref> --agent <agent_id> --setup run --json

# Remote Worker-side guarded alignment before any tracked-file edit
test -z "$(git status --porcelain)"
git fetch <remote> refs/heads/worker-base/<worker_task_id>
git cat-file -e <integration_base_sha>^{commit}
test -z "$(git rev-list <integration_base_sha>..HEAD)"
test -z "$(git for-each-ref --format='%(refname)' refs/heads/<fresh_remote_worker_branch>)"
git checkout -b <fresh_remote_worker_branch> <integration_base_sha>
test "$(git rev-parse HEAD)" = "$(git rev-parse <integration_base_sha>^{commit})"

# Worker-side result publication after commit
test -z "$(git rev-list --merges <integration_base_sha>..<worker_head_sha>)"
git push <remote> <worker_head_sha>:refs/heads/worker-result/<worker_task_id>

# Lead-side exact result acquisition and anchor
git fetch <remote> refs/heads/worker-result/<worker_task_id>
git cat-file -e <worker_head_sha>^{commit}
git update-ref refs/worker-results/<worker_task_id> <worker_head_sha>
```

Both pre-checks before `checkout -b` must succeed. If HEAD contains commits outside the
base or the fresh branch name exists, stop, preserve all refs and redispatch; inability to
do that maps to condition 6. Never use `reset --hard` or `checkout -B`. The Lead
then performs the same ancestry, linear-order, scope, diff and verification checks from
§4.1, records SHA mappings and `cherry-pick -x` exact verified commits. After settlement,
clean the temporary remote refs as §4.1 specifies. Never exchange writable project
directories between nodes.

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

1. handles cognitive conditions 1-5 and routes condition 6 to a human gate or packet
   amendment
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

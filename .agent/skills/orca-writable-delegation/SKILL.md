---
name: orca-writable-delegation
description: >-
  Canonical, load-on-demand procedure for supervised writable Root-to-Execution-Lead and
  Execution-Lead-to-Worker delegation under Orca Orchestration: immutable integration base,
  exact pre-edit HEAD verification, worker-start launch, immutable ordered linear commit-list
  results, git cherry-pick -x integration, worker-release before delivery acknowledgment, and
  Git-invariant-safe settlement. Load this Skill before performing any supervised writable
  delegation. AGENTS.md invokes it; the ORCA_WORKFLOW runbook is the operational reference.
---

# Orca Writable Delegation

This Skill is the **canonical, load-on-demand** source for supervised writable delegation.
Always-loaded files (AGENTS.md) hold only the cross-cutting invariants and this pointer;
role files (root / execution-lead / worker) reference this Skill instead of restating the
mechanics. The `docs/runbooks/ORCA_WORKFLOW.md` runbook is the operational command reference
and delegates to this Skill for the normative contract.

It distinguishes **stable project invariants** from **version-specific Orca CLI mechanics**.
The invariants survive an Orca upgrade; the mechanics are compatibility notes for a specific
installed version and must be re-confirmed against that version's guide.

## Consult the installed Orca guide first

Orca CLI grammar changes between releases. Before any runtime action, consult the
**version-matched installed** Orca guide exposed by the CLI you selected:

```text
<ORCA> skills get orca-cli
<ORCA> skills get orchestration
```

Do not guess subcommands or flags from memory, and do not treat the compatibility notes
below as permanent Orca API semantics. The invariance that each note serves (explicit base
selection, proven pre-dispatch HEAD equality) is stated independently of the flag mechanics.

## Stable project invariants (independent of Orca version)

- Writable delegation happens through a supervised dispatch whose launch is owned by Orca's
  `worker-*` lifecycle registry: `orca orchestration worker-start`. Every supervised
  writable Root-to-Execution-Lead dispatch MUST be launched through
  `orca orchestration worker-start`; low-level `worktree create` plus
  `orchestration dispatch --inject` does not register the Lead in Orca's `worker-*` lifecycle
  registry, so the Root cannot settle it with `worker-release`.
- Every writable Root-to-Execution-Lead packet and Execution Lead-to-Worker dispatch declares
  an immutable `integration_base_sha`; the Root aligns the Lead worktree, and the Lead aligns
  a fresh Worker worktree from an explicit base ref before dispatch.
- The Worker is verify-only before any tracked-file modification: its working tree must be
  clean, the base must exist locally and `git rev-parse HEAD` must exactly equal
  `git rev-parse <integration_base_sha>^{commit}`. On a missing base or a HEAD mismatch the
  Worker stops and escalates to the Lead; it never proceeds on a guessed base and never
  self-aligns.
- Orca parent/child lineage is orchestration provenance, not proof of Git ancestry.
- A Worker returns an immutable **ordered linear** Git commit list; no uncommitted working-tree
  result is accepted, and no merge commit may appear in
  `integration_base_sha..worker_head_sha`.
- The Lead validates ancestry, exact commit order, and every changed path against authorized
  scope before integration.
- Integration is `git cherry-pick -x` of each ordered commit; the Lead anchors `worker_head_sha`
  under `refs/worker-results/<worker_task_id>` before terminal release and records each
  `worker_commit_sha → integrated_commit_sha` mapping.
- Worker branch/worktree Git objects and the anchor stay recoverable until integration
  succeeds or the Execution Lead explicitly rejects the result; temporary refs are cleaned only
  after durable SHA mappings and verification evidence exist.
- An existing worktree may be reused only when it is clean and already at the declared
  base, or when the guarded runbook procedure proves there are no commits ahead of the
  declared base and creates a fresh Worker branch without repointing an existing result
  branch. The concrete command sequence is the Lead-owned alignment recipe in
  `docs/runbooks/ORCA_WORKFLOW.md`, which this Skill references rather than duplicates.
- Do not share one writable Git working directory between Linux nodes; cross-node
  synchronization uses branches, commits, pushes, fetches, pull requests or explicit artifacts.

## Version-specific Orca mechanics (compatibility notes)

These are observations of a specific installed version, **not** permanent Orca API semantics.
Re-verify each mechanism against the installed version-matched guide before relying on it.

- **Orca 1.4.184:** explicit base selection currently uses the `--base-branch
  <integration_base_ref>` mechanism. The launch MUST explicitly select the required Git base
  using the installed version's supported mechanism, currently
  `--base-branch <integration_base_ref>`; confirm that mechanism against the version-matched
  installed Orca guide before dispatch.
- **Orca 1.4.184:** When `worker-start` targets `current`, an existing worktree, or
  `--terminal <handle>`, the installed CLI rejects `--base-branch`; explicit base selection is
  satisfied only by the guarded pre-dispatch HEAD equality proof recorded in the assignment.
- **Orca 1.4.184:** `--retry-of <dispatch_id>` does not inherit placement: repeat the intended
  `--on`/`--worktree` and `--agent`/`--terminal` choices, and either repeat
  `--base-branch <integration_base_ref>` for a new worktree or rerun and record the guarded
  equality proof for reuse.

The invariant served by both base notes is unconditional: **explicit base selection, proven by
a guarded pre-dispatch `HEAD == integration_base_sha` proof, is required before every writable
dispatch.** If a future Orca version changes the flag, the proof requirement remains.

## Mandatory writable-Worker lifecycle

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

## Launch requirements

**Version-specific label:** the `--base-branch <integration_base_ref>` flag named below is a
current installed-version compatibility detail (Orca 1.4.184), not a stable invariant; it
serves the stable explicit-base invariant stated independently in the stable-invariants
section above. Re-confirm it against the version-matched installed Orca guide per the
"Version-specific Orca mechanics (compatibility notes)" section.

Every supervised writable Worker MUST be launched through
`orca orchestration worker-start`. The launch MUST explicitly select the required Git base
using the installed version's supported mechanism, currently
`--base-branch <integration_base_ref>`; confirm that mechanism against the version-matched
installed Orca guide before dispatch. For supervised writable Workers, the Execution Lead
MUST NOT use `worktree create` plus `orchestration dispatch --inject` as the launch path;
that low-level path may create a dispatch visible to `dispatch-show` without registering
the Worker in Orca's `worker-*` lifecycle registry, so `worker-release` cannot settle it.

The Root applies the same launch contract to the Execution Lead, and the Lead to each Worker.

## The immutable base contract

The Worker is verify-only before any tracked-file modification: its working tree must be
clean, the base must exist locally and `git rev-parse HEAD` must exactly equal
`git rev-parse <integration_base_sha>^{commit}`. If the base cannot be obtained, or if
the base exists but HEAD is not exactly equal, stop and escalate to the Lead instead of
using a guessed base. The Worker must not use `git reset --hard`, `git checkout -B`
or any ref-repointing command to self-align. Preserve every existing commit and redispatch
from a safe worktree; inability to do so maps to closed re-entry condition 6. Orca
parent/child lineage is orchestration provenance, not proof of Git ancestry.

## The result contract (V1)

V1 accepts only an immutable ordered linear Git commit list from a Worker. The Worker and
Lead both require no merge commit in `integration_base_sha..worker_head_sha`. No
uncommitted working-tree result is accepted.

## Integration via git cherry-pick -x

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

## Settlement and recovery

Settlement MUST include successful `worker-release` before result-delivery acknowledgment
and before the Worker branch/worktree is retained or removed according to settlement
policy.
Orca replays an unacknowledged Delivery, so the writable Worker terminal MUST be
successfully released before the batch is acknowledged.

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

## Deterministic verification requirements

Before any tracked-file edit, prove alignment:

```text
test -z "$(git status --porcelain)"
git cat-file -e <integration_base_sha>^{commit}
test "$(git rev-parse HEAD)" = "$(git rev-parse <integration_base_sha>^{commit})"
```

Before any tracked-file modification the Worker records the exact result and proves linearity
and in-scope changes:

```text
git status --short
git diff --check
git add <allowed paths>
git commit -m "<message>"
test -z "$(git rev-list --merges <integration_base_sha>..HEAD)"
git rev-parse HEAD
git rev-list --reverse <integration_base_sha>..HEAD
git diff --name-only <integration_base_sha>..HEAD
```

The Lead validates ancestry, exact order and scope before integration, anchors the immutable
result, and after settlement confirms durable mappings before cleaning temporary refs.

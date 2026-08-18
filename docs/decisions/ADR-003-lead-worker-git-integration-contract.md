# ADR-003: Lead-Worker Git Integration Contract v1

- Status: Accepted
- Date: 2026-08-18
- Scope: Writable Execution Lead-to-Worker Git base, result and integration semantics

## Context

A disposable writable Root → Execution Lead → Worker smoke test proved that Orca worktree
isolation and completion propagation worked, but exposed an undefined Git integration
boundary. `docs/ARCHITECTURE.md` described isolation, lineage and Reviewer visibility
without choosing merge, cherry-pick, rebase or patch semantics; it did not define an
accepted Worker result, ancestry validation, conflict ownership or branch-retention order.
The Execution Lead correctly stopped instead of inventing a policy.

The same test measured a silent base divergence. The Lead HEAD was `4680489`, but the
Worker commit `80f6b3ba` had parent `6483423`, the repository's `main` base. The
command:

```text
git merge-base --is-ancestor 4680489 80f6b3ba
```

returned false. Orca child-worktree lineage had recorded orchestration provenance but had
not established Git ancestry. Treating the Worker branch as the Lead result could therefore
discard Lead work, while a base-to-head review diff would misleadingly report roughly
2,300 spurious deleted lines.

## Decision

Adopt Lead ↔ Worker Git Integration Contract v1 for every writable Worker dispatch:

1. The dispatch carries an immutable `integration_base_sha` equal to the Execution Lead
   HEAD, plus the Lead branch, allowed changed paths/scope, verification requirements and
   result mode.
2. Before any tracked-file modification, the Worker requires a clean working tree, obtains
   the declared base locally, aligns Worker HEAD exactly to it and explicitly verifies
   `git rev-parse HEAD` equality. If the base cannot be obtained, the Worker stops and
   escalates instead of guessing.
3. V1 accepts only an immutable ordered Git commit list. The result packet contains
   `integration_base_sha`, `worker_head_sha`, ordered commit SHAs, changed paths,
   verification commands/results and unresolved uncertainty. No uncommitted working-tree
   result is accepted.
4. Before integration, the Lead requires a clean worktree; confirms the expected base;
   validates Worker ancestry and commit order; inspects the base-to-head diff; verifies
   every changed path against authorized scope; rejects unexpected files; and retains
   verification evidence.
5. The V1 integration operation is `git cherry-pick` of the exact ordered Worker commit
   list into the Lead branch. Merging the Worker branch, resetting the Lead branch to
   Worker HEAD, fast-forwarding it and inferring integration from Orca lineage are
   prohibited.
6. The Execution Lead owns integration conflicts. The Worker never modifies the Lead
   worktree. The Lead resolves only within the Execution Packet; otherwise it aborts the
   cherry-pick and escalates or redispatches. Required verification is rerun after any
   resolution.
7. Lifecycle order is Worker implement → verify → commit → immutable result →
   `worker_done`, then Lead receive → validate → integrate → verify integrated state →
   acknowledge. Agent/terminal release may follow receipt of the immutable result, but the
   Worker branch and Git objects remain recoverable until integration succeeds or the Lead
   explicitly rejects the result.
8. The Lead validates parallel results independently and serializes integration. Later
   Worker commits are cherry-picked onto the new Lead HEAD. Changed-path overlap or
   semantic interaction that invalidates acceptance assumptions triggers escalation or
   redispatch.
9. On another node, the base first becomes reachable through an explicit fetchable Git
   ref. The Worker pushes result commits to a task/worker branch or temporary ref, and the
   Lead fetches exact returned SHAs before applying the same validation and cherry-pick
   procedure. Writable project directories are never exchanged between nodes.
10. Orca parent/child lineage is orchestration provenance, not proof of Git ancestry.
    Every writable worktree requires an explicitly verified Git base, and nested writable
    Workers do not rely on the repository default base.

## Relationship to ADR-001 and ADR-002

This ADR adds a Git integration contract and does not supersede ADR-001 or ADR-002.
ADR-001's Orca-first runtime and thin-Controller boundary remain in force. ADR-002's
Cognitive/Engineering Control Plane authority, closed Root re-entry list, cost structure
and independent-review requirements remain in force.

## Consequences

Benefits:

- silent Orca-lineage/Git-ancestry divergence stops before tracked files are edited
- Worker output is immutable, inspectable and recoverable
- one integration operation gives conflict ownership and review diffs deterministic meaning
- local, parallel and remote Workers share the same validation boundary

Costs and residual risks:

- Lead and Worker must exchange more Git metadata and retain branches until settlement
- each integration adds ancestry, scope, diff and verification work
- parallel results can still conflict semantically and may require redispatch
- remote operation requires explicit ref publication and exact-object fetching
- real nested writable and remote-node smoke tests remain necessary validation

## Verification

Repository policy tests assert the writable `integration_base_sha` requirement,
cherry-pick-only V1 operation, prohibited merge/reset/fast-forward inference, Lead conflict
ownership, commit-only Worker result, branch retention, remote fetchable refs and the
Orca-lineage/Git-ancestry distinction.

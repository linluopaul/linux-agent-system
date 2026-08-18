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

A later end-to-end smoke test exposed a distinct lifecycle gap. A writable Worker launched
with low-level `worktree create --base-branch` plus `orchestration dispatch --inject`
reported a valid `worker_done`, but `worker-release` returned `dispatch_not_found` while
`dispatch-show` still reported the Dispatch completed. The low-level Dispatch was visible
without being registered in Orca's `worker-*` lifecycle registry. Separate launches proved
that `orca orchestration worker-start --base-branch <ref>` both pins the explicit Git base
and registers the Worker so `worker-release` can settle it.

## Decision

Every supervised writable Worker MUST be launched through
`orca orchestration worker-start`. The launch MUST explicitly select the required Git base
using the installed version's supported mechanism, currently
`--base-branch <integration_base_ref>`; confirm that mechanism against the version-matched
installed Orca guide before dispatch. For supervised writable Workers, the Execution Lead
MUST NOT use `worktree create` plus `orchestration dispatch --inject` as the launch path;
that low-level path may create a dispatch visible to `dispatch-show` without registering
the Worker in Orca's `worker-*` lifecycle registry, so `worker-release` cannot settle it.

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
  → result delivery acknowledged
  → `worker-release` succeeds
  → Worker branch/worktree retained or removed per settlement policy
```

Settlement MUST include successful `worker-release` after result-delivery acknowledgment
and before the Worker branch/worktree is retained or removed according to settlement
policy.

Adopt Lead ↔ Worker Git Integration Contract v1 for every writable Worker dispatch:

1. Root-to-Lead `integration_base_sha` is the immutable commit the Lead worktree must
   exactly match before editing; `WORKTREE / BASE COMMIT` describes placement/source ref,
   `LEAD BRANCH` the target, `ALLOWED CHANGED PATHS / SCOPE` the path boundary,
   `VERIFICATION REQUIREMENTS` the non-test gates and `RESULT MODE` the immutable
   returned unit. Each Worker dispatch then sets its base to the Execution Lead HEAD.
2. The Lead owns alignment before dispatch: fresh worktrees use an explicit base ref.
   Existing worktrees may be reused only after clean/ahead-commit guards prove no result
   commit can be discarded and a fresh branch name is used. The Worker is verify-only:
   before any tracked edit it explicitly verifies `git rev-parse HEAD` equals the base.
   A missing base or mismatch stops work; `reset --hard`, `checkout -B` and other
   self-alignment ref repointing are prohibited. Unsafe alignment preserves commits and
   triggers redispatch or condition 6.
3. V1 accepts only an immutable ordered linear Git commit list with no merge commits. The
   result packet contains `integration_base_sha`, `worker_head_sha`, ordered commit
   SHAs, changed paths, verification commands/results and unresolved uncertainty. No
   uncommitted working-tree result is accepted.
4. Before integration, the Lead requires a clean worktree; confirms the expected base; runs
   `git merge-base --is-ancestor`; validates exact `git rev-list --reverse` order and
   absence of merge commits; inspects the base-to-head diff; verifies every changed path
   against authorized scope; rejects unexpected files; and retains evidence.
5. The V1 integration operation is one-at-a-time `git cherry-pick -x`. Before release,
   the Lead anchors the Worker head at `refs/worker-results/<worker_task_id>` and records
   every `worker_commit_sha → integrated_commit_sha` mapping. Merging the Worker branch,
   resetting the Lead branch to Worker HEAD, fast-forwarding the Lead branch and inferring
   integration from Orca lineage are prohibited.
6. The Execution Lead owns integration conflicts. The Worker never modifies the Lead
   worktree. The Lead resolves only within the Execution Packet; otherwise it runs
   `git cherry-pick --abort` and uses condition 6. On `now empty`, the Lead proves
   content is present, records `ALREADY_PRESENT@<lead_head_sha>` plus reason and uses
   `git cherry-pick --skip`, never `--allow-empty`. Unprovable content maps to
   condition 5. Required verification follows every resolution or skip.
7. Lifecycle order is the mandatory 11-step sequence above. The Lead anchors the immutable
   result before release, acknowledges the result Delivery after integrated-state
   verification, and then requires `worker-release` to succeed. Worker branch, objects and
   anchor remain recoverable until success or explicit rejection. Temporary refs are
   cleaned only after mappings and verification evidence are durable.
8. The Lead validates parallel results independently and serializes integration onto the
   new Lead HEAD, running integrated-state verification after every result. Verification
   failures route only under conditions 3/5/6 when their definitions apply. Semantic
   interaction means verification passed but evidence disproves a documented acceptance
   assumption; it maps to condition 2 or 6.
9. On another node, the base first becomes reachable through an explicit fetchable Git ref.
   A clean/ahead-commit guard creates a fresh remote Worker branch and runs the same exact
   equality test without discarding refs. The Worker pushes result commits to a task ref;
   the Lead fetches and anchors exact SHAs before the same ancestry, linearity, scope, diff,
   mapping and `cherry-pick -x` procedure. Writable project directories are never
   exchanged between nodes.
10. Orca parent/child lineage is orchestration provenance, not proof of Git ancestry.
    Every writable worktree requires an explicitly verified Git base, and nested writable
    Workers do not rely on the repository default base.

These stop points do not extend ADR-002's closed list. Base/ref unavailable, unsafe
alignment, out-of-packet conflict and remote authority blockers map to condition 6;
unresolved empty-pick proof maps to condition 5; parallel findings map only to condition
2/3/5/6. Routine safe redispatch remains with the Lead, and Root never takes over Git
integration.

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

Repository policy tests assert exact base equality and safe alignment, normalized full
prohibition clauses, Lead-side ancestry/order/scope/linearity, `cherry-pick -x`
provenance, SHA mapping, empty-pick handling, closed-condition routes, commit-only Worker
results, anchored branch retention, remote guarded fetchable refs and the
Orca-lineage/Git-ancestry distinction. Four lifecycle tests assert the low-level launch
prohibition, mandatory `worker-start`, explicit base selection and successful
`worker-release` settlement across every load-bearing document. Removal and inversion
mutation probes prove each normative rule test fails independently.

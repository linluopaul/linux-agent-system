# Procedure: Writable Work

Load before delegating or performing work that writes to a repository.

## Base and provenance

Start from an **explicit, immutable base commit** and record it. The delivered result must be
an identifiable, verified commit or an equivalent immutable integration unit.

Before any edit or other Git mutation, the writable delegated unit verifies actual HEAD
and Git provenance against the declared immutable base. A requested base or runtime label
is not proof. Stop on missing or mismatched evidence; do not mutate to manufacture a match.

Orchestration lineage is **not** Git ancestry. Never infer that a result descends from a base
because the runtime says the child came from the parent; verify ancestry in Git.

## Isolation

Writable delegated work must not silently mutate the protected parent or main checkout. When
external writable work is involved, give it an isolated worktree.

Verify isolation from outside the writable checkout: the protected checkout stays clean and
its HEAD unchanged.

## Reusing an existing worktree

An existing writable delegated worktree may be reused **only when both hold**:

- it is clean; and
- its current base and provenance already match the declared immutable base required for
  this delegated work.

If either condition fails, **do not reset, repoint, retarget or otherwise move an existing
result branch merely to make it match the requested base.** Create or use a fresh isolated
worktree and a fresh result branch from the declared base instead; if that cannot be done
safely, escalate rather than forcing the reuse.

## Integration

The **Lead owns verified integration**. Integrate deliberately, verify ancestry, scope and
linearity against the declared base, and record the provenance of what was integrated.

Before integration, verify the target checkout is clean and suitable for the intended
operation. Stop if unrelated dirty state or an unfinished Git operation makes integration
unsafe; do not silently integrate over it.

After integration, the Lead verifies the integrated result against acceptance and checks
relevant interactions with the target state, including previously integrated results.
An integration command completing successfully is not verification of the result.

## Herdr runtime safety

- Every Herdr mutation must **explicitly target the intended session** (`--session <name>`).
- An inherited `HERDR_SOCKET_PATH` can override `HERDR_SESSION`, so `HERDR_SESSION` alone is
  not reliable for targeting a mutation. An unqualified command can act on the containing
  session.

## Cleanup

Whoever creates a direct child runtime resource owns its normal lifecycle and cleanup; the
parent verifies final state.

Before cleaning or deleting writable delegated resources, preserve recoverable, immutable
evidence outside the resources being removed:

- the result and its commit or equivalent integration unit;
- the declared base, verified provenance and relationship to the integrated result;
- verification outcomes, including integrated-state checks.

Root and Lead must be able to recover and audit this evidence after runtime cleanup.
Runtime output alone is insufficient if cleanup destroys it.

- A dirty worktree must be resolved before normal cleanup. Normal removal is expected to
  refuse a dirty worktree — that refusal is the safety property, not an obstacle.
- Normal cleanup must not silently discard uncommitted work. Forced removal is not routine
  authority.
- After cleanup, verify actual Git worktree state and Herdr resource state. A cleanup
  command's own response is not a complete manifest of what it destroyed.

## resources_clean

Report on completion:

```text
resources_clean: true | false
```

Derive it from observable post-conditions, never from the cleanup command's return value.

`resources_clean: false` prevents normal final acceptance until cleanup succeeds or
exceptional recovery is explicitly handled.

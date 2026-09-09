# Procedure: Writable Work

Load before delegating or performing work that writes to a repository.

## Base and provenance

Start from an **explicit, immutable base commit** and record it. The delivered result must be
an identifiable, verified commit or an equivalent immutable integration unit.

Orchestration lineage is **not** Git ancestry. Never infer that a result descends from a base
because the runtime says the child came from the parent; verify ancestry in Git.

## Isolation

Writable delegated work must not silently mutate the protected parent or main checkout. When
external writable work is involved, give it an isolated worktree.

Verify isolation from outside the writable checkout: the protected checkout stays clean and
its HEAD unchanged.

## Integration

The **Lead owns verified integration**. Integrate deliberately, verify ancestry, scope and
linearity against the declared base, and record the provenance of what was integrated.

## Herdr runtime safety

- Every Herdr mutation must **explicitly target the intended session** (`--session <name>`).
- An inherited `HERDR_SOCKET_PATH` can override `HERDR_SESSION`, so `HERDR_SESSION` alone is
  not reliable for targeting a mutation. An unqualified command can act on the containing
  session.

## Cleanup

Whoever creates a direct child runtime resource owns its normal lifecycle and cleanup; the
parent verifies final state.

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

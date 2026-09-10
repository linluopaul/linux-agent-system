# Procedure: Delegate

Load when deciding whether to delegate, and how to run one Delegate.

## When to delegate

Delegate when the **result must be retained but the execution process does not need to
remain in the parent context**.

Perform the work directly only when one of these holds:

1. the execution process materially affects later parent decisions;
2. continuous access to implicit parent context is required;
3. delegation overhead exceeds the size of the task;
4. the required authority cannot be delegated.

For deterministic batch work, prefer a script, tool or engine over an LLM Agent.

## Choosing the Delegate form

**Native first.** If the current harness provides a native subagent that is adequate for the
task and sufficiently traceable, use it — it avoids a separate runtime object and its
lifecycle cost.

Use an **external Herdr Delegate** when the task requires any of: cross-provider execution;
a specialized or domestic model unreachable from the parent harness; a data source the
parent harness cannot reach; an independent runtime; or stronger isolation or traceability.

Neither form is a permanent binding; choose per task.

## Delegate authority

A Delegate produces a result for its parent. It does not own the parent outcome and does not
redefine acceptance. Ambiguity goes back to the parent rather than being resolved by
invention.

## Return contract

The Delegate returns exactly:

```text
STATUS
RESULT
EVIDENCE
BLOCKERS
UNCERTAINTY
ARTIFACT
```

Writable work also returns `COMMIT`.

Raw and high-volume execution output stays in the artifact. The parent receives only
decision-relevant result, evidence, uncertainty and artifact pointers — never the execution
process itself.

## Runtime

If the Delegate is an external Herdr runtime, follow `writable-work.md` for runtime
targeting, lifecycle and cleanup.

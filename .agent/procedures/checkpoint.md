# Procedure: Context Checkpoint

Load when writing or resuming from a Root checkpoint.

A checkpoint is **session-independent continuation state**. It is not a durable knowledge
base: durable architectural and project knowledge belongs in Git/GitHub.

## Schema — exactly ten fields

```text
ROOT_ID
CHECKPOINT_GENERATION / TIMESTAMP
GOAL
ACCEPTANCE
CURRENT_STATE
DECISIONS_MADE
OPEN_QUESTIONS / BLOCKERS
ACTIVE_CHILD_ROOTS / LEADS
IMPORTANT_EVIDENCE_POINTERS
NEXT_ACTION
```

No eleventh field is added. Anything that seems to need one belongs in an existing field or
in Git/GitHub.

## ACCEPTANCE carries coverage

Each acceptance criterion records its current status and an evidence pointer or short
summary, so a resuming Root can tell which criteria are discharged and on what basis:

```text
ACCEPTANCE

A1 <criterion>
STATUS: PASS
EVIDENCE: <pointer or short summary>

A2 <criterion>
STATUS: OPEN
EVIDENCE: <what is still missing>
```

`ACTIVE_CHILD_ROOTS / LEADS` distinguishes what is actively executing from what is merely
retained; do not list finished work as active.

## Never store in a checkpoint

chain-of-thought · full transcript · routine tool history · raw Delegate execution process ·
full Reviewer transcript · material already promoted to Git/GitHub.

## Resume

A fresh carrier or session resumes with:

```text
same ROOT_ID
+ latest checkpoint
+ Git/GitHub durable state as needed
```

The runtime carrier may differ entirely — session, workspace, process, harness and model may
all change. `ROOT_ID` does not. Re-verify current Git state on resume rather than trusting
the checkpoint's snapshot of it.

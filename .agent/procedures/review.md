# Procedure: Independent Review

Load when independent review is required. Policy decides *whether* review is required and
the retry budget; this procedure covers *how* to run one.

## Reviewer setup

The Reviewer runs **fresh and context-isolated** — a new session with no inherited context
from the Root or the implementer, and no resumed prior thread.

Isolation in V4 is **contractual**: it is established by what is supplied, not by an
operating-system or filesystem sandbox. A stronger sandbox is added only if evidence later
shows it is necessary.

## Review material

Supply only what is needed to verify the work:

```text
GOAL
ACCEPTANCE
result / diff / commit
verification evidence
relevant constraints and material selected by Root/Policy
```

Do not supply Root private reasoning or advocacy for the implementation, implementer
chain-of-thought, unnecessary transcripts, or unrelated execution history.

## Reviewer output

The Reviewer writes its full verdict to an independently preserved artifact and returns:

```text
concise verdict
+ artifact pointer
+ integrity evidence / hash
```

## Verdict preservation

- The original verdict artifact is preserved independently of the implementer.
- The Lead may respond to findings but may not rewrite, suppress or redefine the verdict.
- The Root must be able to recover the original verdict without the Lead as sole transport —
  read the artifact directly and check its integrity evidence.
- Reading the Reviewer's terminal is debug evidence only, never the preservation mechanism.

## Loop ownership

The Lead owns the review/fix loop and runs it to a conclusion. The Root rules on the final
result, not on each cycle.

## Reviewer selection

Reviewer capability and independence requirements are resolved by policy per task. Do not
hard-code a permanent reviewer harness, provider or model here.

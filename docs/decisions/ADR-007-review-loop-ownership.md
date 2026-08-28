# ADR-007: Review/Fix Loop Ownership Moves to the Execution Lead

- Status: Accepted
- Date: 2026-08-27
- Scope: Who arranges independent review, who runs the review/fix loop, and the three
  safeguards that bound the resulting loss of reviewer independence

## Context

Under the v2.x contract, "HIGH-risk independent review is required" was one of the six
closed Root re-entry conditions. In practice that meant the Execution Lead stopped mid-task
and handed the review decision back to the Root, then received findings back through the
Root, then resumed. Each review cycle cost a Root round trip.

That topology has two costs. The Root becomes a relay for findings it did not produce and
cannot verify more cheaply than the Lead can. And the implementation edit/verify/fix loop —
which `ARCHITECTURE.md` §6.2 and §7 assign to the Execution Lead — is interrupted once per
review cycle, which is exactly the Root micromanagement pattern the cost-asymmetry rules
exist to prevent.

The alternative is to let the Lead arrange its own review. That is cheaper and keeps the
loop where it belongs, but it hands the implementer control over what the reviewer sees.
`ARCHITECTURE.md` §6.4 and §8.3 define reviewer independence as fresh-session context
independence plus a bounded review packet; letting the implementer assemble that packet is
a real weakening of the second half of that definition, not a neutral refactor.

## Decision

**The Execution Lead arranges the required review itself and owns the review/fix loop. The
Root rules on the final result, not on each cycle.**

`risk.yaml` remains the sole authority for **whether** independent review is required. This
ADR changes only **who runs the loop** once review has been required.

Closed re-entry condition 4 changes accordingly:

| | condition 4 |
|---|---|
| before | HIGH-risk independent review is required |
| after | the review loop reaches its cap (3 cycles) without passing |

The semantics move from "escalate because review is needed" to "escalate because review was
exhausted".

### The three safeguards

The weakening above is accepted only because all three of the following hold simultaneously:

1. **The reviewer's original findings are preserved in Orca.** What the Root receives must
   be traceable back to the reviewer's own output; a Lead summary alone is not sufficient
   evidence that review happened or that findings were resolved.
2. **The loop is capped at 3 cycles** (`.agent/policies/retry.yaml`, `review_loop.max_cycles`).
   On exhaustion the Lead must stop editing and re-engage the Root under condition 4. The cap
   never makes review required — that stays with `risk.yaml`; it only bounds a loop that has
   already been required.
3. **The review material contract is fixed by the Root in advance**, in the Execution
   Packet's `REVIEW MATERIAL CONTRACT` field (`ARCHITECTURE.md` §10). It names what the
   reviewer must receive (original goal/task, acceptance criteria, diff/commit, verification
   evidence, risk level, relevant docs) and what it must never receive (Root private
   reasoning, Execution Packet rationale, implementer reasoning or long-form implementation
   justification). The Lead executes that contract and may never redefine it.

### Why none of the three can substitute for another

Each safeguard closes a different failure mode:

| failure mode | blocked by |
|---|---|
| The Lead re-tunes the change until the reviewer stops objecting | safeguard 2 |
| The Lead submits a partial diff or omits files, so the first pass silently passes | safeguard 3 |
| The Lead softens the findings when reporting them upward | safeguard 1 |

The cycle cap is a ceiling and the material contract is a floor. A ceiling without a floor
bounds how long a badly-scoped review runs but not what it looks at; a floor without a
ceiling defines the material but allows unbounded re-tuning against it; and both without
safeguard 1 leave the Root reading the implementer's account of its own review.

## Consequences

### Positive

- The implementation edit/verify/fix loop stays whole and stays with the Execution Lead;
- Root round trips per task drop to one decision instead of one per review cycle;
- Review exhaustion becomes an explicit, bounded escalation rather than an open-ended loop.

### Negative / accepted cost

- **Reviewer independence is materially weaker than under v2.x**: the implementer assembles
  the reviewer's input, constrained by contract rather than by structure. The safeguards
  bound this; they do not eliminate it.
- One more mandatory conditional field on the Execution Packet.

### Residual risk

**Whether the Lead actually populated the review material contract in full is not guaranteed
by any of the three safeguards.** Safeguard 3 defines the obligation; nothing in the document
layer proves it was met. It is checkable — the settlement evidence carries the review
material and the reviewer's original findings — but the check is a review of the evidence,
not an automatic gate. Until that check is routine (or automated), an incomplete review
packet is the most likely way this decision fails in practice.

### GPT discussion inside the Root session is not review

Multi-model discussion inside the Root session — for example a GPT reached over MCP — does
**not** constitute independent review, at any risk level. It reads the Root's own problem
statement and works inside the Root's framing, so it fails fresh-session context
independence. "It looks fine to me" from such a discussion means only that it did not leave
that frame. Independent review is a fresh session in its own worktree/terminal, reading the
code and the contracted material.

This must be stated explicitly because in-session multi-model discussion presents itself as
an added layer of scrutiny, which is exactly how a review requirement gets quietly satisfied
by something that is not review.

## Compliance

`risk.yaml` continues to decide whether review is required. `retry.yaml` `review_loop`
bounds the loop and may never make review required. `ARCHITECTURE.md` §6.4 / §8.3 / §10 and
`AGENTS.md` carry the live contract; `docs/runbooks/ORCA_WORKFLOW.md` carries the
operational form. ADR-002's closed re-entry list is a point-in-time record of the pre-v3
wording and is not current policy for condition 4.

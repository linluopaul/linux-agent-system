# ADR-005: Instruction Diet and Adaptive Premium Reasoning

- Status: Accepted
- Date: 2026-08-18
- Scope: AGENTS.md diet, load-on-demand writable-delegation Skill, single-normative-source
  de-duplication, CORE/CONDITIONAL Execution Packet, adaptive premium model/reasoning, bounded
  review budget, harness-file role-default removal, and the anti-drift retargeting of the
  policy test suite.

## Context

v2.1's anti-drift strategy was "same text everywhere": the supervised writable lifecycle, the
closed six-condition list and the Execution Packet were duplicated verbatim across AGENTS.md
(450 lines / ~20.6 KB, always loaded), role files, the runbook and documents/policies, and the
policy test suite enforced that duplication with per-file occurrence counts. This kept texts
in sync but bloated always-loaded context, made single-source-of-truth edits ambiguous, and
invited future drift of a different kind (a fix applied to only one copy).

v2.1.1 replaces "same text in many documents" with "one canonical source + references +
deterministic cross-checks", without changing any validated Orca / Git / risk / review /
human-gate invariant. Tests are retargeted to the canonical home — never deleted — and the
anti-drift guarantee moves from duplicate prose to assertions that each invariant lives at its
canonical source.

## Decision

1. **AGENTS.md is the always-loaded invariant layer.** It shrinks to cross-cutting invariants
   and pointers: project purpose, source-of-truth priority, repository map, the single
   normative source per rule, agent autonomy, the CORE/CONDITIONAL Execution Packet, the closed
   six-condition escalation list (its ONE canonical full wording), immutable-base + Skill
   pointer, risk/review, efficiency principles, human gates, knowledge management and
   definition of done.

2. **`.agent/skills/orca-writable-delegation/SKILL.md` is the canonical writable-delegation
   source.** It preserves, without semantic weakening, every validated lifecycle invariant:
   supervised writable dispatch via `worker-start`; immutable `integration_base_sha`; exact
   pre-edit `HEAD == integration_base_sha`; Orca lineage != Git ancestry; an immutable ordered
   linear commit-list result with no merge commit; Lead validation of ancestry/order/scope;
   anchoring before release; `git cherry-pick -x` integration with worker→integrated SHA
   mappings; Lead ownership of conflicts with deterministic already-present/empty-pick
   handling; integrated-state verification; `worker-release` before delivery acknowledgment;
   no shared writable checkout across nodes; and retry/placement/base semantics.

   The Skill distinguishes **stable project invariants** from **version-specific Orca CLI
   mechanics**. Orca 1.4.184 observations (e.g. `--terminal` rejects `--base-branch`; `--retry-of`
   placement) are retained only as clearly-labelled compatibility notes, each serving an
   invariant stated independently of the flag mechanics so the invariant survives an Orca
   upgrade. The Skill requires consulting the installed version-matched Orca guide before
   runtime actions (ROOT AMENDMENT 4).

3. **The closed six-condition Root re-entry list keeps exactly one canonical full wording in
   AGENTS.md.** Role files reference that canonical invariant rather than maintain a second
   copy; they describe role-specific escalation behavior (one specific question, retain the
   loop, condition 6 as authority escalation) but do not duplicate the list.

4. **Role files answer only: who am I / what I own / what I may decide / what I may delegate /
   when I escalate / which Skills or policies to load.** Detailed Git/Orca mechanics move to
   the Skill.

5. **Harness files carry harness-specific facts only and point to `routing.yaml` for role
   preference**; none declares a role default independently of `routing.yaml`. The "believed
   default" hedge is removed. Host-specific pool naming presented as a property of Pi is moved
   to a runtime inventory/telemetry home if one exists; none exists in this repository, so the
   host detail is dropped and Pi's durable identity no longer names a host pool. No new
   runtime-state subsystem is invented.

6. **The Execution Packet splits into CORE and CONDITIONAL fields** (ROOT AMENDMENT 3). CORE
   fields are always required; CONDITIONAL blocks are required only when the task uses writable
   delegation, independent review, a premium budget envelope, specialized capabilities, or
   remote/system operations. Conditionality is not optionality: when writable delegation is
   used, the writable block is mandatory and a deterministic test enforces it. The premium
   budget envelope is CONDITIONAL structure under `MODEL POLICY` and/or `BUDGET / HUMAN GATES`,
   never a new always-present top-level field — the redesign REDUCES packet surface.

7. **Premium model and reasoning effort become adaptive** (ROOT AMENDMENT model-policy). Model
   choice and reasoning effort for premium pools are ADAPTIVE policy variables selected from
   task complexity, ambiguity, risk, verification strength, observed failure evidence,
   quota/budget pressure and the expected value of additional reasoning — never hard-coded HIGH
   everywhere and never blindly LOW. The Root/Supervisor defines the envelope; the
   agent/harness adapts within it; exceeding it requires escalation. The policy is documented
   independently of whether any harness currently exposes the switching primitive.
   Low-cost pools are unchanged: reasoning stays HIGH or provider-recommended, never lowered to
   save tokens (cost is optimized through routing and context discipline).

8. **Review-cycle budget is bounded** (ROOT AMENDMENT 1). `risk.yaml` remains the SOLE
   authority for WHETHER independent review is required and is not edited. `retry.yaml` governs
   only HOW MANY review/fix/re-review cycles are allowed AFTER review is required (MEDIUM:
   initial_review 1, fix_cycles 1, focused_re_reviews 1, on_further_blocking
   return_to_root_for_diagnosis). Root's options on exhaustion: continue harness, change
   strategy, escalate to Codex Premium, or amend acceptance/tests. Unlimited loops are
   forbidden; HIGH-risk work is governed by `risk.yaml` and may justify more review, never
   fewer. A deterministic test protects this authority boundary.

## Relationship to ADR-004

ADR-005 is a direct continuation of ADR-004's role/harness/model/capability separation. ADR-004
records that separation and its anti-drift reliance on duplicate text; ADR-005 keeps every
validated invariant ADR-004 and the v2.1 lifecycle suite established and changes only WHERE a
rule's canonical text lives and HOW the suite assures it. ADR-004's no-provider-as-role guard
remains the same syntactic forward gate; ADR-005 fixes a grammar slip in that document
("a deliberate, documented syntactic heuristic") without otherwise altering the recorded
decision. ADR-001/002/003 are unchanged and remain the historical foundation.

## Consequences

Benefits:

- always-loaded context shrinks; detailed procedure is load-on-demand
- a single normative source per rule removes ambiguous or conflicting copies
- the anti-drift guarantee becomes "one canonical source + deterministic cross-checks" instead
  of duplicate prose
- premium reasoning is adaptively allocated within a bounded envelope
- review/fix loops are explicitly bounded for MEDIUM

Costs and residual risks:

- agents loading only AGENTS.md must now follow the Skill pointer for writable delegation
- the version-specific Orca compatibility notes must not be mistaken for permanent API
  semantics; the invariant statement beside each note mitigates this
- adaptive premium reasoning requires a Root-defined envelope per task, adding a small packet
  burden on the conditional field

## Verification

The policy test suite is retargeted (not deleted) to the Skill as the canonical writable
lifecycle home, and new semantic/invariant tests are added: AGENTS.md stays within a bounded
byte/line budget; the detailed lifecycle procedure is not duplicated across always-loaded
files; AGENTS.md keeps the immutable-base invariant and Skill pointer; the six-condition list
has exactly one canonical full copy; harness files declare no role default independent of
routing.yaml; low-cost reasoning is not lowered; premium policy is adaptive; the MEDIUM review
budget is bounded; `retry.yaml` cannot make review required (risk.yaml is the sole authority);
a writable task's conditional block is mandatory; and no HANDOFF/memory/SCRATCH subsystem is
introduced. A deterministic mutation bar proves each retargeted test fails when its invariant
is removed from the new canonical home.
# Codex CLI Harness

Codex CLI is a **harness**, not bound to any role. It runs the Codex model and is the
**Codex Premium Execution Lead** harness class.

It is **not** the mandatory Execution Lead for every task. Role → harness routing is owned by
`.agent/policies/routing.yaml`: the Root selects the Execution Lead harness per task,
defaulting to the Pi Standard/Fast harness for well-scoped, lower-complexity, LOW/MEDIUM work
and escalating to the Codex Premium Lead harness for difficult engineering reasoning, complex
repository investigation, difficult debugging, HIGH-risk or cross-module implementation, or
when cheaper execution proves insufficient.

Codex is used in other roles (Root, Worker, Specialist, Reviewer) only when capability,
availability, budget or independence make it the best fit. None of these preferences are
permanent role bindings. For HIGH-risk independent review of a Codex implementation, use
another capable reviewer provider or record a human-visible same-provider correlation waiver.
Codex CLI under Orca launches through `orca orchestration worker-start`; it never bypasses
`worker-start`.
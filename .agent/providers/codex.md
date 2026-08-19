# Codex Model/Provider Pool

This file describes the **Codex model/provider pool**, a selectable pool profiled in
`.agent/providers/` and listed under `model_pools` in `routing.yaml`. It is a pool, not a
role and not a permanent binding.

The Codex pool backs the **Codex Premium Execution Lead** harness class
(`.agent/harnesses/codex-cli.md`), which the Root selects for difficult engineering
reasoning, complex repository investigation, difficult debugging, HIGH-risk or cross-module
implementation, and escalation after cheaper execution proves insufficient. Codex is **not**
the mandatory Execution Lead for every task; the Pi Standard/Fast Lead is the default for
well-scoped, lower-complexity, LOW/MEDIUM work.

Codex may be selected for other roles when capability, availability, budget or independence
make it the best fit. For independent review of a Codex implementation, prefer a different
capable reviewer pool or record a human-visible same-provider correlation waiver.

When selected as Execution Lead, consume the Execution Packet and own implementation
planning, repository investigation, coding, debugging, deterministic tests and verification,
iterative fixes, and the delegation decision. Execute autonomously until acceptance criteria
are met or a closed Root re-entry condition applies. Return compressed evidence, keep
durable state in the repository and GitHub, and never bypass `orca orchestration
worker-start`.

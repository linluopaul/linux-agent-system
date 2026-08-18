# ADR-004: Role / Harness / Model / Capability Separation and Execution-Cost Metrics

- Status: Accepted
- Date: 2026-08-18
- Scope: Role/harness/model/capability abstraction, efficiency and terse reporting,
  Execution Packet extension, execution-cost metrics

## Context

ADR-002 introduced two control planes and recorded provider preferences (Claude preferred
for the Root, Codex for the Execution Lead, DeepSeek for the Worker). Over time these
preferences were read as role bindings: the architecture began to look like DeepSeek is a
Worker and Codex is the Execution Lead for every task, and success was partly measured as
"Codex usage greater than Claude usage."

That is factually wrong and blocks a future Pi Supervisor. Pi is a **harness** whose model
is selected at runtime from a model/provider pool: on one host the default pool is
`volcengine-ark-coding-plan` with request alias `ark-code-latest`, which can route to a
different underlying model, with `deepseek` as fallback. A harness, a model and a provider
are therefore distinct axes; only the **role** is an invariant. Provider-as-role must be
removed from the model.

## Decision

Separate four axes:

- **ROLE** is the invariant (Root, Execution Lead, Worker, Reviewer, Specialist, Platform
  Steward).
- **HARNESS** is runtime-selected (pi, claude-code, codex-cli) and profiled under
  `.agent/harnesses/`.
- **MODEL/PROVIDER POOL** is runtime-selected. `.agent/providers/` is reframed as
  model/provider-pool profiles, and `routing.yaml` gains a `model_pools` list. DeepSeek,
  MiniMax, Kimi, Gemini and future providers are modeled as pools, not roles.
- **CAPABILITY PROFILE** is runtime-selected. `.agent/policies/capabilities.yaml` defines
  the named profiles plus least-capability and progressive-disclosure rules.

`routing.yaml` routes `role -> harness class -> model/provider pool` with no permanent
provider-role binding. Pi under Orca launches through `orca orchestration worker-start`;
choosing a harness never bypasses `worker-start`.

Two Execution Lead harness classes replace the single "Codex Execution Lead":

- **Pi Standard/Fast Lead** — default for well-scoped, lower-complexity, LOW/MEDIUM work.
- **Codex Premium Lead** — for difficult engineering reasoning, complex repository
  investigation, difficult debugging, HIGH-risk or cross-module implementation, and
  escalation after cheaper execution proves insufficient.

The Root selects the Execution Lead harness class per task; the selection is recorded in
the Execution Packet.

## Efficiency and terse reporting

Efficiency and terse reporting are native architecture principles defined in
`.agent/policies/efficiency.yaml`. Ten principles cover cheapest-capable-resource,
deterministic-first, execution-volume-over-root and low-cost-over-premium targets, and
never narrating routine tool usage. Agent-to-agent reports use the terse
`STATUS/CHANGED/VERIFY/COMMIT/BLOCKERS/UNCERTAINTY/NEXT` block. Terseness must not apply
to architecture decisions, acceptance criteria, security warnings, destructive operations,
human approval requests, unresolved ambiguity or HIGH-risk findings; human-facing
Supervisor/Root communication stays concise but normal prose.

## Execution Packet

The Execution Packet (see AGENTS.md and ARCHITECTURE section 10) is extended to carry
`EXECUTION HARNESS`, `MODEL POLICY`, `CAPABILITY PROFILE`, `EFFICIENCY PROFILE`,
`CONTEXT BUDGET`, `OUTPUT MODE`, `SESSION POLICY`, `COMPACTION POLICY`,
`EXECUTION / RETRY BUDGET` and `ESCALATION THRESHOLD`. The Lead-to-Worker assignment
carries a reduced form of these fields.

## Metrics

The "Codex usage greater than Claude usage" objective is retired. The target principle is:
execution volume exceeds root reasoning volume, and low-cost execution volume exceeds
premium execution volume, without compromising acceptance criteria or HIGH-risk
safeguards.

The metrics are renamed:

- `execution_vs_root_usage_share` (lineages from `root_vs_execution_usage_share`; the
  ADR-002 computation and rolling review are kept)
- `premium_vs_low_cost_execution_share`
- `context_and_output_cost_per_successful_task`

## Future Pi Supervisor

The Role/Harness/Model/Capability abstraction admits a future long-lived Pi Supervisor
(Orca observation/control, Git/GitHub, system inspection, SSH, Tailscale, approval gates)
without implementing it here. Capabilities for that role exist in the
`capabilities.yaml` catalog; no Supervisor is built.

## Relationship to ADR-002

ADR-004 supersedes ADR-002's **metric objective** (the "Codex usage greater than Claude
usage" framing) and its **provider-as-role reading** of provider preferences. ADR-002
remains Accepted: the two control-plane authority boundaries, the closed six-condition
escalation list, the Execution Lead as a first-class delegating role, fresh-session review
independence and the workflow rules that keep execution above Root usage all remain in
force. ADR-004 keeps the ADR-002 metric computation and records the lineage of
`root_vs_execution_usage_share` -> `execution_vs_root_usage_share`. ADR-001's Orca-first
and Controller-boundary decisions are unchanged.

## Consequences

Benefits:

- harness, model and provider are decoupled from roles, so a future Pi Supervisor fits the
  model
- the Execution Lead is selected by the Root to match task complexity, not a fixed binding
- efficiency and terse reporting are explicit, with clarity overrides that protect safety
- execution-cost metrics reflect the real objective (cheap first, execution over root)
  rather than provider market share

Costs and residual risks:

- existing tooling that keyed on the old provider-order schema must migrate to the
  role-harness-pool schema
- low-cost-first routing could over-fit cheap pools; escalation rules must remain
  evidence-driven
- terse reporting could obscure findings if the clarity overrides are not honored
- efficiency targets are objectives, not quotas; they must never weaken HIGH-risk
  safeguards

## Verification

Repository policy tests assert that Pi is a harness and not a model or provider, that the
Worker role is not bound to DeepSeek, that Codex is a premium escalation rather than the
mandatory Execution Lead, that the Root selects the Execution Lead harness, that the
capability catalog and the new packet fields exist, that the ten efficiency principles and
the terse-reporting clarity overrides exist, that Caveman is not a dependency, that the
execution-cost metrics replace the provider-usage objective, that efficiency policy does
not weaken HIGH-risk guardrails, and that the validated lifecycle invariants survive.
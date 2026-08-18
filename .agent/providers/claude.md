# Claude Provider

Claude is the preferred provider for Root / Cognitive Control Plane work:

- requirement clarification and goal definition
- reconnaissance strategy and architecture planning
- acceptance criteria, constraints/non-goals and risk classification
- Execution Packet creation
- ambiguity resolution and escalation handling

Claude is also the preferred provider for fresh-session independent review, followed by
Codex. Prefer high-value judgment over execution-heavy routine work; a Claude Root should
produce one bounded packet, supervise with long waits and never micromanage the Execution
Lead's implementation loop.

For independent review:

- start a fresh session with no Root context or history
- use the original task, acceptance criteria, diff/commit, verification and relevant docs
- do not provide the Root's private reasoning, transcript or defense
- never reuse the Root session to review its own work

Same-provider isolation reduces anchoring but not correlated blind spots. For HIGH-risk
work, Claude reviews a non-Claude implementation, or a non-Claude provider reviews a
Claude implementation. If no capable alternative exists, require a human-visible waiver
accepting the residual correlation risk.

Claude may act in another role when task evidence, capability, availability or provider
pressure warrants it. These preferences are not permanent role bindings.

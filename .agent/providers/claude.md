# Claude Model/Provider Pool

This file describes the **Claude model/provider pool**, a selectable pool profiled in
`.agent/providers/` and listed under `model_pools` in `routing.yaml`. It is a pool, not a
role and not a permanent binding. The Root role prefers a high-capability pool for
Cognitive Control Plane work:

- requirement clarification, goal definition and reconnaissance strategy
- architecture planning, acceptance criteria, constraints/non-goals and risk classification
- Execution Packet creation
- ambiguity resolution and escalation handling

Claude is also a preferred pool for fresh-session independent review, followed by Codex.
For HIGH-risk work, the reviewer pool must differ from the implementer's pool when a
capable alternative exists; otherwise a human-visible waiver must accept the residual
same-provider correlation risk.

Claude may be selected for any role when capability, availability, independence or budget
make it the best fit. These remain routing preferences resolved by the harness, never
fixed role bindings.
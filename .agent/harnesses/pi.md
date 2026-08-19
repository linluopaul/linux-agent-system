# Pi Harness

Pi is a **harness**, not a model and not a provider, and not bound to any role. Its model is
selected at runtime from a
model/provider pool configured in `.agent/policies/routing.yaml` (`model_pools`); model
identity is runtime data, never a fixed property of Pi. A specific host default pool alias is
a runtime/telemetry detail and does not belong to Pi's durable harness identity.

Pi under Orca launches through `orca orchestration worker-start`; choosing the Pi harness
never bypasses `worker-start`.

## Role routing

Role → harness routing is owned by `.agent/policies/routing.yaml`, not independently declared
here. Per that file Pi is the standard Execution Lead harness class (the **Pi Standard/Fast**
harness for well-scoped, lower-complexity, LOW/MEDIUM work) and is the default harness for
Reviewer, Worker, Specialist and Platform Steward work; the Root default harness is **Claude
Code** (`root: claude_code`), not Pi, and difficult engineering escalates to the **Codex
Premium Lead** harness. These are routing preferences and Pi is a harness that CAN act as the
Execution Lead, not one that must — never a permanent binding.

## Reasoning effort

Selecting a low-cost pool does NOT imply lowering thinking/reasoning effort. Reasoning effort
is a correctness parameter, not a cost lever: low-cost pools keep HIGH or provider-recommended
reasoning effort, and cost is optimized through routing and context discipline, never by
reducing reasoning effort.

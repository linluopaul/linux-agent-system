# Pi Harness

Pi is a **harness**, not a model and not a provider. Its model is selected at runtime
from a configurable model/provider pool (for example, on host X the default pool is
`volcengine-ark-coding-plan` with request alias `ark-code-latest`, which may itself route
to a different underlying model, with `deepseek` as fallback). Because the model behind a
pool alias may change, Pi must never be documented or relied upon as a fixed model.

Pi under Orca launches through `orca orchestration worker-start`; choosing the Pi harness
never bypasses `worker-start`.

## Execution Lead classes

Pi can act as an **Execution Lead** in two ways:

- **Pi Standard/Fast Lead** — the default for well-scoped, lower-complexity, LOW/MEDIUM
  work where deterministic verification dominates and the model cost floor is sufficient.
- **Pi Premium-aware Lead policy** — for tasks where the Root selects Codex (the Codex
  Premium Lead) instead, Pi remains the harness for Root, Reviewer, Worker and Specialist
  roles.

The Root selects the Execution Lead harness class per task; it is not a permanent binding.

## Role support

- **Root / Cognitive Control Plane** — believed default is the **Claude Code harness** with
  a high-capability pool; Pi with a capable pool remains an acceptable alternative.
  Claude Code remains the preferred Root harness; this is a preference, not a permanent
  binding.
- **Execution Lead / Engineering Control Plane** — Pi Standard/Fast by default; the Root
  escalates to Codex Premium for difficult engineering.
- **Execution Worker** — Pi with a low-cost pool for well-scoped work.
- **Independent Reviewer** — fresh, context-isolated Pi session; HIGH-risk review prefers a
  provider different from the implementer's.

## Model / provider pool

Model identity is runtime data. The routing.yaml `model_pools` section records the pools a
harness may select from (e.g. `volcengine_ark_coding_plan`, `deepseek`, `claude`, `codex`,
`min_max`, `kimi`, `gemini`). Which pool is used is a routing decision, never a fixed
property of the Pi harness.

Selecting a low-cost pool does NOT imply lowering thinking/reasoning effort. Reasoning
effort is a correctness parameter, not a cost lever: low-cost pools keep HIGH or
provider-recommended reasoning effort, and cost is optimized through routing and context
discipline, never by reducing reasoning effort.

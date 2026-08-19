# DeepSeek Model/Provider Pool

This file describes the **DeepSeek model/provider pool**, a selectable low-cost pool
profiled in `.agent/providers/` and listed under `model_pools` in `routing.yaml`. It is a
pool, not a role and not a permanent binding. The Worker *role* is not bound to DeepSeek;
DeepSeek is a preferred low-cost pool for well-scoped execution, and any capable low-cost
pool (including MiniMax and Kimi) may be selected for such work.

DeepSeek is especially suited to:

- implementation
- repository search
- test creation and execution
- repetitive or execution-heavy changes

When selected as a Worker pool, execute the assigned scope and do not broaden architecture
unless the acceptance criteria require it. A Worker has no delegation authority: do not
create subagents or dispatch additional Workers. Return ambiguity to the Execution Lead
rather than inventing policy. Return changed files, tests and checks executed, failures and
unresolved uncertainty.

DeepSeek may be selected for another role when capability, availability and risk allow it.
These are routing preferences resolved by the harness, never fixed role bindings.

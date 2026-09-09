# Harness and Provider Capabilities

What each harness and provider pool **can do**. Which one is selected for a given task is
resolved by policy, not here. Nothing in this file is a role binding, and no entry is a
permanent assignment.

## Harnesses

A harness is an execution environment. It is not a model, not a provider, and not a role.

### Claude Code

- Interactive terminal harness running Claude models; high-capability class.
- Model selection: `--model <alias|id>`.
- Permission mode is selectable at launch: `--permission-mode` accepts `acceptEdits`,
  `auto`, `bypassPermissions`, `manual`, `dontAsk`, `plan`. The active mode is visible in
  the running interface.
- Reads project instructions from the working directory upward at startup; a working
  directory outside the project inherits none of them.

### Codex CLI

- Interactive terminal harness running Codex/GPT models; high-capability class.
- Model selection: `-m, --model <MODEL>`; defaults and reasoning effort may be configured
  in the user-level Codex config.
- A pending self-update prompt can block startup until answered; automation must expect it.

### Pi

- Harness whose model is selected at runtime from a configured pool.
- Model identity is runtime data and never a durable property of the harness.

## Provider / model pools

A pool is a selectable capability class, not a role.

| Pool | Class | Well suited to |
|---|---|---|
| Claude | high-capability | ambiguity resolution, architecture reasoning, difficult diagnosis, high-value judgement |
| Codex | high-capability | difficult engineering reasoning, complex repository investigation, debugging, cross-module implementation |
| DeepSeek | low-cost | implementation, repository search, test creation and execution, repetitive execution-heavy changes |

Any capable low-cost pool is interchangeable with DeepSeek for the work in its row;
MiniMax and Kimi are equivalents where available.

## Cross-cutting runtime facts

- Herdr provides the cross-harness runtime: sessions, workspaces, worktrees, agent
  start/wait/stop, human-visible labels and resource lifecycle.
- Herdr agent names are lowercase technical slugs (`[a-z][a-z0-9_-]{0,31}`). Human-visible
  identity lives on operator-owned workspace and tab labels.
- A terminal title is owned by the running agent and changes with its activity; it is never
  a stable identity carrier.
- A harness may render a predicted next prompt as dim placeholder text. Dim ghost text is
  not submitted input and not task state; screen parsing must distinguish it.

## Not recorded here

Role preferences, routing defaults, review requirements, retry budgets and capability
envelopes are policy, and belong in the policy surface — not in this descriptor.

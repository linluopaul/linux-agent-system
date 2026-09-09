# Linux Agent System

A cross-harness architecture and operating platform for long-running agent projects on
Linux.

The V4 cognitive architecture has four roles — **Root · Lead · Delegate · Reviewer** — with
a Child Root as the Root role applied recursively. Herdr is the cross-harness runtime
substrate. Git and GitHub hold the authoritative durable project knowledge; GitHub Issues
are optional and are not a required task carrier.

## Where things live

| Source | Owns |
|---|---|
| `AGENTS.md` | minimal always-loaded agent instructions |
| `docs/ARCHITECTURE.md` | current V4 architecture |
| `docs/decisions/` | ADR decision log |
| `docs/PROJECT_STATE.md` | current operational and project state |
| `docs/ROADMAP.md` | future work |
| `docs/HISTORY.md` | historical decisions, rejected approaches, evolution record |
| `docs/NODES.md` | machine and network inventory, operational node facts |
| `.agent/capabilities.md` | harness and provider capability facts |
| `.agent/procedures/` | load-on-demand runtime procedures |

Runtime commands are not documented here; see `.agent/procedures/` and the runbooks.

## Historical boundary

The V3 Orca-first and Hermes-era decisions remain in the ADR log and `docs/HISTORY.md` as
historical context. They are superseded and are not the current execution architecture.

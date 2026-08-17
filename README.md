# Linux Agent System

A portable multi-agent development system for Linux.

## Core Architecture

- GitHub — durable system of record
- Herdr — execution and communication plane
- Claude / Codex / DeepSeek — replaceable agent providers
- Python Controller — deterministic control plane
- Git worktrees — isolated concurrent task execution
- Tests and evals — primary verification mechanism
- Multiple Linux nodes — distributed task execution

## Current Stage

The project is currently in the manual workflow validation phase.

Controller automation will be added only after the manual multi-agent
workflow has been tested on real tasks.

## Repository Structure

- `AGENTS.md` — universal agent rules
- `CLAUDE.md` — Claude Code adapter
- `.agent/providers/` — provider-specific guidance
- `.agent/roles/` — agent role definitions
- `.agent/policies/` — routing, risk and retry policies
- `docs/` — architecture, decisions and runbooks
- `controller/` — future Python Controller
- `tests/` — automated tests
- `evals/` — behavioral and high-risk evaluations
- `infra/` — bootstrap and node infrastructure
- `data/` — local datasets, not stored directly in Git

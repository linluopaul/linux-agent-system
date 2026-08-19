# Claude Code Harness

Claude Code is a **harness**, not bound to any role. It runs the Claude model and is a
premium (higher-capability) harness class.

Role → harness routing is owned by `.agent/policies/routing.yaml`. Per that file the Claude
Code harness is the preferred default Root / Cognitive Control Plane harness; it is used
selectively for work that benefits from high-capability reasoning:

- Root / Cognitive Control Plane work
- difficult diagnosis and ambiguity resolution
- fresh-session independent review with a capable reviewer
- architecture consultation and high-value judgment work

Claude Code is not permanently bound to any role. A High-risk reviewer must differ from the
implementer's provider when a capable alternative exists, or a human-visible waiver must
accept the same-provider correlation risk. Claude Code under Orca launches through
`orca orchestration worker-start`; it never bypasses `worker-start`.
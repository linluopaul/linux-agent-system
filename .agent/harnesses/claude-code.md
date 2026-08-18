# Claude Code Harness

Claude Code is a **harness**, not bound to any role. It runs the Claude model and is a
premium (higher-capability) harness class.

Used selectively for:

- Root / Cognitive Control Plane work requiring high-capability reasoning
- difficult diagnosis and ambiguity resolution
- fresh-session independent review that benefits from a capable reviewer
- architecture consultation and high-value judgment work

Claude Code is not permanently bound to any role. The Root may prefer it for its own work,
and the Root may prefer Claude (when it is a capable alternative) for independent review of
a non-Claude implementation. A HIGH-risk reviewer must differ from the implementer's
provider when a capable alternative exists, or a human-visible waiver must accept the
same-provider correlation risk.

Claude Code under Orca launches through `orca orchestration worker-start`; it never
bypasses `worker-start`.

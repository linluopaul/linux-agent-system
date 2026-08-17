from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class ArchitecturePolicyTests(unittest.TestCase):
    def test_orca_is_primary_and_github_is_durable(self) -> None:
        agents = read("AGENTS.md")
        readme = read("README.md")
        architecture = read("docs/ARCHITECTURE.md")

        for document in (agents, readme, architecture):
            self.assertIn("Orca", document)
            self.assertIn("GitHub", document)

        self.assertIn(
            "Orca as the primary agent development environment and execution plane",
            agents,
        )
        self.assertIn("Herdr is not the default", agents)
        self.assertNotIn("Herdr as the execution and communication plane", agents)

    def test_provider_preference_order(self) -> None:
        routing = read(".agent/policies/routing.yaml")

        self.assertIn(
            "defaults:\n  preferred_root:\n    - codex",
            routing,
        )
        self.assertIn(
            "preferred_worker:\n    - deepseek",
            routing,
        )
        self.assertIn(
            "preferred_specialist:\n    - claude",
            routing,
        )
        self.assertIn(
            "preferred_reviewer:\n    - claude",
            routing,
        )
        self.assertIn("risk.yaml is authoritative", routing)
        self.assertIn("do_not_permanently_bind_provider_to_role", routing)

    def test_high_risk_review_guardrail_is_preserved(self) -> None:
        risk = read(".agent/policies/risk.yaml")
        routing = read(".agent/policies/routing.yaml")

        self.assertIn("independent_review: required", risk)
        self.assertIn("controller_security_and_safety_policy", risk)
        self.assertIn("independent_review: required", routing)
        self.assertNotIn("reviewer_independence", routing)

    def test_orchestration_delivery_must_be_acknowledged(self) -> None:
        runbook = read("docs/runbooks/ORCA_WORKFLOW.md")
        architecture = " ".join(read("docs/ARCHITECTURE.md").split())

        self.assertIn("check --ack <delivery_id> --wait", runbook)
        self.assertIn("replays the same oldest Delivery", runbook)
        self.assertIn("check --ack <delivery_id>", architecture)
        self.assertIn("liveness checkpoint", architecture)

    def test_controller_does_not_duplicate_orca_lifecycle(self) -> None:
        agents = read("AGENTS.md")
        adr = " ".join(
            read("docs/decisions/ADR-001-orca-first-execution-plane.md").split()
        )

        self.assertIn("Do not duplicate Orca's deterministic worktree", agents)
        for responsibility in (
            "GitHub task polling",
            "risk and budget policy",
            "node scheduling",
            "deterministic tests and evals",
            "human gates",
            "backup/recovery",
        ):
            self.assertIn(responsibility, agents)

        self.assertIn(
            "will not implement a parallel worktree/terminal/message/dispatch scheduler",
            adr,
        )


if __name__ == "__main__":
    unittest.main()

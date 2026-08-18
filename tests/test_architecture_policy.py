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
            "defaults:\n  preferred_root:\n    - claude",
            routing,
        )
        self.assertIn(
            "preferred_execution_lead:\n    - codex",
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
        self.assertEqual(
            3,
            routing.count("    preferred_root:\n      - claude"),
        )
        self.assertEqual(
            3,
            routing.count("    preferred_execution_lead:\n      - codex"),
        )
        self.assertIn("risk.yaml is authoritative", routing)
        self.assertNotIn("codex_is_default_root_preference", routing)
        for principle in (
            "claude_is_default_root_preference",
            "codex_is_default_execution_lead_preference",
            "deepseek_is_preferred_for_well_scoped_worker_tasks",
            "root_reentry_is_limited_to_the_closed_escalation_list",
            "normal_codex_execution_usage_substantially_exceeds_claude_root_usage",
        ):
            self.assertIn(principle, routing)
        self.assertIn("do_not_permanently_bind_provider_to_role", routing)

    def test_execution_lead_role_and_closed_escalation_contract(self) -> None:
        lead = read(".agent/roles/execution-lead.md")
        agents = read("AGENTS.md")
        architecture = read("docs/ARCHITECTURE.md")

        self.assertIn("first-class Engineering Control Plane", lead)
        self.assertIn("delegation authority", lead.lower())
        self.assertIn("Execute autonomously", lead)

        conditions = (
            "architecture materially changes",
            "acceptance criteria are ambiguous",
            "difficult diagnosis remains unresolved",
            "HIGH-risk independent review is required",
            "deterministic verification cannot resolve uncertainty",
        )
        for document in (agents, architecture):
            self.assertIn("closed Root re-entry list", document)
            for condition in conditions:
                self.assertIn(condition, document)

    def test_execution_packet_is_root_to_execution_lead_interface(self) -> None:
        agents = read("AGENTS.md")
        architecture = read("docs/ARCHITECTURE.md")

        self.assertIn("sole normal interface from\nRoot to Execution Lead", agents)
        self.assertIn("Root → Execution Lead", architecture)
        self.assertIn("sole\nnormal interface", architecture)
        for field in (
            "GOAL",
            "BACKGROUND / PROBLEM STATEMENT",
            "ACCEPTANCE CRITERIA",
            "CONSTRAINTS / NON-GOALS",
            "RISK: LOW | MEDIUM | HIGH",
            "ARCHITECTURE DECISIONS",
            "OPEN QUESTIONS DELEGATED",
            "RECONNAISSANCE STRATEGY",
            "REQUIRED TESTS / EVALS",
            "VERIFICATION EVIDENCE REQUIRED",
            "WORKTREE / BASE COMMIT",
            "BUDGET / HUMAN GATES",
            "ESCALATION CONTRACT",
            "EXPECTED REPORT FORMAT",
        ):
            self.assertIn(field, architecture)

    def test_review_independence_is_fresh_session_context_independence(self) -> None:
        agents = read("AGENTS.md")
        architecture = read("docs/ARCHITECTURE.md")
        reviewer = read(".agent/roles/reviewer.md")

        self.assertIn("fresh-session context independence", agents)
        self.assertIn("fresh-session context independence", reviewer)
        self.assertIn("fresh session", architecture)
        for document in (agents, architecture, reviewer):
            self.assertIn("Root", document)
            self.assertIn("private reasoning", document)
            self.assertIn("correlated", document)
        self.assertIn("must never review its own work", agents)
        self.assertIn("cannot review itself", architecture)
        self.assertIn("may never review its own work", reviewer)

    def test_no_current_document_claims_codex_is_the_default_root(self) -> None:
        historical_adr = ROOT / "docs/decisions/ADR-001-orca-first-execution-plane.md"
        documents = [ROOT / "AGENTS.md", ROOT / "README.md"]
        for directory in (ROOT / "docs", ROOT / ".agent"):
            documents.extend(
                path
                for path in directory.rglob("*")
                if path.is_file() and path.suffix in {".md", ".yaml", ".yml"}
            )

        forbidden = (
            "codex is the default root",
            "codex: default root",
            "codex root",
            "default preference for the root role",
            "default routing preference is codex",
            "codex_is_default_root_preference",
            "| root ownership | codex |",
        )
        for path in documents:
            if path == historical_adr:
                continue
            content = path.read_text(encoding="utf-8").lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, content, str(path.relative_to(ROOT)))

        historical = historical_adr.read_text(encoding="utf-8")
        self.assertIn("Status: Accepted", historical)
        self.assertIn("retained as a historical record", historical)
        self.assertIn("ADR-002 supersedes only the provider-role preference", historical)

    def test_cost_asymmetry_metric_and_adr_are_durable(self) -> None:
        agents = read("AGENTS.md")
        architecture = read("docs/ARCHITECTURE.md")
        adr = read("docs/decisions/ADR-002-cognitive-and-engineering-control-planes.md")

        for document in (agents, architecture):
            self.assertIn("Root micromanagement", document)
            self.assertIn("implementation edit/verify/fix loop", document)
            self.assertIn("compressed evidence", document)
        self.assertIn("root_vs_execution_usage_share", architecture)
        self.assertIn("Status: Accepted", adr)
        self.assertIn("supersedes **only** ADR-001's provider-role preferences", adr)
        self.assertIn("Orca the primary ADE/worktree/collaboration/orchestration", adr)
        self.assertIn("Herdr remains optional future infrastructure", adr)

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

from pathlib import Path
import unittest

try:
    import yaml
except ModuleNotFoundError:
    yaml = None


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def normalize(text: str) -> str:
    return " ".join(text.split())


def fenced_block_after(document: str, heading: str) -> list[str]:
    section = document.split(heading, 1)[1]
    block = section.split("```text", 1)[1].split("```", 1)[0]
    return [line.strip() for line in block.strip().splitlines()]


class ArchitecturePolicyTests(unittest.TestCase):
    def load_yaml(self, relative_path: str):
        if yaml is None:
            self.skipTest(
                "PyYAML is not installed and this repository declares no Python dependencies"
            )
        return yaml.safe_load(read(relative_path))

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

    def test_policy_yaml_parses_and_provider_preferences_hold(self) -> None:
        if yaml is None:
            self.skipTest(
                "PyYAML is not installed and this repository declares no Python dependencies"
            )
        policy_paths = sorted((ROOT / ".agent/policies").glob("*.yaml"))
        parsed = {}
        for path in policy_paths:
            try:
                parsed[path.name] = yaml.safe_load(path.read_text(encoding="utf-8"))
            except yaml.YAMLError as error:
                self.fail(f"{path.relative_to(ROOT)} is not valid YAML: {error}")

        routing = parsed["routing.yaml"]
        defaults = routing["defaults"]
        self.assertEqual("claude", defaults["preferred_root"][0])
        self.assertEqual("codex", defaults["preferred_execution_lead"][0])
        self.assertEqual("deepseek", defaults["preferred_worker"][0])
        self.assertEqual("claude", defaults["preferred_specialist"][0])
        self.assertEqual("claude", defaults["preferred_reviewer"][0])

        first_choices = {
            "preferred_root": "claude",
            "preferred_execution_lead": "codex",
            "preferred_worker": "deepseek",
        }
        for risk_name, risk_policy in routing["risk"].items():
            for role_key, provider in first_choices.items():
                if role_key in risk_policy:
                    self.assertEqual(
                        provider,
                        risk_policy[role_key][0],
                        f"risk.{risk_name}.{role_key}",
                    )

        self.assertEqual(
            "cross_provider_or_human_visible_residual_risk_waiver",
            routing["risk"]["high"]["reviewer_provider_diversity"],
        )
        principles = routing["principles"]
        for principle in (
            "claude_is_default_root_preference",
            "codex_is_default_execution_lead_preference",
            "deepseek_is_preferred_for_well_scoped_worker_tasks",
            "root_reentry_is_limited_to_the_closed_escalation_list",
            "normal_execution_usage_substantially_exceeds_root_usage",
            "do_not_permanently_bind_provider_to_role",
        ):
            self.assertIn(principle, principles)
        self.assertNotIn(
            "normal_codex_execution_usage_substantially_exceeds_claude_root_usage",
            principles,
        )
        self.assertIn("levels", parsed["risk.yaml"])
        self.assertIn("execution_lead_failure", parsed["retry.yaml"])

    def test_execution_lead_role_and_closed_escalation_contract(self) -> None:
        lead = read(".agent/roles/execution-lead.md")
        self.assertIn("first-class Engineering Control Plane", lead)
        self.assertIn("delegation authority", lead.lower())
        self.assertIn("Execute autonomously", lead)

        documents = {
            "AGENTS.md": read("AGENTS.md"),
            ".agent/roles/execution-lead.md": lead,
            ".agent/roles/root.md": read(".agent/roles/root.md"),
            "docs/ARCHITECTURE.md": read("docs/ARCHITECTURE.md"),
            "docs/runbooks/ORCA_WORKFLOW.md": read(
                "docs/runbooks/ORCA_WORKFLOW.md"
            ),
            "docs/decisions/ADR-002-cognitive-and-engineering-control-planes.md": read(
                "docs/decisions/ADR-002-cognitive-and-engineering-control-planes.md"
            ),
        }
        conditions = (
            "architecture materially changes",
            "acceptance criteria are ambiguous",
            "difficult diagnosis remains unresolved",
            "HIGH-risk independent review is required",
            "deterministic verification cannot resolve uncertainty",
            "execution is blocked by something outside the Execution Lead's authority—a "
            "protected human gate, a missing authorization or credential, an exhausted "
            "budget or concurrency limit, an unavailable required dependency, or "
            "acceptance criteria that are infeasible or mutually contradictory",
        )
        for path, document in documents.items():
            normalized = normalize(document)
            self.assertIn("closed", normalized.lower(), path)
            for condition in conditions:
                self.assertIn(condition, normalized, path)

        for path in (
            "AGENTS.md",
            ".agent/roles/execution-lead.md",
            ".agent/roles/root.md",
        ):
            normalized = normalize(documents[path])
            self.assertIn(
                "authority escalation, not a cognitive re-entry", normalized, path
            )
            self.assertIn("worker_done --outcome failed", normalized, path)
            self.assertIn("GitHub Blocked / Needs-Human", normalized, path)

    def test_execution_packet_is_exact_root_to_lead_interface(self) -> None:
        agents = normalize(read("AGENTS.md"))
        architecture = read("docs/ARCHITECTURE.md")

        self.assertIn(
            "sole normal interface from Root to Execution Lead",
            agents,
        )
        self.assertIn(
            "Root → Execution Lead",
            normalize(architecture),
        )
        self.assertEqual(
            [
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
                "LEAD BRANCH",
                "INTEGRATION_BASE_SHA",
                "ALLOWED CHANGED PATHS / SCOPE",
                "VERIFICATION REQUIREMENTS",
                "RESULT MODE",
                "BUDGET / HUMAN GATES",
                "ESCALATION CONTRACT",
                "EXPECTED REPORT FORMAT",
            ],
            fenced_block_after(architecture, "## 10. Task and Review Packets"),
        )
        self.assertIn(
            "may narrow the standing conditions",
            read("AGENTS.md"),
        )
        self.assertIn(
            "不能增加、重定义或绕过六个 standing conditions",
            architecture,
        )

    def test_review_independence_and_high_risk_provider_diversity(self) -> None:
        agents = read("AGENTS.md")
        architecture = read("docs/ARCHITECTURE.md")
        reviewer = read(".agent/roles/reviewer.md")

        self.assertIn("fresh-session context independence", agents)
        self.assertIn("fresh-session context independence", reviewer)
        self.assertIn("fresh session", architecture)
        for document in (agents, architecture, reviewer):
            self.assertIn("Root", document)
            self.assertIn("private reasoning", document)
            self.assertIn("correlation", document)
            self.assertIn("human-visible", document)
        self.assertIn("must never review its own work", agents)
        self.assertIn("cannot review itself", architecture)
        self.assertIn("may never review its own work", reviewer)
        self.assertIn(
            "reviewer's provider MUST differ from the implementer's provider",
            normalize(agents),
        )
        self.assertIn(
            "reviewer provider MUST differ from the implementer provider",
            normalize(reviewer),
        )

    def test_lead_owned_run_topology_and_failure_recovery(self) -> None:
        architecture = read("docs/ARCHITECTURE.md")
        runbook = read("docs/runbooks/ORCA_WORKFLOW.md")
        agents = read("AGENTS.md")
        retry = self.load_yaml(".agent/policies/retry.yaml")

        for document in (architecture, runbook):
            normalized = normalize(document)
            self.assertIn("Root-owned Run", normalized)
            self.assertIn("Lead-owned Run", normalized)
            self.assertIn("run-create", normalized)
            self.assertIn("task-create --run", normalized)
            self.assertIn("parent Task ID", normalized)
            self.assertIn("parent Dispatch ID", normalized)
            self.assertIn("worker-release", normalized)
        self.assertIn("must never call `run-use`", runbook)
        self.assertIn("Worker questions terminate at the Lead", runbook)
        for command in (
            "ORCA orchestration run-create --objective",
            "ORCA orchestration task-create --run",
            "ORCA orchestration worker-start --task",
            "ORCA orchestration worker-release --dispatch",
        ):
            self.assertIn(command, runbook)

        recovery = retry["execution_lead_failure"]
        self.assertEqual(
            "root_parent_run_coordinator", recovery["lifecycle_recovery_owner"]
        )
        self.assertEqual(
            "replacement_execution_lead",
            recovery["resumed_edit_verify_loop_owner"],
        )
        for document in (agents, architecture, runbook):
            normalized = normalize(document)
            self.assertIn("uncommitted", normalized)
            self.assertIn("replacement Execution Lead", normalized)

    def test_no_current_document_claims_codex_is_the_default_root(self) -> None:
        historical_adr = ROOT / "docs/decisions/ADR-001-orca-first-execution-plane.md"
        documents = {ROOT / "AGENTS.md", ROOT / "README.md"}
        for directory in (ROOT / "docs", ROOT / ".agent"):
            documents.update(
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
            content = path.read_text(encoding="utf-8")
            if path == historical_adr:
                marker = (
                    "> Superseded by ADR-002. The list below is historical, "
                    "not current routing policy."
                )
                start = content.index(marker)
                end_marker = (
                    "These are routing preferences, never permanent provider-role bindings."
                )
                end = content.index(end_marker, start) + len(end_marker)
                historical_block = content[start:end]
                self.assertIn("Codex: default Root", historical_block)
                content = content[:start] + content[end:]

            lower = content.lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, lower, str(path.relative_to(ROOT)))

        historical = historical_adr.read_text(encoding="utf-8")
        self.assertIn("Status: Accepted", historical)
        self.assertIn("retained as a historical record", historical)
        self.assertIn("ADR-002 supersedes only the provider-role preference", historical)

    def test_cost_asymmetry_metric_and_adr_are_durable(self) -> None:
        agents = read("AGENTS.md")
        architecture = read("docs/ARCHITECTURE.md")
        steward = read(".agent/roles/platform-steward.md")
        adr = read("docs/decisions/ADR-002-cognitive-and-engineering-control-planes.md")

        for document in (agents, architecture):
            self.assertIn("Root micromanagement", document)
            self.assertIn("implementation edit/verify/fix loop", document)
            self.assertIn("compressed evidence", document)
        for field in (
            "root_usage_units",
            "execution_usage_units",
            "percentage points",
            ".agent/runs/<task>/metrics.yaml",
            "manually recorded, not yet automated",
            "最近 20",
            "execution_share >= 65%",
        ):
            self.assertIn(field, architecture)
        self.assertIn("root_vs_execution_usage_share", steward)
        self.assertIn("rolling 20-task window", steward)
        self.assertNotIn("Enforce\nthat cost asymmetry structurally", agents)
        self.assertNotIn("structural rules 强制", architecture)
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
        self.assertIn(
            "reviewer_provider_diversity: "
            "cross_provider_or_human_visible_residual_risk_waiver",
            routing,
        )
        self.assertNotIn("reviewer_independence", routing)

    def test_orchestration_delivery_must_be_acknowledged(self) -> None:
        runbook = read("docs/runbooks/ORCA_WORKFLOW.md")
        architecture = normalize(read("docs/ARCHITECTURE.md"))

        self.assertIn("check --ack <delivery_id> --wait", runbook)
        self.assertIn("replays the same oldest Delivery", runbook)
        self.assertIn("check --ack <delivery_id>", architecture)
        self.assertIn("liveness checkpoint", architecture)

    def test_writable_worker_requires_exact_integration_base(self) -> None:
        documents = {
            "AGENTS.md": normalize(read("AGENTS.md")),
            ".agent/roles/worker.md": normalize(read(".agent/roles/worker.md")),
            "docs/ARCHITECTURE.md": normalize(read("docs/ARCHITECTURE.md")),
            "docs/runbooks/ORCA_WORKFLOW.md": normalize(
                read("docs/runbooks/ORCA_WORKFLOW.md")
            ),
        }

        for path, document in documents.items():
            self.assertIn("integration_base_sha", document, path)
            self.assertIn("git rev-parse HEAD", document, path)
        for path in (
            "AGENTS.md",
            ".agent/roles/worker.md",
            "docs/runbooks/ORCA_WORKFLOW.md",
        ):
            self.assertIn(
                "before any tracked-file modification",
                documents[path].lower(),
                path,
            )
        self.assertIn(
            "`git rev-parse HEAD` must exactly equal "
            "`git rev-parse <integration_base_sha>^{commit}`",
            documents["AGENTS.md"],
        )
        self.assertIn(
            "explicitly verify that `git rev-parse HEAD` exactly equals "
            "`git rev-parse <integration_base_sha>^{commit}`",
            documents[".agent/roles/worker.md"],
        )
        self.assertIn(
            'test "$(git rev-parse HEAD)" = '
            '"$(git rev-parse <integration_base_sha>^{commit})"',
            documents["docs/runbooks/ORCA_WORKFLOW.md"],
        )
        for path in ("AGENTS.md", ".agent/roles/worker.md", "docs/ARCHITECTURE.md"):
            self.assertIn("stop and escalate", documents[path].lower(), path)
        for path in (
            "AGENTS.md",
            ".agent/roles/worker.md",
            "docs/runbooks/ORCA_WORKFLOW.md",
        ):
            self.assertIn("git reset --hard", documents[path], path)
            self.assertIn("git checkout -B", documents[path], path)
            self.assertIn("preserve", documents[path].lower(), path)

    def test_v1_integration_operation_is_cherry_pick(self) -> None:
        documents = {
            "AGENTS.md": normalize(read("AGENTS.md")),
            ".agent/roles/execution-lead.md": normalize(
                read(".agent/roles/execution-lead.md")
            ),
            "docs/ARCHITECTURE.md": normalize(read("docs/ARCHITECTURE.md")),
            "docs/runbooks/ORCA_WORKFLOW.md": normalize(
                read("docs/runbooks/ORCA_WORKFLOW.md")
            ),
            "docs/decisions/ADR-003-lead-worker-git-integration-contract.md": normalize(
                read("docs/decisions/ADR-003-lead-worker-git-integration-contract.md")
            ),
        }

        for path, document in documents.items():
            self.assertIn("integration operation", document.lower(), path)
            self.assertIn("git cherry-pick", document, path)

    def test_v1_prohibits_branch_merge_reset_fast_forward_and_lineage_inference(
        self,
    ) -> None:
        expected_prohibitions = {
            "AGENTS.md": (
                "do not merge the worker branch, reset the lead branch to worker head, "
                "fast-forward the lead branch, or infer integration from orca lineage"
            ),
            ".agent/roles/execution-lead.md": (
                "never merge the worker branch, reset the lead branch to worker head, "
                "fast-forward the lead branch, or infer integration from orca lineage"
            ),
            "docs/ARCHITECTURE.md": (
                "v1 明确禁止 merge worker branch、reset lead branch to worker head、"
                "fast-forward lead branch，或从 orca lineage infer integration。"
            ),
            "docs/runbooks/ORCA_WORKFLOW.md": (
                "do not merge the worker branch, reset the lead branch to worker head, "
                "fast-forward the lead branch, take over the worker branch, or infer "
                "integration from orca lineage"
            ),
            "docs/decisions/ADR-003-lead-worker-git-integration-contract.md": (
                "merging the worker branch, resetting the lead branch to worker head, "
                "fast-forwarding the lead branch and inferring integration from orca "
                "lineage are prohibited"
            ),
        }

        for path, prohibition in expected_prohibitions.items():
            self.assertIn(prohibition, normalize(read(path)).lower(), path)
        self.assertIn(
            "git cherry-pick --abort",
            normalize(read("docs/runbooks/ORCA_WORKFLOW.md")),
        )

    def test_execution_lead_owns_integration_conflicts(self) -> None:
        for path in (
            "AGENTS.md",
            "docs/ARCHITECTURE.md",
            "docs/runbooks/ORCA_WORKFLOW.md",
            "docs/decisions/ADR-003-lead-worker-git-integration-contract.md",
        ):
            self.assertIn(
                "the execution lead owns integration conflicts",
                normalize(read(path)).lower(),
                path,
            )

        lead = normalize(read(".agent/roles/execution-lead.md")).lower()
        self.assertIn("own every integration conflict", lead)
        self.assertIn("git cherry-pick --abort", lead)
        self.assertIn("condition 6", lead)

    def test_worker_result_must_be_committed(self) -> None:
        for path in (
            "AGENTS.md",
            ".agent/roles/worker.md",
            "docs/ARCHITECTURE.md",
            "docs/runbooks/ORCA_WORKFLOW.md",
            "docs/decisions/ADR-003-lead-worker-git-integration-contract.md",
        ):
            self.assertIn(
                "no uncommitted working-tree result is accepted",
                normalize(read(path)).lower(),
                path,
            )

    def test_worker_branch_is_retained_until_settlement(self) -> None:
        for path in (
            "AGENTS.md",
            "docs/ARCHITECTURE.md",
            "docs/runbooks/ORCA_WORKFLOW.md",
        ):
            normalized = normalize(read(path)).lower()
            self.assertIn(
                "worker worktree/branch must not be deleted until integration succeeds "
                "or the execution lead explicitly rejects the result",
                normalized,
                path,
            )
            self.assertIn("git objects", normalized, path)
            self.assertIn("recoverable", normalized, path)
            self.assertIn("refs/worker-results/<worker_task_id>", normalized, path)

        lead = normalize(read(".agent/roles/execution-lead.md")).lower()
        self.assertIn("refs/worker-results/<worker_task_id>", lead)
        self.assertIn("recoverable until success or explicit rejection", lead)

    def test_remote_worker_uses_fetchable_git_refs(self) -> None:
        architecture = normalize(read("docs/ARCHITECTURE.md")).lower()
        runbook = normalize(read("docs/runbooks/ORCA_WORKFLOW.md")).lower()
        adr = normalize(
            read("docs/decisions/ADR-003-lead-worker-git-integration-contract.md")
        ).lower()

        for path, document in (
            ("docs/ARCHITECTURE.md", architecture),
            ("docs/runbooks/ORCA_WORKFLOW.md", runbook),
            (
                "docs/decisions/ADR-003-lead-worker-git-integration-contract.md",
                adr,
            ),
        ):
            self.assertIn("fetchable", document, path)
        self.assertIn("git push", runbook)
        self.assertIn("git fetch", runbook)
        self.assertIn("exact returned sha", architecture)
        self.assertIn("git checkout -b <fresh_remote_worker_branch>", runbook)
        self.assertIn("git rev-list <integration_base_sha>..head", runbook)
        self.assertIn("git update-ref refs/worker-results/<worker_task_id>", runbook)
        self.assertIn("never use `reset --hard` or `checkout -b`", runbook)
        for path, document in (
            ("docs/ARCHITECTURE.md", architecture),
            ("docs/runbooks/ORCA_WORKFLOW.md", runbook),
        ):
            self.assertIn(
                "never exchange writable project directories between nodes",
                document,
                path,
            )

    def test_lead_validates_worker_ancestry_scope_and_linearity(self) -> None:
        architecture = normalize(read("docs/ARCHITECTURE.md"))
        runbook = normalize(read("docs/runbooks/ORCA_WORKFLOW.md"))

        for path, document in (
            ("docs/ARCHITECTURE.md", architecture),
            ("docs/runbooks/ORCA_WORKFLOW.md", runbook),
        ):
            for command in (
                "git merge-base --is-ancestor",
                "git rev-list --reverse",
                "git rev-list --merges",
            ):
                self.assertIn(command, document, path)
        self.assertIn(
            "every changed path is within authorized scope and reject every "
            "unexpected file",
            architecture.lower(),
        )
        self.assertIn(
            "checks every changed path against the authorized scope and rejects "
            "unexpected files",
            runbook.lower(),
        )

    def test_cherry_pick_provenance_and_empty_pick_are_explicit(self) -> None:
        for path in (
            "AGENTS.md",
            ".agent/roles/execution-lead.md",
            "docs/ARCHITECTURE.md",
            "docs/runbooks/ORCA_WORKFLOW.md",
            "docs/decisions/ADR-003-lead-worker-git-integration-contract.md",
        ):
            document = normalize(read(path))
            self.assertIn("git cherry-pick -x", document, path)
            self.assertIn("refs/worker-results/<worker_task_id>", document, path)
            self.assertIn("worker_commit_sha", document, path)
            self.assertIn("integrated_commit_sha", document, path)
            self.assertIn("git cherry-pick --skip", document, path)
            self.assertIn("--allow-empty", document, path)
            self.assertIn("ALREADY_PRESENT", document, path)

    def test_git_integration_escalations_use_closed_conditions(self) -> None:
        for path in (
            "AGENTS.md",
            "docs/ARCHITECTURE.md",
            "docs/runbooks/ORCA_WORKFLOW.md",
            "docs/decisions/ADR-003-lead-worker-git-integration-contract.md",
        ):
            document = normalize(read(path)).lower()
            self.assertIn("closed", document, path)
            self.assertIn("condition 5", document, path)
            self.assertIn("condition 6", document, path)
            self.assertIn("root", document, path)
            self.assertIn("redispatch", document, path)

    def test_execution_packet_git_fields_have_distinct_semantics(self) -> None:
        for path in (
            "AGENTS.md",
            ".agent/roles/root.md",
            "docs/ARCHITECTURE.md",
            "docs/runbooks/ORCA_WORKFLOW.md",
        ):
            document = normalize(read(path)).lower()
            for meaning in (
                "source ref",
                "target branch",
                "path boundary",
                "integrated-state",
                "immutable unit",
            ):
                self.assertIn(meaning, document, path)

    def test_orca_lineage_is_not_git_ancestry(self) -> None:
        statement = (
            "orca parent/child lineage is orchestration provenance, "
            "not proof of git ancestry"
        )
        for path in (
            "AGENTS.md",
            "docs/ARCHITECTURE.md",
            "docs/runbooks/ORCA_WORKFLOW.md",
            "docs/decisions/ADR-003-lead-worker-git-integration-contract.md",
        ):
            self.assertIn(statement, normalize(read(path)).lower(), path)

    def test_controller_does_not_duplicate_orca_lifecycle(self) -> None:
        agents = read("AGENTS.md")
        adr = normalize(read("docs/decisions/ADR-001-orca-first-execution-plane.md"))

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

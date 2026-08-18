from pathlib import Path
import json
import re
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


def fenced_code_blocks(document: str) -> list[str]:
    return re.findall(r"```[^\n]*\n(.*?)```", document, flags=re.DOTALL)


# ---------------------------------------------------------------------------
# Defect-class enforcement: the architecture must never bind a provider/model-pool
# name to an agent role anywhere in LIVE text (not merely in one quoted section).
# The historical decision records ADR-001/002/003 are explicitly excluded by path
# below; everything else on disk counts as live architecture text.
# ---------------------------------------------------------------------------
# Provider/model-pool names (pool names, not HARNESS class names). Harness classes
# are named claude_code / codex_cli / pi and are deliberately NOT in this set, so
# legitimate harness-class vocabulary is expressible. "Pi" is a harness, not a pool,
# and is likewise absent.
PROVIDER_NAME_RE = r"(?:claude|codex|deepseek|gemini|kimi|minimax|ark|volcengine)"
# Role nouns that must never be directly qualified by a provider name.
ROLE_NOUN_RE = (
    r"(?:root|cognitive control plane|execution lead|engineering control plane|"
    r"execution worker|reviewer)"
)
# Defect class patterns, mirroring the forms the re-review reproduced:
#   "<Provider> <Role>"            (immediate binding, e.g. "Codex Execution Lead")
#   "default ... agent: <Provider>"  (e.g. "default engineering agent: Codex (all tasks)")
#   "preferred provider: <Provider>"
#   "<Role> ... provider: <Provider>"
# The immediate binding requires whitespace (never an underscore), so the HARNESS names
# claude_code / codex_cli never match, and any intervening QUALIFIER (Premium,
# Standard/Fast, "Claude Code") breaks the role adjacency, which is what preserves the
# legitimate harness-class phrases "Codex Premium escalation / Lead" and "Pi Standard/Fast".
PROVIDER_ROLE_BINDING_RE = re.compile(
    r"\b" + PROVIDER_NAME_RE + r"\s+" + ROLE_NOUN_RE + r"\b", flags=re.IGNORECASE
)
DEFAULT_AGENT_BINDING_RE = re.compile(
    r"\bdefault\b[^.\n]{0,60}?\bagent\b[^.\n]{0,12}?\s*[:=]\s*"
    + PROVIDER_NAME_RE + r"\b",
    flags=re.IGNORECASE,
)
PREFERRED_PROVIDER_BINDING_RE = re.compile(
    r"\bpreferred provider\b[^.\n]{0,8}?\s*[:=]\s*" + PROVIDER_NAME_RE + r"\b",
    flags=re.IGNORECASE,
)
ROLE_PROVIDER_BINDING_RE = re.compile(
    ROLE_NOUN_RE + r"\b[^.\n]{0,60}?provider\b[^.\n]{0,12}?\s*[:=]\s*"
    + PROVIDER_NAME_RE + r"\b",
    flags=re.IGNORECASE,
)
PROVIDER_ROLE_BINDINGS = (
    ("provider-role", PROVIDER_ROLE_BINDING_RE),
    ("default-agent", DEFAULT_AGENT_BINDING_RE),
    ("preferred-provider", PREFERRED_PROVIDER_BINDING_RE),
    ("role-provider", ROLE_PROVIDER_BINDING_RE),
)


def live_architecture_documents() -> list[Path]:
    """Every live md/yaml file that documents current architecture or policy.

    Genuinely historical decision records (ADR-001/002/003) are excluded by path so
    their retro-recorded provider preferences do not trip the live invariant.
    """
    historical = {
        ROOT / "docs" / "decisions" / "ADR-001-orca-first-execution-plane.md",
        ROOT / "docs" / "decisions" / "ADR-002-cognitive-and-engineering-control-planes.md",
        ROOT / "docs" / "decisions" / "ADR-003-lead-worker-git-integration-contract.md",
    }
    paths = [ROOT / "AGENTS.md", ROOT / "README.md", ROOT / "CLAUDE.md"]
    for directory in (ROOT / "docs", ROOT / ".agent"):
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".yaml", ".yml"} and path not in historical:
                paths.append(path)
    return paths


WRITABLE_WORKER_LIFECYCLE_DOCUMENTS = (
    "AGENTS.md",
    ".agent/roles/execution-lead.md",
    "docs/ARCHITECTURE.md",
    "docs/runbooks/ORCA_WORKFLOW.md",
    "docs/decisions/ADR-003-lead-worker-git-integration-contract.md",
)

SUPERVISED_ROOT_TO_LEAD_DOCUMENTS = (
    "AGENTS.md",
    ".agent/roles/root.md",
    "docs/ARCHITECTURE.md",
    "docs/runbooks/ORCA_WORKFLOW.md",
)

WORKER_START_REQUIREMENT = """
Every supervised writable Worker MUST be launched through
`orca orchestration worker-start`.
"""

EXPLICIT_BASE_REQUIREMENT = """
The launch MUST explicitly select the required Git base using the installed version's
supported mechanism, currently `--base-branch <integration_base_ref>`; confirm that
mechanism against the version-matched installed Orca guide before dispatch.
"""

LOW_LEVEL_LAUNCH_PROHIBITION = """
For supervised writable Workers, the Execution Lead MUST NOT use `worktree create` plus
`orchestration dispatch --inject` as the launch path; that low-level path may create a
dispatch visible to `dispatch-show` without registering the Worker in Orca's `worker-*`
lifecycle registry, so `worker-release` cannot settle it.
"""

ROOT_TO_LEAD_WORKER_START_REQUIREMENT = """
Every supervised writable Root-to-Execution-Lead dispatch MUST be launched through
`orca orchestration worker-start`; low-level `worktree create` plus
`orchestration dispatch --inject` does not register the Lead in Orca's `worker-*` lifecycle
registry, so the Root cannot settle it with `worker-release`.
"""

EXISTING_WORKTREE_BASE_REQUIREMENT = """
When `worker-start` targets `current`, an existing worktree, or `--terminal <handle>`, the
installed CLI rejects `--base-branch`; explicit base selection is satisfied only by the
guarded pre-dispatch HEAD equality proof recorded in the assignment.
"""

RETRY_BASE_REQUIREMENT = """
`--retry-of <dispatch_id>` does not inherit placement: repeat the intended
`--on`/`--worktree` and `--agent`/`--terminal` choices, and either repeat
`--base-branch <integration_base_ref>` for a new worktree or rerun and record the guarded
equality proof for reuse.
"""

WORKER_RELEASE_REQUIREMENT = """
Settlement MUST include successful `worker-release` before result-delivery acknowledgment
and before the Worker branch/worktree is retained or removed according to settlement
policy.
"""

RELEASE_BEFORE_ACK_REASON = """
Orca replays an unacknowledged Delivery, so the writable Worker terminal MUST be
successfully released before the batch is acknowledged.
"""

WRITABLE_WORKER_LIFECYCLE = """
Lead creates Worker through `worker-start` with explicit base
  → Worker verifies `HEAD == integration_base_sha` before tracked edits
  → Worker implements / verifies / commits
  → immutable result packet
  → `worker_done`
  → Lead validates result
  → Lead cherry-picks ordered commits
  → Lead verifies integrated state
  → `worker-release` succeeds
  → result delivery acknowledged
  → Worker branch/worktree retained or removed per settlement policy
"""


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
        harnesses = routing["harnesses"]
        for harness in ("pi", "claude_code", "codex_cli"):
            self.assertIn(harness, harnesses)
        # pi is a harness, not a model pool
        self.assertNotIn("pi", routing["model_pools"])
        for pool in (
            "claude",
            "codex",
            "deepseek",
            "volcengine_ark_coding_plan",
            "min_max",
            "kimi",
            "gemini",
        ):
            self.assertIn(pool, routing["model_pools"])

        defaults = routing["defaults"]
        self.assertEqual("claude_code", defaults["preferred_harness"]["root"])
        self.assertEqual("pi", defaults["preferred_harness"]["execution_lead"])
        self.assertEqual("pi", defaults["execution_lead"]["standard_harness"])
        self.assertEqual(
            "codex_cli", defaults["execution_lead"]["premium_escalation_harness"]
        )

        # The Execution Lead defaults to Pi (Standard/Fast); Codex is the premium
        # escalation and appears only for high-risk/difficult routing, never as a
        # per-role provider binding.
        self.assertEqual("pi", routing["risk"]["low"]["preferred_harness"]["execution_lead"])
        self.assertEqual(
            "pi", routing["risk"]["medium"]["preferred_harness"]["execution_lead"]
        )
        self.assertEqual(
            "codex_cli", routing["risk"]["high"]["preferred_harness"]["execution_lead"]
        )
        self.assertEqual(
            "cross_provider_or_human_visible_residual_risk_waiver",
            routing["risk"]["high"]["reviewer_provider_diversity"],
        )
        self.assertEqual("required", routing["risk"]["high"]["independent_review"])
        self.assertNotIn("preferred_worker", routing)
        self.assertNotIn("preferred_root", routing)
        self.assertNotIn("preferred_execution_lead", routing)

        principles = routing["principles"]
        for principle in (
            "route_by_role_then_harness_then_model_pool",
            "root_selects_the_execution_lead_harness_class",
            "pi_is_the_default_execution_lead_harness_for_well_scoped_low_medium_work",
            "codex_is_a_premium_execution_lead_escalation_not_a_mandatory_binding",
            "root_reentry_is_limited_to_the_closed_escalation_list",
            "do_not_permanently_bind_provider_to_role",
            "claude_is_default_root_preference",
        ):
            self.assertIn(principle, principles)
        self.assertNotIn(
            "normal_codex_execution_usage_substantially_exceeds_claude_root_usage",
            principles,
        )
        self.assertNotIn(
            "codex_is_default_root_preference",
            principles,
        )
        self.assertNotIn(
            "codex_is_default_execution_lead_preference",
            principles,
        )
        self.assertNotIn(
            "deepseek_is_preferred_for_well_scoped_worker_tasks",
            principles,
        )
        self.assertIn("levels", parsed["risk.yaml"])
        self.assertIn("execution_lead_failure", parsed["retry.yaml"])
        self.assertIn("catalog", parsed["capabilities.yaml"])
        self.assertIn("principles", parsed["efficiency.yaml"])

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
                "EXECUTION HARNESS",
                "MODEL POLICY",
                "CAPABILITY PROFILE",
                "EFFICIENCY PROFILE",
                "CONTEXT BUDGET",
                "OUTPUT MODE",
                "SESSION POLICY",
                "COMPACTION POLICY",
                "EXECUTION / RETRY BUDGET",
                "ESCALATION THRESHOLD",
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

        # v2.1: execution-cost metrics supersede the provider-usage objective while
        # keeping the ADR-002 computation and lineage.
        for metric in (
            "execution_vs_root_usage_share",
            "premium_vs_low_cost_execution_share",
            "context_and_output_cost_per_successful_task",
        ):
            self.assertIn(metric, architecture)
        self.assertIn("root_vs_execution_usage_share", architecture)
        self.assertIn("lineage", architecture)

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

    def test_supervised_writable_worker_prohibits_low_level_launch(self) -> None:
        permissive_low_level_dispatch = re.compile(
            r"(?i)(?:\b(?:may|can|should|or)\b|允许|可以|或)"
            r".{0,100}(?:low-level|低层).{0,100}\bdispatch\b"
        )
        for path in WRITABLE_WORKER_LIFECYCLE_DOCUMENTS:
            raw_document = read(path)
            document = normalize(raw_document)
            self.assertIn(normalize(LOW_LEVEL_LAUNCH_PROHIBITION), document, path)
            self.assertIsNone(
                permissive_low_level_dispatch.search(document),
                path,
            )
            for code_block in fenced_code_blocks(raw_document):
                normalized_block = normalize(code_block).lower()
                prohibited_combination = (
                    "worktree create" in normalized_block
                    and "dispatch" in normalized_block
                    and "--inject" in normalized_block
                )
                self.assertFalse(prohibited_combination, path)

    def test_supervised_root_to_lead_requires_worker_start(self) -> None:
        for path in SUPERVISED_ROOT_TO_LEAD_DOCUMENTS:
            self.assertIn(
                normalize(ROOT_TO_LEAD_WORKER_START_REQUIREMENT),
                normalize(read(path)),
                path,
            )

    def test_supervised_writable_worker_requires_worker_start(self) -> None:
        for path in WRITABLE_WORKER_LIFECYCLE_DOCUMENTS:
            self.assertIn(
                normalize(WORKER_START_REQUIREMENT),
                normalize(read(path)),
                path,
            )

        local_launch = normalize(
            """
            ORCA orchestration worker-start --task <worker_task_id> \\
            --worktree new-child --name <worker_name> \\
            --base-branch <integration_base_ref>
            """
        )
        for path in ("docs/ARCHITECTURE.md", "docs/runbooks/ORCA_WORKFLOW.md"):
            self.assertEqual(2, normalize(read(path)).count(local_launch), path)

    def test_supervised_writable_worker_requires_explicit_base_selection(self) -> None:
        for path in WRITABLE_WORKER_LIFECYCLE_DOCUMENTS:
            self.assertIn(
                normalize(EXPLICIT_BASE_REQUIREMENT),
                normalize(read(path)),
                path,
            )

        remote_launch = normalize(
            """
            ORCA orchestration worker-start --task <worker_task_id> \\
            --on <saved-environment> --worktree new-top-level \\
            --repo <exact_remote_repo_selector> --name <worker_name> \\
            --base-branch <integration_base_ref>
            """
        )
        for path in ("docs/ARCHITECTURE.md", "docs/runbooks/ORCA_WORKFLOW.md"):
            self.assertIn(remote_launch, normalize(read(path)), path)

        for path in (
            "AGENTS.md",
            ".agent/roles/execution-lead.md",
            "docs/ARCHITECTURE.md",
            "docs/runbooks/ORCA_WORKFLOW.md",
        ):
            document = normalize(read(path))
            self.assertIn(
                normalize(EXISTING_WORKTREE_BASE_REQUIREMENT),
                document,
                path,
            )
            self.assertIn(normalize(RETRY_BASE_REQUIREMENT), document, path)

    def test_supervised_writable_worker_requires_release_settlement(self) -> None:
        expected_lifecycle = normalize(WRITABLE_WORKER_LIFECYCLE)
        expected_occurrences = {
            "AGENTS.md": 1,
            ".agent/roles/execution-lead.md": 1,
            "docs/ARCHITECTURE.md": 2,
            "docs/runbooks/ORCA_WORKFLOW.md": 1,
            "docs/decisions/ADR-003-lead-worker-git-integration-contract.md": 1,
        }
        for path in WRITABLE_WORKER_LIFECYCLE_DOCUMENTS:
            document = normalize(read(path))
            self.assertIn(normalize(WORKER_RELEASE_REQUIREMENT), document, path)
            self.assertIn(normalize(RELEASE_BEFORE_ACK_REASON), document, path)
            self.assertEqual(
                expected_occurrences[path],
                document.count(
                    "Lead creates Worker through `worker-start` with explicit base"
                ),
                path,
            )
            self.assertEqual(
                expected_occurrences[path],
                document.count(expected_lifecycle),
                path,
            )

        expected_command_blocks = {
            "docs/ARCHITECTURE.md": 1,
            "docs/runbooks/ORCA_WORKFLOW.md": 2,
        }
        for path, expected_count in expected_command_blocks.items():
            blocks = [
                normalize(block)
                for block in fenced_code_blocks(read(path))
                if "worker-release --dispatch" in block and "check --ack" in block
            ]
            self.assertEqual(expected_count, len(blocks), path)
            for block in blocks:
                self.assertLess(
                    block.index("worker-release --dispatch"),
                    block.index("check --ack"),
                    path,
                )

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


    def test_pi_is_modeled_as_harness_not_model_or_provider(self) -> None:
        routing = self.load_yaml(".agent/policies/routing.yaml")
        self.assertIn("pi", routing["harnesses"])
        self.assertNotIn("pi", routing["model_pools"])
        pi_harness = read(".agent/harnesses/pi.md")
        lower = pi_harness.lower()
        self.assertIn("harness", lower)
        self.assertIn("runtime", lower)
        self.assertIn("model/provider pool", lower)
        self.assertNotIn("pi is a fixed model", lower)
        self.assertIn("worker-start", pi_harness)

    def test_worker_role_is_not_bound_to_deepseek(self) -> None:
        worker = read(".agent/roles/worker.md")
        self.assertIn("bound to any one model/provider pool", worker)
        self.assertIn("not", worker.split("bound to any one")[0])
        deepseek = read(".agent/providers/deepseek.md")
        self.assertIn("Worker *role* is not bound to DeepSeek", deepseek)
        self.assertIn("not a role and not a permanent binding", deepseek)
        routing = self.load_yaml(".agent/policies/routing.yaml")
        self.assertIn("deepseek", routing["model_pools"])
        self.assertNotIn("preferred_worker", routing)
        self.assertNotIn(
            "deepseek_is_preferred_for_well_scoped_worker_tasks",
            routing["principles"],
        )
        architecture = read("docs/ARCHITECTURE.md")
        self.assertNotIn("preferred provider", architecture)
        self.assertNotIn("DeepSeek Execution Worker", architecture)

    def test_codex_is_premium_escalation_not_mandatory_lead(self) -> None:
        routing = self.load_yaml(".agent/policies/routing.yaml")
        self.assertEqual(
            "pi", routing["defaults"]["execution_lead"]["standard_harness"]
        )
        self.assertEqual(
            "codex_cli",
            routing["defaults"]["execution_lead"]["premium_escalation_harness"],
        )
        self.assertNotIn(
            "codex_is_default_execution_lead_preference",
            routing["principles"],
        )
        lead = normalize(read(".agent/roles/execution-lead.md"))
        self.assertIn("Pi Standard/Fast Lead", lead)
        self.assertIn("Codex Premium Lead", lead)
        self.assertIn("permanent binding", lead)
        codex_cli = normalize(read(".agent/harnesses/codex-cli.md"))
        self.assertIn("It is **not** the mandatory Execution Lead for every task", codex_cli)
        self.assertIn("Premium Execution Lead", codex_cli)
        adr = normalize(read("docs/decisions/ADR-004-role-harness-model-capability-separation.md"))
        self.assertIn("Pi Standard/Fast Lead", adr)
        self.assertIn("Codex Premium Lead", adr)
        architecture = read("docs/ARCHITECTURE.md")
        self.assertNotIn("preferred provider: Codex", architecture)
        # Live architecture diagrams express ROLE + HARNESS CLASS, not a per-role
        # provider binding, and the document is actually read (not asserted from memory).
        self.assertIn("Pi Standard/Fast default → Codex Premium escalation", architecture)
        self.assertIn("Claude Code harness default", architecture)

    def test_no_live_provider_as_role_binding_anywhere(self) -> None:
        """The no-provider-as-role invariant holds across ALL live architecture text.

        Earlier B1 assertions pinned literal strings ("preferred provider:",
        "DeepSeek Execution Worker"), so a freshly-worded provider-as-role binding such
        as "default engineering agent: Codex (all tasks)" slipped straight through green
        CI. This test targets the defect CLASS: it scans every live document for a
        provider/model-pool name bound to a role noun in any of the reproduced forms.
        Harness-class vocabulary remains expressible because harness names are
        underscore-connected (claude_code, codex_cli; "Pi" is a harness, not a pool)
        and an intervening qualifier (Premium / Standard/Fast / "Claude Code") breaks
        the adjacency, which is the very distinction the allowlist exists to preserve.
        """
        failures = []
        for path in live_architecture_documents():
            content = path.read_text(encoding="utf-8", errors="replace")
            for name, pattern in PROVIDER_ROLE_BINDINGS:
                for match in pattern.finditer(content):
                    snippet = content[
                        max(0, match.start() - 40): match.end() + 40
                    ].replace("\n", " ")
                    failures.append(f"{name} binding in {path.relative_to(ROOT)}: {snippet!r}")
        if failures:
            self.fail(
                "Live architecture text binds a provider name to an agent role:\n"
                + "\n".join(failures)
            )

    def test_root_selects_execution_lead_harness(self) -> None:
        routing = self.load_yaml(".agent/policies/routing.yaml")
        self.assertIn(
            "root_selects_the_execution_lead_harness_class", routing["principles"]
        )
        root = normalize(read(".agent/roles/root.md"))
        self.assertIn("Select the Execution Lead harness class per task", root)
        agents = read("AGENTS.md")
        self.assertIn("execution lead harness", normalize(agents).lower())
        self.assertIn("EXECUTION HARNESS", agents)
        self.assertIn("EXECUTION HARNESS", read("docs/ARCHITECTURE.md"))

    def test_capability_profile_catalog_exists_and_is_referenced(self) -> None:
        caps = self.load_yaml(".agent/policies/capabilities.yaml")
        catalog = caps["catalog"]
        for capability in (
            "repo",
            "git",
            "python-test",
            "orca-cli",
            "orchestration",
            "worker-integration",
            "github",
            "system-inspection",
            "ssh",
            "tailscale",
            "quantitative-analysis",
        ):
            self.assertIn(capability, catalog)
        self.assertIn("least_capability", caps)
        self.assertIn("progressive_disclosure", caps)
        self.assertIn("profiles", caps)
        agents = read("AGENTS.md")
        self.assertIn(".agent/policies/capabilities.yaml", agents)
        self.assertIn("CAPABILITY PROFILE", agents)
        self.assertIn("CAPABILITY PROFILE", read("docs/ARCHITECTURE.md"))

    def test_execution_packet_declares_harness_model_capability_efficiency_fields(
        self,
    ) -> None:
        agents = read("AGENTS.md")
        architecture = read("docs/ARCHITECTURE.md")
        for field in (
            "EXECUTION HARNESS",
            "MODEL POLICY",
            "CAPABILITY PROFILE",
            "EFFICIENCY PROFILE",
            "CONTEXT BUDGET",
            "OUTPUT MODE",
            "SESSION POLICY",
            "COMPACTION POLICY",
            "EXECUTION / RETRY BUDGET",
            "ESCALATION THRESHOLD",
        ):
            self.assertIn(field, agents)
            self.assertIn(field, architecture)

    def test_efficiency_policy_principles_exist(self) -> None:
        efficiency = self.load_yaml(".agent/policies/efficiency.yaml")
        principles = efficiency["principles"]
        self.assertGreaterEqual(len(principles), 10)
        for principle in (
            "use_the_cheapest_capable_resource",
            "prefer_deterministic_tools_tests_and_evals_before_model_calls",
            "never_narrate_routine_tool_usage",
            "use_terse_structured_agent_to_agent_reporting",
            "minimize_always_loaded_repository_instructions",
        ):
            self.assertIn(principle, principles)

    def test_terse_reporting_principle_and_clarity_exceptions(self) -> None:
        efficiency = self.load_yaml(".agent/policies/efficiency.yaml")
        self.assertEqual(
            "STATUS/CHANGED/VERIFY/COMMIT/BLOCKERS/UNCERTAINTY/NEXT",
            efficiency["report_block"]["header"],
        )
        overrides = efficiency["clarity_overrides"]
        for item in (
            "architecture_decisions",
            "acceptance_criteria",
            "security_warnings",
            "destructive_operations",
            "human_approval_requests",
            "unresolved_ambiguity",
            "high_risk_findings",
        ):
            self.assertIn(item, overrides)
        agents = read("AGENTS.md")
        self.assertIn("STATUS / CHANGED / VERIFY / COMMIT / BLOCKERS /", agents)
        self.assertIn("never narrate routine tool usage", agents)
        architecture = read("docs/ARCHITECTURE.md")
        # Assert the specific clarity-override statement, not a bare substring that
        # could match unrelated text.
        self.assertIn("Clarity override", architecture)

    def test_caveman_is_not_a_dependency(self) -> None:
        # Caveman must not be a declared dependency in any manifest / requirements /
        # lockfile / install instruction that exists in this repository.
        manifest_names = (
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "Pipfile",
            "Pipfile.lock",
            "package.json",
            "package-lock.json",
        )
        for name in manifest_names:
            path = ROOT / name
            if path.exists():
                self.assertNotIn(
                    "caveman", path.read_text(encoding="utf-8").lower(), name
                )

        # Not a routing requirement.
        routing = self.load_yaml(".agent/policies/routing.yaml")
        self.assertNotIn("caveman", json.dumps(routing).lower())

        # Not an execution-policy requirement nor a role/harness profile requirement.
        efficiency = self.load_yaml(".agent/policies/efficiency.yaml")
        self.assertNotIn("caveman", json.dumps(efficiency).lower())
        for directory in (ROOT / ".agent" / "roles", ROOT / ".agent" / "harnesses"):
            if directory.exists():
                for path in directory.rglob("*"):
                    if path.is_file():
                        self.assertNotIn(
                            "caveman",
                            path.read_text(encoding="utf-8").lower(),
                            str(path.relative_to(ROOT)),
                        )

        # Not a required or installed Skill or Extension. (No skill/extension shorthand
        # is present in the repo's .agent/skills; nothing installs Caveman.)
        skills_dir = ROOT / ".agent" / "skills"
        if skills_dir.exists():
            for path in skills_dir.rglob("*"):
                if path.is_file():
                    self.assertNotIn(
                        "caveman",
                        path.read_text(encoding="utf-8").lower(),
                        str(path.relative_to(ROOT)),
                    )

        # Terse reporting is a native principle that stands alone without Caveman.
        self.assertIn(
            "use_terse_structured_agent_to_agent_reporting",
            efficiency["principles"],
        )

    def test_execution_cost_metrics_replace_provider_usage_objective(self) -> None:
        architecture = read("docs/ARCHITECTURE.md")
        steward = read(".agent/roles/platform-steward.md")
        adr = read("docs/decisions/ADR-004-role-harness-model-capability-separation.md")
        for metric in (
            "execution_vs_root_usage_share",
            "premium_vs_low_cost_execution_share",
            "context_and_output_cost_per_successful_task",
        ):
            self.assertIn(metric, architecture)
            self.assertIn(metric, steward)
            self.assertIn(metric, adr)
        # The retired objective is referenced as retired, not as current policy.
        self.assertIn("Codex usage > Claude usage", architecture)
        self.assertIn("Codex usage greater than Claude usage", adr)
        routing = self.load_yaml(".agent/policies/routing.yaml")
        self.assertNotIn(
            "normal_codex_execution_usage_substantially_exceeds_claude_root_usage",
            routing["principles"],
        )
        self.assertNotIn(
            "normal_codex_execution_usage_substantially_exceeds_claude_root_usage",
            adr,
        )

    def test_reasoning_effort_is_not_a_token_savings_lever(self) -> None:
        efficiency = self.load_yaml(".agent/policies/efficiency.yaml")

        # Every efficiency profile keeps HIGH reasoning effort; no profile may pair a
        # low-cost dispatch with below-high reasoning. The `typical` (standard-effort)
        # profile was removed to close the residual token-saving hole. Reasoning effort
        # is a correctness parameter, not a cost lever.
        self.assertNotIn("typical", efficiency["profiles"])
        for name, profile in efficiency["profiles"].items():
            self.assertEqual("high", profile.get("reasoning", ""), name)

        # efficiency.yaml names reasoning/thinking effort as excluded from cost levers.
        self.assertIn(
            "reasoning_effort_is_not_a_token_savings_lever", efficiency["principles"]
        )
        text = read(".agent/policies/efficiency.yaml").lower()
        self.assertIn("not a token-savings lever", text)
        self.assertIn("not a cost parameter", text)

        # The approved cost levers are enumerated.
        cost_levers = efficiency["cost_levers"]
        for lever in (
            "cheaper_model_routing",
            "targeted_context",
            "progressive_disclosure_skills",
            "task_bounded_sessions",
            "terse_reporting",
            "deterministic_verification",
            "premium_model_avoidance",
        ):
            self.assertIn(lever, cost_levers)

    def test_efficiency_policy_does_not_weaken_high_risk_guardrails(self) -> None:
        efficiency = read(".agent/policies/efficiency.yaml")
        self.assertIn("NOT weaken the HIGH-risk", efficiency)
        self.assertIn("risk.yaml", efficiency)
        self.assertIn("human-gate", efficiency)
        risk = read(".agent/policies/risk.yaml")
        self.assertIn("independent_review: required", risk)
        self.assertIn("controller_security_and_safety_policy", risk)
        routing = read(".agent/policies/routing.yaml")
        self.assertIn(
            "reviewer_provider_diversity: "
            "cross_provider_or_human_visible_residual_risk_waiver",
            routing,
        )

    def test_validated_lifecycle_invariants_survive_v21(self) -> None:
        for path in WRITABLE_WORKER_LIFECYCLE_DOCUMENTS:
            document = normalize(read(path))
            self.assertIn(normalize(WORKER_START_REQUIREMENT), document, path)
            self.assertIn(normalize(EXPLICIT_BASE_REQUIREMENT), document, path)
            self.assertIn(normalize(LOW_LEVEL_LAUNCH_PROHIBITION), document, path)
            self.assertIn(normalize(WORKER_RELEASE_REQUIREMENT), document, path)
            self.assertIn(normalize(RELEASE_BEFORE_ACK_REASON), document, path)
            self.assertIn("git cherry-pick -x", document, path)
            self.assertIn("integration_base_sha", document, path)
            self.assertIn("git rev-parse HEAD", document, path)
        for path in SUPERVISED_ROOT_TO_LEAD_DOCUMENTS:
            self.assertIn(
                normalize(ROOT_TO_LEAD_WORKER_START_REQUIREMENT),
                normalize(read(path)),
                path,
            )
        for path in ("AGENTS.md", ".agent/roles/execution-lead.md",
                     "docs/ARCHITECTURE.md"):
            document = normalize(read(path)).lower()
            self.assertIn("closed", document, path)
            self.assertIn("condition 6", document, path)
            self.assertIn("re-entry", document, path)


if __name__ == "__main__":
    unittest.main()

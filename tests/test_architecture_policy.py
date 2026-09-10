"""Repository declaration guards, not tests of Herdr runtime enforcement.

Run normally against working files; V4_TEST_TREE=index reads the staged future tree.
Prose guards recognize bounded assertion forms, not arbitrary natural-language meaning.
Historical decisions are preserved and checked for presence, not scanned as live policy.
"""
import copy
import importlib
import os
from pathlib import Path
import re
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TREE = os.environ.get("V4_TEST_TREE", "working")
ROLES = {"root", "lead", "delegate", "reviewer"}
PROCEDURES = {f".agent/procedures/{name}.md" for name in
              ("checkpoint", "delegate", "review", "writable-work")}
AGENT_FILES = PROCEDURES | {".agent/policy.yaml", ".agent/capabilities.md"}
ADRS = {
    "docs/decisions/ADR-001-orca-first-execution-plane.md",
    "docs/decisions/ADR-002-cognitive-and-engineering-control-planes.md",
    "docs/decisions/ADR-003-lead-worker-git-integration-contract.md",
    "docs/decisions/ADR-004-role-harness-model-capability-separation.md",
    "docs/decisions/ADR-005-instruction-diet-and-adaptive-premium-reasoning.md",
    "docs/decisions/ADR-006-hermes-retirement.md",
    "docs/decisions/ADR-007-review-loop-ownership.md",
    "docs/decisions/ADR-008-v4-cognitive-architecture-and-herdr-runtime.md",
}
REQUIRED = AGENT_FILES | ADRS | {
    "AGENTS.md", "CLAUDE.md", "README.md", ".gitignore", "docs/ARCHITECTURE.md",
    "docs/PROJECT_STATE.md", "docs/ROADMAP.md", "docs/HISTORY.md", "docs/NODES.md",
    "docs/inventory/agent-desktop.md", "docs/runbooks/REMOTE_WORK.md",
    "tests/test_architecture_policy.py", ".github/workflows/architecture-policy.yml",
}
# Exact current normative homes. State, plans, inventory and historical records have
# different responsibilities; their presence does not make old claims live policy.
NORMATIVE = AGENT_FILES | {
    "AGENTS.md", "CLAUDE.md", "README.md", "docs/ARCHITECTURE.md",
    "docs/NODES.md", "docs/runbooks/REMOTE_WORK.md",
}
CHECKPOINT = [
    "ROOT_ID", "CHECKPOINT_GENERATION / TIMESTAMP", "GOAL", "ACCEPTANCE",
    "CURRENT_STATE", "DECISIONS_MADE", "OPEN_QUESTIONS / BLOCKERS",
    "ACTIVE_CHILD_ROOTS / LEADS", "IMPORTANT_EVIDENCE_POINTERS", "NEXT_ACTION",
]
RETURN = ["STATUS", "RESULT", "EVIDENCE", "BLOCKERS", "UNCERTAINTY", "ARTIFACT"]


def git(*args):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, text=True,
                              capture_output=True, check=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError("Git inspection failed; refusing a reduced validation surface") from exc


def tracked_files():
    if TREE not in {"working", "index"}:
        raise RuntimeError("V4_TEST_TREE must be working or index")
    paths = set(filter(None, git("ls-files", "-z").split("\0")))
    if not paths:
        raise RuntimeError("Git returned an empty tracked tree")
    if TREE == "working":
        # Explicit pending deletions participate in pre-stage validation. Missing
        # required canonical files still fail the required-surface check below.
        paths -= set(git("diff", "--name-only", "--diff-filter=D", "-z").split("\0"))
    return paths


def read(path):
    return git("show", f":{path}") if TREE == "index" else (ROOT / path).read_text(encoding="utf-8")


def load_policy():
    try:
        yaml = importlib.import_module("yaml")
    except ImportError as exc:
        raise RuntimeError("PyYAML is required: install PyYAML before running this suite") from exc
    policy = yaml.safe_load(read(".agent/policy.yaml"))
    if not isinstance(policy, dict):
        raise ValueError("Canonical policy must parse as a YAML mapping")
    return policy


def plain(text):
    return re.sub(r"\s+", " ", re.sub(r"[`*]", "", text)).strip().lower()


def section(document, title):
    # Match semantic section titles, ignoring heading level, numbering and emphasis.
    parts = re.split(r"(?m)^#{1,6}\s+(.+)$", document)
    for heading, body in zip(parts[1::2], parts[2::2]):
        if re.sub(r"^\d+\.\s*", "", plain(heading)) == title.lower():
            return body
    raise AssertionError(f"Missing canonical section: {title}")


def blocks(text):
    return [[re.sub(r"\s+", " ", line.strip()) for line in body.splitlines() if line.strip()]
            for body in re.findall(r"```[^\n]*\n(.*?)```", text, re.S)]


def require(text, *patterns):
    """Check section-local relationships; whitespace and Markdown are irrelevant."""
    normalized = plain(text)
    for pattern in patterns:
        if not re.search(pattern, normalized):
            raise AssertionError(f"Missing obligation matching {pattern!r}")


def keys(node):
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from keys(value)
    elif isinstance(node, list):
        for value in node:
            yield from keys(value)


ROLE = r"\b(root|lead|delegate|reviewer)\b"
TECH = r"\b(claude(?:[ _-]+code)?|codex(?:[ _-]+cli)?|pi|deepseek|gemini|kimi|minimax|gpt(?:[ -]?\d[\w.-]*)?(?:[ -]+astra)?)\b"
# Assignment operators are deliberate: merely mentioning a harness alongside a role,
# or describing a selectable capability, is not a permanent assignment.
BINDINGS = [
    rf"{ROLE}\s*(?:role\s*)?(?:[:=→]|->)\s*{TECH}",
    rf"{ROLE}\s+(?:must|always)\s+(?:use|uses|run on)\s+{TECH}",
    rf"{TECH}\s*(?:[:=→]|->)\s*{ROLE}",
    rf"{ROLE}[ \t-]+{TECH}", rf"{TECH}[ \t-]+{ROLE}",
    rf"{ROLE}\s+(?:is|are)\s+(?:always\s+)?(?:the\s+)?{TECH}",
    rf"{ROLE}\s+(?:is\s+)?(?:assigned|bound)\s+to\s+(?:the\s+)?{TECH}",
    rf"{ROLE}\s+(?:is\s+)?(?:always\s+)?run\s+by\s+{TECH}",
    rf"{TECH}(?:\s+harness)?\s+(?:is\s+)?(?:always\s+)?(?:the\s+)?(?:default\s+)?{ROLE}",
    rf"{TECH}(?:\s+harness)?\s+(?:is\s+)?(?:assigned\s+to|the\s+default\s+(?:harness\s+)?for)\s+(?:the\s+)?{ROLE}",
    rf"{ROLE}\s*(?:是|绑定(?:到|于)?|永久绑定(?:到|于)?)\s*{TECH}",
    rf"{TECH}\s*(?:是|绑定(?:到|于)?|永久绑定(?:到|于)?)\s*{ROLE}",
    rf"{ROLE}\s+(?:provider|harness)\s*[:=]\s*{TECH}",
    rf"{ROLE}\s*\n\s*{TECH}(?:\s+harness)?\s*(?:\n|$)",
    rf"\|\s*{ROLE}\s*\|\s*{TECH}(?:\s+harness)?\s*\|",
]


def binding_claims(text):
    findings = []
    text = re.sub(r"[`*]", "", text)
    for paragraph in re.split(r"\n\s*\n", text):
        for pattern in BINDINGS:
            findings.extend(m.group(0) for m in re.finditer(pattern, paragraph, re.I))
    return findings


def current_claims(text):
    # Scan assertion clauses, not historical/negative vocabulary anywhere in a file.
    findings = []
    for clause in re.split(r"[.!?。;；\n]", plain(text)):
        for pattern in (
            r"orca\s+is\s+(?:the\s+)?(?:primary\s+)?(?:execution|review)\s+plane",
            r"hermes(?: supervisor)?\s+is\s+(?:the\s+)?(?:current\s+)?(?:supervisor|control plane)",
            r"(?:worker|platform steward)\s+is\s+(?:a\s+)?(?:current\s+)?cognitive role",
            r"(?:github issues?|kanban)\s+(?:is|are)\s+(?:the\s+)?mandatory",
            r"(?:require|requires|use|uses)\s+(?:a\s+|the\s+)?(?:giant\s+)?execution packet",
            r"(?:require|requires|use|uses)\s+(?:the\s+)?six-condition\s+(?:root\s+)?re-entry",
        ):
            for match in re.finditer(pattern, clause):
                prefix = clause[:match.start()]
                if not re.search(r"(?:do not|must not|never)\s*$", prefix):
                    findings.append(match.group(0))
    return findings


def canonical_references(path, document):
    # Only explicit repo-relative canonical pointers in current homes, not arbitrary
    # Markdown links, shell paths, historical section numbers or external URLs.
    for token in re.findall(r"`([^`\n]+)`", document):
        for target in token.split():
            target = target.rstrip(",;.") if not target.endswith(".md") else target
            if target.startswith((".agent/", "docs/")) or target in {"AGENTS.md", "CLAUDE.md", "README.md"}:
                yield target
            elif path in PROCEDURES and target.endswith(".md") and "/" not in target:
                yield ".agent/procedures/" + target
    # Standing entry and architecture also list pointers in fenced navigation tables.
    yield from re.findall(r"(?m)^\s*((?:\.agent/|docs/)[\w./-]+\.(?:md|yaml))\s", document)


class ArchitecturePolicyTests(unittest.TestCase):
    def test_canonical_tree_and_reference_integrity(self):
        tracked = tracked_files()
        self.assertFalse(REQUIRED - tracked, sorted(REQUIRED - tracked))
        self.assertEqual(AGENT_FILES, {p for p in tracked if p.startswith(".agent/")})
        self.assertFalse({p for p in tracked if p.endswith("/.gitkeep")})
        self.assertNotIn(".github/ISSUE_TEMPLATE/task.md", tracked)
        for prefix in ("infra/", ".agent/roles/", ".agent/policies/", ".agent/skills/"):
            self.assertFalse(any(p.startswith(prefix) for p in tracked), prefix)
        for path in NORMATIVE:
            for target in canonical_references(path, read(path)):
                with self.subTest(source=path, target=target):
                    if target.endswith("/"):
                        self.assertTrue(any(p.startswith(target) for p in tracked))
                    else:
                        self.assertIn(target, tracked)
        # Explicit dependencies cover navigation rendered without backticks as well.
        self.assertIn("@AGENTS.md", read("CLAUDE.md"))
        self.assertIn("tests", read(".github/workflows/architecture-policy.yml"))

    def test_dependency_and_inventory_fail_closed(self):
        with patch("importlib.import_module", side_effect=ModuleNotFoundError("yaml")):
            with self.assertRaisesRegex(RuntimeError, "PyYAML is required"):
                load_policy()
        for error in (FileNotFoundError(), subprocess.CalledProcessError(1, "git"),
                      subprocess.TimeoutExpired("git", 30)):
            with self.subTest(error=type(error).__name__), patch("subprocess.run", side_effect=error):
                with self.assertRaisesRegex(RuntimeError, "Git inspection failed"):
                    tracked_files()
        with patch(__name__ + ".git", return_value=""):
            with self.assertRaisesRegex(RuntimeError, "empty tracked tree"):
                tracked_files()

    def test_policy_roles_and_routing(self):
        policy = load_policy()
        self.assertEqual(4, policy["version"])
        self.assertEqual(ROLES, set(policy["cognitive_roles"]))
        self.assertEqual(4, len(policy["cognitive_roles"]))
        routing = policy["routing"]
        self.assertEqual(ROLES, set(routing["role_preference"]))
        self.assertIs(False, routing["preferences_are_permanent_bindings"])
        for preference in routing["role_preference"].values():
            self.assertIn(preference["capability"], routing["capability_classes"])
            self.assertIn(preference["fallback"], {*routing["capability_classes"], "any_capable"})
        architecture = section(read("docs/ARCHITECTURE.md"), "Responsibility")
        declared = re.findall(r"(?m)^\*\*(\w+)\*\*", architecture)
        self.assertEqual(4, len(declared))
        self.assertEqual(ROLES, {name.lower() for name in declared})
        require(architecture, r"root.*owns.*outcome", r"lead.*execution.*verification",
                r"delegate.*does not own.*outcome.*does not redefine acceptance",
                r"reviewer.*fresh.*independent.*verification")
        require(section(read("docs/ARCHITECTURE.md"), "Child Root criterion"),
                r"own.*outcome and acceptance", r"never by task size")

    def test_review_authority_and_additive_triggers(self):
        policy = load_policy()
        review = policy["review"]
        self.assertIs(True, review["canonical_source"])
        self.assertEqual({"low": False, "medium": "conditional", "high": True},
                         {k: v["review_required"] for k, v in review["levels"].items()})
        self.assertNotIn("review_required", set(keys(policy["routing"])))
        self.assertNotIn("independent_review", set(keys(policy["routing"])))
        self.assertEqual("whether_review_is_required", policy["routing"]["never_decides"])
        triggers = review["triggers"]
        self.assertEqual("review.levels.medium.review_required", triggers["resolves"])
        self.assertEqual("level_requirement_first_then_triggers", triggers["precedence"])
        for name in ("may_only_add", "never_reduces_level_requirement"):
            self.assertIs(True, triggers[name])
        categories = triggers["categories"]
        self.assertEqual({"money_movement", "data_mutation", "permissions_and_credentials",
                          "destructive_operations"}, set(categories))
        for category in categories.values():
            self.assertIs(True, category["requires_independent_review"])
            self.assertTrue(category["matches"])
        self.assertIn("deleting_production_or_source_data", categories["destructive_operations"]["matches"])
        otherwise = triggers["otherwise"]
        self.assertEqual("no_level_requirement_and_no_category_match", otherwise["condition"])
        self.assertEqual("not_required_by_trigger", otherwise["review_required"])
        self.assertEqual("required_tests_must_still_run_and_pass", otherwise["then"])
        guards = review["safeguards"]
        self.assertEqual({"human", "root"}, set(guards["may_be_strengthened_by"]))
        for name in ("may_be_silently_weakened", "routing_may_override_review_required", "retry_may_require_review"):
            self.assertIs(False, guards[name])

    def test_review_route_and_retry(self):
        policy = load_policy()
        independence = policy["review"]["independence"]
        self.assertIs(True, independence["reviewer_must_be_fresh_and_context_isolated"])
        self.assertEqual("cross_provider_or_human_visible_residual_risk_waiver",
                         independence["provider_diversity_when_required"])
        route = policy["routing"]["review_route"]
        self.assertIs(True, route["when_review_required_must_resolve_eligible_reviewer"])
        self.assertIs(False, route["may_downgrade_to_none_or_optional"])
        self.assertEqual("escalate_authority_blocked", route["on_no_eligible_reviewer"])
        for requirement in ("fresh_context_isolated_session", {"capability_class": "strong_independent"},
                            "provider_differs_from_implementer_when_review_independence_requires_it"):
            self.assertIn(requirement, route["eligibility"])
        retry = policy["retry"]
        self.assertIs(True, retry["canonical_source"])
        self.assertIs(False, retry["may_require_review"])
        loop = retry["review_loop"]
        self.assertIs(type(loop["max_cycles"]), int)
        self.assertGreater(loop["max_cycles"], 0)
        self.assertEqual("stop_and_escalate_to_root", loop["on_exhaustion"])
        self.assertIs(False, loop["may_continue_editing_after_exhaustion"])
        for path in NORMATIVE - {".agent/policy.yaml"}:
            self.assertNotIn("max_cycles", read(path), path)

    def test_human_gates_capabilities_and_profiles(self):
        policy = load_policy()
        gates = policy["human_gates"]
        self.assertIs(False, gates["may_be_relaxed_by_agent"])
        self.assertLessEqual({"production_trading_permissions", "destructive_data_access_restrictions",
                             "secret_and_credential_protections", "high_risk_independent_review_requirement",
                             "order_and_capital_safety_guardrails", "maximum_budget_and_concurrency_limits",
                             "production_deployment_gates", "minimum_backup_retention"}, set(gates["protected"]))
        cap = policy["capabilities"]
        self.assertEqual("grant_only_capabilities_the_assignment_requires", cap["least_capability"])
        self.assertEqual("escalate_capabilities_stepwise_and_only_on_evidence", cap["progressive_disclosure"])
        self.assertEqual({"root-standard", "lead-standard", "delegate-readonly", "delegate-writable",
                          "reviewer-independent"}, set(cap["profiles"]))
        for name, profile in cap["profiles"].items():
            self.assertLessEqual(set(profile["includes"]), set(cap["catalog"]))
            self.assertEqual(name == "lead-standard", "delegate-integration" in profile["includes"])
        for item in cap["catalog"].values():
            self.assertIs(type(item["sensitive"]), bool)
        profiles = policy["operating_profiles"]
        self.assertIn(profiles["active"], profiles.keys() - {"active"})
        for name, profile in profiles.items():
            if name == "active":
                continue
            self.assertLessEqual(set(profile), {"description", "writable_delegation", "delegate_permissions",
                                               "integration", "exit_condition"})
            self.assertIn(profile["writable_delegation"], {"allowed", "forbidden"})
        travel = profiles["travel"]
        self.assertEqual("forbidden", travel["writable_delegation"])
        self.assertEqual({"read_only", "run_tests", "produce_patch_suggestions_only"}, set(travel["delegate_permissions"]))
        self.assertEqual("deferred_until_operator_returns", travel["integration"])
        self.assertNotRegex(read("docs/runbooks/REMOTE_WORK.md"), r"当前\s*=\s*`?travel")

    def test_credential_handling_and_delegate_write_boundary(self):
        policy = load_policy()
        credentials = policy["human_gates"].get("credential_handling", {})
        self.assertLessEqual({"git", "messages", "terminal_logs", "review_artifacts"},
                             set(credentials.get("forbidden_value_destinations", [])))
        self.assertEqual(["environment_variables", "gitignored_env_file", "os_keyring", "controlled_secret_manager"],
                         credentials.get("local_storage"))
        self.assertEqual("task_required_least_privilege", credentials.get("per_node_access"))
        self.assertIs(False, credentials.get("validation_may_read_print_or_copy_real_credentials"))
        profiles = policy["capabilities"]["profiles"]
        self.assertIs(False, profiles["delegate-readonly"].get("repository_write"))
        self.assertIs(True, profiles["delegate-writable"].get("repository_write"))
        for name in ("delegate-readonly", "delegate-writable"):
            self.assertEqual({"repo", "git", "python-test"}, set(profiles[name]["includes"]))

    def test_efficiency_and_instruction_diet(self):
        efficiency = load_policy()["efficiency"]
        self.assertLessEqual({"use_the_cheapest_capable_resource", "prefer_deterministic_tools_tests_and_evals_before_model_calls",
                             "delegate_when_result_is_needed_but_process_need_not_remain_in_parent_context",
                             "report_compressed_evidence_not_transcripts_or_reasoning_dumps",
                             "reasoning_effort_is_not_a_token_savings_lever"}, set(efficiency["principles"]))
        adapt = efficiency["premium_adaptivity"]
        self.assertEqual("root", adapt["envelope_owner"])
        for flag in ("allowed", "hardcoded_high_forbidden", "low_cost_reasoning_stays_high"):
            self.assertIs(True, adapt[flag])
        for lever in efficiency["cost_levers"]:
            self.assertNotRegex(lever, r"reasoning|review|skip")
        self.assertFalse({"review_required", "independent_review", "skip_review"} & set(keys(efficiency)))
        standing = read("AGENTS.md")
        self.assertLessEqual(len(standing.splitlines()), 60)
        self.assertLessEqual(len(standing.encode()), 4096)
        for path in ("AGENTS.md", "CLAUDE.md"):
            self.assertNotRegex(read(path), r"--session|cherry-pick|resources_clean")
        architecture = read("docs/ARCHITECTURE.md")
        self.assertNotIn(CHECKPOINT, blocks(architecture))
        self.assertNotIn("--session", architecture)

    def test_contracts_and_checkpoint(self):
        architecture = read("docs/ARCHITECTURE.md")
        task = blocks(section(architecture, "Minimal Task Contract"))[0]
        self.assertEqual(["GOAL", "ACCEPTANCE", "CONSTRAINTS"], task[:3])
        self.assertEqual(4, len(task))
        self.assertRegex(task[3], r"^OVERRIDES\s+.*optional")
        self.assertEqual(RETURN, blocks(section(architecture, "Communication contract"))[0])
        require(section(architecture, "Communication contract"), r"writable.*commit", r"uncertainty.*evidence")
        escalation = blocks(section(architecture, "Escalation"))
        self.assertEqual([["DECISION_REQUIRED", "UNCERTAINTY_UNRESOLVED", "AUTHORITY_BLOCKED"],
                          ["TYPE", "QUESTION", "EVIDENCE"]], escalation)
        checkpoint = read(".agent/procedures/checkpoint.md")
        schemas = [b for b in blocks(checkpoint) if b and b[0] == "ROOT_ID"]
        self.assertEqual([CHECKPOINT], schemas)
        coverage = section(checkpoint, "ACCEPTANCE carries coverage")
        require(coverage, r"each acceptance criterion.*status.*evidence", r"actively executing.*retained")
        for example in re.split(r"\bA\d+\b", "\n".join(blocks(coverage)[0]))[1:]:
            self.assertRegex(example, r"STATUS:\s*\w+")
            self.assertRegex(example, r"EVIDENCE:\s*\S+")
        require(section(checkpoint, "Resume"), r"same root_id.*latest checkpoint.*git/github",
                r"re-verify.*git state.*resume")
        require(checkpoint, r"no eleventh field", r"session-independent continuation state")
        require(section(architecture, "Root Carrier"), r"root_id.*stable",
                r"children.*worktrees.*review state.*reconciled", r"must not.*orphan")

    def test_delegation_selection_and_return(self):
        procedure = read(".agent/procedures/delegate.md")
        selection = section(procedure, "When to delegate")
        require(selection, r"delegate when.*result must be retained.*process does not need.*parent context",
                r"directly only when", r"deterministic batch.*prefer.*script.*tool.*engine")
        exceptions = re.findall(r"(?m)^\s*\d+\.\s*(.*(?:\n(?!\s*\d+\.|\n).*)*)", selection)
        self.assertEqual(4, len(exceptions))
        for text, pattern in zip(exceptions, [r"process.*affects.*decisions", r"implicit.*context",
                                            r"overhead.*size", r"authority cannot be delegated"]):
            require(text, pattern)
        form = section(procedure, "Choosing the Delegate form")
        require(form, r"native first.*adequate.*traceable", r"external herdr.*cross-provider",
                r"model unreachable", r"data source.*cannot reach", r"independent runtime", r"isolation or traceability")
        require(section(procedure, "Delegate authority"), r"does not own.*outcome.*does not redefine acceptance")
        self.assertEqual([RETURN], blocks(section(procedure, "Return contract")))
        require(section(procedure, "Return contract"), r"writable.*commit", r"high-volume.*artifact")

    def test_independent_review_preservation(self):
        procedure = read(".agent/procedures/review.md")
        require(section(procedure, "Reviewer setup"), r"fresh.*context-isolated.*new session.*no inherited context",
                r"contractual", r"stronger sandbox.*evidence")
        material = section(procedure, "Review material")
        self.assertEqual(["GOAL", "ACCEPTANCE", "result / diff / commit", "verification evidence",
                          "relevant constraints and material selected by Root/Policy"], blocks(material)[0])
        require(material, r"do not supply.*private reasoning.*advocacy.*chain-of-thought.*transcripts")
        require(section(procedure, "Verdict preservation"), r"original verdict.*preserved independently",
                r"lead.*may not.*rewrite.*suppress.*redefine", r"root.*recover.*without.*lead.*sole transport",
                r"check.*integrity", r"terminal.*debug.*never.*preservation")
        require(section(procedure, "Loop ownership"), r"lead owns.*review/fix loop", r"root rules.*final result")

    def test_writable_base_reuse_and_isolation(self):
        procedure = read(".agent/procedures/writable-work.md")
        require(section(procedure, "Base and provenance"), r"explicit.*immutable base commit",
                r"before.*edit.*mutation.*verifies actual head.*git provenance.*declared immutable base",
                r"stop.*missing or mismatched", r"orchestration lineage is not git ancestry")
        require(section(procedure, "Isolation"), r"must not.*mutate.*protected parent or main",
                r"external writable.*isolated worktree", r"outside.*protected checkout.*clean.*head unchanged")
        reuse = section(procedure, "Reusing an existing worktree")
        require(reuse, r"only when both", r"clean.*and.*base and provenance.*match.*immutable base",
                r"do not reset.*repoint.*retarget", r"fresh isolated worktree.*fresh result branch",
                r"cannot.*safely.*escalate")

    def test_writable_ownership_handoff(self):
        ownership = section(read(".agent/procedures/writable-work.md"), "Ownership after Lead failure")
        require(ownership, r"clean git status.*not that no agent is using it",
                r"before reusing.*after lead failure.*must confirm.*previous executor has exited or.*explicit ownership transfer has completed",
                r"ending.*previous executor.*write authority", r"must not have concurrent write authority",
                r"clean status alone is insufficient", r"cannot be confirmed.*escalate to the owning root",
                r"do not terminate unknown processes, reset branches or force takeover")

    def test_writable_integration_and_recoverable_cleanup(self):
        procedure = read(".agent/procedures/writable-work.md")
        require(section(procedure, "Integration"), r"lead owns verified integration",
                r"verify ancestry.*scope.*linearity.*base", r"before integration.*target.*clean and suitable",
                r"stop.*dirty state.*unfinished git operation", r"do not.*integrate over",
                r"after integration.*lead verifies.*result.*acceptance.*interactions.*target state",
                r"command.*successfully is not verification")
        cleanup = section(procedure, "Cleanup")
        require(cleanup, r"creates.*direct child.*owns.*cleanup.*parent verifies",
                r"before cleaning or deleting.*preserve recoverable.*immutable.*outside.*removed",
                r"result.*commit.*integration unit", r"base.*provenance.*integrated result",
                r"verification outcomes.*integrated-state", r"root and lead.*recover and audit.*after.*cleanup",
                r"dirty worktree must be resolved", r"must not.*discard uncommitted work",
                r"forced removal is not routine", r"after cleanup.*verify.*git worktree.*herdr resource")
        require(section(procedure, "resources_clean"), r"observable post-conditions.*never.*command.*return",
                r"resources_clean: false.*prevents.*acceptance.*exceptional recovery")

    def test_herdr_targeting_and_runtime_boundaries(self):
        require(section(read(".agent/procedures/writable-work.md"), "Herdr runtime safety"),
                r"every herdr mutation.*explicitly.*intended session.*--session",
                r"herdr_socket_path.*override.*herdr_session.*alone.*not reliable")
        require(section(read("docs/runbooks/REMOTE_WORK.md"), "Herdr 定位安全（必守）"),
                r"mutation.*显式.*目标 session.*--session", r"不要只依赖.*herdr_session.*herdr_socket_path.*优先")
        architecture = read("docs/ARCHITECTURE.md")
        require(section(architecture, "Herdr boundary"), r"cross-harness.*runtime substrate",
                r"not a cognitive agent.*not a reasoning supervisor")
        require(section(architecture, "Project Control Plane boundary"), r"outside.*cognitive role model")
        require(section(architecture, "Git and GitHub"), r"authoritative durable project knowledge",
                r"not.*mandatory task entry", r"issue or kanban state is not.*task state")

    def test_binding_scanner_controls(self):
        technologies = ("Codex", "Claude", "DeepSeek", "GPT-6 Astra", "Pi", "Claude Code",
                        "claude_code", "claude-code", "Codex CLI", "codex_cli", "codex-cli")
        for role in sorted(ROLES):
            for tech in technologies:
                for fixture in (f"{role}: {tech}", f"{tech} {role}", f"{role} = {tech}",
                                f"The {role} is assigned to the {tech} harness for every task.",
                                f"{tech} is the default harness for {role}.", f"{role} 是 {tech}",
                                f"| {role} | {tech} harness |", f"**{role}** → `{tech}`",
                                f"```text\n{role}\nprovider: {tech}\n```",
                                f"{role} is always {tech}", f"{role} must use {tech}",
                                f"```text\n{role}\n{tech} harness\n```" ):
                    with self.subTest(fixture=fixture):
                        self.assertTrue(binding_claims(fixture), fixture)
        for fixture in ("Claude Code is an interactive terminal harness running Claude models.",
                        "Pi is a harness whose model is selected at runtime.",
                        "Root prefers the Claude Code harness with a capable pool.",
                        "For this task, Lead selects Codex CLI based on capability.",
                        "Root is not Claude. Delegate is not Codex.",
                        "Do not bind Reviewer to Codex.",
                        "Lead owns integration.\n\nCodex is available."):
            self.assertEqual([], binding_claims(fixture), fixture)
        self.assertTrue(binding_claims("Root is not Claude. Delegate = Codex."))

    def test_document_guards_reject_missing_obligations(self):
        cases = [
            ("test_contracts_and_checkpoint", ".agent/procedures/checkpoint.md",
             "NEXT_ACTION\n", "NEXT_ACTION\nEXTRA_FIELD\n"),
            ("test_contracts_and_checkpoint", ".agent/procedures/checkpoint.md", "STATUS:", "STATE:"),
            ("test_contracts_and_checkpoint", ".agent/procedures/checkpoint.md", "EVIDENCE:", "DETAIL:"),
            ("test_delegation_selection_and_return", ".agent/procedures/delegate.md",
             "4. the required authority cannot be delegated.", ""),
            ("test_delegation_selection_and_return", ".agent/procedures/delegate.md", "Native first.", "External first."),
            ("test_independent_review_preservation", ".agent/procedures/review.md",
             "may not rewrite, suppress or redefine", "may rewrite, suppress or redefine"),
            ("test_writable_base_reuse_and_isolation", ".agent/procedures/writable-work.md",
             "verifies actual HEAD", "trusts requested HEAD"),
            ("test_writable_base_reuse_and_isolation", ".agent/procedures/writable-work.md",
             "it is clean; and", "it is clean; or"),
            ("test_writable_base_reuse_and_isolation", ".agent/procedures/writable-work.md",
             "do not reset, repoint, retarget", "reset, repoint, retarget"),
            ("test_writable_integration_and_recoverable_cleanup", ".agent/procedures/writable-work.md",
             "clean and suitable", "dirty but usable"),
            ("test_writable_integration_and_recoverable_cleanup", ".agent/procedures/writable-work.md",
             "relevant interactions", "unrelated logs"),
            ("test_writable_integration_and_recoverable_cleanup", ".agent/procedures/writable-work.md",
             "Before cleaning or deleting", "After cleaning or deleting"),
            ("test_writable_integration_and_recoverable_cleanup", ".agent/procedures/writable-work.md",
             "observable post-conditions", "command success"),
        ]
        original_read = read
        for old, new in (
            ("previous executor has exited", "worktree is clean"),
            ("an explicit ownership transfer has completed", "a transfer has been requested"),
            ("must not have\nconcurrent write authority", "may have\nconcurrent write authority"),
            ("escalate to the owning Root", "proceed without confirmation"),
            ("do not terminate unknown", "terminate unknown"),
        ):
            cases.append(("test_writable_ownership_handoff", ".agent/procedures/writable-work.md", old, new))
        for method, path, old, new in cases:
            with self.subTest(method=method, defect=old):
                original = original_read(path)
                self.assertIn(old, original)
                def modified(candidate):
                    return original.replace(old, new) if candidate == path else original_read(candidate)
                result = unittest.TestResult()
                with patch(__name__ + ".read", side_effect=modified):
                    ArchitecturePolicyTests(method).run(result)
                self.assertTrue(result.failures, f"Guard accepted defective obligation: {old}")
                self.assertFalse(result.errors, result.errors)

    def test_policy_guards_reject_weakened_controls(self):
        policy = load_policy()
        cases = [
            ("test_policy_roles_and_routing", ("cognitive_roles",), ["root", "lead", "worker", "reviewer"]),
            ("test_review_authority_and_additive_triggers", ("review", "levels", "high", "review_required"), False),
            ("test_review_authority_and_additive_triggers", ("review", "triggers", "may_only_add"), False),
            ("test_review_route_and_retry", ("routing", "review_route", "may_downgrade_to_none_or_optional"), True),
            ("test_review_route_and_retry", ("retry", "review_loop", "on_exhaustion"), "continue"),
            ("test_human_gates_capabilities_and_profiles", ("human_gates", "may_be_relaxed_by_agent"), True),
            ("test_human_gates_capabilities_and_profiles", ("operating_profiles", "active"), "missing"),
            ("test_human_gates_capabilities_and_profiles", ("operating_profiles", "default", "human_gates"), {}),
            ("test_human_gates_capabilities_and_profiles", ("operating_profiles", "travel", "writable_delegation"), "allowed"),
            ("test_human_gates_capabilities_and_profiles", ("capabilities", "profiles", "delegate-writable", "includes"),
             ["repo", "git", "delegate-integration"]),
        ]
        guard = "test_credential_handling_and_delegate_write_boundary"
        credential_path = ("human_gates", "credential_handling")
        destinations = ["git", "messages", "terminal_logs", "review_artifacts"]
        for forbidden in destinations:
            cases.append((guard, credential_path + ("forbidden_value_destinations",),
                          [item for item in destinations if item != forbidden]))
        cases.extend([
            (guard, credential_path + ("local_storage",), ["tracked_file"]),
            (guard, credential_path + ("per_node_access",), "unrestricted"),
            (guard, credential_path + ("validation_may_read_print_or_copy_real_credentials",), True),
            (guard, ("capabilities", "profiles", "delegate-readonly", "repository_write"), True),
            (guard, ("capabilities", "profiles", "delegate-readonly", "repository_write"), None),
            (guard, ("capabilities", "profiles", "delegate-writable", "repository_write"), False),
        ])
        for method, path, value in cases:
            with self.subTest(path=path):
                broken = copy.deepcopy(policy)
                node = broken
                for key in path[:-1]:
                    node = node[key]
                node[path[-1]] = value
                result = unittest.TestResult()
                with patch(__name__ + ".load_policy", return_value=broken):
                    ArchitecturePolicyTests(method).run(result)
                self.assertTrue(result.failures, f"Guard accepted weakened policy: {path}")
                self.assertFalse(result.errors, result.errors)
        # Either defined operating profile can be selected without relaxing gates.
        for name in ("default", "travel"):
            selected = copy.deepcopy(policy)
            selected["operating_profiles"]["active"] = name
            result = unittest.TestResult()
            with patch(__name__ + ".load_policy", return_value=selected):
                ArchitecturePolicyTests("test_human_gates_capabilities_and_profiles").run(result)
            self.assertTrue(result.wasSuccessful(), result.failures + result.errors)

    def test_current_claim_controls_and_live_sweep(self):
        for assertion in ("Orca is the execution plane", "Hermes Supervisor is the control plane",
                          "Worker is a cognitive role", "Platform Steward is a cognitive role",
                          "GitHub Issues are mandatory", "Kanban is mandatory",
                          "Root requires a giant Execution Packet", "Use the six-condition Root re-entry mechanism"):
            self.assertTrue(current_claims(assertion), assertion)
        for negative in ("Orca is not the execution plane.", "Do not use the six-condition Root re-entry mechanism.",
                         "Worker and Platform Steward are retired roles.", "GitHub Issues are optional."):
            self.assertEqual([], current_claims(negative), negative)
        self.assertTrue(current_claims("Orca is not current. Worker is a cognitive role."))
        for path in NORMATIVE:
            document = read(path)
            if path.endswith(".yaml"):
                document = "\n".join(line.lstrip()[1:] for line in document.splitlines() if line.lstrip().startswith("#"))
            self.assertEqual([], binding_claims(document), path)
            self.assertEqual([], current_claims(document), path)
        self.assertFalse(ADRS & NORMATIVE)
        self.assertNotIn("docs/HISTORY.md", NORMATIVE)


if __name__ == "__main__":
    unittest.main()

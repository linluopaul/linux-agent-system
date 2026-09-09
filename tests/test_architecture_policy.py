from pathlib import Path
import json
import re
import subprocess
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
# Bilingual no-provider-as-role invariant.
#
# Scope and known limits (stated here so the docstring never overclaims):
#   * The invariant is LANGUAGE-INDEPENDENT. docs/ARCHITECTURE.md is majority-Chinese
#     prose, and role nouns appear as the same Latin tokens in both languages, so the
#     provider and role vocabularies below cover BOTH an English sentence and a Chinese
#     sentence. Chinese binding operators (provider 偏好 / 默认 provider / 偏好为 /
#     绑定 / 是) are detected as binding markers, so the pre-amendment B1 defect text
#     reintroduced in Chinese is caught.
#   * Provider/model-pool names (pool names, NOT HARNESS class names). Harness classes
#     are named claude_code / codex_cli / pi and are deliberately NOT in this set, so
#     legitimate harness-class vocabulary is expressible. "Pi" is a harness, not a pool,
#     and is likewise absent.
#   * The guard is a syntactic scan of the documented binding forms, NOT semantic proof.
#     A provider name only triggers when it is bound to a role noun through an explicit
#     structural operator (adjacency incl. a markdown table pipe `|`, "is"/"run by",
#     "for", ":" , "=", "role:", "agent:", or the Chinese operators). Mere
#     co-occurrence in a sentence - e.g. "Root prefers the Claude Code harness with a
#     capable pool" - is a preference and is NOT flagged.
#   * Genuinely historical / superseded-model narration is excluded ONLY when wrapped in
#     the explicit escape hatch `<!-- HISTORICAL-BINDING-START --> ... <!--
#     HISTORICAL-BINDING-END -->` (or a single-line `HISTORICAL-BINDING` comment). Every
#     usage is auditable by grepping for HISTORICAL-BINDING; the escape hatch is for
#     real history, never for live policy. ADR-004 uses it for its pre-amendment Context
#     narrative and the superseded single-Codex quote.
#   * Machine-readable policy config (YAML key/value assignments, e.g. `reviewer:
#     claude`, `preferred_pool: deepseek`) is a routed preference, not prose, so ONLY
#     YAML comment lines are scanned. A pool name appearing as a config VALUE is not
#     swept up merely for existing (see S3).
#   * ADR-001/002/003 are excluded by path below (they are retained as historical
#     records of the provider-role preferences ADR-004 supersedes).
# ---------------------------------------------------------------------------
PROVIDER_NAME_RE = r"(?:claude|codex|deepseek|gemini|kimi|minimax|volcengine|ark)"
# Role nouns that must never be qualified by a provider name. Hyphens are tolerated in
# compound role names so "Codex-Execution-Lead" and "Codex Execution Lead" (and a
# trailing plural "Execution Leads") are all recognized. The bare nouns lead, worker,
# reviewer, specialist, steward, root are included per the reproducible evasions.
ROLE_NOUN_RE = (
    r"(?:execution[ \-]?lead|engineering[ \-]?control[ \-]?plane|"
    r"cognitive[ \-]?control[ \-]?plane|execution[ \-]?worker|"
    r"platform[ \-]?steward|lead|worker|reviewer|specialist|steward|root)"
)
# Adjacent-bound patterns: a provider or role name glued to the OTHER by spaces, tabs,
# a hyphen, or a markdown table pipe `|` (never an underscore, so the HARNESS names
# claude_code / codex_cli and a config key like `preferred_pool` cannot match). Adding the
# pipe closes the table-row blind spot: an `| Execution Lead | Codex |` row binds a role
# CELL to a bare provider CELL across one pipe separator and is caught here, yet the
# legitimate §7 rows (``| Role | pi harness + low-cost pool |``) stay clean because the
# provider must be immediately adjacent to a role noun with no intervening token - a
# "harness + pool" description contributes no bare provider-role adjacency. These only
# match WITHIN a line and do not cross a newline, so a fenced-diagram line like "Control
# Plane\nClaude Code harness" is not collapsed into a false "Control Plane Claude"
# adjacency.
IMMEDIATE_BINDINGS = (
    (
        "provider-role",
        re.compile(
            r"\b(?:%s)[ \t\-\u2010\|]+%s(?:s\b)?" % (PROVIDER_NAME_RE, ROLE_NOUN_RE),
            flags=re.IGNORECASE,
        ),
    ),
    (
        "role-provider",
        re.compile(
            r"%s(?:s\b)?[ \t\-\u2010\|]+(?:%s)\b" % (ROLE_NOUN_RE, PROVIDER_NAME_RE),
            flags=re.IGNORECASE,
        ),
    ),
)
# Structural / operator-bound patterns. These require an explicit binding operator, so
# they are safe to apply after collapsing newlines to spaces (catching a role on one
# line and "provider: X" on the next) WITHOUT inventing text out of fenced diagrams:
# a bare diagram line has no operator to attach to.
LINK_BINDINGS = (
    (
        "role-:-",
        re.compile(
            r"%s\b[^\n:.=]{0,26}?[:=][ \t]*(?:%s)\b" % (ROLE_NOUN_RE, PROVIDER_NAME_RE),
            flags=re.IGNORECASE,
        ),
    ),
    (
        "role-is",
        re.compile(
            r"%s\b[^\n.]{0,20}?\b(?:is|are)\b[ \t]*(?:always|run by|the|a|an)?"
            r"[ \t]*(?:%s)\b" % (ROLE_NOUN_RE, PROVIDER_NAME_RE),
            flags=re.IGNORECASE,
        ),
    ),
    (
        "is-role",
        re.compile(
            r"\b(?:%s)\b[ \t]*(?:is|are|was|were)[ \t]*(?:the|a|an|permanent)?"
            r"[ \t]*%s\b" % (PROVIDER_NAME_RE, ROLE_NOUN_RE),
            flags=re.IGNORECASE,
        ),
    ),
    (
        "for-role",
        re.compile(
            r"\b(?:%s)\b[ \t]*,?[ \t]*(?:for|preferred for|preferred)"
            r"[ \t]*(?:the[ \t]*)?%s\b" % (PROVIDER_NAME_RE, ROLE_NOUN_RE),
            flags=re.IGNORECASE,
        ),
    ),
    (
        "default-agent",
        re.compile(
            r"\bdefault\b[^\n:.]{0,40}?\b(?:agent|role)\b[^\n:.]{0,20}?[:=][ \t]*(?:%s)\b"
            % PROVIDER_NAME_RE,
            flags=re.IGNORECASE,
        ),
    ),
    # Chinese binding operators (majority-chinese doc: these MUST catch the original
    # B1 defect reintroduced as 默认 provider 偏好为 X / 绑定).
    (
        "cn-provider-pref",
        re.compile(
            r"provider[ \t]*偏好[ \t]*为?[ \t]*[:：]?[ \t]*(?:%s)\b" % PROVIDER_NAME_RE,
            flags=re.IGNORECASE,
        ),
    ),
    (
        "cn-default-provider",
        re.compile(
            r"默认[ \t]*provider[ \t]*(?:偏好)?[ \t]*为?[ \t]*[:：]?[ \t]*(?:%s)\b"
            % PROVIDER_NAME_RE,
            flags=re.IGNORECASE,
        ),
    ),
    (
        "cn-pref-wei",
        re.compile(
            r"偏好[ \t]*为[ \t]*[:：]?[ \t]*(?:%s)\b" % PROVIDER_NAME_RE,
            flags=re.IGNORECASE,
        ),
    ),
    (
        "cn-provider-colon",
        re.compile(
            r"provider[ \t]*[:：=][ \t]*(?:%s)\b" % PROVIDER_NAME_RE,
            flags=re.IGNORECASE,
        ),
    ),
    (
        "cn-role-shi",
        re.compile(
            r"%s\b[ \t]*是[ \t]*(?:%s)\b" % (ROLE_NOUN_RE, PROVIDER_NAME_RE),
            flags=re.IGNORECASE,
        ),
    ),
    (
        "cn-bind-after",
        re.compile(
            r"\b(?:%s)\b[\s\u4e00-\u9fff]{0,8}?(?:绑定|永久绑定)(?:到|至|于)?"
            % PROVIDER_NAME_RE,
            flags=re.IGNORECASE,
        ),
    ),
    (
        "cn-bind-before",
        re.compile(
            r"绑定(?:到|至|于)?[ \t]*(?:%s)\b" % PROVIDER_NAME_RE,
            flags=re.IGNORECASE,
        ),
    ),
    (
        "cn-role-pref",
        re.compile(
            r"%s\b[ \t]*偏好[ \t]*为[ \t]*(?:%s)\b" % (ROLE_NOUN_RE, PROVIDER_NAME_RE),
            flags=re.IGNORECASE,
        ),
    ),
)
# The explicit escape hatch: any passage wrapped between
#   <!-- HISTORICAL-BINDING-START --> ... <!-- HISTORICAL-BINDING-END -->
# (or a single-line comment whose body contains HISTORICAL-BINDING) is stripped before
# scanning, so genuinely historical / superseded-model narration can be quoted verbatim
# without tripping the live invariant. Every usage is auditable via a grep for
# HISTORICAL-BINDING and is reserved for real history, never for live policy.
HISTORICAL_ESCAPE_START = re.compile(r"(?s)<!--\s*HISTORICAL-BINDING-START.*?HISTORICAL-BINDING-END\s*-->")
HISTORICAL_ESCAPE_SINGLE = re.compile(r"<!--\s*HISTORICAL-BINDING[^>]*?-->")


def strip_historical_escape_hatch(text: str) -> str:
    """Remove HISTORICAL-BINDING escape-hatch regions before scanning."""
    return HISTORICAL_ESCAPE_SINGLE.sub(" ", HISTORICAL_ESCAPE_START.sub(" ", text))


def provider_bindings_in_text(text: str) -> list[tuple[str, str]]:
    """Return (pattern-name, matched-snippet) for every live provider-as-role binding.

    Immediate (adjacency) patterns run per physical line so they can never fuse across
    a newline inside a fenced diagram; operator-bound patterns run on the newline-
    collapsed text so a role on one line and a binding on the next (e.g. "Execution
    Lead\nprovider: Codex") is caught.
    """
    text = strip_historical_escape_hatch(text)
    findings: list[tuple[str, str]] = []
    for line in text.splitlines():
        for name, pattern in IMMEDIATE_BINDINGS:
            for match in pattern.finditer(line):
                findings.append((name, match.group(0)))
    collapsed = re.sub(r"\s+", " ", text)
    for name, pattern in LINK_BINDINGS:
        for match in pattern.finditer(collapsed):
            findings.append((name, match.group(0)))
    return findings


def provider_bindings_in_document(path: Path) -> list[tuple[str, str]]:
    """Scan one live architecture document for provider-as-role bindings.

    For YAML policy files only the comment lines are treated as prose: a structural
    key/value assignment (e.g. `reviewer: claude`, `preferred_pool: deepseek`) is a
    routed preference keyed to a pool name, NOT prose narration, so it must not be
    scooped up merely for existing. This is the config-vs-prose distinction.
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    text = strip_historical_escape_hatch(raw)
    if path.suffix in {".yaml", ".yml"}:
        comments = [
            line.lstrip().lstrip("#").strip()
            for line in text.splitlines()
            if line.lstrip().startswith("#")
        ]
        findings: list[tuple[str, str]] = []
        for comment in comments:
            findings.extend(provider_bindings_in_text(comment))
        return findings
    return provider_bindings_in_text(text)


def _is_under(path: Path, parent: Path) -> bool:
    """True if `path` is equal to `parent` or nested below it."""
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _is_live_architecture_path(path: Path) -> bool:
    """Is `path` part of the shared live-architecture document set?

    True for a .md/.yaml/.yml file anywhere under the repository root (repo-root
    manifests AGENTS/README/CLAUDE and any authored root-level prose), docs/ or .agent/,
    and NOT under .github/ or the .agent/runs/ telemetry directory. This is the ONE
    definition of "live architecture text" shared by every repository-walking scanner,
    so none of them can be perturbed by local runtime telemetry, scratch files or build
    artifacts.
    """
    if path.suffix not in {".md", ".yaml", ".yml"}:
        return False
    if _is_under(path, ROOT / ".github"):
        return False
    if _is_under(path, ROOT / ".agent" / "runs"):
        return False
    return True


def tracked_repository_paths() -> list[Path] | None:
    """Every version-controlled file tracked by Git (any type), or None if git is
    unavailable. Used to scope every repository-walking scanner to tracked files so a
    verdict never depends on untracked local telemetry, scratch files or build
    artifacts."""
    try:
        listing = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return [ROOT / rel for rel in listing.stdout.split("\0") if rel]


def tracked_architecture_documents() -> list[Path]:
    """The shared live-architecture document set: version-controlled docs only.

    This is the single reproducible definition of "live architecture text" used by
    every repository-walking scanner (the no-provider-as-role invariant, the
    role->harness cross-check, the codex-default-root guard and the escape-hatch
    audit). Runtime telemetry under .agent/runs/ is NEVER part of it, so a policy
    gate returns identical results in CI and in a dirty local working tree.

    Mechanism (preferred): the set is derived from Git with `git ls-files`, so only
    files recorded in the repository index can ever be scanned. Untracked and
    git-ignored paths - e.g. the .agent/runs/<task>/report.md telemetry files a local
    run leaves behind - are excluded by construction even though they exist on disk.
    A scanner whose verdict depends on untracked local files would not be a reliable
    gate, and a locally-run task would otherwise produce a spurious failure that CI
    cannot reproduce.

    Fallback: if Git is unavailable, fall back to an explicit directory allowlist
    (repo-root AGENTS/README/CLAUDE, docs/, .agent/) plus an explicit .agent/runs/**
    exclusion, producing the same set without relying on the repository index.
    """
    tracked = tracked_repository_paths()
    if tracked is None:
        return _allowlisted_architecture_documents()
    return [p for p in tracked if _is_live_architecture_path(p)]


def _allowlisted_architecture_documents() -> list[Path]:
    """Git-unavailable fallback: explicit allowlist plus .agent/runs exclusion."""
    paths = [ROOT / "AGENTS.md", ROOT / "README.md", ROOT / "CLAUDE.md"]
    for directory in (ROOT / "docs", ROOT / ".agent"):
        paths.extend(path for path in directory.rglob("*") if _is_live_architecture_path(path))
    return paths


def live_architecture_documents() -> list[Path]:
    """Every live md/yaml file that documents current architecture or policy.

    Backed by tracked_architecture_documents, so only version-controlled files are
    ever read - runtime telemetry under .agent/runs/ is excluded by construction.
    Genuinely historical decision records (ADR-001/002/003) are additionally excluded
    by path so their retro-recorded provider preferences do not trip the live
    invariant.
    """
    historical = {
        ROOT / "docs" / "decisions" / "ADR-001-orca-first-execution-plane.md",
        ROOT / "docs" / "decisions" / "ADR-002-cognitive-and-engineering-control-planes.md",
        ROOT / "docs" / "decisions" / "ADR-003-lead-worker-git-integration-contract.md",
    }
    return [p for p in tracked_architecture_documents() if p not in historical]


# ---------------------------------------------------------------------------
# v2.1: deterministic role -> harness cross-check against routing.yaml.
#
# Purpose. This closes a specific defect CLASS. Three of the last four BLOCKING
# findings (ARCHITECTURE.md:566, :738, :694) were the same defect: a live document
# asserting a role -> harness mapping that contradicted .agent/policies/routing.yaml
# `defaults.preferred_harness`. Each was fixed one-off, and each time the next one
# survived because nothing asserted the invariant. This cross-check does.
#
# Policy is the single source of truth. The blessed role->harness mapping and the
# recognised harness spellings are both READ from routing.yaml (via the test), never
# hardcoded in these helpers or in the assertions. A future policy edit therefore
# cannot silently desync the prose: whatever routing.yaml now prefers is what a live
# claim must still agree with.
#
# RECOGNISABLE-FORM CONSTRAINT (stated explicitly, not hidden): to associate a live
# claim with a role deterministically while avoiding false positives, a role->harness
# claim is checked ONLY when it is expressed in one of the four shapes the four past
# defects actually hid in, and only when it names the harness in a recognised spelling:
#   * markdown table cell      (the §7 form   ) - a role cell + a "<H> harness" cell
#   * fenced diagram block     (the §6.6 form ) - a role label line + a harness
#     annotation line in the same code fence (nearest preceding role label)
#   * bilingual prose sentence (the §6.1 form ) - one role noun and a "<H> harness"
#     mention on the same line with no competing role noun
#   * any other structured    (the sweep form) - a bullet/numbered list item carrying
#     a role noun and a "<H> harness" mention gets the same same-line treatment as
#     prose, so a future list-embedded claim is covered too.
# A claim too free-form to pin to a single role (e.g. ORCA_WORKFLOW prose naming both
# Root and Execution Lead on one line, or a bare "Root harness" with no spelling) is
# deliberately NOT silently swept up: it is excluded by the recognisable form and this
# is declared here rather than glossed over. The accepted residual prose evasions
# (R1-R4 and the reviewer's other documented cases) remain out of scope.
# ---------------------------------------------------------------------------

# Role key -> recognisable role noun spellings used to locate role->harness claims.
# These tokens are structural labels from the architecture/theory of roles, not new
# policy; the BLESSED mapping (which harness a role may use) always comes from YAML.
ROLE_CLAIM_TOKENS = {
    "root": ["root", "cognitive control plane"],
    "execution_lead": ["execution lead", "engineering control plane"],
    "specialist": ["specialist"],
    "reviewer": ["independent review", "high-risk review", "reviewer"],
    "platform_steward": ["platform steward"],
    "worker": ["execution worker", "worker"],
}

# v2.1.1 F4: a harness file documents exactly ONE harness, so the subject of an
# 'assigned to <Role>' / 'used for <Role> work' sentence in a harness file IS that file's
# harness. The v2.1 cross-check missed pi.md's false Root claim precisely because the claim
# was harness-first ('Pi is assigned to Root ... work'), the reverse of the four role-first
# shapes it models. This map pins which harness a harness file is about so the F4 guard can
# resolve a harness-first claim to a (harness, role) pair deterministically.

def _harness_spelling_map(harness_keys: list[str]) -> dict[str, str]:
    """Map every textual spelling of a policy harness key back to that key.

    Policy stores harness keys as snake_case (claude_code, codex_cli, pi) which prose
    and diagrams render as "Claude Code harness", "claude-code harness", "codex-cli
    harness" etc. All three forms (snake_case, hyphenated, spaced) are recognised so a
    future editor who writes the hyphenated or spaced form -- not just the exact
    policy key -- is checked, never false-positived. Values are derived from the YAML
    keys; assertions never hardcode a harness name.
    """
    spelling_to_key: dict[str, str] = {}
    for key in harness_keys:
        lower = key.lower()
        for spelling in (lower, lower.replace("_", "-"), lower.replace("_", " ")):
            spelling_to_key[spelling] = key
    return spelling_to_key


def _alternation(items: list[str]) -> str:
    return "|".join(re.escape(i) for i in sorted(items, key=len, reverse=True))


def _harness_claims(segment: str, spelling_to_key: dict[str, str]) -> list[tuple[str, str]]:
    """Find "<H> harness" mentions in a fragment -> (policy_harness_key, snippet).

    The trailing ``(?![A-Za-z0-9])`` boundary accepts a CJK parenthetical right after
    the word "harness" (e.g. ``harness（capable pool）``) while still rejecting a plain
    word that merely starts with the letters (e.g. "harnessed"). This matters because
    the §6.1 prose claim wraps onto two physical lines and is re-joined by the prose
    shape before this runs.
    """
    spellings = sorted(spelling_to_key, key=len, reverse=True)
    pattern = re.compile(r"\b(" + _alternation(spellings) + r")\s+harness\b(?![A-Za-z0-9])", re.IGNORECASE)
    return [
        (spelling_to_key[m.group(1).lower()], m.group(0))
        for m in pattern.finditer(segment)
    ]


def _role_key(line: str) -> str | None:
    """The single role key a line's tokens resolve to, or None if none/ambiguous.

    The trailing ``(?![-_])`` guard keeps command- and product-tokens from being read as
    role nouns: "worker-start" / "worker-release" / "worker_done" and "root-owned" are
    orchestration or prose tokens, NOT role->harness claim subjects. A genuine role label
    ("Root /", "Execution Lead /", a table cell) is never immediately followed by a
    hyphen or underscore, so this excludes only non-role matches.
    """
    found = {
        role
        for role, tokens in ROLE_CLAIM_TOKENS.items()
        if re.search(
            r"\b(?:%s)\b(?![-_])" % _alternation(tokens), line, re.IGNORECASE
        )
    }
    return found.pop() if len(found) == 1 else None


def _table_row_claims(line: str, spelling_to_key) -> list[tuple[str, str, str]]:
    """A markdown table row -> (role_key, harness_key, snippet) for role+harness cells.

    The role must be a cell that appears BEFORE the harness cell, so a Notes column
    that happens to mention a different role noun (e.g. ``Root 决定``) cannot add a
    competing role token to the same row.
    """
    cells = [c.strip() for c in line.split("|")[1:-1]]
    harness_indices = [
        i for i, cell in enumerate(cells) if _harness_claims(cell, spelling_to_key)
    ]
    if not harness_indices:
        return []
    role_cells = {
        _role_key(cell)
        for cell in cells[: harness_indices[0]]
        if _role_key(cell)
    }
    if len(role_cells) != 1:
        return []
    role_key = next(iter(role_cells))
    claims = []
    for i, cell in enumerate(cells):
        if i < harness_indices[0]:
            continue
        for harness_key, snippet in _harness_claims(cell, spelling_to_key):
            claims.append((role_key, harness_key, snippet))
    return claims


def _fence_claims(block: str, spelling_to_key) -> list[tuple[str, str, str]]:
    """A fenced diagram block -> role->harness claims via nearest preceding role label."""
    claims = []
    current_role = None
    for line in block.splitlines():
        harness = _harness_claims(line, spelling_to_key)
        role = _role_key(line)
        if harness:
            owner = role if role is not None else current_role
            if owner is not None:
                for harness_key, snippet in harness:
                    claims.append((owner, harness_key, snippet))
        if role is not None:
            current_role = role
    return claims


def _prose_units(text: str) -> list[str]:
    """Running prose / structured list text -> sentence units for role->harness claims.

    A role->harness prose claim can wrap across physical lines (the §6.1 sentence does:
    ``默认偏好使用 Claude Code\nharness（capable pool）``), so it is re-joined before it
    is split into sentences. Blank lines and the start of a bullet/numbered list item
    bound a unit so two unrelated items are never fused into one pseudo-sentence.
    """
    units: list[str] = []
    parts = re.split(r"\n\s*\n|\n[ \t]*(?:[-*+] |\d+\. )", text)
    for part in parts:
        collapsed = re.sub(r"\s+", " ", part).strip()
        if not collapsed:
            continue
        for sentence in re.split(r"(?<=[。！？.!?])\s*", collapsed):
            sentence = sentence.strip()
            if sentence:
                units.append(sentence)
    return units


def _prose_claims(sentence: str, spelling_to_key) -> list[tuple[str, str, str]]:
    """Bilingual prose / structured list role->harness claims in one sentence.

    A role noun followed (within a short gap) by an explicit binding operator and then
    a recognised "<H> harness" phrase. The binding operator is what separates a real
    role->harness assignment from mere co-occurrence, so a compound English sentence
    that separately says "the default is the Pi Standard/Fast Lead (pi harness ...)"
    and "the Root selects the Codex Premium Lead" does NOT associate Root with "pi
    harness". Chinese §6.1 form (``默认偏好使用 <H> harness``) and English forms
    (``prefers/default is/uses <H> harness`` / ``default ... for <H>``) are both
    recognised, keeping the check bilingual like the live documents.
    """
    bind = (
        r"(?:默认偏好(?:使用)?|默认provider偏好\s*为?|[ ]?provider偏好\s*为?|"
        r"偏好\s*为|default\s+(?:is|s\s+to)|prefers?|uses?|绑定(?:为|到|于))"
    )
    harness_alt = _alternation(sorted(spelling_to_key, key=len, reverse=True))
    claims: list[tuple[str, str, str]] = []
    for role, tokens in ROLE_CLAIM_TOKENS.items():
        role_alt = _alternation(tokens)
        pattern = re.compile(
            rf"\b(?:{role_alt})\b(?![-_])[^\n]{{0,60}}?{bind}"
            rf"[^\n]{{0,20}}?(?:the\s+|an\s+|a\s+)?({harness_alt})\s+harness",
            re.IGNORECASE,
        )
        for match in pattern.finditer(sentence):
            harness_key = spelling_to_key[match.group(1).lower()]
            claims.append((role, harness_key, match.group(0)))
    return claims


def _role_harness_claims(path: Path, spelling_to_key) -> list[tuple[str, str, str, str]]:
    """All recognisable (role_key, harness_key, shape, snippet) claims in one document."""
    raw = strip_historical_escape_hatch(path.read_text(encoding="utf-8", errors="replace"))
    claims: list[tuple[str, str, str, str]] = []
    # Shape 2: markdown table rows live outside code fences.
    for line in raw.splitlines():
        if line.lstrip().startswith("|"):
            for role_key, harness_key, snippet in _table_row_claims(line, spelling_to_key):
                claims.append((role_key, harness_key, "md-table", snippet))
    # Shape 3: fenced diagram blocks.
    for block in fenced_code_blocks(raw):
        for role_key, harness_key, snippet in _fence_claims(block, spelling_to_key):
            claims.append((role_key, harness_key, "fence", snippet))
    # Shapes 1 & 4: bilingual prose sentence and structured list item. Both are running
    # text carrying a role noun plus a binding-operator role->harness assignment, so
    # the same sentence-level, binding-gated sweep covers them.
    non_fence = re.sub(r"```[^\n]*\n.*?```", "", raw, flags=re.DOTALL)
    for sentence in _prose_units(non_fence):
        for role_key, harness_key, snippet in _prose_claims(sentence, spelling_to_key):
            claims.append((role_key, harness_key, "prose", snippet))
    return claims


# Sorted alternation of every recognisable role-noun spelling, used by the F4
# harness-first assignment scan below.
_ROLE_TOKEN_ALT = _alternation(
    sorted(
        {token for tokens in ROLE_CLAIM_TOKENS.values() for token in tokens},
        key=len,
        reverse=True,
    )
)

# The binding forms the two harness-first role-assignment defects used-and-closed by F4.
# Deliberately narrow: only these exact binders are checked, never generic 'for'/
# 'default ... for', so pointer-style 'per routing.yaml Pi is the default harness for
# <Role>' sentences (which legitimately describe the policy default) never trip the guard.
_HARNESS_ASSIGN_BINDERS = ("assigned to", "used for")


def _harness_assignment_claims_on_text(
    text: str, spelling_to_key, subject_harness: str
) -> list[tuple[str, str]]:
    """Harness-first '<H> is assigned to <Role> ...' / '<H> used for <Role> ... work' claims.

    A harness file is about one harness, so the subject of an 'assigned to' / 'used for ...
    work' sentence is resolved to the file's harness (passed as ``subject_harness``). We
    match only the exact binder forms the F1 defect used and require the role noun(s)
    immediately after the binder, so conditional hedges ('used in other roles ... only
    when') and pointer-style references to routing.yaml never match. Returns a list of
    (role_key, snippet) pairs.
    """
    text = strip_historical_escape_hatch(text)
    findings: list[tuple[str, str]] = []
    for binder in _HARNESS_ASSIGN_BINDERS:
        pattern = re.compile(
            rf"\b{re.escape(binder)}\b\s+(?:the\s+|a\s+|an\s+)?"
            rf"(?P<roles>{_ROLE_TOKEN_ALT}(?:[ \t]*[,，、and&]+\s*{_ROLE_TOKEN_ALT})*)",
            re.IGNORECASE,
        )
        for match in pattern.finditer(text):
            segment = match.group("roles")
            roles = {
                role
                for role, tokens in ROLE_CLAIM_TOKENS.items()
                for token in tokens
                if re.search(
                    rf"(?<![\w-])\b{re.escape(token)}\b(?:-(?![ \t]))*(?!\w)",
                    segment,
                    re.IGNORECASE,
                )
            }
            for role in sorted(roles):
                findings.append((role, match.group(0)[:90]))
    return findings


def _file_harness_assignment_claims(path: Path, spelling_to_key) -> list[tuple[str, str, str]]:
    """The harness-first 'assigned to/used for <Role>' claims in ONE harness file.

    Returns (role_key, harness_key, snippet) triples where harness_key is the harness the
    file documents (its own harness), enabling a direct check against routing.yaml's
    allowed/default harness for that role. Non-harness files and files whose subject
    harness the map does not know return no claims.
    """
    rel = str(path.relative_to(ROOT))
    file_harness_key = HARNESS_FILE_TO_KEY.get(rel)
    if file_harness_key is None:
        return []
    raw = strip_historical_escape_hatch(
        path.read_text(encoding="utf-8", errors="replace")
    )
    return [
        (role, file_harness_key, snippet)
        for role, snippet in _harness_assignment_claims_on_text(
            raw, spelling_to_key, file_harness_key
        )
    ]


ROOT_TO_LEAD_EXISTING_WORKTREE_BASE_REQUIREMENT = """
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


class ArchitecturePolicyTests(unittest.TestCase):
    def load_yaml(self, relative_path: str):
        if yaml is None:
            self.skipTest(
                "PyYAML is not installed and this repository declares no Python dependencies"
            )
        return yaml.safe_load(read(relative_path))


    def test_policy_yaml_parses_and_declares_exactly_four_cognitive_roles(self) -> None:
        """One canonical policy file; exactly four cognitive roles; no retired V3 role."""
        policy = self.load_yaml(".agent/policy.yaml")
        self.assertEqual(["root", "lead", "delegate", "reviewer"], policy["cognitive_roles"])
        self.assertEqual(
            sorted(["root", "lead", "delegate", "reviewer"]),
            sorted(policy["routing"]["role_preference"]),
        )
        flat = read(".agent/policy.yaml").lower()
        for retired in ("worker", "platform_steward", "supervisor", "meta_root", "memory_agent"):
            self.assertNotIn(retired, flat, f"retired cognitive role key in policy: {retired}")
        self.assertFalse(policy["routing"]["preferences_are_permanent_bindings"])

    def test_v4_role_model_and_escalation_types(self) -> None:
        """Structural: exactly four cognitive roles, recursive Child Root, and the three
        semantic escalation types. Replaces the V3 numbered closed re-entry contract."""
        for path in ("AGENTS.md", "docs/ARCHITECTURE.md"):
            document = read(path)
            for role in ("Root", "Lead", "Delegate", "Reviewer"):
                self.assertIn(role, document, path)
            self.assertIn("Child Root", document, path)
            for escalation in (
                "DECISION_REQUIRED",
                "UNCERTAINTY_UNRESOLVED",
                "AUTHORITY_BLOCKED",
            ):
                self.assertIn(escalation, document, path)

        standing = read("AGENTS.md")
        for retired in (
            "Worker",
            "Platform Steward",
            "Supervisor",
            "Meta Root",
            "Memory Agent",
            "Orca",
            "Execution Packet",
        ):
            self.assertNotIn(
                retired, standing, f"retired V3 concept in standing source: {retired}"
            )



    def test_review_independence_and_verdict_preservation(self) -> None:
        """Fresh context-isolated Reviewer, minimal material, independently preserved
        verdict, Lead not the sole transport. Canonical home: .agent/procedures/review.md."""
        procedure = normalize(read(".agent/procedures/review.md")).lower()
        self.assertIn("fresh", procedure)
        self.assertIn("context-isolated", procedure)
        self.assertIn("integrity evidence", procedure)
        self.assertIn("may not rewrite, suppress or redefine", procedure)
        self.assertIn("without the lead as sole transport", procedure)
        self.assertIn("contractual", procedure)

        architecture = normalize(read("docs/ARCHITECTURE.md")).lower()
        self.assertIn("fresh, context-isolated reviewer", architecture)
        self.assertIn("lead owns the review/fix loop", architecture)

        independence = self.load_yaml(".agent/policy.yaml")["review"]["independence"]
        self.assertTrue(independence["reviewer_must_be_fresh_and_context_isolated"])
        self.assertIn("cross_provider", independence["provider_diversity_when_required"])

    def test_no_current_document_claims_codex_is_the_default_root(self) -> None:
        historical_adr = ROOT / "docs/decisions/ADR-001-orca-first-execution-plane.md"
        # The original set was AGENTS.md + README.md + everything under docs/ and
        # .agent/: this repo-root-to-docs/.agent tracked set minus CLAUDE.md. Shared
        # tracked_architecture_documents() keeps the set identical to the old coverage
        # while excluding untracked .agent/runs/ telemetry by construction.
        documents = set(tracked_architecture_documents()) - {ROOT / "CLAUDE.md"}

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



    def test_review_requirement_has_exactly_one_canonical_source(self) -> None:
        """R2: policy.review is the sole source deciding WHETHER review is required.
        Routing carries no legacy independent_review mirror."""
        policy = self.load_yaml(".agent/policy.yaml")
        review = policy["review"]
        self.assertTrue(review["canonical_source"])
        self.assertIs(False, review["levels"]["low"]["review_required"])
        self.assertEqual("conditional", review["levels"]["medium"]["review_required"])
        self.assertIs(True, review["levels"]["high"]["review_required"])

        def keys(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    yield k
                    yield from keys(v)
            elif isinstance(node, list):
                for item in node:
                    yield from keys(item)

        routing_keys = set(keys(policy["routing"]))
        self.assertNotIn("independent_review", routing_keys, "legacy mirror in routing")
        self.assertNotIn("review_required", routing_keys, "routing must not decide review")
        self.assertEqual("whether_review_is_required", policy["routing"]["never_decides"])

    def test_escalation_format_is_type_question_evidence(self) -> None:
        """One escalation asks one concrete question, in a fixed three-part shape."""
        architecture = normalize(read("docs/ARCHITECTURE.md"))
        for part in ("TYPE", "QUESTION", "EVIDENCE"):
            self.assertIn(part, architecture, part)
        self.assertIn("one concrete question", architecture.lower())
        self.assertIn("TYPE / QUESTION / EVIDENCE", normalize(read("AGENTS.md")))

    def test_no_live_provider_as_role_binding_anywhere(self) -> None:
        """Bilingual no-provider-as-role invariant across ALL live architecture text.

        This is NOT a string-pin test: it targets the defect CLASS through the bilingual
        provider/role vocabularies and the binding operators defined above. What it
        genuinely enforces, and its honest limits, are:

        - It flags a provider/model-pool name bound to a role noun in the documented
          forms (adjacency incl. a markdown table pipe `|`, "is"/"are"/"run by",
          "for", ":", "=", "role:", "agent:", and the Chinese operators provider 偏好 /
          默认 provider / 偏好为 / 绑定 / 是) in English OR Chinese.
        - Harness-class vocabulary stays expressible: claude_code / codex_cli / pi are
          harnesses, "Pi" is never a pool, and an intervening qualifier (Premium,
          Standard/Fast, "Claude Code harness") breaks the adjacency.
        - It is a syntactic scan, not semantic proof. A binding phrased with an operator
          the documented pattern set does not cover could still evade and must be
          reported, never asserted away.
        - It does not scan structural YAML key/value assignments (config preference), and
          it trusts the HISTORICAL-BINDING escape hatch for genuinely superseded
          narration; ADR-001/002/003 are excluded by path.
        """
        failures = []
        for path in live_architecture_documents():
            for name, matched in provider_bindings_in_document(path):
                failures.append(
                    f"{name} binding in {path.relative_to(ROOT)}: {matched!r}"
                )
        if failures:
            self.fail(
                "Live architecture text binds a provider name to an agent role:\n"
                + "\n".join(failures)
            )

    def test_guard_catches_documented_evasion_cases(self) -> None:
        """Every reproducible evasion E1-E14 must now FAIL the guard when present.

        These are the 14 rewording+insertion cases the review pass mounted against the
        previous English-only, line-anchored regexes; all 14 previously passed. The guard
        must catch every one. Harness-class vocabulary (Pi Standard/Fast Lead, Codex
        Premium escalation, claude_code, codex_cli) must still pass.
        """
        evasions = {
            "E1 Execution Lead: Codex": "Execution Lead: Codex",
            "E2 Codex Lead for every task": "Codex Lead for every task",
            "E3 DeepSeek Worker dispatched by the Lead": "DeepSeek Worker dispatched by the Lead",
            "E4 Root agent: Claude": "Root agent: Claude",
            "E5 The Execution Lead is always Codex.": "The Execution Lead is always Codex.",
            "E6 Execution Worker = DeepSeek": "Execution Worker = DeepSeek",
            "E7 Codex Execution Leads own delivery": "Codex Execution Leads own delivery",
            "E8 Codex-Execution-Lead owns delivery": "Codex-Execution-Lead owns delivery",
            "E9 Codex Specialist owns hard problems": "Codex Specialist owns hard problems",
            "E10 Platform Steward: Claude": "Platform Steward: Claude",
            "E11 role triple": (
                "Execution Lead role: Codex. "
                "Execution Worker role: DeepSeek. "
                "Root role: Claude."
            ),
            "E12 newline gap": "Execution Lead\nprovider: Codex",
            "E13 run by": "The Execution Lead is run by Codex on every task.",
            "E14 verbatim pre-amendment Chinese": (
                "Execution Lead 是 first-class Engineering Control Plane，默认 provider "
                "偏好为 Codex，但不是永久绑定。"
            ),
            # Table rows are live architecture text too: a role CELL bound to a bare
            # provider CELL across one `|` must trip the guard. This is the exact
            # reintroduction vector the reviewer's P11 observation confirmed (and the
            # shape of the §7 preference table itself, which caused the T1 contradiction
            # to survive four passes unseen).
            "E15 table row role-provider cell": "| Execution Lead | Codex |",
            "E16 table header + row": "| Role | Provider |\n|---|---|\n| Execution Lead | Codex |",
        }
        for label, inserted in evasions.items():
            findings = provider_bindings_in_text(inserted)
            self.assertTrue(
                findings,
                f"guard failed to catch {label}: {inserted!r}",
            )

        legit = [
            "Root prefers the Claude Code harness with a capable pool",
            "Codex Premium Lead",
            "Pi Standard/Fast Lead",
            # Corrected §7 preference-table rows pair a role CELL with a HARNESS + POOL
            # description CELL, never a bare provider - they must not trip the guard even
            # with the pipe separator in play.
            "| Root / Cognitive Control Plane | claude_code harness + capable pool |",
            "| Execution Lead Standard/Fast | pi harness + low-cost pool |",
            "| Execution Lead Premium | codex-cli harness + codex pool |",
            "| Well-scoped implementation | low-cost pool (e.g. deepseek) |",
            "Claude Code harness default / capable pool",
            "Pi Standard/Fast default becomes Codex Premium escalation on difficult work",
            "codex-cli harness + codex pool",
            "claude_code harness",
            "没有任何 harness 或 model/provider pool 是永久 role binding",
            "Worker role 不绑定任何 model/provider pool",
            "Root / Execution Lead / Worker / Reviewer 是动态角色，不与 provider 永久绑定",
        ]
        for phrase in legit:
            self.assertEqual(
                [],
                provider_bindings_in_text(phrase),
                f"false positive on legitimate harness vocabulary: {phrase!r}",
            )


    def test_guard_escape_hatch_and_config_distinction(self) -> None:
        """Historical narration (escape hatch) and machine-readable policy config both stay
        unflagged, while the same clause in live prose is flagged."""
        historical = 'the single "Codex Execution Lead" binding'
        self.assertTrue(provider_bindings_in_text(historical), "quote should flag as live prose")
        marked = (
            "<!-- HISTORICAL-BINDING-START: superseded pre-ADR-004 binding -->\n"
            + historical
            + "\n<!-- HISTORICAL-BINDING-END -->"
        )
        self.assertEqual(
            [], provider_bindings_in_text(marked), "escape hatch must un-flag historical prose"
        )
        self.assertEqual(
            [],
            provider_bindings_in_document(ROOT / ".agent" / "policy.yaml"),
            "policy config keys must not be flagged as prose role bindings",
        )

    def test_historical_binding_escape_hatch_only_in_adr_004(self) -> None:
        """T3: the HISTORICAL-BINDING escape hatch exists so genuinely superseded
        narration can be quoted verbatim, but it must never be used to park a LIVE binding
        in a current document. The reviewer confirmed escape-hatch use is "abusable only by
        writing a false label, unaudited by any test". This assertion makes every usage
        audited deterministically: the marker may appear only in
        docs/decisions/ADR-004-*.md. Any occurrence in ARCHITECTURE.md, AGENTS.md,
        README.md, a runbook, a role/harness/provider profile, or a policy file fails here
        instead of relying on a reader to notice a false label.
        """
        scanned = tracked_architecture_documents()

        offenders = []
        for path in scanned:
            if "HISTORICAL-BINDING" not in path.read_text(
                encoding="utf-8", errors="replace"
            ):
                continue
            rel = path.relative_to(ROOT)
            allowed = path.parent.name == "decisions" and path.name.startswith(
                "ADR-004-"
            )
            if not allowed:
                offenders.append(str(rel))
        self.assertEqual(
            [],
            offenders,
            "HISTORICAL-BINDING escape hatch used outside docs/decisions/ADR-004-*.md",
        )


    def test_capability_profile_integrity(self) -> None:
        """V4 capability profiles exist, are least-capability gated, and carry no
        Worker or Platform Steward profile."""
        caps = self.load_yaml(".agent/policy.yaml")["capabilities"]
        self.assertIn("least_capability", caps)
        self.assertIn("progressive_disclosure", caps)
        profiles = caps["profiles"]
        for required in ("root-standard", "lead-standard", "delegate-readonly",
                         "delegate-writable", "reviewer-independent"):
            self.assertIn(required, profiles, required)
        for name in profiles:
            self.assertFalse(name.startswith("worker-"), name)
            self.assertFalse(name.startswith("platform-steward"), name)
        catalog = caps["catalog"]
        for granted in (c for p in profiles.values() for c in p["includes"]):
            self.assertIn(granted, catalog, granted)
        self.assertTrue(catalog["delegate-integration"]["sensitive"])


    def test_efficiency_principles_exist(self) -> None:
        policy = self.load_yaml(".agent/policy.yaml")
        principles = policy["efficiency"]["principles"]
        for required in (
            "use_the_cheapest_capable_resource",
            "prefer_deterministic_tools_tests_and_evals_before_model_calls",
            "delegate_when_result_is_needed_but_process_need_not_remain_in_parent_context",
            "report_compressed_evidence_not_transcripts_or_reasoning_dumps",
            "reasoning_effort_is_not_a_token_savings_lever",
        ):
            self.assertIn(required, principles, required)

    def test_caveman_is_not_a_dependency(self) -> None:
        """No external tool is a hard dependency of the policy surface."""
        policy = read(".agent/policy.yaml").lower()
        for forbidden in ("caveman", "required_tool:", "hard_dependency"):
            self.assertNotIn(forbidden, policy, forbidden)


    def test_reasoning_effort_is_not_a_token_savings_lever(self) -> None:
        """Reasoning effort is a correctness parameter: it must not appear as a cost lever."""
        policy = self.load_yaml(".agent/policy.yaml")
        efficiency = policy["efficiency"]
        self.assertIn("reasoning_effort_is_not_a_token_savings_lever", efficiency["principles"])
        for lever in efficiency["cost_levers"]:
            self.assertNotIn("reasoning", lever, lever)
        self.assertTrue(efficiency["premium_adaptivity"]["low_cost_reasoning_stays_high"])

    def test_premium_capability_and_reasoning_effort_are_adaptive(self) -> None:
        adaptivity = self.load_yaml(".agent/policy.yaml")["efficiency"]["premium_adaptivity"]
        self.assertTrue(adaptivity["allowed"])
        self.assertEqual("root", adaptivity["envelope_owner"])
        self.assertTrue(adaptivity["hardcoded_high_forbidden"])
        self.assertTrue(adaptivity["low_cost_reasoning_stays_high"])

    def test_efficiency_does_not_weaken_review_guardrails(self) -> None:
        """Cost optimisation may never reach the review requirement."""
        policy = self.load_yaml(".agent/policy.yaml")
        levers = yaml.safe_dump(policy["efficiency"])
        for forbidden in ("review_required", "independent_review", "skip_review"):
            self.assertNotIn(forbidden, levers, forbidden)
        self.assertIs(True, policy["review"]["levels"]["high"]["review_required"])


    def test_role_harness_binding_guard_with_positive_control(self) -> None:
        """The role->harness parser is proven against synthetic fixtures, then swept over
        the live tree. A guard whose only evidence is 'the repo happens to be clean' cannot
        show it still detects anything, so the positive control runs first."""
        spelling_to_key = _harness_spelling_map(["pi", "claude_code", "codex_cli"])

        # POSITIVE CONTROL: each fixture is an illegal role->harness binding and the
        # parser MUST resolve it to a (role, harness) pair.
        illegal = {
            "table row": "| Root | pi harness | owns the outcome |",
            "prose": "The Reviewer is assigned to the codex-cli harness for every task.",
            "fenced": "```text\nRoot -> claude-code harness\n```",
        }
        for shape, fixture in illegal.items():
            with self.subTest(positive_control=shape):
                detected = (
                    _prose_claims(fixture, spelling_to_key)
                    + _table_row_claims(fixture, spelling_to_key)
                    + _fence_claims(fixture, spelling_to_key)
                )
                self.assertTrue(
                    detected,
                    f"parser missed an illegal role->harness binding ({shape}): {fixture!r}",
                )

        # NEGATIVE CONTROL: a plain capability description names a harness but binds no
        # role, and must not be flagged.
        for legal in (
            "Claude Code is an interactive terminal harness running Claude models.",
            "Pi is a harness whose model is selected at runtime from a configured pool.",
        ):
            with self.subTest(negative_control=legal):
                self.assertEqual([], _prose_claims(legal, spelling_to_key), legal)

        # LIVE SWEEP: the V4 architecture and standing surfaces bind no role to a harness.
        for path in ("AGENTS.md", "docs/ARCHITECTURE.md", ".agent/capabilities.md"):
            self.assertEqual(
                [],
                _role_harness_claims(ROOT / path, spelling_to_key),
                f"{path} must not bind a role to a harness",
            )


    def test_capability_descriptor_cannot_assign_roles(self) -> None:
        """The capability descriptor answers WHAT a harness/provider can do, never WHICH
        role must use it. Role selection belongs to policy."""
        descriptor = read(".agent/capabilities.md")
        self.assertEqual([], provider_bindings_in_document(ROOT / ".agent" / "capabilities.md"))
        for role_word in ("Root", "Lead", "Delegate", "Reviewer", "Worker", "Platform Steward"):
            self.assertNotIn(
                role_word, descriptor, f"capability descriptor names a role: {role_word}"
            )
        self.assertIn("resolved by policy", descriptor)

    def test_agents_md_stays_within_budget(self) -> None:
        """V4: the always-loaded standing source is one short file. The V3 207-line
        instruction layer must not grow back."""
        agents = read("AGENTS.md")
        lines = agents.count("\n") + 1
        size = len(agents.encode("utf-8"))
        self.assertLessEqual(lines, 60, "AGENTS.md exceeds the V4 standing-source line budget")
        self.assertLessEqual(size, 4096, "AGENTS.md exceeds the V4 standing-source byte budget")

    def test_detailed_lifecycle_not_duplicated_in_always_loaded_files(self) -> None:
        """The detailed writable-work procedure lives in the load-on-demand layer, never
        in the always-loaded standing source."""
        agents = read("AGENTS.md")
        for marker in ("immutable base commit", "resources_clean", "cherry-pick", "--session"):
            self.assertNotIn(marker, agents, marker)
        procedure = read(".agent/procedures/writable-work.md")
        self.assertIn("immutable base commit", procedure)
        self.assertIn("resources_clean", procedure)
        self.assertIn("--session", procedure)

    def test_retry_budget_has_one_canonical_source(self) -> None:
        """The review/fix budget lives in exactly one place and is bounded."""
        policy = self.load_yaml(".agent/policy.yaml")
        retry = policy["retry"]
        self.assertTrue(retry["canonical_source"])
        loop = retry["review_loop"]
        self.assertIsInstance(loop["max_cycles"], int)
        self.assertGreater(loop["max_cycles"], 0)
        self.assertIs(False, loop["may_continue_editing_after_exhaustion"])
        # The number itself must not be duplicated into the always-loaded surface.
        for path in ("AGENTS.md", "docs/ARCHITECTURE.md"):
            self.assertNotIn(f"max_cycles", read(path), path)

    def test_review_authority_boundary_and_safeguards(self) -> None:
        """Retry cannot require review; routing cannot override it; safeguards may be
        strengthened but never silently weakened."""
        policy = self.load_yaml(".agent/policy.yaml")
        self.assertIs(False, policy["retry"]["may_require_review"])
        guards = policy["review"]["safeguards"]
        self.assertIs(False, guards["may_be_silently_weakened"])
        self.assertIs(False, guards["routing_may_override_review_required"])
        self.assertIs(False, guards["retry_may_require_review"])
        self.assertEqual(["human", "root"], guards["may_be_strengthened_by"])


    def test_review_triggers_resolve_conditional_and_may_only_add(self) -> None:
        """Triggers resolve `medium: conditional` deterministically and can only ADD
        review. A trigger list read as exhaustive must never exempt HIGH work."""
        review = self.load_yaml(".agent/policy.yaml")["review"]
        triggers = review["triggers"]

        self.assertEqual("review.levels.medium.review_required", triggers["resolves"])
        self.assertEqual("level_requirement_first_then_triggers", triggers["precedence"])
        self.assertTrue(triggers["may_only_add"])
        self.assertTrue(triggers["never_reduces_level_requirement"])

        categories = triggers["categories"]
        self.assertEqual(
            ["money_movement", "data_mutation", "permissions_and_credentials",
             "destructive_operations"],
            list(categories),
        )
        for name, category in categories.items():
            self.assertTrue(category["requires_independent_review"], name)
            self.assertTrue(category["matches"], name)

        # HIGH keeps its own requirement regardless of any trigger match.
        self.assertIs(True, review["levels"]["high"]["review_required"])
        for example in ("backtesting", "look_ahead_sensitive_logic", "adjustment_factor_logic"):
            self.assertIn(example, review["levels"]["high"]["examples"], example)

        otherwise = triggers["otherwise"]
        self.assertEqual("no_level_requirement_and_no_category_match", otherwise["condition"])
        self.assertEqual("not_required_by_trigger", otherwise["review_required"])

        # destructive_operations is general, not migration-only.
        destructive = categories["destructive_operations"]["matches"]
        self.assertIn("destructive_migrations", destructive)
        self.assertGreater(
            len([m for m in destructive if m != "destructive_migrations"]), 1,
            "destructive_operations must cover general destruction, not only migrations",
        )

        # Human-gate overlaps are pointers, never a competing second rule.
        for name in ("permissions_and_credentials", "destructive_operations"):
            reference = categories[name]["human_gate_reference"]
            self.assertIn("does not restate or relax", reference, name)

    def test_no_mandatory_handoff_memory_scratch_subsystem(self) -> None:
        """V4 has no Memory Agent and no mandatory handoff/scratch knowledge store.
        Continuation is the Context Checkpoint; durable knowledge is Git/GitHub."""
        for relative in ("AGENTS.md", "docs/ARCHITECTURE.md", ".agent/policy.yaml",
                         ".agent/procedures/checkpoint.md"):
            low = read(relative).lower()
            for marker in ("handoff.md", "scratch.md", "# handoff", "memory agent"):
                if marker == "memory agent" and "no memory agent" in low:
                    continue
                self.assertNotIn(marker, low, f"{relative}: {marker}")

    def test_minimal_task_contract_and_return_envelope(self) -> None:
        """Four-field task contract, six-field return envelope, COMMIT only for writable
        work. Policy - not the task author - derives execution metadata."""
        for path in ("AGENTS.md", "docs/ARCHITECTURE.md"):
            document = read(path)
            for field in ("GOAL", "ACCEPTANCE", "CONSTRAINTS", "OVERRIDES"):
                self.assertIn(field, document, path)
            for field in (
                "STATUS",
                "RESULT",
                "EVIDENCE",
                "BLOCKERS",
                "UNCERTAINTY",
                "ARTIFACT",
            ):
                self.assertIn(field, document, path)
            self.assertIn("COMMIT", document, path)

        architecture = normalize(read("docs/ARCHITECTURE.md")).lower()
        for owned in ("review route", "human gate", "capability envelope", "retry budget"):
            self.assertIn(owned, architecture, owned)
        self.assertIn("never silently weakened", architecture)

    def test_writable_work_base_and_isolation(self) -> None:
        """Writable work starts from an explicit immutable base with provenance and
        cannot silently mutate the protected checkout."""
        procedure = normalize(read(".agent/procedures/writable-work.md")).lower()
        self.assertIn("immutable base commit", procedure)
        self.assertIn("provenance", procedure)
        self.assertIn("must not silently mutate", procedure)
        self.assertIn("isolated worktree", procedure)

    def test_writable_work_integration_is_lead_owned_and_verified(self) -> None:
        """The Lead owns verified integration, and orchestration lineage is never
        accepted as Git ancestry."""
        procedure = normalize(read(".agent/procedures/writable-work.md")).lower()
        self.assertIn("lead owns", procedure)
        self.assertIn("ancestry", procedure)
        self.assertIn("linearity", procedure)
        self.assertIn("orchestration lineage is **not** git ancestry", procedure)

    def test_writable_work_cleanup_and_resources_clean(self) -> None:
        """Dirty work is never silently discarded, and resources_clean is derived from
        post-conditions rather than a cleanup command's return value."""
        procedure = normalize(read(".agent/procedures/writable-work.md")).lower()
        self.assertIn("dirty worktree must be resolved", procedure)
        self.assertIn("must not silently discard uncommitted work", procedure)
        self.assertIn("not routine authority", procedure)
        self.assertIn("post-conditions", procedure)
        self.assertIn("resources_clean: false", procedure)
        self.assertIn("prevents normal final acceptance", procedure)

        architecture = normalize(read("docs/ARCHITECTURE.md")).lower()
        self.assertIn("post-condition verification", architecture)
        self.assertIn("resources_clean: false", architecture)

    def test_review_routing_cannot_weaken_the_review_requirement(self) -> None:
        """R2 clause 3: when review is required, routing must resolve an eligible
        independent reviewer, and may never downgrade the requirement."""
        routing = self.load_yaml(".agent/policy.yaml")["routing"]
        route = routing["review_route"]
        self.assertTrue(route["when_review_required_must_resolve_eligible_reviewer"])
        self.assertIs(False, route["may_downgrade_to_none_or_optional"])
        self.assertEqual("escalate_authority_blocked", route["on_no_eligible_reviewer"])
        eligibility = yaml.safe_dump(route["eligibility"])
        self.assertIn("fresh_context_isolated_session", eligibility)
        self.assertIn("strong_independent", eligibility)

    def test_human_gates_are_policy_owned_and_agent_immutable(self) -> None:
        """The protected gate list has a canonical home and no agent may relax it."""
        gates = self.load_yaml(".agent/policy.yaml")["human_gates"]
        self.assertIs(False, gates["may_be_relaxed_by_agent"])
        for protected in (
            "production_trading_permissions",
            "destructive_data_access_restrictions",
            "secret_and_credential_protections",
            "high_risk_independent_review_requirement",
            "order_and_capital_safety_guardrails",
            "maximum_budget_and_concurrency_limits",
            "production_deployment_gates",
            "minimum_backup_retention",
        ):
            self.assertIn(protected, gates["protected"], protected)

    def test_retired_agent_surfaces_are_gone(self) -> None:
        """Retired V3 surfaces must not return to the tracked tree: the role, harness,
        provider and multi-file policy layers, the Orca writable-delegation Skill, the
        Orca runbook, the in-repo Orca GUI persistence units, and placeholder-only
        scaffolding that no longer has a V4 purpose."""
        tracked = set(tracked_repository_paths() or [])

        retired_files = (
            ".agent/skills/orca-writable-delegation/SKILL.md",
            "docs/runbooks/ORCA_WORKFLOW.md",
        )
        for relative in retired_files:
            self.assertNotIn(ROOT / relative, tracked, f"retired file returned: {relative}")

        retired_trees = (
            ".agent/roles", ".agent/harnesses", ".agent/providers", ".agent/policies",
            ".agent/skills", ".agent/runs", "infra", "src", "controller", "data", "evals",
        )
        for directory in retired_trees:
            present = sorted(
                str(p.relative_to(ROOT)) for p in tracked
                if str(p.relative_to(ROOT)).startswith(directory + "/")
            )
            self.assertEqual([], present, f"retired tree has tracked files: {directory}")

        # The V4 agent surface is exactly policy, capabilities and load-on-demand procedures.
        agent_surface = sorted(
            str(p.relative_to(ROOT)) for p in tracked
            if str(p.relative_to(ROOT)).startswith(".agent/")
        )
        self.assertEqual(
            [".agent/capabilities.md", ".agent/policy.yaml"],
            [p for p in agent_surface if not p.startswith(".agent/procedures/")],
        )
        self.assertTrue([p for p in agent_surface if p.startswith(".agent/procedures/")])

    def test_remote_work_runbook_is_current_v4_not_orca_runtime(self) -> None:
        """The remote-work runbook describes the current runtime, not the retired one."""
        runbook = read("docs/runbooks/REMOTE_WORK.md").lower()
        for retired in ("worker-start", "worker-release", "orca-ide", "orca gui",
                        "dispatch", "orca"):
            self.assertNotIn(retired, runbook, f"retired Orca mechanic in runbook: {retired}")

    def test_herdr_session_targeting_safety_is_documented(self) -> None:
        """Explicit --session targeting, and the reason HERDR_SESSION alone is unsafe,
        must survive in the canonical procedure and in the remote-work runbook."""
        for relative in ("docs/runbooks/REMOTE_WORK.md", ".agent/procedures/writable-work.md"):
            document = read(relative)
            self.assertIn("--session", document, relative)
            self.assertIn("HERDR_SOCKET_PATH", document, relative)
            self.assertIn("HERDR_SESSION", document, relative)

    def test_writable_work_reuse_requires_clean_declared_base(self) -> None:
        """Reusing an existing writable worktree is safe only when it is clean AND already
        at the declared immutable base. A mismatch must never be resolved by moving an
        existing result branch onto the requested base.

        This invariant previously lived only in the retired writable-delegation Skill; it
        is general Git/worktree safety and belongs to the V4 canonical procedure.
        """
        procedure = normalize(read(".agent/procedures/writable-work.md")).lower()

        # 1. reuse requires a clean worktree
        self.assertIn("may be reused **only when both hold**", procedure)
        self.assertIn("it is clean", procedure)

        # 2. reuse requires the existing base/provenance to already match the declared base
        self.assertIn("base and provenance already match the declared immutable base", procedure)

        # 3. a mismatch must not be forced by repointing an existing result branch
        for forbidden_move in ("reset", "repoint", "retarget"):
            self.assertIn(forbidden_move, procedure, forbidden_move)
        self.assertIn("do not reset, repoint, retarget", procedure)
        self.assertIn("fresh isolated worktree and a fresh result branch", procedure)
        self.assertIn("escalate rather than forcing the reuse", procedure)





if __name__ == "__main__":
    unittest.main()

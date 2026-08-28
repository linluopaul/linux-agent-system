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
HARNESS_FILE_TO_KEY = {
    ".agent/harnesses/pi.md": "pi",
    ".agent/harnesses/claude-code.md": "claude_code",
    ".agent/harnesses/codex-cli.md": "codex_cli",
}


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


WRITABLE_WORKER_LIFECYCLE_DOCUMENTS = (
    ".agent/skills/orca-writable-delegation/SKILL.md",
    "docs/ARCHITECTURE.md",
    "docs/runbooks/ORCA_WORKFLOW.md",
    "docs/decisions/ADR-003-lead-worker-git-integration-contract.md",
)

SUPERVISED_ROOT_TO_LEAD_DOCUMENTS = (
    ".agent/skills/orca-writable-delegation/SKILL.md",
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
            "Orca as the execution and review plane",
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

        # v2.1.1: the six conditions have ONE canonical full wording in AGENTS.md; role
        # files reference that canonical invariant rather than duplicate it.
        conditions = (
            "architecture materially changes",
            "acceptance criteria are ambiguous",
            "difficult diagnosis remains unresolved",
            "the review loop reaches its cap (3 cycles) without passing",
            "deterministic verification cannot resolve uncertainty",
            "execution is blocked by something outside the Execution Lead's authority—a "
            "protected human gate, a missing authorization or credential, an exhausted "
            "budget or concurrency limit, an unavailable required dependency, or "
            "acceptance criteria that are infeasible or mutually contradictory",
        )
        # v3 (ADR-007): the LIVE canonical set is the three live documents. ADR-002 is a
        # point-in-time record and is deliberately NOT updated, so it is no longer required
        # to carry the live wording; its historical wording is pinned separately below.
        canonical_documents = {
            "AGENTS.md": read("AGENTS.md"),
            "docs/ARCHITECTURE.md": read("docs/ARCHITECTURE.md"),
            "docs/runbooks/ORCA_WORKFLOW.md": read(
                "docs/runbooks/ORCA_WORKFLOW.md"
            ),
        }
        for path, document in canonical_documents.items():
            normalized = normalize(document)
            self.assertIn("closed", normalized.lower(), path)
            for condition in conditions:
                self.assertIn(condition, normalized, path)

        # Narrow historical-preservation assertion. ADR-002 must keep the PRE-v3 wording of
        # condition 4 verbatim so the point-in-time record cannot be silently rewritten -
        # and must NOT be read as current policy: ADR-007 supersedes condition 4, and the
        # live wording must not have leaked into the ADR.
        adr_002 = normalize(
            read("docs/decisions/ADR-002-cognitive-and-engineering-control-planes.md")
        )
        self.assertIn("Root re-entry is a closed list", adr_002)
        self.assertIn("HIGH-risk independent review is required", adr_002)
        self.assertNotIn(
            "the review loop reaches its cap (3 cycles) without passing", adr_002
        )
        adr_007 = read("docs/decisions/ADR-007-review-loop-ownership.md")
        self.assertIn("Status: Accepted", adr_007)
        self.assertIn(
            "the review loop reaches its cap (3 cycles) without passing", adr_007
        )

        # Role files must reference the canonical list; each references AGENTS.md as the
        # single canonical full wording and never carries the whole six again.
        for role_path in (
            ".agent/roles/execution-lead.md",
            ".agent/roles/root.md",
        ):
            text = read(role_path)
            normalized = normalize(text)
            self.assertIn("six-condition", normalized.lower(), role_path)
            self.assertIn("AGENTS.md", normalized, role_path)
            self.assertLess(
                sum(1 for c in conditions if c in normalized),
                len(conditions),
                role_path,
            )

        for path in (
            "AGENTS.md",
            ".agent/roles/execution-lead.md",
            ".agent/roles/root.md",
        ):
            normalized = normalize(read(path))
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
                "REVIEW MATERIAL CONTRACT",
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
            "docs/ARCHITECTURE.md",
            "docs/runbooks/ORCA_WORKFLOW.md",
            ".agent/skills/orca-writable-delegation/SKILL.md",
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
            ".agent/skills/orca-writable-delegation/SKILL.md": 1,
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
        skill = ".agent/skills/orca-writable-delegation/SKILL.md"
        documents = {
            skill: normalize(read(skill)),
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
            skill,
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
            documents[skill],
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
        for path in (skill, ".agent/roles/worker.md", "docs/ARCHITECTURE.md"):
            self.assertIn("stop and escalate", documents[path].lower(), path)
        for path in (skill, ".agent/roles/worker.md", "docs/runbooks/ORCA_WORKFLOW.md"):
            self.assertIn("git reset --hard", documents[path], path)
            self.assertIn("git checkout -B", documents[path], path)
            self.assertIn("preserve", documents[path].lower(), path)

    def test_v1_integration_operation_is_cherry_pick(self) -> None:
        skill = ".agent/skills/orca-writable-delegation/SKILL.md"
        documents = {
            skill: normalize(read(skill)),
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
            ".agent/skills/orca-writable-delegation/SKILL.md": (
                "do not merge the worker branch, reset the lead branch to worker head, "
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
            ".agent/skills/orca-writable-delegation/SKILL.md",
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
            ".agent/skills/orca-writable-delegation/SKILL.md",
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
            ".agent/skills/orca-writable-delegation/SKILL.md",
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
            ".agent/skills/orca-writable-delegation/SKILL.md",
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
            ".agent/skills/orca-writable-delegation/SKILL.md",
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
        """S3: historical narration (escape hatch) and policy-config both stay unflagged.

        The same historical clause is FLAGGED as a live prose binding but PASSES once it
        is wrapped in the HISTORICAL-BINDING escape hatch; and a machine-readable config
        preference (`reviewer: claude`) is a key whose value is a pool name, so it must
        not be swept up as a prose role binding. routing.yaml carries such a key today.
        """
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

        routing = self.load_yaml(".agent/policies/routing.yaml")
        self.assertIn("claude", routing["risk"]["high"]["preferred_pool"]["reviewer"])
        self.assertEqual(
            [],
            provider_bindings_in_document(ROOT / ".agent" / "policies" / "routing.yaml"),
            "policy-config preference keys must not be flagged as prose role bindings",
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
            "REVIEW MATERIAL CONTRACT",
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
        role_harness_dirs = (ROOT / ".agent" / "roles", ROOT / ".agent" / "harnesses")
        tracked = tracked_repository_paths()
        if tracked is None:
            role_harness_paths = [
                p for d in role_harness_dirs if d.exists() for p in d.rglob("*") if p.is_file()
            ]
        else:
            role_harness_paths = [
                p for p in tracked if any(_is_under(p, d) for d in role_harness_dirs)
            ]
        for path in role_harness_paths:
            self.assertNotIn(
                "caveman",
                path.read_text(encoding="utf-8", errors="replace").lower(),
                str(path.relative_to(ROOT)),
            )

        # Not a required or installed Skill or Extension. (No skill/extension shorthand
        # is present in the repo's .agent/skills; nothing installs Caveman.)
        skills_dir = ROOT / ".agent" / "skills"
        if skills_dir.exists():
            if tracked is None:
                skill_paths = [p for p in skills_dir.rglob("*") if p.is_file()]
            else:
                skill_paths = [p for p in tracked if _is_under(p, skills_dir)]
            for path in skill_paths:
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

        # The `typical` (standard-effort) profile was removed to close the residual
        # token-saving hole. EVERY LOW-COST profile keeps HIGH reasoning effort (never
        # lowered to save tokens); reasoning effort is a correctness parameter, not a cost
        # lever. Premium profiles are ADAPTIVE (see the dedicated premium-policy test).
        self.assertNotIn("typical", efficiency["profiles"])
        low_cost_profiles = [
            (name, profile.get("reasoning", ""))
            for name, profile in efficiency["profiles"].items()
            if profile.get("pool_class") == "low_cost"
            or not profile.get("pool_class")
        ]
        self.assertTrue(low_cost_profiles, "no low-cost profile to enforce HIGH reasoning")
        for name, reasoning in low_cost_profiles:
            self.assertEqual("high", reasoning, name)

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

    def test_premium_model_and_reasoning_effort_are_adaptive(self) -> None:
        """Premium model choice and reasoning effort are ADAPTIVE, never hard-coded HIGH
        everywhere. The policy is documented independently of whether any harness currently
        exposes the switching primitive."""
        efficiency = self.load_yaml(".agent/policies/efficiency.yaml")
        self.assertIn(
            "premium_model_and_reasoning_effort_are_adaptive", efficiency["principles"]
        )
        adaptivity = efficiency.get("premium_adaptivity", {})
        self.assertTrue(adaptivity.get("allowed"))
        self.assertEqual(
            "root_or_supervisor", adaptivity.get("envelope_owner")
        )
        self.assertTrue(adaptivity.get("hardcoded_high_forbidden"))
        decision_points = adaptivity.get("decisions_occur_at", [])
        for point in (
            "task_start",
            "major_phase_boundary",
            "evidence_based_escalation",
        ):
            self.assertIn(point, decision_points)

        # No premium profile may hard-code HIGH; the premium profile is adaptive.
        premium = [
            p
            for p in efficiency["profiles"].values()
            if p.get("pool_class") == "premium"
        ]
        self.assertTrue(premium, "no premium (adaptive) profile is declared")
        for profile in premium:
            self.assertNotEqual("high", profile.get("reasoning"), "premium must be adaptive")
            self.assertEqual("adaptive", profile.get("reasoning"))

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

    def test_live_role_harness_claims_agree_with_policy(self) -> None:
        """v2.1: every live role->harness statement agrees with routing.yaml.

        routing.yaml is the single source of truth: the blessed role->harness mapping
        and the recognised harness spellings are both read from the YAML, never
        hardcoded. The test sweeps all four recognisable claim shapes (md table cell,
        fenced diagram block, bilingual prose sentence, and any other structured list
        item) across every live architecture document and asserts that each claim
        names a harness policy actually allows for that role. A stale "pi harness for
        Root", "pi harness for Root in the §7 table", or a stale pi-Root prose claim
        each fails below. The recognised-harness-forms constraint the helpers enforce
        (a claim is checked only when it appears in one of these shapes and names the
        harness in a recognised spelling) is documented next to the helpers and is
        intentionally strict to avoid false positives.
        """
        routing = self.load_yaml(".agent/policies/routing.yaml")
        defaults = routing["defaults"]
        preferred = defaults["preferred_harness"]
        allowed = {role: [preferred[role]] for role in preferred}
        premium = defaults.get("execution_lead", {}).get("premium_escalation_harness")
        if premium and premium not in allowed["execution_lead"]:
            allowed["execution_lead"].append(premium)
        spelling_to_key = _harness_spelling_map(list(routing["harnesses"].keys()))

        failures = []
        discovered: list[str] = []
        total = 0
        for path in live_architecture_documents():
            for role_key, harness_key, shape, snippet in _role_harness_claims(
                path, spelling_to_key
            ):
                total += 1
                discovered.append(
                    f"{path.relative_to(ROOT)} [{shape}] {role_key} -> "
                    f"{harness_key} :: {snippet!r}  "
                    f"(policy allows {sorted(allowed.get(role_key, []))})"
                )
                if harness_key not in allowed.get(role_key, []):
                    failures.append(
                        f"{path.relative_to(ROOT)} [{shape}] role '{role_key}' claims "
                        f"harness '{harness_key}' but routing.yaml defaults."
                        f"preferred_harness allows {sorted(allowed.get(role_key, []))} "
                        f":: {snippet!r}"
                    )

        # The sweep must have actually seen claims, or it cannot have closed the class.
        self.assertGreater(total, 0, "cross-check swept no role->harness claims")
        if failures:
            self.fail(
                "Live role->harness claim(s) contradict routing.yaml "
                "defaults.preferred_harness:\n" + "\n".join(failures)
            )

    def test_harness_files_cannot_claim_role_assignment_contradicting_policy(self) -> None:
        """F1/F4 guard: a harness file may not use the harness-first prose forms 'assigned
        to <Role>' or 'used for <Role> work' to claim a role assignment that routing.yaml
        does not default/prefer that harness for.

        The F1 defect is exactly the shape this guard closes: pi.md claimed Pi 'is assigned
        to Root, Reviewer, Worker and Specialist work' even though routing.yaml sets
        `defaults.preferred_harness.root: claude_code`. The v2.1 role-first cross-check
        (test_live_role_harness_claims_agree_with_policy) missed it because the claim is
        harness-first - the reverse of the four role-first shapes it models. This guard
        closes only that named prose form and never the pointer-style 'per routing.yaml'
        sentences.
        """
        routing = self.load_yaml(".agent/policies/routing.yaml")
        defaults = routing["defaults"]
        preferred = defaults["preferred_harness"]
        allowed = {role: [preferred[role]] for role in preferred}
        premium = defaults.get("execution_lead", {}).get("premium_escalation_harness")
        if premium and premium not in allowed["execution_lead"]:
            allowed["execution_lead"].append(premium)
        spelling_to_key = _harness_spelling_map(list(routing["harnesses"].keys()))

        # The guard MUST fail on the exact pre-fix pi.md claim (mutation (a), also covered
        # in the scratch-checkout bar) and pass on the corrected text.
        pre_fix = (
            "Per that file Pi is the standard Execution Lead harness class and is "
            "assigned to Root, Reviewer, Worker and Specialist work where a cheap "
            "low-cost harness fits."
        )
        self.assertTrue(
            _harness_assignment_claims_on_text(pre_fix, spelling_to_key, "pi"),
            "F4 guard must catch the pre-fix 'assigned to Root' claim",
        )
        corrected = (
            "Per that file Pi is the standard Execution Lead harness class and is the "
            "default harness for Reviewer, Worker, Specialist and Platform Steward work; "
            "the Root default harness is Claude Code (root: claude_code), not Pi."
        )
        self.assertEqual(
            [],
            _harness_assignment_claims_on_text(corrected, spelling_to_key, "pi"),
            "false positive on corrected pi.md role-routing prose",
        )

        failures = []
        for path in (ROOT / ".agent" / "harnesses").glob("*.md"):
            for role_key, harness_key, snippet in _file_harness_assignment_claims(
                path, spelling_to_key
            ):
                if harness_key not in allowed.get(role_key, []):
                    failures.append(
                        f"{path.relative_to(ROOT)} claims harness '{harness_key}' is "
                        f"assigned/used for role '{role_key}' but routing.yaml "
                        f"defaults.preferred_harness allows "
                        f"{sorted(allowed.get(role_key, []))} :: {snippet!r}"
                    )
        if failures:
            self.fail(
                "Live harness-first role-assignment claim contradicts routing.yaml:\n"
                + "\n".join(failures)
            )

    def test_skill_preserves_existing_worktree_reuse_invariant(self) -> None:
        """v2.1.1 F2: the guarded worktree-reuse invariant must live at its canonical home
        in the writable-delegation Skill, stated independently of any version-specific flag
        mechanics.

        This invariant survived only in the ORCA_WORKFLOW runbook after the diet, so an
        agent loading the Skill (the canonical writable-delegation source) never learned it.
        Removing it from the Skill fails this test (mutation (b), also in the scratch-
        checkout bar).
        """
        skill_path = ".agent/skills/orca-writable-delegation/SKILL.md"
        skill = normalize(read(skill_path)).lower()
        self.assertIn(
            "an existing worktree may be reused only when it is clean and already at the "
            "declared base",
            skill,
        )
        self.assertIn(
            "creates a fresh worker branch without repointing an existing result branch",
            skill,
        )
        # The concrete command sequence stays in the runbook; the Skill references it
        # rather than duplicating the version-specific alignment recipe.
        self.assertIn("ORCA_WORKFLOW.md", read(skill_path))

    def test_agents_md_stays_within_budget(self) -> None:
        """The always-loaded invariant layer stays small (diet target). A regression
        back to the 450-line / ~20.6KB pre-diet AGENTS.md must fail this guard."""
        agents = read("AGENTS.md")
        lines = agents.count("\n") + 1
        size = len(agents.encode("utf-8"))
        self.assertLess(lines, 210, "AGENTS.md line count exceeds the instruction-diet budget")
        self.assertLess(size, 13_000, "AGENTS.md byte size exceeds the instruction-diet budget")

    def test_detailed_lifecycle_not_duplicated_in_always_loaded_files(self) -> None:
        """The detailed writable-lifecycle procedure is NOT duplicated into the always-
        loaded layer; it lives at its canonical home in the load-on-demand Skill."""
        agents = read("AGENTS.md")
        skill = read(".agent/skills/orca-writable-delegation/SKILL.md")
        # AGENTS.md carries invariants and pointers only, never the detailed procedure.
        for marker in (
            "Lead creates Worker through",
            "git cherry-pick --skip",
            "ALREADY_PRESENT",
        ):
            self.assertNotIn(marker, agents, marker)
        # The canonical home retains the full procedure.
        self.assertIn("Lead creates Worker through", skill)
        self.assertIn("ALREADY_PRESENT", skill)
        self.assertIn("git cherry-pick --skip", skill)

    def test_agents_md_immutable_base_invariant_and_skill_pointer(self) -> None:
        agents = read("AGENTS.md")
        self.assertIn("integration_base_sha", agents)
        self.assertIn(".agent/skills/orca-writable-delegation/SKILL.md", agents)

    def test_six_condition_list_has_single_canonical_copy(self) -> None:
        conditions = (
            "architecture materially changes",
            "acceptance criteria are ambiguous",
            "difficult diagnosis remains unresolved",
            "the review loop reaches its cap (3 cycles) without passing",
            "deterministic verification cannot resolve uncertainty",
            "execution is blocked by something outside the Execution Lead's authority—a "
            "protected human gate, a missing authorization or credential, an exhausted "
            "budget or concurrency limit, an unavailable required dependency, or "
            "acceptance criteria that are infeasible or mutually contradictory",
        )
        agents = normalize(read("AGENTS.md"))
        for condition in conditions:
            self.assertIn(condition, agents)
        # No role file carries the full six-condition list again.
        for role_path in (
            ".agent/roles/execution-lead.md",
            ".agent/roles/root.md",
            ".agent/roles/worker.md",
            ".agent/roles/reviewer.md",
            ".agent/roles/platform-steward.md",
        ):
            text = normalize(read(role_path))
            self.assertLess(
                sum(1 for c in conditions if c in text),
                len(conditions),
                role_path,
            )

    def test_harness_files_do_not_declare_role_default_independently(self) -> None:
        routing = self.load_yaml(".agent/policies/routing.yaml")
        # routing.yaml is the normative role->harness source; Pi is a harness, not a pool.
        self.assertIn("pi", routing["harnesses"])
        self.assertNotIn("pi", routing["model_pools"])
        self.assertEqual("claude_code", routing["defaults"]["preferred_harness"]["root"])
        self.assertEqual("pi", routing["defaults"]["preferred_harness"]["execution_lead"])
        self.assertEqual(
            "codex_cli", routing["defaults"]["execution_lead"]["premium_escalation_harness"]
        )
        # Every harness file points to routing.yaml for role preference; none independently
        # declares a role default, and the "believed default" hedge is removed.
        for harness in ("pi", "claude-code", "codex-cli"):
            text = read(f".agent/harnesses/{harness}.md")
            self.assertIn("routing.yaml", text, harness)
            self.assertIn("bound", text.lower(), harness)
        self.assertNotIn("believed default", read(".agent/harnesses/pi.md").lower())
        # Pi's durable identity no longer names a host-specific default pool.
        self.assertNotIn("default pool is", read(".agent/harnesses/pi.md").lower())

    def test_medium_review_budget_is_bounded(self) -> None:
        retry = self.load_yaml(".agent/policies/retry.yaml")
        medium = retry["review_budget"]["medium"]
        self.assertTrue(medium["applies_when_review_is_required"])
        for key in ("initial_review", "fix_cycles", "focused_re_reviews"):
            self.assertIsInstance(medium[key], int, key)
            self.assertGreaterEqual(medium[key], 1, key)
        self.assertEqual("return_to_root_for_diagnosis", medium["on_further_blocking"])

    def test_review_authority_boundary_retry_cannot_require_review(self) -> None:
        """AMENDMENT 1: retry.yaml may govern only how many review cycles run AFTER
        review is required; it must never itself make review required. risk.yaml remains
        the sole authority for whether independent review is required."""
        retry = self.load_yaml(".agent/policies/retry.yaml")
        import json as _json

        flat = _json.dumps(retry)
        self.assertNotIn("independent_review", flat)
        self.assertNotIn("make review required", flat)
        risk = self.load_yaml(".agent/policies/risk.yaml")
        self.assertEqual("conditional", risk["levels"]["medium"]["independent_review"])
        self.assertEqual("required", risk["levels"]["high"]["independent_review"])

        # v3 (ADR-007): the Lead-owned review/fix loop has a hard ceiling here. The ceiling
        # bounds a loop that risk.yaml has already required; the assertNotIn above still
        # proves this file cannot make review required itself.
        loop = retry["review_loop"]
        self.assertEqual(3, loop["max_cycles"])
        self.assertEqual("stop_and_return_to_root", loop["on_exhaustion"])
        self.assertFalse(loop["lead_may_continue_editing_after_exhaustion"])

    def test_review_triggers_resolve_conditional_without_weakening_high(self) -> None:
        """E-1: risk.yaml carries a deterministic review-trigger procedure that resolves
        `levels.medium.independent_review: conditional`, and it may only ADD review.

        The defect class this closes is drift: an unresolved `conditional` is re-argued on
        every task and the re-argument drifts loose. The second defect class is a subtler
        one - a trigger list read as EXHAUSTIVE would silently exempt HIGH work that
        matches none of the four categories. Both are asserted below.
        """
        risk = self.load_yaml(".agent/policies/risk.yaml")
        triggers = risk["review_triggers"]

        # 1. All four categories exist and each one REQUIRES review.
        categories = triggers["categories"]
        self.assertEqual(
            [
                "money_movement",
                "data_mutation",
                "permissions_and_credentials",
                "destructive_operations",
            ],
            list(categories),
        )
        for name, category in categories.items():
            self.assertTrue(category["requires_independent_review"], name)
            self.assertTrue(category["matches"], name)

        # 2. Direction is add-only, and the procedure is bound to the state it resolves.
        self.assertTrue(triggers["may_only_add"])
        self.assertTrue(triggers["never_reduces_level_requirement"])
        self.assertEqual("levels.medium.independent_review", triggers["resolves"])
        self.assertEqual(
            "level_requirement_first_then_triggers", triggers["precedence"]
        )

        # 3. HIGH keeps its own requirement, independent of any trigger match.
        self.assertEqual("required", risk["levels"]["high"]["independent_review"])
        self.assertEqual("conditional", risk["levels"]["medium"]["independent_review"])

        # 4. The concrete anti-downgrade cases: HIGH examples that need not match any
        #    category above must remain HIGH, so the fallback can never reach them.
        high_examples = risk["levels"]["high"]["examples"]
        for example in (
            "backtesting",
            "look_ahead_sensitive_logic",
            "adjustment_factor_logic",
        ):
            self.assertIn(example, high_examples, example)

        # 5. The fallback is gated on BOTH conditions and never overrides a level.
        otherwise = triggers["otherwise"]
        self.assertEqual(
            "no_level_requirement_and_no_category_match", otherwise["condition"]
        )
        self.assertEqual("not_required_by_trigger", otherwise["independent_review"])
        self.assertIn("tests_must_still_run_and_pass", otherwise["then"])
        self.assertIn("already requires review", otherwise["note"])

        # 6. destructive_operations is general, not migration-only.
        destructive = categories["destructive_operations"]["matches"]
        self.assertIn("destructive_migrations", destructive)
        self.assertGreater(
            len([m for m in destructive if m != "destructive_migrations"]),
            1,
            "destructive_operations must cover general destruction, not only migrations",
        )

        # 7. Human-gate overlaps are pointers, never a competing second rule.
        for name in ("permissions_and_credentials", "destructive_operations"):
            reference = categories[name]["human_gate_reference"]
            self.assertIn("AGENTS.md", reference, name)
            self.assertIn("does not restate or relax", reference, name)

        # 8. The architecture doc points at this procedure instead of re-deciding.
        architecture = read("docs/ARCHITECTURE.md")
        self.assertIn("`review_triggers`", architecture)

    def test_writable_conditional_block_is_mandatory_when_used(self) -> None:
        """CORE/CONDITIONAL: conditionality is not optionality — when writable delegation
        is used, the writable block is mandatory."""
        agents = normalize(read("AGENTS.md"))
        self.assertIn(
            "when writable delegation is used, the writable block is mandatory",
            agents.lower(),
        )
        for field in (
            "WORKTREE / BASE COMMIT",
            "LEAD BRANCH",
            "INTEGRATION_BASE_SHA",
            "ALLOWED CHANGED PATHS / SCOPE",
            "VERIFICATION REQUIREMENTS",
            "RESULT MODE",
        ):
            self.assertIn(field, agents, field)
        self.assertIn("CORE", agents)
        self.assertIn("CONDITIONAL", agents)

    def test_no_mandatory_handoff_memory_scratch_subsystem(self) -> None:
        """The diet must not introduce a second state system: no mandatory HANDOFF,
        memory hierarchy, SCRATCH, or automatic-Learnings protocol in the governed docs."""
        governed = [
            "AGENTS.md",
            ".agent/skills/orca-writable-delegation/SKILL.md",
            ".agent/roles/root.md",
            ".agent/roles/execution-lead.md",
            ".agent/roles/worker.md",
        ]
        for relative in governed:
            low = read(relative).lower()
            for marker in ("handoff.md", "scratch.md", "# handoff", "# memory", "learnings"):
                self.assertNotIn(marker, low, f"{relative}: {marker}")


if __name__ == "__main__":
    unittest.main()

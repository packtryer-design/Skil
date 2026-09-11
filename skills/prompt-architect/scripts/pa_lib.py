"""Shared helpers for the Prompt Architect tooling.

Provides frontmatter parsing (templates), parsing of the Architect's output
format (Compilation Summary / Questions / Review / Prompt / Notes), and a
deterministic lint of compiled prompts. Standard library only; PyYAML is used
for frontmatter when installed, with a small fallback parser otherwise.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

SKILL_DIR = Path(__file__).resolve().parent.parent
ROOT = SKILL_DIR.parent.parent

DOMAINS = ["software", "security", "research", "documents", "data", "business", "content", "meta"]
RISKS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
MODES = [
    "ADVISOR", "ANALYST", "RESEARCHER", "ARCHITECT", "ENGINEER", "EXECUTOR",
    "REVIEWER", "TEACHER", "AGENT", "ORCHESTRATOR", "HYBRID",
]
AUTONOMY = ["A0", "A1", "A2", "A3", "A4"]
LEVELS = [1, 2, 3, 4]
# Named runtime profiles (references/runtime-profiles.md). The older free-text host
# names are kept as aliases so earlier outputs still parse.
TARGETS = [
    "claude-code", "claude-ai", "coding-agent", "open-webui", "ollama", "lm-studio",
    "api-no-tools", "custom-agent", "unknown",
]
TARGET_ALIASES = {
    "claude code": "claude-code",
    "claude.ai chat": "claude-ai",
    "claude.ai": "claude-ai",
    "api without tools": "api-no-tools",
    "api": "api-no-tools",
    "agent with tools": "coding-agent",
    "cursor": "coding-agent",
    "codex": "coding-agent",
    "cline": "coding-agent",
    "jan": "lm-studio",
    "msty": "lm-studio",
    "llama.cpp": "lm-studio",
    "vllm": "api-no-tools",
}
TEMPLATE_STATUSES = ["candidate", "draft", "tested", "stable"]
TEMPLATE_CATEGORIES = [
    "software", "security", "research", "documents", "business", "data", "content", "meta",
    "skill", "local",
]

# Capability of the model that will execute the artifact, ordered strongest first.
MODEL_TIERS = ["frontier", "mid", "small", "tiny"]

# What the runtime provides, as opposed to what the model can do (references/capabilities.md).
CAPABILITIES = [
    "files.read", "files.write", "shell", "code.run", "web.search", "web.fetch", "browser",
    "db", "git", "vision", "audio", "image.gen", "structured.output", "mcp", "network",
]
CAPABILITY_VALUES = ["yes", "no", "unknown"]
ARTIFACTS = ["prompt", "template", "skill"]

# Skill upgrader: a folder of user-added references that adapt what the Architect
# generates (references/skill-upgrader.md). Consulted in the working project first,
# then in the project that contains this skill.
UPGRADER_DIRNAME = "skill-upgrader"
UPGRADER_SAMPLES_DIRNAME = "examples"     # shipped samples; never applied
UPGRADER_TEMPLATES_DIRNAME = "templates"  # user templates, in the library format
UPGRADER_KEYS = {"name", "description", "domains", "artifacts", "targets", "models", "kinds"}
# Any one of these makes an artifact executable; without all three, A3/A4 and
# EXECUTOR/AGENT are not available whatever the task wants.
EXECUTE_CAPABILITIES = ["shell", "code.run", "files.write"]
EXECUTING_MODES = ["EXECUTOR", "AGENT"]

CANONICAL_SECTIONS = [
    "Role", "Objective", "Context", "Task", "Requirements", "Constraints", "Assumptions",
    "Resources", "Operating Mode", "Autonomy", "Workflow", "Decision Rules", "Tool Rules",
    "Safety Boundaries", "Quality Standards", "Validation", "Testing", "Failure Handling",
    "Output Format", "Examples", "Completion Criteria", "Final Instructions",
]

# Accepted alternative headings, mapped to their canonical section.
SECTION_ALIASES = {
    "mission": "Objective",
    "goal": "Objective",
    "security": "Safety Boundaries",
    "safety": "Safety Boundaries",
    "boundaries": "Safety Boundaries",
    "change boundaries": "Safety Boundaries",
    "safety and security": "Safety Boundaries",
    "safety and change boundaries": "Safety Boundaries",
    "validation and testing": "Validation",
    "verification": "Validation",
    "output contract": "Output Format",
    "output": "Output Format",
    "deliverables": "Output Format",
    "deliverable": "Output Format",
    "report format": "Output Format",
    "done criteria": "Completion Criteria",
    "definition of done": "Completion Criteria",
    "completion": "Completion Criteria",
    "tools": "Tool Rules",
    "tool use": "Tool Rules",
    "decisions": "Decision Rules",
    "quality": "Quality Standards",
    "process": "Workflow",
    "steps": "Workflow",
    "method": "Workflow",
    "when blocked": "Failure Handling",
    "error handling": "Failure Handling",
    "inputs": "Resources",
    "materials": "Resources",
    "background": "Context",
    "scope": "Task",
    "example": "Examples",
    "worked example": "Examples",
    "worked examples": "Examples",
    "few-shot examples": "Examples",
    "example output": "Examples",
}

LENGTH_BUDGET = {1: 25, 2: 60, 3: 140, 4: 220}
# Warn only when a prompt exceeds the guideline by this factor.
LENGTH_TOLERANCE = 1.5

# Model tier caps. A weaker model gets fewer rules, sections, and tools plus worked
# examples -- not a longer prompt. See references/model-tiers.md.
TIER_LENGTH_FACTOR = {"frontier": 1.0, "mid": 1.0, "small": 1.5, "tiny": 1.0}
TIER_MAX_LINES = {"tiny": 30}          # hard line cap, whatever the level
TIER_MAX_SECTIONS = {"mid": 10, "small": 6, "tiny": 3}
TIER_MAX_TOOLS = {"small": 1, "tiny": 0}
TIER_SENTENCE_WORDS = {"mid": 25, "small": 20, "tiny": 12}
TIER_AUTONOMY_CAP = {"mid": 3, "small": 2, "tiny": 1}

# Tool-ish words counted inside a Tool Rules section to approximate the tool budget.
TOOL_WORD_RE = re.compile(
    r"\b(bash|shell|terminal|command line|read|write|edit|grep|glob|search|fetch|browser|"
    r"python|script|sql|api call|web search|web fetch)\b",
    re.I,
)
# Wording that asks the model to arbitrate; small models cannot.
CONDITIONAL_CUE_RE = re.compile(
    r"\b(unless|except when|if applicable|as appropriate|where relevant|where appropriate|"
    r"use your judgment|use your judgement|at your discretion|if necessary|when in doubt)\b",
    re.I,
)
PRIORITY_SOFT_RE = re.compile(r"\b(SHOULD|MAY)\b")

CAPABILITY_PAIR_RE = re.compile(r"\b([a-z]+(?:\.[a-z]+)?)\s*=\s*(yes|no|unknown)\b", re.I)
GAP_RE = re.compile(r"\b([a-z]+(?:\.[a-z]+)?)\s*\((blocking|non-blocking)\)", re.I)

# Instructions that imply a capability. Used by C01 (the no-fake-capability rule) and
# C04, and only ever consulted for a capability the profile states explicitly.
CAPABILITY_CLAIM_RE: list[tuple[str, re.Pattern]] = [
    ("files.write", re.compile(
        r"\b(edit|modify|update|patch|rewrite|create|delete|rename|save)\s+(the\s+|each\s+|every\s+|any\s+)?"
        r"(file|files|module|script|config\w*|source)\b|\bwrite (it|them|the \w+)\s+(to|into)\b|"
        r"\bapply the (patch|change|fix|edit)e?s?\b", re.I)),
    ("shell", re.compile(
        r"\brun\s+(the\s+|all\s+|any\s+)?(tests?|test suite|commands?|build|linter|lint|scripts?|migrations?)\b|"
        r"\bexecute\s+(the\s+)?(commands?|shell|scripts?)\b|\bin the terminal\b|\bfrom the (command line|shell)\b", re.I)),
    ("code.run", re.compile(
        r"\b(run|execute)\s+(the\s+|this\s+|your\s+)?code\b|\brun it and (report|check|verify|show)\b", re.I)),
    ("web.search", re.compile(
        r"\bsearch\s+(the\s+)?(web|internet|online)\b|\blook (it |them )?up online\b|\bweb search\b|"
        r"\bfind (the )?current\b", re.I)),
    ("web.fetch", re.compile(
        r"\b(fetch|retrieve|download|open)\s+(the\s+)?(url|link|page|web page|website)\b", re.I)),
    ("browser", re.compile(r"\b(use|open|drive)\s+(a\s+|the\s+)?browser\b|\bnavigate to\b", re.I)),
    ("db", re.compile(
        r"\b(query|connect to|inspect)\s+(the\s+)?(database|schema)\b|\brun the (sql|query) against\b", re.I)),
    ("git", re.compile(
        r"\bgit\s+(commit|push|pull|checkout|branch|merge|rebase)\b|\bopen a pull request\b|"
        r"\b(commit|push)\s+(the\s+|your\s+)?(change|work)s?\b", re.I)),
    ("vision", re.compile(
        r"\b(look at|examine|inspect|read|interpret)\s+(the\s+)?(image|screenshot|diagram|photo|picture)s?\b", re.I)),
    ("files.read", re.compile(
        r"\b(read|inspect|open|examine)\s+(the\s+|each\s+|every\s+)?"
        r"(file|files|repository|repo|codebase|directory|folder)\b", re.I)),
]
# A line that forbids the action, or offers it as a conditional or a fallback, is the
# prescribed way to handle a missing capability rather than a violation of it.
CAPABILITY_EXCUSE_RE = re.compile(
    r"\b(do not|don't|never|cannot|can not|can't|without|instead of|rather than|if you can|"
    r"if the|when you can|unable to|not available|unavailable|list the|ask the user)\b", re.I)
CONDITIONAL_PHRASING_RE = re.compile(
    r"\bif (you can|you are able|available|the \w+ is available)\b|\botherwise\b|\bwhen available\b|"
    r"\bif possible\b|\bif it is available\b", re.I)
FALLBACK_RE = re.compile(
    r"\b(instead|fallback|falls back|cannot|list the (exact )?commands?|paste|supply|"
    r"provide the|ask the user (to|for)|state (what|which))\b", re.I)

FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
VARIABLE_RE = re.compile(r"\{\{\s*([A-Z][A-Z0-9_]*)\s*\}\}")
ARCHITECT_COMMENT_RE = re.compile(r"<!--\s*architect:", re.I)
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


# ---------------------------------------------------------------------------
# Frontmatter
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a Markdown file into (frontmatter dict, body)."""
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?(.*)$", text, re.S)
    if not match:
        return {}, text
    raw, body = match.group(1), match.group(2)
    try:
        import yaml  # type: ignore

        try:
            meta = yaml.safe_load(raw) or {}
        except yaml.YAMLError:
            # Invalid YAML: fall back to the line parser so callers can still report on the file;
            # frontmatter_yaml_error() exposes the problem for linting.
            meta = _mini_yaml(raw)
        if not isinstance(meta, dict):
            meta = {}
    except ImportError:
        meta = _mini_yaml(raw)
    return meta, body


def frontmatter_yaml_error(text: str) -> str | None:
    """Return a message when the frontmatter is not valid YAML (None when valid or PyYAML is absent)."""
    match = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?", text, re.S)
    if not match:
        return None
    try:
        import yaml  # type: ignore
    except ImportError:
        return None
    try:
        yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        first = str(exc).splitlines()[0]
        return f"{first} (quote values that contain a colon followed by a space or that start with a quote)"
    return None


def _unquote(value: str):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    if value.lstrip("-").isdigit():
        return int(value)
    if value in ("true", "false"):
        return value == "true"
    return value


def _mini_yaml(raw: str) -> dict:
    """Parse the flat YAML subset used by template frontmatter.

    Supports `key: value`, `key: [a, b]`, and `key:` followed by `- item` lines.
    """
    meta: dict = {}
    current_list_key: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        item = re.match(r"^\s+-\s+(.*)$", line)
        if item and current_list_key is not None:
            meta[current_list_key].append(_unquote(item.group(1)))
            continue
        kv = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if not kv:
            continue
        key, value = kv.group(1), kv.group(2).strip()
        if value == "":
            meta[key] = []
            current_list_key = key
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            meta[key] = [_unquote(v) for v in inner.split(",")] if inner else []
            current_list_key = None
        else:
            meta[key] = _unquote(value)
            current_list_key = None
    return meta


# ---------------------------------------------------------------------------
# Architect output parsing
# ---------------------------------------------------------------------------

SKILL_KINDS = ["output-style", "workflow", "domain-expert", "tool-wrapper", "knowledge"]
FILE_HEADING_RE = re.compile(r"^###\s+`?([\w./@-][^`\s]*)`?\s*$")


@dataclass
class ArchitectOutput:
    raw: str
    summary: dict[str, str] = field(default_factory=dict)
    questions: list[str] = field(default_factory=list)
    review: str | None = None
    prompt: str | None = None
    notes: str | None = None
    has_summary: bool = False
    skill_files: dict[str, str] = field(default_factory=dict)
    skill_location: str | None = None
    compatibility: str | None = None

    # Derived fields ---------------------------------------------------------
    @property
    def artifact(self) -> str:
        """'prompt' (default), 'template', or 'skill'."""
        value = self.summary.get("artifact", "").strip().lower()
        if value.startswith("skill") or (not value and self.skill_files):
            return "skill"
        if value.startswith("template"):
            return "template"
        return "prompt"

    @property
    def skill_kind(self) -> str | None:
        value = self.summary.get("artifact", "").lower()
        for kind in SKILL_KINDS:
            if kind in value:
                return kind
        return None

    @property
    def tier(self) -> int | None:
        match = re.search(r"\btier\s*([1-3])\b", self.summary.get("artifact", "").lower())
        return int(match.group(1)) if match else None

    @property
    def skill_name(self) -> str | None:
        for path in self.skill_files:
            if path.endswith("SKILL.md"):
                parts = path.split("/")
                return parts[-2] if len(parts) >= 2 else None
        return None

    @property
    def skill_md(self) -> str | None:
        for path, content in self.skill_files.items():
            if path.endswith("SKILL.md") and "/.cursor/" not in "/" + path:
                return content
        return None
    @property
    def domains(self) -> list[str]:
        """Domains named in the summary, ignoring the parenthesized subdomains.

        Accepts `software (x) + security (y)` as specified, and tolerates commas,
        slashes, or "and" as separators.
        """
        value = re.sub(r"\([^)]*\)", " ", self.summary.get("domain", "").lower())
        found = []
        for part in re.split(r"\+|,|/|\band\b|&", value):
            match = re.match(r"\s*([a-z]+)", part.strip())
            if match and match.group(1) in DOMAINS and match.group(1) not in found:
                found.append(match.group(1))
        return found

    @property
    def risk(self) -> str | None:
        value = self.summary.get("risk", "").upper()
        for risk in RISKS:
            if re.search(rf"\b{risk}\b", value):
                return risk
        return None

    @property
    def modes(self) -> list[str]:
        value = self.summary.get("mode", "")
        tokens = re.findall(r"[A-Z]{4,}", value)
        return [t for t in tokens if t in MODES]

    @property
    def autonomy(self) -> str | None:
        match = re.search(r"\bA([0-4])\b", self.summary.get("autonomy", ""))
        return f"A{match.group(1)}" if match else None

    @property
    def level(self) -> int | None:
        match = re.search(r"\b([1-4])\b", self.summary.get("level", ""))
        return int(match.group(1)) if match else None

    @property
    def target(self) -> str | None:
        """The named runtime profile, accepting the older free-text host names."""
        value = self.summary.get("target", "").strip().lower()
        if not value:
            return None
        for name in TARGETS:
            if re.search(rf"\b{re.escape(name)}\b", value):
                return name
        for alias in sorted(TARGET_ALIASES, key=len, reverse=True):
            if alias in value:
                return TARGET_ALIASES[alias]
        return value

    @property
    def capabilities(self) -> dict[str, str]:
        """Recognized `name=value` pairs from the `Capabilities:` line."""
        found: dict[str, str] = {}
        for name, state in CAPABILITY_PAIR_RE.findall(self.summary.get("capabilities", "")):
            if name.lower() in CAPABILITIES:
                found[name.lower()] = state.lower()
        return found

    @property
    def capability_names(self) -> list[str]:
        """Every name written as a pair, recognized or not, for validation."""
        return [n.lower() for n, _ in CAPABILITY_PAIR_RE.findall(self.summary.get("capabilities", ""))]

    @property
    def capabilities_none_required(self) -> bool:
        return self.summary.get("capabilities", "").strip().lower().startswith("none")

    @property
    def gaps(self) -> list[tuple[str, str]]:
        """[(capability, 'blocking' | 'non-blocking')] from the `Gaps:` line."""
        value = self.summary.get("gaps", "")
        if value.strip().lower().startswith("none"):
            return []
        return [(name.lower(), kind.lower()) for name, kind in GAP_RE.findall(value)]

    @property
    def upgrades(self) -> list[str]:
        """Names of the skill-upgrader references the summary says were applied."""
        value = self.summary.get("upgrades", "").strip()
        if not value or value.lower().startswith("none"):
            return []
        return [re.sub(r"\.md$", "", n.strip().strip("`")) for n in value.split(",") if n.strip()]

    @property
    def model_tier(self) -> str | None:
        """The `Model:` tier. Reads the leading token first ('small (3B local)')."""
        value = self.summary.get("model", "").strip().lower()
        if not value:
            return None
        lead = re.match(r"`?([a-z]+)", value)
        if lead and lead.group(1) in MODEL_TIERS:
            return lead.group(1)
        for tier in MODEL_TIERS:
            if re.search(rf"\b{tier}\b", value):
                return tier
        return None

    @property
    def template(self) -> str | None:
        value = self.summary.get("template", "").strip()
        if not value or value.lower().startswith("none"):
            return None
        match = re.match(r"`?([a-z0-9][a-z0-9-]*)`?", value.lower())
        return match.group(1) if match else None

    @property
    def question_count(self) -> int:
        if self.questions:
            return len(self.questions)
        value = self.summary.get("questions", "").strip().lower()
        if not value or value.startswith("none") or value.startswith("0"):
            return 0
        match = re.match(r"(\d+)", value)
        return int(match.group(1)) if match else 1


def _split_top_sections(text: str) -> list[tuple[str, str]]:
    """Split Markdown into (heading, body) pairs on `## ` headings outside fences."""
    sections: list[tuple[str, list[str]]] = []
    fence_char: str | None = None
    fence_len = 0
    current_heading = ""
    current_lines: list[str] = []
    for line in text.splitlines():
        fence = FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)
            if fence_char is None:
                fence_char, fence_len = marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_len and line.strip() == marker:
                fence_char = None
        heading = HEADING_RE.match(line) if fence_char is None else None
        if heading:
            sections.append((current_heading, current_lines))
            current_heading, current_lines = heading.group(1).strip(), []
        else:
            current_lines.append(line)
    sections.append((current_heading, current_lines))
    return [(h, "\n".join(lines).strip("\n")) for h, lines in sections]


def _extract_fenced(body: str) -> str | None:
    """Return the content of the first fenced block in `body`.

    A fence of three backticks that contains nested three-backtick fences is
    handled by treating the last matching fence line as the closer.
    """
    lines = body.splitlines()
    opener_idx = None
    for idx, line in enumerate(lines):
        if FENCE_RE.match(line):
            opener_idx = idx
            break
    if opener_idx is None:
        return None
    marker = FENCE_RE.match(lines[opener_idx]).group(1)
    closers = [
        idx for idx in range(opener_idx + 1, len(lines))
        if lines[idx].strip() == marker or (
            lines[idx].strip().startswith(marker[0] * len(marker))
            and set(lines[idx].strip()) == {marker[0]}
        )
    ]
    if not closers:
        return "\n".join(lines[opener_idx + 1:]).strip("\n")
    closer_idx = closers[0] if len(marker) > 3 else closers[-1]
    return "\n".join(lines[opener_idx + 1:closer_idx]).strip("\n")


def parse_architect_output(text: str) -> ArchitectOutput:
    out = ArchitectOutput(raw=text)
    if "## Compilation Summary" not in text:
        # Bare prompt (no architect wrapper).
        out.prompt = text.strip()
        return out
    out.has_summary = True
    # Discard anything before the summary heading (assistant chatter).
    text = text[text.index("## Compilation Summary"):]
    for heading, body in _split_top_sections(text):
        key = heading.lower()
        if key.startswith("compilation summary"):
            for line in body.splitlines():
                match = re.match(r"^\s*[-*]\s*\**([A-Za-z ]+?)\**\s*:\s*(.*)$", line)
                if match:
                    out.summary[match.group(1).strip().lower()] = match.group(2).strip()
        elif key.startswith("questions"):
            out.questions = [
                m.group(1).strip()
                for m in re.finditer(r"^\s*\d+[.)]\s+(.*)$", body, re.M)
            ]
            if not out.questions and body.strip() and not body.strip().lower().startswith("none"):
                out.questions = [body.strip()]
        elif key.startswith("review"):
            out.review = body
        elif key.startswith("compatibility"):
            out.compatibility = body
        elif key.startswith("prompt"):
            out.prompt = _extract_fenced(body) or (body.strip() or None)
        elif key.startswith("skill"):
            out.skill_files, out.skill_location = _parse_skill_files(body)
        elif key.startswith("notes"):
            out.notes = body
    return out


def _parse_skill_files(body: str) -> tuple[dict[str, str], str | None]:
    """Parse '### <path>' headings each followed by a fenced block into {path: content}."""
    files: dict[str, str] = {}
    location = None
    lines = body.splitlines()
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        loc = re.match(r"^\s*(?:Written to|Location|Not written)\s*:\s*(.+)$", line, re.I)
        if loc and location is None:
            location = loc.group(1).strip().strip("`")
        heading = FILE_HEADING_RE.match(line)
        if heading:
            path = heading.group(1).strip()
            rest = "\n".join(lines[idx + 1:])
            content = _extract_fenced(rest)
            if content is not None:
                files[path] = content
                # Skip past the closing fence of this block.
                opener_idx = next((i for i in range(idx + 1, len(lines)) if FENCE_RE.match(lines[i])), None)
                if opener_idx is not None:
                    marker = FENCE_RE.match(lines[opener_idx]).group(1)
                    closer_idx = next((i for i in range(opener_idx + 1, len(lines)) if lines[i].strip() == marker), None)
                    idx = (closer_idx if closer_idx is not None else opener_idx) + 1
                    continue
        idx += 1
    return files, location


def materialize_skill_files(out: ArchitectOutput, root: Path) -> list[Path]:
    """Write parsed skill files under `root`; return the SKILL.md paths written."""
    skill_mds: list[Path] = []
    for rel_path, content in out.skill_files.items():
        safe = Path(*[p for p in Path(rel_path).parts if p not in ("..", "")])
        target = root / safe
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
        if target.name == "SKILL.md":
            skill_mds.append(target)
    return skill_mds


# ---------------------------------------------------------------------------
# Prompt structure
# ---------------------------------------------------------------------------

def canonical_section(heading: str) -> str | None:
    """Map a heading to its canonical section name, or None if unknown."""
    cleaned = re.sub(r"[*_`]", "", heading).strip().rstrip(":").lower()
    for name in CANONICAL_SECTIONS:
        if cleaned == name.lower():
            return name
    return SECTION_ALIASES.get(cleaned)


def prompt_sections(prompt: str) -> list[tuple[str, str | None, str]]:
    """Return [(raw heading, canonical name or None, body)] for a prompt."""
    result = []
    for heading, body in _split_top_sections(prompt):
        if heading:
            result.append((heading, canonical_section(heading), body))
    return result


def _rule_lines(prompt: str) -> list[str]:
    """Prose lines that carry rules.

    Skips fenced blocks, tables, headings, authoring comments, and the whole Examples
    section: worked examples are data, so their wording is not held to the tier's rules.
    """
    prompt = re.sub(r"<!--.*?-->", "", prompt, flags=re.S)
    lines: list[str] = []
    fence_char: str | None = None
    fence_len = 0
    in_examples = False
    for line in prompt.splitlines():
        fence = FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)
            if fence_char is None:
                fence_char, fence_len = marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_len and line.strip() == marker:
                fence_char = None
            continue
        if fence_char is not None:
            continue
        heading = HEADING_RE.match(line)
        if heading:
            in_examples = canonical_section(heading.group(1).strip()) == "Examples"
            continue
        stripped = line.strip()
        if in_examples or not stripped or stripped.startswith(("|", "#", ">")):
            continue
        lines.append(stripped)
    return lines


def _sentences(lines: Iterable[str]) -> list[str]:
    """Split rule lines into sentence units, one instruction each."""
    units: list[str] = []
    for line in lines:
        text = re.sub(r"`[^`]*`", "CODE", line)
        text = re.sub(r"^(?:[-*+]|\d+[.)])\s+", "", text)
        text = re.sub(r"^(?:MUST NOT|MUST|SHOULD NOT|SHOULD|MAY)\b:?\s*", "", text)
        for part in re.split(r"(?<=[.!?])\s+", text):
            part = part.strip()
            if part:
                units.append(part)
    return units


# ---------------------------------------------------------------------------
# Lint
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    severity: str  # "error" | "warning"
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.severity.upper():7} {self.code}: {self.message}"


CONTRADICTION_PAIRS = [
    (r"\b(do not|don\x27t|never) ask\b(?!\s+(before|for confirmation|for permission|when|if|unless|at|until))",
     r"\bask (the user |for )?(before|for confirmation|permission)\b",
     "'do not ask' conflicts with 'ask before'"),
    (r"\brewrite (everything|the (entire|whole)|from scratch)\b",
     r"\bminimal\b|\bwithin the requested scope\b|\bscoped\b",
     "'rewrite everything' conflicts with minimal or scoped changes"),
    (r"\bno tools\b|\bwithout (using )?tools\b|\bcannot run\b",
     r"\brun (the |all |relevant )?tests\b",
     "'no tools' conflicts with 'run tests'"),
    (r"\bfully autonomous\b|\bnever stop\b",
     r"\[checkpoint\]|\bstop and (report|ask|confirm)\b",
     "'fully autonomous' conflicts with checkpoints"),
]

EVIDENCE_RULE_RE = re.compile(
    r"(did not run|not run\b|never report|do not (claim|report)|unperformed|were not performed|"
    r"you did not perform|not (actually )?perform|without running|was not run|only report .*ran|"
    r"you actually ran|record the exact command)",
    re.I,
)
EXTERNAL_CONTENT_RE = re.compile(
    r"\b(repositor(y|ies)|files?|web ?(page|site|search)|documents?|attachments?|tool output|urls?|"
    r"command output|log files?)\b",
    re.I,
)
UNTRUSTED_RULE_RE = re.compile(
    r"(untrusted|not instructions|as data\b|is data\b|are data\b|data, not instructions|"
    r"treat .{0,60} as data)",
    re.I,
)
CONFIRMATION_RE = re.compile(r"\b(confirm|confirmation|approval|approve|approved|checkpoint)\b", re.I)
PERSONA_RE = re.compile(
    r"world[- ]class|you are (a|an) (senior|expert|world|highly|brilliant|legendary)|"
    r"\b\d{1,2}\+? years of experience\b",
    re.I,
)


def lint_prompt(
    prompt: str,
    *,
    autonomy: str | None = None,
    risk: str | None = None,
    modes: Iterable[str] = (),
    level: int | None = None,
    model_tier: str | None = None,
    capabilities: dict[str, str] | None = None,
    gaps: Iterable[tuple[str, str]] = (),
    template_mode: bool = False,
) -> list[Finding]:
    """Deterministic checks on a compiled prompt (or a template when template_mode)."""
    findings: list[Finding] = []
    err = lambda code, msg: findings.append(Finding("error", code, msg))  # noqa: E731
    warn = lambda code, msg: findings.append(Finding("warning", code, msg))  # noqa: E731

    modes = [m.upper() for m in modes]
    sections = prompt_sections(prompt)
    present = [canon for _, canon, _ in sections if canon]
    raw_headings = [raw for raw, _, _ in sections]
    body_by_section = {canon: body for _, canon, body in sections if canon}

    # Structure ---------------------------------------------------------------
    if "Objective" not in present:
        err("E01", "no '## Objective' section (or accepted alias)")
    unfilled = sorted(set(VARIABLE_RE.findall(prompt)))
    if unfilled and not template_mode:
        err("E02", f"unfilled variables: {', '.join('{{' + v + '}}' for v in unfilled)}")
    if ARCHITECT_COMMENT_RE.search(prompt) and not template_mode:
        err("E03", "leftover '<!-- architect: ... -->' comment")
    seen: dict[str, int] = {}
    for canon in present:
        seen[canon] = seen.get(canon, 0) + 1
    for canon, count in seen.items():
        if count > 1:
            err("E04", f"duplicate section '{canon}' ({count} times)")
    for raw, canon, _ in sections:
        if canon is None:
            warn("W06", f"unknown section heading '{raw}' (not in the catalog)")
    order = [CANONICAL_SECTIONS.index(c) for c in present]
    if order != sorted(order):
        warn("W08", "sections are not in catalog order")

    # Autonomy-driven requirements -------------------------------------------
    if autonomy in ("A3", "A4"):
        for needed in ("Workflow", "Completion Criteria", "Output Format", "Failure Handling"):
            if needed not in present:
                err("E05", f"autonomy {autonomy} requires a '{needed}' section")
        if "Autonomy" not in present:
            warn("W12", f"autonomy {autonomy} but no '## Autonomy' section stating the checkpoint triggers")
    elif autonomy == "A2":
        if "Output Format" not in present:
            err("E06", "autonomy A2 requires an 'Output Format' section")
        if "Completion Criteria" not in present:
            warn("W13", "autonomy A2 without 'Completion Criteria'")

    # Risk-driven requirements -----------------------------------------------
    if risk in ("HIGH", "CRITICAL"):
        if "Safety Boundaries" not in present:
            err("E07", f"risk {risk} requires a 'Safety Boundaries' section")
        if "Validation" not in present and "Testing" not in present:
            err("E07", f"risk {risk} requires a 'Validation' or 'Testing' section")
        if "Workflow" not in present:
            err("E07", f"risk {risk} requires a 'Workflow' section")
    if risk == "MEDIUM" and "Validation" not in present and "Testing" not in present:
        # At small and tiny tiers the section budget cannot hold a separate Validation
        # section; an explicit evidence rule inside Requirements carries it instead.
        carried_in_rules = model_tier in ("small", "tiny") and EVIDENCE_RULE_RE.search(prompt)
        if not carried_in_rules:
            warn("W15", "risk MEDIUM without a 'Validation' or 'Testing' section")
    if risk == "CRITICAL" and not CONFIRMATION_RE.search(prompt):
        err("E08", "risk CRITICAL but the prompt never requires confirmation or a checkpoint")
    requirements_body = body_by_section.get("Requirements", "")
    requirements_is_slot = template_mode and bool(VARIABLE_RE.search(requirements_body))
    if risk in ("MEDIUM", "HIGH", "CRITICAL") and "Requirements" in present and not requirements_is_slot:
        if not re.search(r"\bMUST NOT\b", requirements_body):
            warn("W14", f"risk {risk} with Requirements but no scope-bounding MUST NOT")

    # Reliability rules -------------------------------------------------------
    executes = autonomy in ("A3", "A4") or any(m in ("ENGINEER", "EXECUTOR", "AGENT") for m in modes)
    if executes and not EVIDENCE_RULE_RE.search(prompt):
        warn("W03", "prompt executes work but has no rule against reporting unperformed verification")
    if EXTERNAL_CONTENT_RE.search(prompt) and not UNTRUSTED_RULE_RE.search(prompt) and (level is None or level >= 2):
        warn("W04", "prompt involves external content but has no untrusted-content rule")
    if "Requirements" in present and not requirements_is_slot and not re.search(r"\bMUST\b", requirements_body):
        warn("W05", "Requirements section has no MUST / SHOULD / MAY / MUST NOT priorities")
    if PERSONA_RE.search(prompt):
        warn("W07", "persona theatrics detected (credentials or 'world-class' framing)")

    # Contradictions ----------------------------------------------------------
    for pat_a, pat_b, message in CONTRADICTION_PAIRS:
        if re.search(pat_a, prompt, re.I) and re.search(pat_b, prompt, re.I):
            warn("W02", f"possible contradiction: {message}")

    # Capabilities -------------------------------------------------------------
    # The no-fake-capability rule. Every check here needs the profile to state the
    # capability explicitly, so nothing fires on 'unknown' or on a missing profile.
    caps = capabilities or {}
    if caps and not template_mode:
        capability_lines = _rule_lines(prompt)
        for name, pattern in CAPABILITY_CLAIM_RE:
            state = caps.get(name)
            if state not in ("no", "unknown"):
                continue
            hits = [line for line in capability_lines if pattern.search(line)]
            if not hits:
                continue
            if state == "no":
                plain = [line for line in hits if not CAPABILITY_EXCUSE_RE.search(line)]
                if plain:
                    err("C01", f"{name} is 'no' but the prompt instructs it: {plain[0][:70]!r}")
                else:
                    warn("C01", f"{name} is 'no' and the prompt mentions it; it reads as a limit "
                                f"or a fallback, so verify: {hits[0][:70]!r}")
            elif not any(CONDITIONAL_PHRASING_RE.search(line) for line in hits):
                warn("C04", f"{name} is 'unknown' but the prompt instructs it unconditionally; "
                            f"write 'if you can ..., otherwise ...': {hits[0][:70]!r}")
        if "Tool Rules" in present and all(state == "no" for state in caps.values()):
            warn("C02", "Tool Rules section present but every declared capability is 'no'")
    blocking = [name for name, kind in gaps if kind == "blocking"]
    if blocking and not FALLBACK_RE.search(prompt):
        warn("C03", f"blocking gap(s) {', '.join(blocking)} but the prompt states no fallback")

    # Model tier ---------------------------------------------------------------
    # Every check here is gated on a non-frontier tier, so frontier output is unaffected.
    tier = model_tier if model_tier in MODEL_TIERS else None
    if tier and tier != "frontier":
        max_sections = TIER_MAX_SECTIONS.get(tier)
        if max_sections is not None and len(sections) > max_sections:
            warn("W16", f"{len(sections)} sections exceeds the {tier}-tier limit of {max_sections}")
        if tier in ("small", "tiny") and "Examples" not in present:
            err("E09", f"model tier {tier} requires an 'Examples' section of worked input-to-output pairs")
        rule_lines = _rule_lines(prompt)
        joined_rules = "\n".join(rule_lines)
        word_cap = TIER_SENTENCE_WORDS.get(tier)
        if word_cap:
            long_units = [u for u in _sentences(rule_lines) if len(u.split()) > word_cap]
            if long_units:
                warn("W17", f"{len(long_units)} sentence(s) over the {tier}-tier limit of {word_cap} words; "
                            f"first: {long_units[0][:60]!r}")
        if tier in ("small", "tiny"):
            if PRIORITY_SOFT_RE.search(joined_rules):
                warn("W18", f"model tier {tier} should use MUST and MUST NOT only; SHOULD or MAY found")
            cues = sorted({m.group(0).lower() for m in CONDITIONAL_CUE_RE.finditer(joined_rules)})
            if cues:
                warn("W20", f"conditional wording a {tier} model cannot arbitrate: {', '.join(cues)}")
        tool_cap = TIER_MAX_TOOLS.get(tier)
        if tool_cap is not None:
            named = sorted({m.group(0).lower() for m in TOOL_WORD_RE.finditer(body_by_section.get("Tool Rules", ""))})
            if len(named) > tool_cap:
                warn("W19", f"Tool Rules names {len(named)} tools ({', '.join(named)}); "
                            f"model tier {tier} allows {tool_cap}")

    # Size and shape ----------------------------------------------------------
    line_count = len([ln for ln in prompt.splitlines() if ln.strip()])
    hard_cap = TIER_MAX_LINES.get(tier) if tier else None
    if hard_cap is not None:
        if line_count > hard_cap:
            warn("W01", f"{line_count} non-empty lines exceeds the {tier}-tier cap of {hard_cap}")
    elif level in LENGTH_BUDGET:
        budget = LENGTH_BUDGET[level] * LENGTH_TOLERANCE * TIER_LENGTH_FACTOR.get(tier or "frontier", 1.0)
        if line_count > budget:
            warn("W01", f"{line_count} non-empty lines exceeds the Level {level} guideline of about {LENGTH_BUDGET[level]}")
    if level == 1 and len(present) > 4:
        warn("W11", f"Level 1 prompt has {len(present)} sections; Level 1 should stay minimal")
    workflow = body_by_section.get("Workflow", "")
    steps = re.findall(r"^\s*\d+[.)]\s", workflow, re.M)
    if len(steps) > 10:
        warn("W09", f"Workflow has {len(steps)} steps; keep it to ten or fewer")
    final = body_by_section.get("Final Instructions", "")
    if len([ln for ln in final.splitlines() if ln.strip()]) > 6:
        warn("W10", "Final Instructions longer than a few lines; keep the two to four rules that matter most")
    _ = raw_headings
    return findings


def lint_summary(out: ArchitectOutput) -> list[Finding]:
    """Check the Compilation Summary block for completeness and consistency."""
    findings: list[Finding] = []
    err = lambda code, msg: findings.append(Finding("error", code, msg))  # noqa: E731
    warn = lambda code, msg: findings.append(Finding("warning", code, msg))  # noqa: E731
    if not out.has_summary:
        err("S00", "no '## Compilation Summary' block")
        return findings
    for key in ("objective", "domain", "risk", "mode", "autonomy", "level", "target", "model",
                "capabilities", "gaps", "template", "upgrades", "questions"):
        if key not in out.summary:
            err("S01", f"summary is missing '{key.capitalize()}:'")
    if "domain" in out.summary and not out.domains:
        err("S02", f"Domain value not recognized: {out.summary['domain']!r}")
    if "risk" in out.summary and not out.risk:
        err("S02", f"Risk value not recognized: {out.summary['risk']!r}")
    if "mode" in out.summary and not out.modes:
        err("S02", f"Mode value not recognized: {out.summary['mode']!r}")
    if "autonomy" in out.summary and not out.autonomy:
        err("S02", f"Autonomy value not recognized: {out.summary['autonomy']!r}")
    if "level" in out.summary and not out.level:
        err("S02", f"Level value not recognized: {out.summary['level']!r}")
    if "model" in out.summary and not out.model_tier:
        err("S02", f"Model value not recognized: {out.summary['model']!r} (expected one of {MODEL_TIERS})")
    level, risk, autonomy = out.level, out.risk, out.autonomy
    if level and risk == "HIGH" and level < 3:
        err("S03", "risk HIGH requires Level >= 3")
    if level and risk == "CRITICAL" and level != 4:
        err("S03", "risk CRITICAL requires Level 4")
    if level and autonomy in ("A3", "A4") and level < 3:
        err("S03", f"autonomy {autonomy} requires Level >= 3")
    if risk == "CRITICAL" and autonomy == "A4":
        err("S03", "risk CRITICAL never gets autonomy A4")
    if level and len(out.domains) > 1 and level < 2:
        err("S03", "multi-domain tasks require Level >= 2")
    # Capability profile ------------------------------------------------------
    caps = out.capabilities
    if "capabilities" in out.summary:
        unknown_names = sorted(set(out.capability_names) - set(CAPABILITIES))
        if unknown_names:
            err("S11", f"unknown capability name(s): {', '.join(unknown_names)}; "
                       f"use the vocabulary in references/capabilities.md")
        elif not caps and not out.capabilities_none_required:
            err("S11", f"Capabilities value not parseable: {out.summary['capabilities']!r} "
                       "(expected 'none required' or 'name=yes|no|unknown' pairs)")
    gaps_value = out.summary.get("gaps", "").strip()
    if gaps_value and not gaps_value.lower().startswith("none") and not out.gaps:
        err("S12", f"Gaps value not parseable: {gaps_value!r} "
                   "(expected 'none' or 'name (blocking|non-blocking) -> what was done')")
    if "capabilities" in out.summary:
        executable = any(caps.get(c) == "yes" for c in EXECUTE_CAPABILITIES)
        if autonomy in ("A3", "A4") and not executable:
            err("S13", f"autonomy {autonomy} acts on real files, data, or systems, but none of "
                       f"{', '.join(EXECUTE_CAPABILITIES)} is 'yes'")
        executing = [m for m in out.modes if m in EXECUTING_MODES]
        if executing and not executable:
            err("S14", f"mode {executing[0]} requires execution, but none of "
                       f"{', '.join(EXECUTE_CAPABILITIES)} is 'yes'")

    tier = out.model_tier
    if tier and autonomy:
        value = int(autonomy[1])
        cap = TIER_AUTONOMY_CAP.get(tier)
        if cap is not None and value > cap:
            err("S09", f"model tier {tier} caps autonomy at A{cap}, got {autonomy}")
        if tier in ("small", "tiny") and risk in ("HIGH", "CRITICAL") and value > 1:
            err("S10", f"model tier {tier} at risk {risk} caps autonomy at A1 with a human "
                       f"verification step, got {autonomy}")
    if level and level >= 3 and out.prompt and "review" not in out.summary:
        warn("S04", "Level >= 3 summary should include a 'Review:' line")
    if out.question_count and (out.prompt or out.skill_files):
        err("S05", "questions were asked but a prompt or skill was still emitted; asking should stop compilation")
    if not out.question_count and not out.prompt and not out.skill_files and out.review is None:
        err("S06", "no questions, no prompt, and no skill were emitted")
    if out.artifact == "skill":
        if not out.skill_files:
            err("S07", "Artifact is a skill but no '### <path>' file blocks were found under '## Skill'")
        elif not any(p.endswith("SKILL.md") for p in out.skill_files):
            err("S07", "skill output has no SKILL.md file")
        if out.skill_kind is None:
            warn("S08", f"Artifact line should name the skill kind ({', '.join(SKILL_KINDS)}) and tier")
    return findings


def lint_skill_output(out: ArchitectOutput) -> list[Finding]:
    """Materialize the emitted skill files in a temporary directory and lint them."""
    import tempfile

    import pa_skill

    findings: list[Finding] = []
    with tempfile.TemporaryDirectory(prefix="pa-skill-") as tmp:
        root = Path(tmp)
        skill_mds = materialize_skill_files(out, root)
        for skill_md in skill_mds:
            if ".cursor" in skill_md.parts:
                continue
            findings += pa_skill.lint_skill(skill_md.parent, strict_generated=True)
        for manifest in root.rglob("plugin.json"):
            if manifest.parent.name == ".claude-plugin":
                plugin_findings, _ = pa_skill.lint_plugin(manifest.parent.parent)
                findings += plugin_findings
    return findings


def lint_output(out: ArchitectOutput, *, template_mode: bool = False) -> list[Finding]:
    """Lint a full Architect output: summary consistency plus prompt or skill checks."""
    findings = lint_summary(out) if out.has_summary else []
    if out.artifact == "skill" and out.skill_files:
        findings += lint_skill_output(out)
    elif out.prompt:
        findings += lint_prompt(
            out.prompt,
            autonomy=out.autonomy,
            risk=out.risk,
            modes=out.modes,
            level=out.level,
            model_tier=out.model_tier,
            capabilities=out.capabilities,
            gaps=out.gaps,
            template_mode=template_mode,
        )
    return findings


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Skill upgrader
# ---------------------------------------------------------------------------

def upgrader_dirs(cwd: str | Path | None = None) -> list[Path]:
    """The `skill-upgrader/` directories to consult, most specific first.

    The working project's folder holds references for that project; the folder in
    the project that contains this skill holds references for every compilation.
    """
    found: list[Path] = []
    base = Path(cwd).resolve() if cwd else Path.cwd().resolve()
    for root in (base, ROOT.resolve()):
        candidate = root / UPGRADER_DIRNAME
        if candidate.is_dir() and candidate not in found:
            found.append(candidate)
    return found


def upgrader_files(directory: str | Path) -> list[Path]:
    """Reference files in one upgrader directory: top-level Markdown, minus README.md.

    `examples/` holds shipped samples and `templates/` holds user templates; neither
    is a reference, so neither is returned here.
    """
    directory = Path(directory)
    return sorted(
        p for p in directory.glob("*.md")
        if p.is_file() and p.name.lower() != "readme.md"
    )


def _as_tags(value) -> list[str]:
    if value is None:
        return []
    items = value if isinstance(value, list) else str(value).split(",")
    return [str(v).strip().lower() for v in items if str(v).strip()]


def upgrader_applies(
    meta: dict,
    *,
    domains: Iterable[str] = (),
    artifact: str | None = None,
    target: str | None = None,
    model: str | None = None,
    kind: str | None = None,
) -> bool:
    """True when every filter the file declares admits this compilation.

    A filter that is absent matches everything; `all` inside a filter matches
    everything for that axis. Filters combine with AND across axes and OR within one.
    """
    wanted_domains = _as_tags(meta.get("domains"))
    if wanted_domains and "all" not in wanted_domains:
        if not set(wanted_domains) & {d.lower() for d in domains}:
            return False
    for key, value in (("artifacts", artifact), ("targets", target), ("models", model), ("kinds", kind)):
        wanted = _as_tags(meta.get(key))
        if wanted and "all" not in wanted:
            if value is None or value.lower() not in wanted:
                return False
    return True

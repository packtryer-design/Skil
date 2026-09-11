"""Skill and plugin validation for the Prompt Architect tooling.

`lint_skill(skill_dir)` checks a skill directory against the Agent Skills
specification and the Claude Code skill frontmatter, then runs a static
security scan whose categories follow NVIDIA SkillSpector (prompt injection,
anti-refusal, exfiltration, privilege escalation, excessive agency, supply
chain, persistence, trigger abuse). `lint_plugin(plugin_dir)` checks the plugin
manifests and every skill they contain. Standard library only.

Documentation that describes forbidden patterns would trip the scanner, so two
mechanisms exist: a line that prohibits, describes, or detects a pattern is
downgraded to a warning, and a file may opt out entirely with the marker
`<!-- skillcheck: allow-security-terms -->` (the checker then reports that the
marker is present). This module contains the marker string and the patterns
themselves, so it self-suppresses; that is expected.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pa_lib
from pa_lib import Finding

NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
SEMVER_RE = pa_lib.SEMVER_RE

# Frontmatter keys accepted by the Agent Skills spec and Claude Code, plus common
# ecosystem keys that runtimes ignore harmlessly.
KNOWN_SKILL_KEYS = {
    "name", "description", "license", "compatibility", "metadata", "allowed-tools",
    "when_to_use", "argument-hint", "arguments", "disable-model-invocation", "user-invocable",
    "disallowed-tools", "model", "effort", "context", "agent", "background", "hooks", "paths", "shell",
    "version", "triggers", "related", "category", "tags", "author",
}
BUILTIN_COMMAND_NAMES = {
    "commit", "review", "code-review", "init", "help", "config", "clear", "compact", "model", "plugin",
    "plugins", "skills", "doctor", "status", "login", "logout", "memory", "cost", "resume", "agents",
    "hooks", "mcp", "permissions", "terminal", "vim", "bug", "release-notes", "add-dir", "exit", "quit",
    "synced",
}
TEXT_SUFFIXES = {
    ".md", ".txt", ".yaml", ".yml", ".json", ".toml", ".py", ".sh", ".bash", ".zsh", ".ps1", ".js",
    ".mjs", ".cjs", ".ts", ".rb", ".php", ".cfg", ".ini", ".env", "",
}
DOC_SUFFIXES = {".md", ".txt", ".html", ".yaml", ".yml", ".json"}
MAX_FILE_BYTES = 1_000_000

# Files whose content is prose meant for a model, not code: security terms in them are
# usually rules about the pattern rather than uses of it.
PROSE_SUFFIXES = {".md", ".txt"}
PROSE_NAMES = {"Modelfile", "openai-system.txt"}

# Derived local-model adapters (see references/skill-authoring.md section 11).
ADAPTER_FILES = ("system.md", "Modelfile", "openai-system.txt")
ADAPTER_FORBIDDEN = (
    (r"\$\{CLAUDE_SKILL_DIR\}", "${CLAUDE_SKILL_DIR}"),
    (r"\$\{CLAUDE_PLUGIN_ROOT\}", "${CLAUDE_PLUGIN_ROOT}"),
    (r"\$ARGUMENTS\b", "$ARGUMENTS"),
    (r"(?<![\w./-])references/", "a references/ pointer (progressive disclosure)"),
    (r"^(allowed-tools|disallowed-tools|disable-model-invocation|user-invocable):", "Claude Code frontmatter"),
)

# Zero-width, joiner, bidirectional-override, and BOM characters, built from
# code points so this source file contains none of them.
_INVISIBLE_CODEPOINTS = (
    0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0x2060, 0x2061, 0x2062, 0x2063, 0x2064,
    0xFEFF, 0x202A, 0x202B, 0x202C, 0x202D, 0x202E, 0x2066, 0x2067, 0x2068, 0x2069,
)
INVISIBLE_RE = re.compile("[" + "".join(chr(c) for c in _INVISIBLE_CODEPOINTS) + "]")
HTML_COMMENT_RE = re.compile(r"<!--(.*?)-->", re.S)
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s#]+)(?:#[^)]*)?\)")
BARE_PATH_RE = re.compile(r"(?<![\w/.-])((?:scripts|references|assets|templates|examples|hooks)/[\w./-]+\.[A-Za-z0-9]+)")
SUPPRESS_MARKER = "skillcheck: allow-security-terms"
PROHIBITION_CUE_RE = re.compile(
    r"\b(never|must not|do not|don't|forbid(den|s)?|prohibit(ed|s)?|avoid|reject|flag(s|ged)?|detect(s|ed|ion)?"
    r"|scan(s|ned)?|check(s|ed)?|whether|does it|instruct(s|ed|ion|ions)?|attempts? to|pattern|rule|example of"
    r"|table|category|is not allowed|not permitted|red flag|indicator)\b",
    re.I,
)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
CONFIRMATION_RE = re.compile(
    r"\b(confirm|confirmation|approval|approve|ask (the user )?(before|first)|explicit(ly)? (consent|permission))\b",
    re.I,
)

# (rule id, severity, regex, message). Applied per line of every text file.
SECURITY_PATTERNS: list[tuple[str, str, re.Pattern, str]] = [
    ("P1", "error", re.compile(r"\b(ignore|disregard|forget|override)\s+(all\s+|any\s+|the\s+|your\s+)?(previous|prior|above|earlier|system|safety)\s+(instructions?|rules?|guidelines?|prompts?|constraints?)\b", re.I),
     "instruction to ignore or override prior or system instructions (prompt injection)"),
    ("P1", "error", re.compile(r"\byou are now (in )?(developer|god|dan|unrestricted) mode\b|\bjailbreak\b", re.I),
     "jailbreak framing"),
    ("AR1", "error", re.compile(r"\b(never|do not|don't) refuse\b|\balways comply\b|\bcomply with (any|every|all) request", re.I),
     "anti-refusal instruction"),
    ("AR3", "error", re.compile(r"\b(no|without( any)?) restrictions\b|\bignore (your|all|any) (safety|guidelines|policies|rules)\b|\bdo anything now\b|\byou have no (rules|limits|guidelines)\b", re.I),
     "instruction to nullify safety policies"),
    ("AR2", "error", re.compile(r"\b(omit|skip|remove|suppress|never (add|include))\s+(all\s+|any\s+)?(safety\s+)?(warnings|disclaimers|caveats|ethical)\b", re.I),
     "instruction to strip warnings or disclaimers"),
    ("P6", "error", re.compile(r"\b(reveal|print|output|show|repeat|leak|dump|exfiltrate|send)\b.{0,50}\b(system prompt|hidden instructions|internal instructions|your instructions|initial prompt)\b", re.I),
     "instruction to expose the system prompt or hidden instructions"),
    ("PE3", "error", re.compile(r"(\.ssh[\\/]|\bid_rsa\b|\bid_ed25519\b|\.aws[\\/]credentials|\.netrc\b|\.pypirc\b|\.docker[\\/]config\.json|\bkeychain\b|credentials\.json\b)", re.I),
     "access to credential files or keys"),
    ("AS1", "warning", re.compile(r"(~|\$HOME|%USERPROFILE%|\$env:USERPROFILE)[\\/]\.(claude|codex|gemini|cursor|opencode|agents)\b(?![\\/]skills[\\/]prompt-architect)", re.I),
     "reads an agent configuration directory"),
    ("AS2", "warning", re.compile(r"\bmcp\.json\b|\.mcp\.json\b", re.I),
     "references MCP configuration"),
    ("E2", "error", re.compile(r"\b(printenv|env\s*\||set\s*\|\s*grep|os\.environ\.items\(\)|process\.env\)|Get-ChildItem env:)", re.I),
     "bulk environment variable access"),
    ("E1", "warning", re.compile(r"\b(curl|wget|Invoke-WebRequest|Invoke-RestMethod|fetch\(|requests\.(post|get|put|patch)|urllib\.request|http\.client|axios\.)", re.I),
     "network call; verify the destination is documented and necessary"),
    ("SSRF1", "error", re.compile(r"169\.254\.169\.254|metadata\.google\.internal", re.I),
     "cloud metadata endpoint access"),
    ("PE2", "warning", re.compile(r"(^|[\s;&|])sudo\s|\bStart-Process\b.*-Verb\s+RunAs|\brunas\b", re.I),
     "privilege elevation"),
    ("EA2", "warning", re.compile(r"\brm\s+-rf\b|\brmdir\s+/s\b|\bgit push\s+(-f|--force)\b|\bgit reset --hard\b|\bDROP\s+(TABLE|DATABASE)\b|\bTRUNCATE\s+TABLE\b|\bRemove-Item\b.*-Recurse|\bchmod\s+777\b|--no-verify\b|\bdel\s+/[fq]\b", re.I),
     "destructive or bypass command; requires an explicit confirmation rule"),
    ("SC2", "error", re.compile(r"\b(curl|wget)\b[^|\n]*\|\s*(sudo\s+)?(sh|bash|zsh|python\d?|node|perl)\b", re.I),
     "remote code downloaded and executed"),
    ("SC3", "error", re.compile(r"base64\s+(-d|--decode)[^|\n]*\|\s*(sh|bash|python\d?|node)\b|\b(eval|exec)\s*\(\s*(base64|atob|bytes\.fromhex|binascii|codecs\.decode|compile)\b|\bFromBase64String\b.*\bInvoke-Expression\b", re.I),
     "obfuscated or encoded execution"),
    ("SC1", "warning", re.compile(r"\bpip3?\s+install\s+(?!-r\b|--requirement\b|-e\b|\.)([A-Za-z0-9_.-]+)(?![=<>~\[])(\s|$)|\bnpm\s+(install|i)\s+(?!-)([A-Za-z0-9@/_.-]+)(?!@)(\s|$)", re.I),
     "unpinned dependency install"),
    ("RA2", "warning", re.compile(r"\bcrontab\b|\blaunchctl\b|\bsystemctl\s+(--user\s+)?enable\b|\bschtasks\b|\bRegister-ScheduledTask\b|(?<![\w.])\.(bashrc|zshrc|bash_profile|profile)\b|/etc/profile\b|HKCU:.*\\Run\b", re.I),
     "persistence mechanism (scheduled task, startup, shell profile)"),
    ("MP1", "warning", re.compile(r"\b(remember|store|save|keep)\b.{0,40}\b(forever|permanently|indefinitely|all future|every (future )?(session|conversation))\b|\badd (this |these )?to your (memory|long[- ]term memory)\b", re.I),
     "attempts to persist instructions across sessions"),
    ("TM3", "warning", re.compile(r"\bshell\s*=\s*True\b|\bverify\s*=\s*False\b|--insecure\b|\bNODE_TLS_REJECT_UNAUTHORIZED\s*=\s*0|\bcurl\b[^\n]*\s-k\s", re.I),
     "unsafe default (shell=True, TLS verification disabled)"),
    ("AST1", "warning", re.compile(r"\beval\s*\(|\bexec\s*\(|\bos\.system\s*\(|\bsubprocess\.(run|call|Popen)\b|\bInvoke-Expression\b", re.I),
     "dynamic or shell execution in a bundled script; review inputs"),
]
TRIGGER_ABUSE_RE = re.compile(
    r"\b(any|all|every|each) (task|request|question|prompt|message|interaction)s?\b"
    r"|\balways (use|invoke|activate|apply|load) (this|the) skill\b|\bwhenever the user (asks|says|types) anything\b|\bfor everything\b",
    re.I,
)


def _is_prose(path: Path) -> bool:
    """True for files whose content is prose for a model rather than executable code."""
    return path.suffix.lower() in PROSE_SUFFIXES or path.name in PROSE_NAMES


def _iter_text_files(skill_dir: Path):
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file():
            continue
        parts = {p.lower() for p in path.relative_to(skill_dir).parts}
        if ".git" in parts or "node_modules" in parts or "__pycache__" in parts or "results" in parts:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            continue
        try:
            yield path, path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue


def scan_file(path: Path, content: str, rel: str) -> list[Finding]:
    """Security scan of one text file: hidden text, padding, and the pattern table.

    Shared by the skill linter and the skill-upgrader checker so user-added reference
    files are held to the same rules as skill files.
    """
    findings: list[Finding] = []
    err = lambda code, msg: findings.append(Finding("error", code, msg))  # noqa: E731
    warn = lambda code, msg: findings.append(Finding("warning", code, msg))  # noqa: E731
    if INVISIBLE_RE.search(content):
        err("P2", f"{rel}: invisible or bidirectional Unicode characters (hidden text)")
    suppressed = SUPPRESS_MARKER in content
    if suppressed:
        warn("SUPPRESS", f"{rel}: security-term findings suppressed by an explicit '{SUPPRESS_MARKER}' marker; review the file by hand")
    content_lines = content.splitlines()
    blank_run = 0
    for line_no, line in enumerate(content_lines, start=1):
        blank_run = blank_run + 1 if not line.strip() else 0
        if blank_run == 25:
            warn("P9", f"{rel}:{line_no}: 25 or more consecutive blank lines (padding can hide content)")
        if len(line) - len(line.rstrip(" ")) >= 100:
            warn("P9", f"{rel}:{line_no}: long run of trailing spaces (padding can hide content)")
        if suppressed:
            continue
        for rule, severity, pattern, message in SECURITY_PATTERNS:
            if not pattern.search(line):
                continue
            # Scripts may legitimately execute commands; markdown rarely should.
            if rule == "AST1" and _is_prose(path):
                continue
            if rule == "E1" and re.search(r"localhost|127\.0\.0\.1|\bexample\.com\b", line):
                continue
            # Install instructions name the skills directory legitimately; reading other config is what AS1 targets.
            if rule == "AS1" and re.search(r"[\\/]skills[\\/]", line) and re.search(r"\b(copy|clone|install|load(s|ed)?|place|put|move)\b", line, re.I):
                continue
            snippet = line.strip()[:120]
            # A line that prohibits, describes, or detects a pattern is documentation, not an
            # instruction. Look for the cue in the text around the match, not inside it: the
            # injection phrase itself contains words like "instructions" and must not excuse itself.
            if severity == "error" and _is_prose(path) and PROHIBITION_CUE_RE.search(pattern.sub(" ", line)):
                findings.append(Finding("warning", rule, f"{rel}:{line_no}: {message} (appears in a prohibition or description; verify): {snippet}"))
                continue
            if rule == "EA2":
                window = " ".join(content_lines[max(0, line_no - 4): line_no + 3])
                if CONFIRMATION_RE.search(window):
                    findings.append(Finding("warning", rule, f"{rel}:{line_no}: {message} (confirmation language found nearby): {snippet}"))
                    continue
            findings.append(Finding(severity, rule, f"{rel}:{line_no}: {message}: {snippet}"))
    if path.suffix.lower() in DOC_SUFFIXES:
        for match in HTML_COMMENT_RE.finditer(content):
            comment = match.group(1).strip()
            lowered = comment.lower()
            if not comment or lowered.startswith("architect:") or lowered.startswith("skillcheck:"):
                continue
            if re.search(r"\b(ignore|must|always|never|do not|don't|you are|instruction)\b", comment, re.I):
                err("P2", f"{rel}: HTML comment contains instruction-like text: {comment[:100]!r}")
            else:
                warn("P2", f"{rel}: HTML comment present; agents read it even though humans may not: {comment[:80]!r}")
    return findings


def lint_skill(skill_dir: Path, *, strict_generated: bool = False) -> list[Finding]:
    """Validate one skill directory. `strict_generated` also rejects authoring leftovers."""
    skill_dir = Path(skill_dir)
    findings: list[Finding] = []
    err = lambda code, msg: findings.append(Finding("error", code, msg))  # noqa: E731
    warn = lambda code, msg: findings.append(Finding("warning", code, msg))  # noqa: E731

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        err("SK01", f"{skill_dir}: SKILL.md not found")
        return findings
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        err("SK02", "SKILL.md must start with YAML frontmatter on line 1")
    meta, body = pa_lib.parse_frontmatter(text)
    if not meta:
        err("SK02", "SKILL.md frontmatter missing or unparseable")
    yaml_error = pa_lib.frontmatter_yaml_error(text)
    if yaml_error:
        err("SK02", f"SKILL.md frontmatter is not valid YAML, so runtimes may drop it: {yaml_error}")

    # Frontmatter --------------------------------------------------------------
    name = str(meta.get("name", "") or "")
    if not name:
        err("SK03", "frontmatter 'name' is missing")
    else:
        if not NAME_RE.match(name) or "--" in name:
            err("SK03", f"name {name!r} must be 1-64 lowercase letters, digits, and single hyphens, not starting or ending with a hyphen")
        if name != skill_dir.name:
            err("SK03", f"name {name!r} does not match directory name {skill_dir.name!r}")
        if name in BUILTIN_COMMAND_NAMES:
            warn("TR2", f"name {name!r} shadows a built-in command or reserved name")
        if any(ord(ch) > 127 for ch in name):
            err("TP2", "name contains non-ASCII characters")
    description = str(meta.get("description", "") or "").strip()
    if not description:
        err("SK04", "frontmatter 'description' is missing or empty")
    else:
        if len(description) > 1024:
            err("SK04", f"description is {len(description)} characters; the Agent Skills limit is 1024")
        elif len(description) < 40:
            warn("SK04", "description is very short; say what the skill does and when to use it")
        if not re.search(r"\b(use when|use (this|it) when|trigger|when (the )?user|when asked|for requests|invoke)\b", description, re.I):
            warn("SK04", "description does not say when to use the skill (no 'use when', trigger phrases, or 'when the user ...')")
        if re.search(r"<[^>]+>", description):
            warn("SK04", "description contains angle-bracket tags; keep it plain text")
        if TRIGGER_ABUSE_RE.search(description):
            warn("TR1", "description claims to apply to any or every request (trigger abuse)")
        if INVISIBLE_RE.search(description):
            err("TP2", "description contains invisible or bidirectional Unicode characters")
    compatibility = meta.get("compatibility")
    if compatibility and len(str(compatibility)) > 500:
        err("SK05", "compatibility exceeds 500 characters")
    for key in meta:
        if key not in KNOWN_SKILL_KEYS:
            warn("SK06", f"unknown frontmatter key {key!r} (runtimes ignore it)")
    allowed_tools = meta.get("allowed-tools")
    if allowed_tools is not None:
        tools_text = " ".join(allowed_tools) if isinstance(allowed_tools, list) else str(allowed_tools)
        if re.search(r"(^|\s)(\*|all)(\s|$)", tools_text, re.I):
            err("LP2", "allowed-tools grants a wildcard; declare specific tools")
    metadata = meta.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        warn("SK06", "metadata should be a map of string keys to string values")
    elif isinstance(metadata, dict):
        # Declared capability requirements (references/skill-authoring.md section 12).
        seen_levels: dict[str, str] = {}
        for level in ("required", "recommended", "optional"):
            raw = metadata.get(f"capabilities-{level}")
            if raw in (None, ""):
                continue
            names = [n.strip().lower() for n in str(raw).replace(";", ",").split(",") if n.strip()]
            for name in names:
                if name not in pa_lib.CAPABILITIES:
                    err("SK11", f"capabilities-{level} names {name!r}, which is not in the capability "
                                f"vocabulary; see references/capabilities.md")
                elif name in seen_levels:
                    err("SK11", f"capability {name!r} is declared both {seen_levels[name]} and {level}")
                else:
                    seen_levels[name] = level

    # Body ---------------------------------------------------------------------
    body_lines = body.splitlines()
    line_count = len(body_lines)
    if line_count == 0 or not body.strip():
        err("SK07", "SKILL.md body is empty")
    elif line_count > 1000:
        err("SK07", f"SKILL.md body is {line_count} lines; keep it under 500 and move detail to references")
    elif line_count > 500:
        warn("SK07", f"SKILL.md body is {line_count} lines; the guideline is under 500")
    leftovers = sorted(set(pa_lib.VARIABLE_RE.findall(INLINE_CODE_RE.sub("", body))))
    if leftovers:
        err("SK09", f"unfilled placeholders in SKILL.md: {', '.join('{{' + v + '}}' for v in leftovers)}")
    if pa_lib.ARCHITECT_COMMENT_RE.search(text):
        err("SK09", "leftover '<!-- architect: -->' authoring comment in SKILL.md")
    if strict_generated and re.search(r"\[TODO|\bTBD\b|\bFIXME\b|lorem ipsum", body, re.I):
        err("SK09", "TODO/TBD/FIXME or filler text left in SKILL.md")
    referenced = set(LINK_RE.findall(body)) | set(BARE_PATH_RE.findall(body))
    for ref in sorted(referenced):
        if re.match(r"^[a-z]+:", ref) or ref.startswith("$") or ref.startswith("{"):
            continue
        cleaned = ref.replace("${CLAUDE_SKILL_DIR}/", "").replace("${CLAUDE_PLUGIN_ROOT}/", "")
        if cleaned.startswith("/") or cleaned.startswith("~"):
            continue
        if not (skill_dir / cleaned).exists():
            warn("SK08", f"SKILL.md references {cleaned!r}, which does not exist in the skill directory")

    # Local-model adapters ----------------------------------------------------
    # A skill compiled for a local runtime keeps SKILL.md canonical and derives
    # system.md / Modelfile / openai-system.txt. None of the Claude Code mechanisms
    # exist there, so the derived system prompt has to stand on its own.
    adapters = {name for name in ADAPTER_FILES if (skill_dir / name).exists()}
    if adapters:
        system_md = skill_dir / "system.md"
        if not system_md.exists():
            warn("SK10", f"local-model adapters present ({', '.join(sorted(adapters))}) but system.md is "
                         "missing; it is the portable form of the body")
        else:
            system_text = system_md.read_text(encoding="utf-8", errors="replace")
            for pattern, what in ADAPTER_FORBIDDEN:
                if re.search(pattern, system_text, re.M):
                    err("SK10", f"system.md contains {what}, which does not exist outside Claude Code; "
                                "the portable system prompt must be self-contained")

    # Security scan over every text file --------------------------------------
    for path, content in _iter_text_files(skill_dir):
        findings += scan_file(path, content, path.relative_to(skill_dir).as_posix())
    if any(p.suffix.lower() in {".pyc", ".pyo"} and "__pycache__" not in p.parts for p in skill_dir.rglob("*") if p.is_file()):
        warn("SC8", "compiled Python bytecode shipped with the skill")
    return findings


def lint_plugin(plugin_dir: Path) -> tuple[list[Finding], list[Path]]:
    """Validate plugin manifests and return (findings, skill directories found)."""
    plugin_dir = Path(plugin_dir)
    findings: list[Finding] = []
    err = lambda code, msg: findings.append(Finding("error", code, msg))  # noqa: E731
    warn = lambda code, msg: findings.append(Finding("warning", code, msg))  # noqa: E731
    manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
    manifest: dict = {}
    if not manifest_path.is_file():
        err("PL01", f"{manifest_path} not found")
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            err("PL01", f"plugin.json is not valid JSON: {exc}")
        name = str(manifest.get("name", "") or "")
        if not name or not NAME_RE.match(name):
            err("PL02", f"plugin.json name {name!r} must be kebab-case")
        version = str(manifest.get("version", "") or "")
        if version and not SEMVER_RE.match(version):
            err("PL03", f"plugin.json version {version!r} is not MAJOR.MINOR.PATCH")
        if not manifest.get("description"):
            warn("PL04", "plugin.json has no description")
    marketplace_path = plugin_dir / ".claude-plugin" / "marketplace.json"
    if marketplace_path.is_file():
        try:
            marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
            entries = marketplace.get("plugins", [])
            if not entries:
                warn("PL05", "marketplace.json lists no plugins")
            for entry in entries:
                source = entry.get("source")
                if isinstance(source, str) and source.startswith("./"):
                    if not (plugin_dir / source).is_dir():
                        err("PL05", f"marketplace.json source {source!r} does not exist")
        except json.JSONDecodeError as exc:
            err("PL05", f"marketplace.json is not valid JSON: {exc}")
    skill_dirs: list[Path] = []
    declared = manifest.get("skills")
    if isinstance(declared, list):
        for item in declared:
            candidate = (plugin_dir / str(item)).resolve()
            if candidate.is_dir() and (candidate / "SKILL.md").is_file():
                skill_dirs.append(candidate)
            elif candidate.is_dir():
                skill_dirs.extend(sorted(p for p in candidate.iterdir() if (p / "SKILL.md").is_file()))
            else:
                err("PL06", f"plugin.json declares skill path {item!r}, which does not exist")
    elif isinstance(declared, str):
        base = plugin_dir / declared
        if base.is_dir():
            skill_dirs.extend(sorted(p for p in base.iterdir() if (p / "SKILL.md").is_file()))
        else:
            err("PL06", f"skills path {declared!r} does not exist")
    base = plugin_dir / "skills"
    if base.is_dir():
        for p in sorted(base.iterdir()):
            if (p / "SKILL.md").is_file() and p.resolve() not in {s.resolve() for s in skill_dirs}:
                skill_dirs.append(p)
    if not skill_dirs and (plugin_dir / "SKILL.md").is_file():
        skill_dirs.append(plugin_dir)
    if not skill_dirs:
        warn("PL06", "no skills found under skills/ or at the plugin root")
    hooks_path = plugin_dir / "hooks" / "hooks.json"
    if hooks_path.is_file():
        try:
            hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
            for event, entries in (hooks.get("hooks") or {}).items():
                for entry in entries:
                    for hook in entry.get("hooks", []):
                        command = str(hook.get("command", ""))
                        if re.search(r"\b(curl|wget|Invoke-WebRequest|fetch\()", command, re.I):
                            warn("BH2", f"hook on {event} performs a network call: {command[:80]}")
                        if "timeout" not in hook:
                            warn("BH1", f"hook on {event} declares no timeout")
        except json.JSONDecodeError as exc:
            err("BH1", f"hooks.json is not valid JSON: {exc}")
    return findings, skill_dirs

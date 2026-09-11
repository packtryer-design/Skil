#!/usr/bin/env python3
"""Flatten the skill into one self-contained system prompt for hosts without file access.

The skill relies on Claude Code: it reads references on demand, runs scripts through
${CLAUDE_SKILL_DIR}, and writes generated files to disk. None of that exists on
claude.ai, ChatGPT, Gemini, a raw API call, or a local runtime. This build inlines the
references and rewrites those instructions, producing a prompt that stands on its own.

Usage:
    python scripts/build_portable.py                  # write every profile to dist/
    python scripts/build_portable.py --profile full   # write one profile
    python scripts/build_portable.py --check          # fail if dist/ is stale

Profiles:
    full     SKILL.md plus every runtime reference. For a frontier model on any host.
    compact  SKILL.md plus classification, capabilities, runtime profiles, model tiers,
             requirements and sections. Prompts and templates only. For a mid model.

There is deliberately no small or tiny profile: the Architect is a multi-stage compiler
and a model at those tiers cannot run it. Such a model is what the Architect compiles
*for*, not what it runs *on*.

Every rewrite below is required. If SKILL.md changes so that one no longer matches, the
build fails rather than shipping a prompt that tells the reader to run a script it does
not have.
"""

from __future__ import annotations

import argparse
import re
import sys

sys.dont_write_bytecode = True
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pa_lib  # noqa: E402

DIST_DIR = pa_lib.ROOT / "dist"
REFERENCES_DIR = pa_lib.SKILL_DIR / "references"

RUNTIME_REFERENCES = [
    "classification",
    "capabilities",
    "runtime-profiles",
    "model-tiers",
    "requirements",
    "sections",
    "workflows",
    "review",
    "skill-authoring",
    "skill-security",
    "skill-upgrader",
]

PROFILES: dict[str, dict] = {
    "full": {
        "filename": "prompt-architect.portable.md",
        "references": RUNTIME_REFERENCES,
        "audience": "a frontier model on any host (claude.ai, ChatGPT, Gemini, a raw API call)",
        "scope": "Compiles prompts, templates, and skills.",
    },
    "compact": {
        "filename": "prompt-architect.compact.md",
        "references": ["classification", "capabilities", "runtime-profiles", "model-tiers",
                       "requirements", "sections"],
        "audience": "a mid-tier model, or a host with a smaller context budget",
        # Skill authoring and skill security are both left out, so skill creation is out of
        # scope here rather than half-supported: a skill emitted without the security
        # checklist is worse than no skill.
        "scope": "Compiles prompts and templates only. If the request is for a skill, a slash"
                 " command, or a plugin, say that this build does not compile skills and point"
                 " the user to the full build; do not improvise one.",
    },
}

# (name, pattern, replacement). Applied in order to the SKILL.md body; each must match.
REWRITES: list[tuple[str, re.Pattern, str]] = [
    (
        "skill-files section",
        re.compile(r"^## Skill files\n.*?(?=^## Procedure$)", re.S | re.M),
        "## What is in this document\n\n"
        "Everything the compilation needs is inlined below, in this order: the procedure,"
        " then the reference sections it names. There are no files to open and no scripts"
        " to run. When a stage says to consult a reference, scroll to the matching"
        " `# Reference:` heading in this document.\n\n",
    ),
    (
        "template selection",
        re.compile(
            r"\*\*Prompts and templates\.\*\* Select a base template from `templates/INDEX\.md`"
            r".*?author a new base template using `references/template-authoring\.md` and offer to"
            r" save it as a candidate\."
        ),
        "**Prompts and templates.** This build carries no template library, so compose from"
        " the section catalog in the Sections reference below and report `Template: none`."
        " Never cite a template by name here: you cannot read one, and a cited name the user"
        " cannot find is worse than none.",
    ),
    (
        "skill template selection",
        re.compile(
            r"Select the matching `skill-\*` template from `templates/INDEX\.md`"
            r" \(plus `skill-plugin-scaffold` for package tier 2 and 3\) and specialize it the same way\. "
        ),
        "Build the files from the kind's shape described in the Skill Authoring reference below. ",
    ),
    (
        "skill file writing",
        re.compile(
            r"In Claude Code, write the files to the chosen location \(creating directories;"
            r" never overwriting an existing skill of the same name without confirmation\)"
            r" and then run `python \$\{CLAUDE_SKILL_DIR\}/scripts/check_skill\.py --generated <dir>`"
            r" \(add `--plugin` for tier 2\)\. Elsewhere, print the files\."
        ),
        "You cannot write files here: print every file in full, each under its own"
        " `### <path>` heading, and tell the user where to save them.",
    ),
    (
        "skill security check",
        re.compile(
            r"`check_skill\.py --generated` must report zero errors; fix warnings that indicate real risk\."
        ),
        "No scanner is available here, so run that checklist by reading the files yourself,"
        " and fix what you find before returning them.",
    ),
    (
        "prompt validation script",
        re.compile(
            r" `python \$\{CLAUDE_SKILL_DIR\}/scripts/validate_prompt\.py <file>` performs the"
            r" mechanical part of this check on a saved output\."
        ),
        " Perform this check by reading; there is no validator in this build.",
    ),
    (
        "prompt reviewer template",
        re.compile(
            r"perform the review yourself using `templates/prompt-reviewer\.md` as the method and"
            r" the scoring rubric in `references/review\.md`"
        ),
        "perform the review yourself using the critique checklist and scoring rubric in the"
        " Review reference below",
    ),
    (
        "review template citation",
        re.compile(r", and Template names `prompt-reviewer`"),
        ", and Template is `none`",
    ),
    (
        "skill review scanner",
        re.compile(r"run the review procedure in `references/skill-security\.md` \(static scan with"
                   r" `check_skill\.py`, source reading, semantic review\)"),
        "run the review procedure in the Skill Security reference below (source reading and"
        " semantic review; there is no scanner here)",
    ),
    (
        "local-model template selection",
        re.compile(r"use `skill-local-model` instead: "),
        "follow section 11 of the Skill Authoring reference below: ",
    ),
    (
        "generated-skill scan",
        re.compile(r"; `check_skill\.py --generated` reports zero errors before the skill is returned\."),
        "; that list is checked by reading, before the skill is returned.",
    ),
    (
        "upgrader selection script",
        re.compile(
            r"Run `python \$\{CLAUDE_SKILL_DIR\}/scripts/check_upgrader\.py --for domains=<\.\.\.>"
            r" artifact=<\.\.\.> target=<\.\.\.> model=<\.\.\.>` \(or read the folders' frontmatter"
            r" yourself\) and read only the files it names\."
        ),
        "If you can read files, list both folders and read each file's frontmatter to decide what"
        " applies, then read only those files; if you cannot, ask the user once whether they have"
        " a `skill-upgrader/` folder and to paste the files that apply.",
    ),
    (
        "saving a prompt",
        re.compile(
            r"in Claude Code, write it to `prompts/<slug>\.md` in the current project\."
            r" Skills are written to their location by default\. Never write into this skill's own"
            r" directory unless the user asks to store a candidate template\."
        ),
        "you cannot write files here; print it and name the path the user should save it to"
        " (`prompts/<slug>.md` for a prompt, the skill's directory for a skill).",
    ),
]

# Applied to the assembled document, including the inlined references, which
# cross-reference each other and the scripts. Optional: a profile may not carry the
# reference a rewrite targets.
GLOBAL_REWRITES: list[tuple[re.Pattern, str]] = [
    (
        re.compile(r"`scripts/validate_prompt\.py` checks the mechanical items:"),
        "Check these mechanical items by reading (in Claude Code a script does it):",
    ),
    (
        re.compile(r"6\. Validate: `python \$\{CLAUDE_SKILL_DIR\}/scripts/check_skill\.py --generated <dir>`"
                   r" must report zero errors; fix warnings that indicate real risk\."),
        "6. Validate by reading the files against the security checklist; fix anything you find.",
    ),
    (
        re.compile(r"Run `python \$\{CLAUDE_SKILL_DIR\}/scripts/check_upgrader\.py --for domains=<d1,d2>"
                   r" artifact=<prompt\|skill\|template> target=<target> model=<tier> kind=<kind>` with the"
                   r" values you settled at Stages 1 and 2\. It prints the files that apply, with their"
                   r" descriptions, and nothing when none do\. Without the script, list"),
        "There is no script in this build, so list",
    ),
    (
        re.compile(r"`check_upgrader\.py` runs the skill security scan over these files for the same"
                   r" reason, and a file that fails it is not applied at all\."),
        "In Claude Code a checker scans these files for the same reason; here, apply the same"
        " judgment by reading, and do not apply a file that fails it.",
    ),
    (
        re.compile(r"Use template `skill-local-model` alongside the skill-kind template, and"),
        "Derive the files below alongside the canonical SKILL.md, and",
    ),
]

# `references/<name>.md` points at a file this build does not ship. Every pointer becomes
# a pointer into this document, or an honest statement that it was left out.
POINTER_RE = re.compile(r"`?references/([a-z-]+)\.md`?")

REFERENCE_TITLES = {
    "classification": "Classification",
    "capabilities": "Capabilities",
    "runtime-profiles": "Runtime Profiles",
    "model-tiers": "Model Tiers",
    "requirements": "Requirements and the Clarification Gate",
    "sections": "Sections",
    "workflows": "Workflows",
    "review": "Review",
    "skill-authoring": "Skill Authoring",
    "skill-security": "Skill Security",
    "skill-upgrader": "Skill Upgrader",
}


def _strip_frontmatter(text: str) -> str:
    return re.sub(r"^---[ \t]*\r?\n.*?\r?\n---[ \t]*\r?\n", "", text, count=1, flags=re.S)


def _demote_headings(text: str) -> str:
    """Push a reference's own headings one level down so it nests under its `# Reference:`."""
    return re.sub(r"^(#{1,5}) ", r"#\1 ", text, flags=re.M)


def _rewrite_pointers(text: str, included: list[str]) -> str:
    def replace(match: re.Match) -> str:
        name = match.group(1)
        title = REFERENCE_TITLES.get(name)
        if title is None:
            return "a reference not included in this build"
        if name in included:
            return f"the {title} reference in this document"
        return f"the {title} reference (not included in this build)"

    return POINTER_RE.sub(replace, text)


def build(profile_name: str) -> str:
    profile = PROFILES[profile_name]
    body = _strip_frontmatter(pa_lib.read_text(pa_lib.SKILL_DIR / "SKILL.md"))
    for name, pattern, replacement in REWRITES:
        body, count = pattern.subn(replacement, body, count=1)
        if not count:
            raise SystemExit(
                f"build_portable: the '{name}' rewrite no longer matches SKILL.md. "
                "Update REWRITES in scripts/build_portable.py to match the new wording, "
                "so the portable build does not ship instructions for tools it lacks."
            )
    # Mentions are fine (a rule about what must not appear in a portable skill); an
    # instruction to *run* a script that this build does not carry is not.
    leftover = re.search(r"python \$\{CLAUDE_(SKILL_DIR|PLUGIN_ROOT)\}", body)
    if leftover:
        raise SystemExit(
            f"build_portable: {leftover.group(0)} survives in the flattened body; add a rewrite for it."
        )

    parts = [
        f"# Prompt Architect ({profile_name} build)",
        "",
        "Self-contained system prompt, generated by `scripts/build_portable.py` from"
        " `skills/prompt-architect/`. Do not edit by hand; edit the skill and rebuild.",
        "",
        f"Built for {profile['audience']}. Paste it as the system prompt, then send the request"
        " as the user message.",
        "",
        profile["scope"],
        "",
        "Two things differ from the Claude Code skill this is generated from. There is no"
        " template library: template names appearing in the references below (`repository-agent`,"
        " `prompt-reviewer` and the rest) name files this build does not carry, so compose from"
        " the section catalog and report `Template: none`. And there are no scripts: every check"
        " is performed by reading. Guidance about `${CLAUDE_SKILL_DIR}`, `allowed-tools`, and"
        " plugin manifests still applies, because it describes the skills you write, not the"
        " host you are running on.",
        "",
        "---",
        "",
        body.strip(),
        "",
    ]
    for ref in profile["references"]:
        text = _strip_frontmatter(pa_lib.read_text(REFERENCES_DIR / f"{ref}.md"))
        # Drop the reference's own H1 so the injected heading is the only title.
        text = re.sub(r"\A#\s+.*\n+", "", text)
        parts += ["---", "", f"# Reference: {REFERENCE_TITLES[ref]}", "", _demote_headings(text).strip(), ""]

    document = "\n".join(parts).rstrip("\n") + "\n"
    for pattern, replacement in GLOBAL_REWRITES:
        document = pattern.sub(replacement, document)
    return _rewrite_pointers(document, profile["references"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", choices=sorted(PROFILES), action="append", default=[],
                        help="profile to build (repeatable; default: all)")
    parser.add_argument("--check", action="store_true", help="fail if dist/ is stale instead of writing")
    args = parser.parse_args(argv)

    names = args.profile or sorted(PROFILES)
    stale: list[str] = []
    for name in names:
        text = build(name)
        path = DIST_DIR / PROFILES[name]["filename"]
        if args.check:
            current = path.read_text(encoding="utf-8").replace("\r\n", "\n") if path.exists() else ""
            if current != text:
                stale.append(path.name)
            continue
        DIST_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        lines = len(text.splitlines())
        print(f"wrote {path.relative_to(pa_lib.ROOT)} ({lines} lines, {len(text) // 1024} KB)")

    if args.check:
        if stale:
            print(f"dist/ is stale ({', '.join(stale)}); run scripts/build_portable.py", file=sys.stderr)
            return 1
        print(f"dist/ is up to date ({len(names)} profile(s))")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    sys.exit(main())

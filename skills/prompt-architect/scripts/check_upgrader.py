#!/usr/bin/env python3
"""Validate and select skill-upgrader references.

The skill upgrader is a `skill-upgrader/` folder of user-added Markdown references that
adapt what the Architect generates: house style, project conventions, model-specific
notes, domain knowledge, corrections. Each file may carry frontmatter saying which
compilations it applies to. See references/skill-upgrader.md and skill-upgrader/README.md.

Usage:
    python scripts/check_upgrader.py                      # validate every folder found
    python scripts/check_upgrader.py --dir <folder>       # validate one folder
    python scripts/check_upgrader.py --list               # show folders, files, filters
    python scripts/check_upgrader.py --for domains=software,security artifact=prompt \\
                                          target=claude-code model=frontier
                                                          # print the files that apply

Folders are found in the working project first, then in the project that contains this
skill. Files under `examples/` are shipped samples and are validated but never applied;
files under `templates/` are user templates and are validated with the template rules.

Checks: frontmatter keys and vocabularies, a non-empty body, and the same security scan
that skill files get, because these files are read into the Architect's context and a
file that tries to change the procedure or a safety rule is prompt injection, whoever
wrote it. Exit status 1 on any error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

sys.dont_write_bytecode = True
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pa_lib  # noqa: E402
import pa_skill  # noqa: E402
from check_templates import validate_template  # noqa: E402

VOCAB = {
    "domains": set(pa_lib.DOMAINS) | {"all"},
    "artifacts": set(pa_lib.ARTIFACTS) | {"all"},
    "targets": set(pa_lib.TARGETS) | {"all"},
    "models": set(pa_lib.MODEL_TIERS) | {"all"},
    "kinds": set(pa_lib.SKILL_KINDS) | {"all"},
}
MAX_DESCRIPTION = 200
MAX_BODY_LINES = 400

# The skill security scan knows generic injection. These guard the Architect's own
# invariants, which a well-meaning user can try to relax without any malice: "skip the
# review to save time" is the common case, and the answer is the same.
INVARIANT_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(skip|do not run|don't run|never run|disable|omit|drop)\s+(the\s+|any\s+)?"
                r"(security|safety|adversarial|capability)\s+(review|scan|check)s?\b", re.I),
     "asks to skip a review the Architect always runs"),
    (re.compile(r"\b(ignore|skip|bypass|exceed|remove|lift|relax)\s+(the\s+|any\s+|all\s+)?"
                r"(autonomy|risk|capability|tier|section|length)\s+(cap|caps|floor|floors|limit|limits)\b", re.I),
     "asks to bypass a cap or floor"),
    (re.compile(r"\b(raise|set|use|grant)\s+(the\s+)?autonomy\s+to\s+A[34]\b.{0,60}"
                r"\b(whenever|always|regardless|without|even)\b", re.I),
     "asks for execution autonomy on a blanket condition rather than the task's caps"),
    (re.compile(r"\b(report|claim|say|state|mark)\b.{0,40}\b(template|test|check|verification|review)s?\b"
                r".{0,40}\b(even (when|if|though)|whether or not|regardless)\b", re.I),
     "asks the Architect to report something that did not happen"),
    (re.compile(r"\b(ignore|skip|change|drop|replace)\s+(the\s+)?(output|summary)\s+format\b", re.I),
     "asks to change the output format"),
    (re.compile(r"\btreat\b.{0,50}\b(file|web|page|tool output|document)s?\b.{0,30}\bas instructions\b", re.I),
     "inverts the untrusted-content rule"),
    (re.compile(r"\b(never|do not|don't)\s+(ask|state|record|list)\s+(the\s+)?(assumption|question|gap)s?\b", re.I),
     "asks to hide assumptions, questions, or gaps"),
]


def validate_reference(path: Path) -> tuple[dict, list[pa_lib.Finding]]:
    findings: list[pa_lib.Finding] = []
    err = lambda code, msg: findings.append(pa_lib.Finding("error", code, msg))  # noqa: E731
    warn = lambda code, msg: findings.append(pa_lib.Finding("warning", code, msg))  # noqa: E731
    text = pa_lib.read_text(path)
    meta, body = pa_lib.parse_frontmatter(text)
    yaml_error = pa_lib.frontmatter_yaml_error(text)
    if yaml_error:
        err("U00", f"frontmatter is not valid YAML: {yaml_error}")
    for key in meta:
        if key not in pa_lib.UPGRADER_KEYS:
            warn("U01", f"unknown frontmatter key {key!r}; known keys are {sorted(pa_lib.UPGRADER_KEYS)}")
    for key, allowed in VOCAB.items():
        for tag in pa_lib._as_tags(meta.get(key)):
            if tag not in allowed:
                err("U02", f"{key} names {tag!r}, which is not one of {sorted(allowed)}")
    description = str(meta.get("description", "")).strip()
    if description and len(description) > MAX_DESCRIPTION:
        warn("U03", f"description is {len(description)} characters; keep it under {MAX_DESCRIPTION}")
    if not description:
        warn("U03", "no description; one line saying what this reference changes helps the Architect pick it")
    body_lines = [ln for ln in body.splitlines() if ln.strip()]
    if not body_lines:
        err("U04", "empty body; a reference has to say something")
    elif len(body_lines) > MAX_BODY_LINES:
        warn("U04", f"body is {len(body_lines)} lines; references this long crowd out the task. Split it by topic")
    if pa_lib.VARIABLE_RE.search(body):
        warn("U05", "body contains {{VARIABLES}}; references are read as-is, only templates/ files are filled")
    for line_no, line in enumerate(body.splitlines(), start=1):
        for pattern, what in INVARIANT_PATTERNS:
            if pattern.search(line):
                err("U06", f"{path.name}:{line_no}: {what}; references adapt preferences, never "
                           f"invariants: {line.strip()[:100]}")
                break
    findings += pa_skill.scan_file(path, text, path.name)
    return meta, findings


def check_directory(directory: Path, quiet: bool) -> tuple[int, int]:
    errors = warnings = 0
    targets: list[tuple[Path, str]] = [(p, "reference") for p in pa_lib.upgrader_files(directory)]
    samples = directory / pa_lib.UPGRADER_SAMPLES_DIRNAME
    if samples.is_dir():
        targets += [(p, "sample") for p in sorted(samples.glob("*.md"))]
    templates = directory / pa_lib.UPGRADER_TEMPLATES_DIRNAME
    if templates.is_dir():
        targets += [(p, "template") for p in sorted(templates.glob("*.md")) if p.name != "INDEX.md"]
    if not targets:
        print(f"{directory}: no references (add Markdown files here, see README.md)")
        return 0, 0
    for path, role in targets:
        if role == "template":
            _, findings = validate_template(path)
        else:
            _, findings = validate_reference(path)
        errs = [f for f in findings if f.severity == "error"]
        warns = [f for f in findings if f.severity == "warning"]
        errors += len(errs)
        warnings += len(warns)
        if errs or warns or not quiet:
            status = "FAIL" if errs else "ok"
            print(f"[{status}] {path.relative_to(directory).as_posix()} ({role}): "
                  f"{len(errs)} error(s), {len(warns)} warning(s)")
        for finding in errs + warns:
            print(f"    {finding}")
    return errors, warnings


def parse_context(pairs: list[str]) -> dict:
    context: dict = {"domains": []}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"--for expects key=value, got {pair!r}")
        key, value = pair.split("=", 1)
        key = key.strip().lower()
        if key in ("domain", "domains"):
            context["domains"] = [v.strip().lower() for v in value.split(",") if v.strip()]
        elif key in ("artifact", "target", "model", "kind"):
            context[key] = value.strip().lower()
        else:
            raise SystemExit(f"--for: unknown key {key!r}; use domains, artifact, target, model, kind")
    return context


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", help="one skill-upgrader folder to use instead of discovery")
    parser.add_argument("--cwd", help="working project to search (default: current directory)")
    parser.add_argument("--list", action="store_true", help="show folders, files, and their filters")
    parser.add_argument("--for", dest="context", nargs="*", metavar="KEY=VALUE",
                        help="print the files that apply to a compilation")
    parser.add_argument("--json", action="store_true", help="machine-readable output for --list and --for")
    parser.add_argument("--quiet", action="store_true", help="only print problems when validating")
    args = parser.parse_args(argv)

    directories = [Path(args.dir).resolve()] if args.dir else pa_lib.upgrader_dirs(args.cwd)
    if args.dir and not directories[0].is_dir():
        print(f"not a directory: {directories[0]}", file=sys.stderr)
        return 2

    if args.list or args.context is not None:
        context = parse_context(args.context or []) if args.context is not None else None
        rows = []
        for directory in directories:
            for path in pa_lib.upgrader_files(directory):
                meta, _ = pa_lib.parse_frontmatter(pa_lib.read_text(path))
                applies = pa_lib.upgrader_applies(meta, **context) if context is not None else None
                rows.append({
                    "path": str(path),
                    "name": str(meta.get("name") or path.stem),
                    "description": str(meta.get("description") or ""),
                    "filters": {k: pa_lib._as_tags(meta.get(k)) for k in ("domains", "artifacts", "targets", "models", "kinds") if meta.get(k)},
                    "applies": applies,
                })
        if context is not None:
            rows = [r for r in rows if r["applies"]]
        if args.json:
            print(json.dumps({"directories": [str(d) for d in directories], "references": rows}, indent=2))
            return 0
        if not directories:
            print("no skill-upgrader folder found (looked in the working project and this project)")
            return 0
        heading = "applies" if context is not None else "references"
        print(f"skill-upgrader: {len(directories)} folder(s), {len(rows)} {heading}")
        for directory in directories:
            print(f"  {directory}")
        for row in rows:
            filters = "; ".join(f"{k}: {', '.join(v)}" for k, v in row["filters"].items()) or "always"
            print(f"- {row['path']}")
            print(f"    {row['description'] or row['name']}  [{filters}]")
        return 0

    if not directories:
        print("no skill-upgrader folder found; nothing to validate")
        return 0
    total_errors = total_warnings = 0
    for directory in directories:
        print(f"== {directory}")
        errors, warnings = check_directory(directory, args.quiet)
        total_errors += errors
        total_warnings += warnings
    print(f"{len(directories)} folder(s): {total_errors} error(s), {total_warnings} warning(s)")
    return 1 if total_errors else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    sys.exit(main())

#!/usr/bin/env python3
"""Validate skill directories and plugins: spec conformance plus a static security scan.

Usage:
    python scripts/check_skill.py <skill-dir> [<skill-dir> ...] [--json] [--strict] [--generated]
    python scripts/check_skill.py --plugin <plugin-dir> [--skillspector]

Checks each SKILL.md against the Agent Skills specification and the Claude Code
frontmatter (name format and directory match, description length and "when to
use" cue, body size, referenced files, leftover placeholders), then scans every
text file in the skill for the security patterns described in
skills/prompt-architect/references/skill-security.md (prompt injection,
anti-refusal, credential access, exfiltration, privilege escalation, destructive
commands without confirmation, remote or obfuscated execution, persistence,
trigger abuse, hidden text). With --plugin, the plugin manifests and hooks are
checked and every skill in the plugin is scanned. With --skillspector, the
external `skillspector` CLI is run as a second opinion when it is installed.

Exit status: 0 when no errors (warnings allowed unless --strict), 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pa_lib  # noqa: E402
import pa_skill  # noqa: E402


def run_skillspector(target: Path) -> dict | None:
    exe = shutil.which("skillspector")
    if not exe:
        return None
    try:
        proc = subprocess.run(
            [exe, "scan", str(target), "--no-llm", "--format", "json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"error": str(exc)}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"error": "unparseable skillspector output", "stdout": proc.stdout[:500], "stderr": proc.stderr[:500]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("targets", nargs="*", help="skill directories (or a plugin directory with --plugin)")
    parser.add_argument("--plugin", action="store_true", help="treat the target as a plugin directory")
    parser.add_argument("--generated", action="store_true", help="stricter checks for freshly generated skills (no TODO/TBD)")
    parser.add_argument("--skillspector", action="store_true", help="also run the skillspector CLI when installed")
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = parser.parse_args(argv)
    if not args.targets:
        parser.error("at least one target is required")

    report: list[dict] = []
    total_errors = total_warnings = 0
    for target in args.targets:
        target_path = Path(target).resolve()
        entries: list[tuple[str, list[pa_lib.Finding]]] = []
        if args.plugin:
            plugin_findings, skill_dirs = pa_skill.lint_plugin(target_path)
            entries.append((f"{target_path.name} (plugin manifests)", plugin_findings))
            for skill_dir in skill_dirs:
                entries.append((skill_dir.relative_to(target_path).as_posix(), pa_skill.lint_skill(skill_dir, strict_generated=args.generated)))
        else:
            entries.append((target_path.name, pa_skill.lint_skill(target_path, strict_generated=args.generated)))
        spector = run_skillspector(target_path) if args.skillspector else None
        for label, findings in entries:
            errors = [f for f in findings if f.severity == "error"]
            warnings = [f for f in findings if f.severity == "warning"]
            total_errors += len(errors)
            total_warnings += len(warnings)
            report.append({"target": label, "errors": [f.__dict__ for f in errors], "warnings": [f.__dict__ for f in warnings]})
            if not args.json:
                status = "FAIL" if errors else "ok"
                print(f"[{status}] {label}: {len(errors)} error(s), {len(warnings)} warning(s)")
                for finding in errors + warnings:
                    print(f"    {finding}")
        if args.skillspector:
            if spector is None:
                note = "skillspector CLI not installed; static line only"
            elif "error" in spector:
                note = f"skillspector failed: {spector['error']}"
            else:
                note = f"skillspector score={spector.get('risk_score', spector.get('score'))} severity={spector.get('severity')} recommendation={spector.get('recommendation')}"
            report[-1]["skillspector"] = spector
            if not args.json:
                print(f"    {note}")

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{len(report)} target(s): {total_errors} error(s), {total_warnings} warning(s)")
    if total_errors or (args.strict and total_warnings):
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    sys.exit(main())

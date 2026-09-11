#!/usr/bin/env python3
"""Lint a compiled prompt or a full Prompt Architect output.

Usage:
    python scripts/validate_prompt.py <file> [--json] [--strict] [--template]
                                            [--autonomy A3] [--risk HIGH] [--level 3]
    python scripts/validate_prompt.py <file> --profile-matrix
    cat output.md | python scripts/validate_prompt.py -

If the file contains a '## Compilation Summary' block, the summary is parsed and
the prompt is extracted from the '## Prompt' fence; the declared autonomy, risk,
mode, and level drive the checks. Otherwise the whole file is treated as a bare
prompt and the --autonomy/--risk/--level flags supply that information.

--profile-matrix re-lints the prompt against progressively weaker runtimes and
reports which ones it would still be honest on. A prompt written for a full
toolchain is expected to fail the lower rows; one that degrades honestly is not.

Exit status: 0 when there are no errors (warnings allowed unless --strict),
1 when errors (or warnings with --strict) were found, 2 on usage problems.
"""

from __future__ import annotations

import argparse
import json
import sys

sys.dont_write_bytecode = True
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pa_lib  # noqa: E402

# Progressively weaker runtimes, for --profile-matrix. A prompt written for a full
# toolchain is expected to fail the lower rows; that is the point of the check. One
# written to degrade honestly survives all of them.
MATRIX_PROFILES: list[tuple[str, dict[str, str]]] = [
    ("full tools", {c: "yes" for c in pa_lib.CAPABILITIES}),
    ("files only", {**{c: "no" for c in pa_lib.CAPABILITIES}, "files.read": "yes", "files.write": "yes"}),
    ("read only", {**{c: "no" for c in pa_lib.CAPABILITIES}, "files.read": "yes"}),
    ("no tools", {c: "no" for c in pa_lib.CAPABILITIES}),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="path to the output or prompt file, or '-' for stdin")
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--template", action="store_true", help="allow {{VARIABLES}} and architect comments")
    parser.add_argument("--autonomy", choices=pa_lib.AUTONOMY, help="declared autonomy for a bare prompt")
    parser.add_argument("--risk", choices=pa_lib.RISKS, help="declared risk for a bare prompt")
    parser.add_argument("--level", type=int, choices=pa_lib.LEVELS, help="declared level for a bare prompt")
    parser.add_argument("--mode", action="append", default=[], help="declared mode(s) for a bare prompt")
    parser.add_argument("--profile-matrix", action="store_true",
                        help="re-lint the prompt against weaker runtime profiles and report which it survives")
    args = parser.parse_args(argv)

    try:
        text = sys.stdin.read() if args.file == "-" else pa_lib.read_text(args.file)
    except OSError as exc:
        print(f"cannot read {args.file}: {exc}", file=sys.stderr)
        return 2

    out = pa_lib.parse_architect_output(text)
    if out.has_summary:
        findings = pa_lib.lint_output(out, template_mode=args.template)
    else:
        findings = pa_lib.lint_prompt(
            out.prompt or "",
            autonomy=args.autonomy,
            risk=args.risk,
            modes=args.mode,
            level=args.level,
            template_mode=args.template,
        )

    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]

    if args.json:
        print(json.dumps({
            "file": args.file,
            "has_summary": out.has_summary,
            "summary": out.summary,
            "errors": [f.__dict__ for f in errors],
            "warnings": [f.__dict__ for f in warnings],
        }, indent=2))
    else:
        if out.has_summary:
            print(
                f"summary: level={out.level} risk={out.risk} autonomy={out.autonomy} "
                f"modes={','.join(out.modes) or '-'} domains={','.join(out.domains) or '-'} "
                f"template={out.template or 'none'} questions={out.question_count}"
            )
        for finding in findings:
            print(finding)
        print(f"{len(errors)} error(s), {len(warnings)} warning(s)")

    if args.profile_matrix:
        print()
        print("profile matrix: would this prompt still be honest on a weaker runtime?")
        for label, profile in MATRIX_PROFILES:
            matrix = pa_lib.lint_prompt(
                out.prompt or "",
                autonomy=out.autonomy or args.autonomy,
                risk=out.risk or args.risk,
                modes=out.modes or args.mode,
                level=out.level or args.level,
                model_tier=out.model_tier,
                capabilities=profile,
                template_mode=args.template,
            )
            faked = [f for f in matrix if f.code == "C01" and f.severity == "error"]
            verdict = ("ok" if not faked else
                       f"assumes {len(faked)} capabilit{'y' if len(faked) == 1 else 'ies'} "
                       "the runtime lacks")
            print(f"  {label:<22} {verdict}")
            for finding in faked:
                print(f"      {finding.message}")

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    sys.exit(main())

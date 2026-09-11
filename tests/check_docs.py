#!/usr/bin/env python3
"""Verify that the summary lines README quotes really come from the worked examples.

The "How to ask" section teaches by quoting compiled output. Those quotes are only
persuasive while they are true, and nothing else would catch them drifting: they are
prose, so no linter reads them, and the examples they came from change over time.

Usage:
    python tests/check_docs.py        # exit 1 if a quoted line is not in examples/
"""

from __future__ import annotations

import re
import sys

sys.dont_write_bytecode = True
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
EXAMPLES_DIR = ROOT / "skills" / "prompt-architect" / "examples"
SECTION = "## How to ask"


def quoted_summary_lines(text: str) -> list[str]:
    """Summary lines ('- Key: value') inside fenced blocks of the How to ask section."""
    start = text.find(SECTION)
    if start == -1:
        raise SystemExit(f"check_docs: README.md has no '{SECTION}' section")
    rest = text[start + len(SECTION):]
    end = re.search(r"^## ", rest, re.M)
    section = rest[: end.start()] if end else rest
    lines: list[str] = []
    for block in re.findall(r"^```[a-z]*\n(.*?)^```", section, re.S | re.M):
        lines += [ln.rstrip() for ln in block.splitlines() if ln.startswith("- ") and ":" in ln]
    return lines


def main() -> int:
    corpus = {p.name: p.read_text(encoding="utf-8") for p in sorted(EXAMPLES_DIR.glob("*.md"))}
    if not corpus:
        raise SystemExit(f"check_docs: no examples found in {EXAMPLES_DIR}")
    quoted = quoted_summary_lines(README.read_text(encoding="utf-8"))
    if not quoted:
        raise SystemExit("check_docs: the How to ask section quotes no summary lines")

    missing = []
    for line in quoted:
        if not any(line in text for text in corpus.values()):
            missing.append(line)
    for line in missing:
        print(f"FAIL not found in any example: {line}", file=sys.stderr)
    print(f"{len(quoted)} quoted summary line(s) checked against {len(corpus)} example(s): "
          f"{len(missing)} stale")
    return 1 if missing else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    sys.exit(main())

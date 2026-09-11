#!/usr/bin/env python3
"""Evaluation harness for the Prompt Architect skill.

Runs the cases in tests/cases/*.toml through the skill, grades each output
deterministically (summary values, sections, patterns, lint), optionally asks a
model to judge softer criteria, optionally executes the compiled prompt on a
sample task and judges the result, and writes a report to tests/results/.

Backends:
  cli  - drives the local Claude Code CLI in print mode with the skill installed
         in a temporary project (default; uses your Claude Code login)
  api  - calls the Anthropic API directly with the skill as the system prompt
         and a read_file tool over the skill directory (pip install anthropic)

Examples:
  python tests/run_tests.py --list
  python tests/run_tests.py --from-dir examples             # grade pre-generated outputs offline
  python tests/run_tests.py --case simple-explain-oauth     # run one case through the CLI
  python tests/run_tests.py --category high-risk --judge --jobs 3
  python tests/run_tests.py --backend api --model claude-opus-5 --judge --execute
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
import tempfile
import threading
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "prompt-architect" / "scripts"))
import pa_lib  # noqa: E402

CASES_DIR = ROOT / "tests" / "cases"
RESULTS_DIR = ROOT / "tests" / "results"
FIXTURES_DIR = ROOT / "tests" / "fixtures"
SKILL_DIR = pa_lib.SKILL_DIR
SKILL_ITEMS = ["SKILL.md", "references", "templates", "examples", "scripts"]
KNOWN_EXPECT_KEYS = {
    "domains_all", "domains_any", "risk", "modes_all", "modes_any", "autonomy", "level",
    "template", "template_any", "clarify", "review", "required_sections", "forbidden_sections",
    "model_tier", "target", "capabilities_yes", "capabilities_no", "gaps_blocking", "compatibility",
    "upgrades",
    "must_match", "must_not_match", "max_prompt_lines",
    "artifact", "skill_kind", "tier", "skill_name", "required_files", "max_skill_lines",
}

JUDGE_INSTRUCTIONS = (
    "You are grading the output of a prompt compiler against explicit criteria. Judge strictly and "
    "literally from the artifact alone; do not reward length, tone, or confidence. Respond with a JSON "
    "array only, one object per criterion in the given order: "
    '[{"criterion": "<text>", "pass": true, "reason": "<one sentence>"}]'
)


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------

def load_cases() -> list[dict]:
    cases: list[dict] = []
    for path in sorted(CASES_DIR.glob("*.toml")):
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        for case in data.get("case", []):
            case.setdefault("category", path.stem)
            case["_file"] = path.name
            cases.append(case)
    seen: set[str] = set()
    for case in cases:
        if "id" not in case or "request" not in case:
            raise SystemExit(f"{case.get('_file')}: every case needs 'id' and 'request'")
        if case["id"] in seen:
            raise SystemExit(f"duplicate case id {case['id']!r}")
        seen.add(case["id"])
        unknown = set(case.get("expect", {})) - KNOWN_EXPECT_KEYS
        if unknown:
            raise SystemExit(f"{case['id']}: unknown expect keys {sorted(unknown)}")
    return cases


def select_cases(cases: list[dict], ids: list[str], categories: list[str]) -> list[dict]:
    selected = cases
    if ids:
        missing = set(ids) - {c["id"] for c in cases}
        if missing:
            raise SystemExit(f"unknown case id(s): {sorted(missing)}")
        selected = [c for c in selected if c["id"] in ids]
    if categories:
        selected = [c for c in selected if c["category"] in categories]
    return selected


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------

def find_claude_bin(explicit: str | None) -> str:
    if explicit:
        return explicit
    env = os.environ.get("CLAUDE_BIN")
    if env:
        return env
    found = shutil.which("claude") or shutil.which("claude.exe")
    if found:
        return found
    for base in (Path.home() / ".vscode" / "extensions", Path.home() / ".vscode-insiders" / "extensions"):
        hits = sorted(base.glob("anthropic.claude-code-*/resources/native-binary/claude*"))
        if hits:
            return str(hits[-1])
    raise SystemExit("claude CLI not found: pass --claude-bin or set CLAUDE_BIN")


class ClaudeCliBackend:
    """Runs the skill through `claude -p` inside a temporary project that contains it."""

    name = "cli"

    def __init__(self, claude_bin: str, model: str | None, judge_model: str | None, invoke: str,
                 max_turns: int, timeout: float, max_budget_usd: float | None, effort: str | None):
        self.claude_bin = claude_bin
        self.model = model
        self.judge_model = judge_model
        self.invoke = invoke
        self.max_turns = max_turns
        self.timeout = timeout
        self.max_budget_usd = max_budget_usd
        self.effort = effort
        self.total_cost_usd = 0.0
        self._cost_lock = threading.Lock()
        self.workdir = self._make_workdir()

    @staticmethod
    def _make_workdir(fixtures: tuple[str, ...] = ()) -> Path:
        """A temporary project with the skill installed and any fixture folders at its root."""
        workdir = Path(tempfile.mkdtemp(prefix="prompt-architect-eval-"))
        skill_dir = workdir / ".claude" / "skills" / "prompt-architect"
        skill_dir.mkdir(parents=True)
        for item in SKILL_ITEMS:
            source = SKILL_DIR / item
            if source.is_dir():
                shutil.copytree(source, skill_dir / item)
            elif source.exists():
                shutil.copy2(source, skill_dir / item)
        for name in fixtures:
            source = FIXTURES_DIR / name
            if not source.is_dir():
                raise FileNotFoundError(f"fixture {name!r} not found under {FIXTURES_DIR}")
            shutil.copytree(source, workdir / source.name)
        return workdir

    def close(self) -> None:
        shutil.rmtree(self.workdir, ignore_errors=True)

    def _run(self, prompt_arg: str | None, extra: list[str], model: str | None, stdin: str | None = None,
             cwd: Path | None = None) -> str:
        cmd = [self.claude_bin, "-p", "--output-format", "json", "--no-session-persistence"]
        if prompt_arg is not None:
            cmd.insert(2, prompt_arg)
        if model:
            cmd += ["--model", model]
        if self.max_budget_usd:
            cmd += ["--max-budget-usd", str(self.max_budget_usd)]
        cmd += extra
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)
        env.pop("CLAUDE_CODE_ENTRYPOINT", None)
        proc = subprocess.run(
            cmd, cwd=cwd or self.workdir, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=self.timeout, env=env, input=stdin,
        )
        if proc.returncode != 0 and not proc.stdout.strip():
            raise RuntimeError(f"claude exited {proc.returncode}: {proc.stderr.strip()[:500]}")
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            raise RuntimeError(f"unparseable CLI output: {proc.stdout[:300]!r} {proc.stderr[:300]!r}")
        cost = data.get("total_cost_usd")
        if isinstance(cost, (int, float)):
            with self._cost_lock:
                self.total_cost_usd += float(cost)
        if data.get("is_error"):
            raise RuntimeError(f"claude reported an error: {str(data.get('result'))[:500]}")
        return str(data.get("result", ""))

    def compile(self, request: str, fixtures: tuple[str, ...] = ()) -> str:
        if fixtures:
            workdir = self._make_workdir(fixtures)
            try:
                return self._compile_in(request, workdir)
            finally:
                shutil.rmtree(workdir, ignore_errors=True)
        return self._compile_in(request, self.workdir)

    def _compile_in(self, request: str, workdir: Path) -> str:
        if self.invoke == "slash":
            prompt = f"/prompt-architect {request}"
        else:
            prompt = (
                "Use the prompt-architect skill to compile the following request into a Claude prompt. "
                "Follow the skill's output format exactly.\n\n<request>\n" + request + "\n</request>"
            )
        extra = [
            "--max-turns", str(self.max_turns),
            "--allowedTools", "Skill", "Read", "Glob", "Grep",
            "--disallowedTools", "Bash", "Write", "Edit", "MultiEdit", "WebSearch", "WebFetch", "Agent",
        ]
        if self.effort:
            extra += ["--effort", self.effort]
        return self._run(prompt, extra, self.model, cwd=workdir)

    def complete(self, system: str, user: str, *, judge: bool = False) -> str:
        extra = ["--max-turns", "1", "--system-prompt", system, "--tools", ""]
        return self._run(None, extra, self.judge_model if judge else self.model, stdin=user)


class AnthropicApiBackend:
    """Calls the Messages API with the skill as the system prompt and a read_file tool."""

    name = "api"

    def __init__(self, model: str, judge_model: str, effort: str, timeout: float, fallbacks: bool):
        try:
            import anthropic  # type: ignore
        except ImportError as exc:
            raise SystemExit("the api backend needs the anthropic package: pip install anthropic") from exc
        self.anthropic = anthropic
        self.client = anthropic.Anthropic(timeout=timeout)
        self.model = model
        self.judge_model = judge_model
        self.effort = effort
        self.fallbacks = fallbacks
        self.total_cost_usd = None
        skill_text = pa_lib.read_text(SKILL_DIR / "SKILL.md")
        _, body = pa_lib.parse_frontmatter(skill_text)
        self.system = (
            f"Base directory for this skill: {SKILL_DIR}\n"
            "Use the read_file tool to read files under the skill directory (references/, templates/, examples/).\n\n"
            + body.replace("`$ARGUMENTS`", "the user's message")
        )
        self.tools = [{
            "name": "read_file",
            "description": "Read a UTF-8 text file from the prompt-architect skill directory. "
                           "The path is relative to the skill directory, for example 'references/sections.md'.",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Relative path inside the skill directory"}},
                "required": ["path"],
                "additionalProperties": False,
            },
            "strict": True,
        }]

    def close(self) -> None:
        return None

    def _read_file(self, rel_path: str) -> str:
        target = (SKILL_DIR / rel_path).resolve()
        allowed = [SKILL_DIR / item for item in SKILL_ITEMS] + [SKILL_DIR / "scripts"]
        inside = any(target == base.resolve() or base.resolve() in target.parents for base in allowed)
        if not inside or not target.is_file():
            return f"error: '{rel_path}' is not a readable file inside the skill directory"
        return target.read_text(encoding="utf-8")

    def _request(self, *, model: str, system: str, messages: list, tools: list | None, max_tokens: int):
        kwargs = dict(
            model=model, max_tokens=max_tokens, system=system, messages=messages,
            thinking={"type": "adaptive"}, output_config={"effort": self.effort},
        )
        if tools:
            kwargs["tools"] = tools
        if self.fallbacks:
            api = self.client.beta.messages
            kwargs["betas"] = ["server-side-fallback-2026-07-01"]
            kwargs["fallbacks"] = "default"
        else:
            api = self.client.messages
        with api.stream(**kwargs) as stream:
            return stream.get_final_message()

    @staticmethod
    def _text(response) -> str:
        return "".join(block.text for block in response.content if getattr(block, "type", "") == "text")

    def compile(self, request: str) -> str:
        messages: list = [{"role": "user", "content": f"Compile this request into a Claude prompt:\n\n{request}"}]
        for _ in range(20):
            response = self._request(model=self.model, system=self.system, messages=messages,
                                     tools=self.tools, max_tokens=64000)
            if response.stop_reason == "refusal":
                raise RuntimeError("the model refused the request")
            if response.stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": response.content})
                continue
            tool_uses = [b for b in response.content if getattr(b, "type", "") == "tool_use"]
            if not tool_uses:
                return self._text(response)
            messages.append({"role": "assistant", "content": response.content})
            results = []
            for block in tool_uses:
                path = str(block.input.get("path", "")) if isinstance(block.input, dict) else ""
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": self._read_file(path)})
            messages.append({"role": "user", "content": results})
        raise RuntimeError("tool loop did not finish within 20 turns")

    def complete(self, system: str, user: str, *, judge: bool = False) -> str:
        response = self._request(model=self.judge_model if judge else self.model, system=system,
                                 messages=[{"role": "user", "content": user}], tools=None, max_tokens=16000)
        if response.stop_reason == "refusal":
            raise RuntimeError("the model refused the request")
        return self._text(response)


class FromDirBackend:
    """Grades pre-generated outputs (<dir>/<case-id>.md) without calling any model."""

    name = "from-dir"

    def __init__(self, directory: Path):
        self.directory = directory
        self.total_cost_usd = None

    def close(self) -> None:
        return None

    def compile(self, request: str, case_id: str = "") -> str:
        path = self.directory / f"{case_id}.md"
        if not path.exists():
            raise FileNotFoundError(f"no pre-generated output for {case_id} at {path}")
        return pa_lib.read_text(path)

    def complete(self, system: str, user: str, *, judge: bool = False) -> str:
        raise RuntimeError("the from-dir backend cannot call a model; drop --judge and --execute")


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------

def run_judge(backend, artifact: str, criteria: list[str]) -> list[dict]:
    user = "<artifact>\n" + artifact + "\n</artifact>\n\nCriteria:\n" + "\n".join(
        f"{i + 1}. {c}" for i, c in enumerate(criteria)
    )
    text = backend.complete(JUDGE_INSTRUCTIONS, user, judge=True)
    match = re.search(r"\[.*\]", text, re.S)
    try:
        verdicts = json.loads(match.group(0)) if match else []
    except json.JSONDecodeError:
        verdicts = []
    if len(verdicts) != len(criteria):
        return [{"criterion": c, "pass": False, "reason": "judge output unparseable"} for c in criteria]
    return [{"criterion": c, "pass": bool(v.get("pass")), "reason": str(v.get("reason", ""))}
            for c, v in zip(criteria, verdicts)]


def grade_case(case: dict, text: str, backend, *, use_judge: bool, execute: bool) -> dict:
    out = pa_lib.parse_architect_output(text)
    exp = case.get("expect", {})
    checks: list[dict] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    lint = pa_lib.lint_output(out)
    errors = [str(f) for f in lint if f.severity == "error"]
    warnings = [str(f) for f in lint if f.severity == "warning"]
    check("format", out.has_summary, "no '## Compilation Summary' block found")
    check("lint", not errors, "; ".join(errors))

    prompt = out.prompt or ""
    present = [canon for _, canon, _ in pa_lib.prompt_sections(prompt) if canon]
    clarify = exp.get("clarify")
    if clarify is True:
        check("clarify", out.question_count > 0 and not out.prompt,
              f"questions={out.question_count}, prompt={'yes' if out.prompt else 'no'}")
    elif clarify is False:
        check("no-clarify", out.question_count == 0 and bool(out.prompt or out.review or out.skill_files),
              f"questions={out.question_count}, prompt={'yes' if out.prompt else 'no'}, skill files={len(out.skill_files)}")
    if "domains_all" in exp:
        missing = [d for d in exp["domains_all"] if d not in out.domains]
        check("domains_all", not missing, f"missing {missing}; got {out.domains}")
    if "domains_any" in exp:
        check("domains_any", any(d in out.domains for d in exp["domains_any"]),
              f"got {out.domains}; expected one of {exp['domains_any']}")
    if "risk" in exp:
        check("risk", out.risk in exp["risk"], f"got {out.risk}; expected one of {exp['risk']}")
    if "modes_all" in exp:
        missing = [m for m in exp["modes_all"] if m not in out.modes]
        check("modes_all", not missing, f"missing {missing}; got {out.modes}")
    if "modes_any" in exp:
        check("modes_any", any(m in out.modes for m in exp["modes_any"]),
              f"got {out.modes}; expected one of {exp['modes_any']}")
    if "autonomy" in exp:
        check("autonomy", out.autonomy in exp["autonomy"], f"got {out.autonomy}; expected one of {exp['autonomy']}")
    if "level" in exp:
        check("level", out.level in exp["level"], f"got {out.level}; expected one of {exp['level']}")
    if "model_tier" in exp:
        check("model_tier", out.model_tier in exp["model_tier"],
              f"got {out.model_tier}; expected one of {exp['model_tier']}")
    if "target" in exp:
        check("target", out.target in exp["target"], f"got {out.target}; expected one of {exp['target']}")
    caps = out.capabilities
    for wanted, state in (("capabilities_yes", "yes"), ("capabilities_no", "no")):
        for name in exp.get(wanted, []):
            check(f"cap:{name}={state}", caps.get(name) == state,
                  f"got {name}={caps.get(name)}; capabilities: {caps}")
    if "gaps_blocking" in exp:
        blocking = [name for name, kind in out.gaps if kind == "blocking"]
        missing = [g for g in exp["gaps_blocking"] if g not in blocking]
        check("gaps_blocking", not missing, f"missing {missing}; blocking gaps: {blocking}")
    if "compatibility" in exp:
        present_section = out.compatibility is not None
        check("compatibility", present_section == bool(exp["compatibility"]),
              f"'## Compatibility' section {'present' if present_section else 'absent'}")
    if "upgrades" in exp:
        wanted = [u.lower() for u in exp["upgrades"]]
        applied = [u.lower() for u in out.upgrades]
        if not wanted:
            check("upgrades", not applied, f"expected 'Upgrades: none'; got {applied}")
        else:
            missing = [u for u in wanted if u not in applied]
            check("upgrades", not missing, f"missing {missing}; applied: {applied}")
    if "template" in exp:
        wanted = exp["template"]
        ok = out.template is None if wanted == "none" else out.template == wanted
        check("template", ok, f"got {out.template}; expected {wanted}")
    if "template_any" in exp:
        check("template", out.template in exp["template_any"], f"got {out.template}; expected one of {exp['template_any']}")
    if exp.get("review"):
        check("review", out.review is not None and bool(re.search(r"(?i)score", out.review or "")),
              "no '## Review' section with a score")
    if "artifact" in exp:
        check("artifact", out.artifact == exp["artifact"], f"got {out.artifact}; expected {exp['artifact']}")
    if "skill_kind" in exp:
        check("skill_kind", out.skill_kind == exp["skill_kind"], f"got {out.skill_kind}; expected {exp['skill_kind']}")
    if "tier" in exp:
        check("tier", out.tier == exp["tier"], f"got {out.tier}; expected {exp['tier']}")
    if "skill_name" in exp:
        check("skill_name", out.skill_name == exp["skill_name"], f"got {out.skill_name}; expected {exp['skill_name']}")
    for wanted in exp.get("required_files", []):
        check(f"file:{wanted}", any(path == wanted or path.endswith("/" + wanted) for path in out.skill_files),
              f"files: {sorted(out.skill_files)}")
    if out.artifact == "skill" and out.skill_files:
        skill_text = out.skill_md or ""
        for pattern in exp.get("must_match", []):
            check(f"match:{pattern}", bool(re.search(pattern, skill_text)), "pattern not found in SKILL.md")
        for pattern in exp.get("must_not_match", []):
            check(f"no-match:{pattern}", not re.search(pattern, skill_text), "forbidden pattern found in SKILL.md")
        if "max_skill_lines" in exp:
            count = len([ln for ln in skill_text.splitlines() if ln.strip()])
            check("length", count <= exp["max_skill_lines"], f"{count} lines > {exp['max_skill_lines']}")
    elif prompt:
        for section in exp.get("required_sections", []):
            check(f"section:{section}", section in present, f"present: {present}")
        for section in exp.get("forbidden_sections", []):
            check(f"no-section:{section}", section not in present, "section present")
        for pattern in exp.get("must_match", []):
            check(f"match:{pattern}", bool(re.search(pattern, prompt)), "pattern not found in prompt")
        for pattern in exp.get("must_not_match", []):
            check(f"no-match:{pattern}", not re.search(pattern, prompt), "forbidden pattern found in prompt")
        if "max_prompt_lines" in exp:
            count = len([ln for ln in prompt.splitlines() if ln.strip()])
            check("length", count <= exp["max_prompt_lines"], f"{count} lines > {exp['max_prompt_lines']}")

    judge_results: list[dict] = []
    if use_judge and case.get("judge", {}).get("criteria"):
        judge_results = run_judge(backend, text, case["judge"]["criteria"])
        for verdict in judge_results:
            check("judge:" + verdict["criterion"][:60], verdict["pass"], verdict["reason"])

    task_results: dict = {}
    if execute and case.get("task") and prompt:
        task = case["task"]
        response = backend.complete(prompt, task["input"])
        artifact = f"<task_input>\n{task['input']}\n</task_input>\n<response>\n{response}\n</response>"
        verdicts = run_judge(backend, artifact, task["criteria"])
        task_results = {"response": response, "verdicts": verdicts}
        for verdict in verdicts:
            check("task:" + verdict["criterion"][:60], verdict["pass"], verdict["reason"])

    return {
        "id": case["id"],
        "category": case["category"],
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
        "lint_warnings": warnings,
        "summary": out.summary,
        "judge": judge_results,
        "task": task_results,
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def run_one(case: dict, backend, args) -> dict:
    started = time.time()
    try:
        fixtures = tuple(case.get("fixtures", []))
        if isinstance(backend, FromDirBackend):
            text = backend.compile(case["request"], case_id=case["id"])
        elif isinstance(backend, ClaudeCliBackend):
            text = backend.compile(case["request"], fixtures=fixtures)
        elif fixtures:
            raise RuntimeError("fixtures are supported by the cli and from-dir backends only")
        else:
            text = backend.compile(case["request"])
        result = grade_case(case, text, backend, use_judge=args.judge, execute=args.execute)
        result["output"] = text
    except Exception as exc:  # noqa: BLE001 - report any failure per case
        result = {"id": case["id"], "category": case["category"], "passed": False,
                  "checks": [{"name": "run", "ok": False, "detail": f"{type(exc).__name__}: {exc}"}],
                  "lint_warnings": [], "summary": {}, "judge": [], "task": {}, "output": ""}
    result["seconds"] = round(time.time() - started, 1)
    return result


def write_report(run_dir: Path, results: list[dict], args, backend_name: str, total_cost_usd: float | None) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    for result in results:
        if result.get("output"):
            (run_dir / f"{result['id']}.md").write_text(result["output"], encoding="utf-8", newline="\n")
    passed = sum(1 for r in results if r["passed"])
    report = {
        "run": run_dir.name,
        "backend": backend_name,
        "model": getattr(args, "model", None),
        "judge": args.judge,
        "execute": args.execute,
        "passed": passed,
        "total": len(results),
        "total_cost_usd": total_cost_usd,
        "cases": [{k: v for k, v in r.items() if k != "output"} for r in results],
    }
    (run_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8", newline="\n")
    lines = [
        f"# Prompt Architect evaluation: {run_dir.name}",
        "",
        f"Backend: {backend_name}. Model: {getattr(args, 'model', None) or 'default'}. "
        f"Judge: {'on' if args.judge else 'off'}. Execute: {'on' if args.execute else 'off'}.",
        "",
        f"**{passed} / {len(results)} cases passed.**"
        + (f" Total cost: ${total_cost_usd:.2f}." if isinstance(total_cost_usd, (int, float)) else ""),
        "",
        "| Case | Category | Result | Level | Risk | Autonomy | Template | Failed checks |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        failed = [c["name"] for c in r["checks"] if not c["ok"]]
        summary = r.get("summary", {})
        lines.append(
            f"| {r['id']} | {r['category']} | {'PASS' if r['passed'] else 'FAIL'} | "
            f"{summary.get('level', '')} | {summary.get('risk', '')} | {summary.get('autonomy', '')} | "
            f"{summary.get('template', '')} | {', '.join(failed)[:120]} |"
        )
    lines.append("")
    for r in results:
        failed = [c for c in r["checks"] if not c["ok"]]
        if failed or r["lint_warnings"]:
            lines.append(f"## {r['id']}")
            for c in failed:
                lines.append(f"- FAIL {c['name']}: {c['detail']}")
            for w in r["lint_warnings"]:
                lines.append(f"- warning: {w}")
            lines.append("")
    (run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--backend", choices=["cli", "api"], default="cli")
    parser.add_argument("--from-dir", help="grade pre-generated outputs named <case-id>.md in this directory")
    parser.add_argument("--case", action="append", default=[], help="case id to run (repeatable)")
    parser.add_argument("--category", action="append", default=[], help="category to run (repeatable)")
    parser.add_argument("--jobs", type=int, default=1, help="parallel cases")
    parser.add_argument("--judge", action="store_true", help="ask a model to grade the [case.judge] criteria")
    parser.add_argument("--execute", action="store_true", help="run compiled prompts on [case.task] inputs and judge")
    parser.add_argument("--model", help="model for compilation (cli: alias or id; api: model id, default claude-opus-5)")
    parser.add_argument("--judge-model", default="claude-sonnet-5", help="model for judging and task execution")
    parser.add_argument("--effort", help="effort level (cli: --effort passthrough; api: output_config.effort, default high)")
    parser.add_argument("--claude-bin", help="path to the claude CLI (cli backend)")
    parser.add_argument("--invoke", choices=["slash", "natural"], default="slash", help="how to trigger the skill (cli)")
    parser.add_argument("--max-turns", type=int, default=25, help="max agent turns per compilation (cli)")
    parser.add_argument("--max-budget-usd", type=float, help="per-call spend cap passed to the CLI")
    parser.add_argument("--timeout", type=float, default=900, help="seconds per model call")
    parser.add_argument("--no-fallbacks", action="store_true", help="api: do not enable server-side refusal fallbacks")
    parser.add_argument("--list", action="store_true", help="list cases and exit")
    parser.add_argument("--dry-run", action="store_true", help="validate cases and show what would run")
    parser.add_argument("--out", help="results directory (default tests/results/<timestamp>)")
    args = parser.parse_args(argv)

    cases = load_cases()
    selected = select_cases(cases, args.case, args.category)
    if args.list or args.dry_run:
        for case in selected:
            flags = []
            if case.get("expect", {}).get("clarify"):
                flags.append("clarify")
            if case.get("judge"):
                flags.append("judge")
            if case.get("task"):
                flags.append("task")
            print(f"{case['id']:36} {case['category']:14} {' '.join(flags)}")
        print(f"{len(selected)} case(s)")
        return 0

    if args.from_dir:
        backend = FromDirBackend(Path(args.from_dir))
        if args.judge or args.execute:
            raise SystemExit("--from-dir cannot be combined with --judge or --execute")
    elif args.backend == "api":
        backend = AnthropicApiBackend(
            model=args.model or "claude-opus-5", judge_model=args.judge_model,
            effort=args.effort or "high", timeout=args.timeout, fallbacks=not args.no_fallbacks,
        )
    else:
        backend = ClaudeCliBackend(
            claude_bin=find_claude_bin(args.claude_bin), model=args.model, judge_model=args.judge_model,
            invoke=args.invoke, max_turns=args.max_turns, timeout=args.timeout,
            max_budget_usd=args.max_budget_usd, effort=args.effort,
        )

    run_dir = Path(args.out) if args.out else RESULTS_DIR / dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"running {len(selected)} case(s) with backend={backend.name}; results in {run_dir}")
    results: list[dict] = []
    try:
        if args.jobs > 1 and not isinstance(backend, FromDirBackend):
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
                futures = {pool.submit(run_one, case, backend, args): case for case in selected}
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    results.append(result)
                    _print_result(result)
            results.sort(key=lambda r: [c["id"] for c in selected].index(r["id"]))
        else:
            for case in selected:
                result = run_one(case, backend, args)
                results.append(result)
                _print_result(result)
    finally:
        backend.close()

    total_cost = backend.total_cost_usd
    write_report(run_dir, results, args, backend.name, total_cost)
    passed = sum(1 for r in results if r["passed"])
    cost_note = f" Total cost: ${total_cost:.2f}." if isinstance(total_cost, (int, float)) else ""
    print(f"\n{passed} / {len(results)} passed.{cost_note} Report: {run_dir / 'report.md'}")
    return 0 if passed == len(results) else 1


def _print_result(result: dict) -> None:
    status = "PASS" if result["passed"] else "FAIL"
    failed = [c for c in result["checks"] if not c["ok"]]
    print(f"[{status}] {result['id']} ({result.get('seconds', 0)}s)")
    for c in failed:
        print(f"    - {c['name']}: {c['detail'][:200]}")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except AttributeError:
        pass
    sys.exit(main())

# How to load it

Four ways, of equal standing. Pick the one that matches where you work.

## Any agent: point it at the folder

Clone the repository and open it, or add it, as a project in the agent you use. The agent reads
`AGENTS.md`, which tells it to read `skills/prompt-architect/SKILL.md` and follow it. No
install step.

```bash
git clone https://github.com/packtryer-design/Skil
```

Cursor and GitHub Copilot also pick up their own entry points (`.cursor/rules/` and
`.github/copilot-instructions.md`), which point at the same `SKILL.md`. Any runtime that reads
the Agent Skills format can load `skills/prompt-architect/` directly.

To keep references of your own that adapt what it generates, add Markdown files to
`skill-upgrader/` here or in the project you are working in; see `skill-upgrader/README.md`.

## Claude Code, as a plugin

```bash
claude plugin marketplace add packtryer-design/Skil
claude plugin install prompt-architect@prompt-architect
```

Invoke with `/prompt-architect:prompt-architect <request>`.

Verify: `claude plugin list`. Update: `claude plugin marketplace update prompt-architect`.
Uninstall: `claude plugin uninstall prompt-architect`; keep it installed but off with
`claude plugin disable prompt-architect`.

## Claude Code, as a skills directory (no marketplace)

```bash
git clone https://github.com/packtryer-design/Skil ~/.claude/skills/prompt-architect
```

The repository carries a plugin manifest, so it loads on the next session as
`prompt-architect@skills-dir` and the command is `/prompt-architect`. For one project only,
clone into `.claude/skills/prompt-architect` inside that project (loads after workspace trust).
Update with `git pull`; remove by deleting the directory.

For development: `claude --plugin-dir /path/to/Skil` loads it for one session without
installing, `claude plugin validate /path/to/Skil` checks the manifests and skills, and
`/reload-plugins` picks up an edited `SKILL.md` in a running session.

## A single file, for hosts without file access

`dist/` holds the whole skill flattened into one self-contained system prompt, references
inlined, with nothing that depends on reading files or running scripts:

| File | For |
| --- | --- |
| `dist/prompt-architect.portable.md` | A frontier model anywhere: claude.ai, ChatGPT, Gemini, a raw API call |
| `dist/prompt-architect.compact.md` | A mid-tier model or a smaller context budget; prompts and templates only |

Paste one as the system prompt and send your request as the user message. Regenerate them
after changing the skill with `python skills/prompt-architect/scripts/build_portable.py`.

For claude.ai specifically, the other option is to zip `skills/prompt-architect/` and upload it
as a skill in settings; the scripts do not run there, so the Architect applies its checklists
by reading and prints skills instead of writing files.

## Requirements

None at run time beyond a capable agent or model. The tooling (`scripts/`, `tests/`) needs
Python 3.11 or newer; PyYAML is optional. The optional `--skillspector` flag of
`check_skill.py` needs NVIDIA SkillSpector installed separately.

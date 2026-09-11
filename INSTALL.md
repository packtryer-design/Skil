# How to install

## Claude Code (plugin, recommended)

```bash
claude plugin marketplace add MountaZer/Skil
claude plugin install prompt-architect@prompt-architect
```

Invoke with `/prompt-architect:prompt-architect <request>`.

Verify: `claude plugin list`. Update: `claude plugin marketplace update prompt-architect`. Uninstall: `claude plugin uninstall prompt-architect`; keep it installed but off with `claude plugin disable prompt-architect`.

## Claude Code (skills directory, no marketplace)

```bash
git clone https://github.com/MountaZer/Skil ~/.claude/skills/prompt-architect
```

The repository carries a plugin manifest, so it loads on the next session as `prompt-architect@skills-dir` and the command is `/prompt-architect`. For one project only, clone into `.claude/skills/prompt-architect` inside that project (loads after workspace trust). Update with `git pull`; remove by deleting the directory.

## Claude Code (development)

```bash
claude --plugin-dir /path/to/Skil       # load for this session only
claude plugin validate /path/to/Skil    # check the manifests and skills
```

Run `/reload-plugins` after editing `SKILL.md` in a running session.

## claude.ai

Zip the `skills/prompt-architect/` directory (it contains `SKILL.md`, `references/`, `templates/`, `examples/`, `scripts/`) and upload it as a skill in claude.ai settings. The scripts are not executed there; the Architect applies its checklists by hand and prints skills instead of writing files.

## Other runtimes

The skill follows the Agent Skills specification, so any runtime that reads `SKILL.md` can load `skills/prompt-architect/`. Runtimes without file tools receive printed prompts and skill files rather than written ones.

## Requirements

None at run time beyond Claude. The tooling (`scripts/`, `tests/`) needs Python 3.11 or newer; PyYAML is optional. The optional `--skillspector` flag of `check_skill.py` needs NVIDIA SkillSpector installed separately.

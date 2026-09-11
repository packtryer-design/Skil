# Contributing

Contributions from people and coding agents are welcome. Keep changes understandable, reviewable, safe to run, and compatible with existing users.

## Provenance

Say in the pull request whether the change is human-authored, agent-authored, or hybrid. For agent-authored or hybrid work, name the tool and model, what it did, what a person reviewed, and any check that failed. The submitting person is accountable for the whole diff.

## Scope

One focused change per pull request. No drive-by formatting, unrelated dependency changes, or broad rewrites that hide behavior changes. Discuss large behavior changes, new integrations, and new hooks in an issue first.

The pull request description states what changed and why, the observable behavior before and after, safety and compatibility considerations, and the exact verification performed.

## Safety

Changes must not weaken safeguards, override higher-priority instructions, conceal risky behavior, or encourage inaccurate claims. Nothing in the skill, templates, examples, or tests may instruct an agent to read or transmit credentials, environment variables, private files, or repository data; modify shell profiles, global configuration, or unrelated agent configuration; bypass confirmation for destructive, privileged, production, or externally visible actions; install software silently, fetch and execute remote code, or create persistence.

Scripts and tests validate inputs, use temporary directories, make no network calls (the harness's model backends excepted, and those require explicit flags), and never write outside the repository or a documented temporary directory. Live evaluation runs need an explicit budget and must record the model, cases, and results.

## Where things live

`skills/prompt-architect/SKILL.md` is the source of truth; references add depth; templates are validated and indexed by `check_templates.py`; the output format is shared with `pa_lib.py` and the harness. See `AGENTS.md` for the full map and the verification commands.

## Versioning

Templates carry their own semantic versions and changelogs. The plugin version in `.claude-plugin/plugin.json` is bumped for any change that users should receive as an update.

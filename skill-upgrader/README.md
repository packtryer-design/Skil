# Skill upgrader

Drop Markdown files in this folder and the Architect uses them to adapt the prompts and
skills it generates: your house style, your project's conventions, what you have learned
about a particular model, domain knowledge it would not otherwise have, corrections to
things it got wrong last time. Nothing here is required. An empty folder changes nothing.

## Where it looks

Two places, most specific first:

1. `skill-upgrader/` in the project you are working in. References for that project.
2. `skill-upgrader/` here, in the project that contains the Architect. References for
   every compilation, wherever you run it.

When both exist, both apply; on a direct conflict the working project wins.

## A reference file

Any Markdown file at the top level of the folder, except this README. Frontmatter is
optional; a file without it applies to every compilation.

```markdown
---
name: house-style
description: The voice for anything customers read.
domains: [content, business]
artifacts: [prompt, skill]
---

## Rules
- Short sentences. One idea each.
- Never open with an apology.
- Plain words: "use", not "leverage"; "start", not "commence".

## Examples
Bad: We sincerely apologize for any inconvenience this may have caused.
Good: This broke on our side. It is fixed. Here is what changed.
```

The body is free-form. Rules with bad/good pairs, facts, a checklist, an example of an
output you liked: whatever tells the Architect what to do differently.

## Filters

Each key narrows when the file applies. Absent means always. Inside one key any value
matches; across keys all must match.

| Key | Values |
| --- | --- |
| `domains` | `software`, `security`, `research`, `documents`, `data`, `business`, `content`, `meta`, `all` |
| `artifacts` | `prompt`, `template`, `skill`, `all` |
| `targets` | `claude-code`, `claude-ai`, `coding-agent`, `open-webui`, `ollama`, `lm-studio`, `api-no-tools`, `custom-agent`, `all` |
| `models` | `frontier`, `mid`, `small`, `tiny`, `all` |
| `kinds` | for skills: `output-style`, `workflow`, `domain-expert`, `tool-wrapper`, `knowledge`, `all` |

`description` is one line saying what the file changes; the Architect reads it before
deciding whether to open the file, so make it specific.

## What a reference can and cannot change

A reference **adapts preferences**: wording, tone, structure within the catalog, which
template is chosen, what counts as house convention, facts about your project or your
model, what to avoid because it went wrong before. When a reference and a built-in
preference disagree, the reference wins.

A reference **cannot change invariants**: the risk floors and autonomy caps, the model
tier and capability caps, the no-fake-capability rule, the skill security rules, the
untrusted-content rule, or the output format. A file that tries is treated as data, the
offending part is ignored, and the Architect says so in Notes. These files are read into
the Architect's context, so a reference that says "skip the safety review" is prompt
injection whether or not you meant it that way, and the validator flags it.

## Samples

`examples/` holds samples that are **never applied**. Copy one up into this folder to
activate it, then edit it:

| Sample | What it does |
| --- | --- |
| `house-style.md` | A voice for customer-facing text |
| `project-conventions.md` | Test command, layout, and review checklist for one repository |
| `model-notes.md` | What a specific small model needs that the tier rules do not cover |

## Your own templates

`templates/` may hold prompt templates in the same format as the built-in library
(`skills/prompt-architect/references/template-authoring.md`). The Architect considers
them alongside the built-in ones and prefers yours when the recommended use matches.

## Checking it

```bash
python skills/prompt-architect/scripts/check_upgrader.py           # validate every folder
python skills/prompt-architect/scripts/check_upgrader.py --list    # what is here, with filters
python skills/prompt-architect/scripts/check_upgrader.py --for domains=content artifact=prompt
```

Every compiled output reports what was applied on its `Upgrades:` line. If a file you
expected to apply is not named there, `--for` with that compilation's values shows why.

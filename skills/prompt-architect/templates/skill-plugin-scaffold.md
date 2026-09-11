---
name: skill-plugin-scaffold
version: 1.0.0
status: tested
category: skill
purpose: The files that turn a skill directory into a distributable Claude Code plugin (tier 2), with optional multi-runtime adapters (tier 3).
complexity: 3
recommended_use: When the user wants to share, publish, version, or install a skill through a marketplace, or asks for "a plugin like i-have-adhd". Combine with one skill-kind template for the SKILL.md itself.
autonomy_default: A2
risk_default: LOW
variables: [PLUGIN_NAME, VERSION, DESCRIPTION, AUTHOR, REPO_URL, CATEGORY, KEYWORDS, WHAT_IT_DOES, USAGE, EVAL_CASE, EVAL_PROMPT, EVAL_CRITERIA]
required_tools: [none]
changelog:
  - "1.0.0 - Initial version; layout follows the i-have-adhd repository (MIT)."
---

<!-- architect: Single-skill plugins use the same name for the plugin and the skill (skills/PLUGIN_NAME/SKILL.md), invoked as /PLUGIN_NAME:PLUGIN_NAME when installed as a plugin, or /PLUGIN_NAME when the directory is copied into ~/.claude/skills/. Generate three to five eval cases (repeat the evals block per case). Emit the tier 3 blocks only when the user asked for other runtimes. Keep the plugin free of CLAUDE.md at its root; it is not loaded as plugin context. -->

### {{PLUGIN_NAME}}/.claude-plugin/plugin.json
````json
{
  "$schema": "https://anthropic.com/claude-code/plugin.schema.json",
  "name": "{{PLUGIN_NAME}}",
  "version": "{{VERSION}}",
  "description": "{{DESCRIPTION}}",
  "author": {
    "name": "{{AUTHOR}}"
  },
  "homepage": "{{REPO_URL}}",
  "repository": "{{REPO_URL}}",
  "license": "MIT",
  "keywords": {{KEYWORDS}}
}
````

### {{PLUGIN_NAME}}/.claude-plugin/marketplace.json
````json
{
  "$schema": "https://www.schemastore.org/claude-code-marketplace.json",
  "name": "{{PLUGIN_NAME}}",
  "description": "{{DESCRIPTION}}",
  "owner": {
    "name": "{{AUTHOR}}"
  },
  "plugins": [
    {
      "name": "{{PLUGIN_NAME}}",
      "description": "{{DESCRIPTION}}",
      "source": "./",
      "category": "{{CATEGORY}}"
    }
  ]
}
````

### {{PLUGIN_NAME}}/README.md
````markdown
# {{PLUGIN_NAME}}

{{WHAT_IT_DOES}}

## Install

```bash
claude plugin marketplace add <owner>/{{PLUGIN_NAME}}
claude plugin install {{PLUGIN_NAME}}@{{PLUGIN_NAME}}
```

Or copy this directory to `~/.claude/skills/{{PLUGIN_NAME}}/`; it loads on the next session. Full instructions in [INSTALL.md](INSTALL.md).

## Use

{{USAGE}}

## Tune it

Fork, edit `skills/{{PLUGIN_NAME}}/SKILL.md`, and install your copy. Run `claude plugin validate .` before sharing.

## License

MIT.
````

### {{PLUGIN_NAME}}/INSTALL.md
````markdown
# Install

## Claude Code (plugin)

```bash
claude plugin marketplace add <owner>/{{PLUGIN_NAME}}
claude plugin install {{PLUGIN_NAME}}@{{PLUGIN_NAME}}
```

Invoke with `/{{PLUGIN_NAME}}:{{PLUGIN_NAME}}`. Verify with `claude plugin list`. Update with `claude plugin marketplace update {{PLUGIN_NAME}}`. Uninstall with `claude plugin uninstall {{PLUGIN_NAME}}`.

## Claude Code (skills directory)

Clone or copy this directory to `~/.claude/skills/{{PLUGIN_NAME}}/` (personal) or `.claude/skills/{{PLUGIN_NAME}}/` (one project). It loads on the next session as `{{PLUGIN_NAME}}@skills-dir`; invoke with `/{{PLUGIN_NAME}}`. Remove by deleting the directory.

## Development

```bash
claude --plugin-dir ./{{PLUGIN_NAME}}      # load for one session without installing
claude plugin validate ./{{PLUGIN_NAME}}   # check the manifests and skills
```

## claude.ai

Zip `skills/{{PLUGIN_NAME}}/` and upload it as a skill in claude.ai settings.
````

### {{PLUGIN_NAME}}/AGENTS.md
````markdown
# Agent guide

Map of this repository for agents. The canonical behavior is `skills/{{PLUGIN_NAME}}/SKILL.md`; everything else derives from it.

| Area | Location | Purpose |
| --- | --- | --- |
| Canonical skill | `skills/{{PLUGIN_NAME}}/SKILL.md` | Source of truth for the behavior |
| Plugin metadata | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Manifest and marketplace entry; keep versions aligned |
| Documentation | `README.md`, `INSTALL.md`, `CHANGELOG.md` | User-facing behavior and installation |
| Evaluation | `evals/` | Cases and criteria for `claude plugin eval` |

Rules: change the canonical skill first, then synchronize any mirror; keep installation claims accurate; run `claude plugin validate .` and the evals before proposing a change; do not read or modify files outside this repository.
````

### {{PLUGIN_NAME}}/CHANGELOG.md
````markdown
# Changelog

## {{VERSION}}

- Initial release.
````

### {{PLUGIN_NAME}}/evals/{{EVAL_CASE}}/prompt.md
````markdown
{{EVAL_PROMPT}}
````

### {{PLUGIN_NAME}}/evals/{{EVAL_CASE}}/graders/criteria.md
````markdown
{{EVAL_CRITERIA}}
````

<!-- architect: Tier 3 blocks below are optional. Include only the runtimes the user named. -->

### {{PLUGIN_NAME}}/.cursor/skills/{{PLUGIN_NAME}}/SKILL.md
````markdown
(byte-identical copy of skills/{{PLUGIN_NAME}}/SKILL.md; keep in sync)
````

### {{PLUGIN_NAME}}/.codex-plugin/plugin.json
````json
{
  "name": "{{PLUGIN_NAME}}",
  "version": "{{VERSION}}",
  "description": "{{DESCRIPTION}}",
  "license": "MIT",
  "skills": "./skills/"
}
````

### {{PLUGIN_NAME}}/skills/{{PLUGIN_NAME}}/agents/openai.yaml
````yaml
interface:
  display_name: "{{PLUGIN_NAME}}"
  short_description: "{{DESCRIPTION}}"
policy:
  allow_implicit_invocation: false
````

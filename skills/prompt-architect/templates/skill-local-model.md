---
name: skill-local-model
version: 1.0.0
status: candidate
category: skill
purpose: The derived files that let a skill run on a local model runtime - a self-contained system prompt, an Ollama Modelfile, and per-runtime load instructions.
complexity: 2
recommended_use: When the skill will run on a local or small model (Ollama, LM Studio, llama.cpp, vLLM) or the user names a model under about 30B. Combine with one skill-kind template, which supplies the canonical SKILL.md.
autonomy_default: A2
risk_default: LOW
model_tiers: [small, tiny]
variables: [SKILL_NAME, PURPOSE, RULES, OUTPUT, EXAMPLES, BASE_MODEL, TEMPERATURE, NUM_CTX]
required_tools: [none]
changelog:
  - "1.0.0 - Initial version."
---

<!-- architect: SKILL.md stays canonical and comes from the matching skill-kind template, so the skill still works in Claude Code; these files are derived from its body. Nothing here may depend on Claude Code: no ${CLAUDE_SKILL_DIR}, no references/ pointers, no $ARGUMENTS, no allowed-tools, no progressive disclosure. A local runtime has no permission system either, so a rule the skill must not break has to be enforced by not giving the model the capability, never by prose. Write RULES, OUTPUT, and EXAMPLES at the model's tier per references/model-tiers.md: short imperative sentences, MUST and MUST NOT only, a literal output template, worked examples. system.md and the Modelfile hold the same text; regenerate both whenever SKILL.md changes. -->

### {{SKILL_NAME}}/system.md
````markdown
{{PURPOSE}}

## Rules

{{RULES}}

## Output

{{OUTPUT}}

## Examples

{{EXAMPLES}}
````

### {{SKILL_NAME}}/Modelfile
````text
FROM {{BASE_MODEL}}

PARAMETER temperature {{TEMPERATURE}}
PARAMETER num_ctx {{NUM_CTX}}

SYSTEM """
{{PURPOSE}}

Rules:
{{RULES}}

Output:
{{OUTPUT}}

Examples:
{{EXAMPLES}}
"""
````

### {{SKILL_NAME}}/README.md
````markdown
# {{SKILL_NAME}}

{{PURPOSE}}

Runs on a local model. `SKILL.md` is the canonical version and works in Claude Code; `system.md` is the same behavior as a self-contained system prompt, with nothing that depends on a Claude Code host.

## Ollama

```bash
ollama create {{SKILL_NAME}} -f Modelfile
ollama run {{SKILL_NAME}}
```

## LM Studio

Paste the contents of `system.md` into the system prompt field for the loaded model.

## llama.cpp and vLLM

Pass `system.md` as the system prompt file (`--system-prompt-file system.md`), or send it as the `system` message of an OpenAI-compatible request.

## Claude Code

Copy this directory to `~/.claude/skills/{{SKILL_NAME}}/` (personal) or `.claude/skills/{{SKILL_NAME}}/` (one project). It loads on the next session.

## Keeping the copies in sync

`SKILL.md` is the source of truth. `system.md` and the `SYSTEM` block in `Modelfile` are derived from its body; change `SKILL.md` first, then regenerate both. After an Ollama model already exists, re-run `ollama create` to pick up a changed `Modelfile`.

## Sizing

Built for `{{BASE_MODEL}}` at `num_ctx {{NUM_CTX}}`. A smaller context window truncates the examples first, which is what makes the output drift: shorten the rules before shortening the examples.
````

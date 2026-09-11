---
name: model-notes
description: What Qwen 2.5 3B and similar small local models need beyond the tier rules, learned from running them.
models: [small, tiny]
targets: [ollama, lm-studio, open-webui]
---

## Facts

- Qwen 2.5 3B follows a JSON output template reliably when the template appears twice: once as the rule and once inside a worked example. Once is not enough.
- At Q4 quantization it starts ignoring the system prompt above roughly 1,500 tokens of context. Keep the whole prompt under that.
- It treats "Do not X" as a suggestion and "Output only Y" as a rule. Prefer the second form.

## Rules

- End every prompt with the input slot and the first key of the output template, so the model's next token is the answer.
- Set `temperature 0.1` in the Modelfile for classification and extraction; the default drifts.
- Put the closed value list in the output template itself, not only in the rules.

# Template Authoring

How to create, specialize, and maintain base prompts in `templates/`. Base prompts are treated like software: named, versioned, categorized, tested, and changed through a changelog.

## When to create a template

Create one when a task type recurs and composing from the section catalog each time would reproduce the same workflow, safety rules, and output contract. Do not create one for a one-off task, and do not force a task into an existing template when that lowers quality.

Process:

```
Identify the recurring task type
-> Determine the behavior Claude needs (mode, autonomy, evidence standards)
-> Identify domain-specific risks
-> Design the workflow
-> Define the output contract
-> Define validation and completion criteria
-> Write the template
-> Review it with references/review.md
-> Register it as a candidate (status: candidate) and add test cases
```

## File format

One file per template: `templates/<name>.md`, where `<name>` is lowercase kebab-case and matches the `name` field.

Frontmatter (YAML, flat keys, inline or block lists):

| Key | Required | Values |
| --- | --- | --- |
| `name` | yes | Matches the file name without extension |
| `version` | yes | Semantic version `MAJOR.MINOR.PATCH` |
| `status` | yes | `candidate` (new, untested), `draft` (in use, not yet verified by tests), `tested` (passes its test cases), `stable` (tested and unchanged across several releases) |
| `category` | yes | `software`, `security`, `research`, `documents`, `business`, `data`, `content`, `meta`, `skill` (a SKILL.md scaffold rather than a prompt), `local` (defined by the runtime and model tier rather than a domain) |
| `purpose` | yes | One sentence |
| `complexity` | yes | Default level 1-4 |
| `recommended_use` | yes | When to pick this template, one or two sentences |
| `autonomy_default` | yes | `A0`-`A4` |
| `risk_default` | yes | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `variables` | yes | List of slot names used in the body, without braces |
| `required_tools` | yes | List; use `none` when the template works without tools |
| `model_tiers` | no | List of model tiers the body is written for (`frontier`, `mid`, `small`, `tiny`). Absent means `frontier`, which is what the library targets before compile-time adaptation. The body is linted at the least restrictive tier declared. |
| `changelog` | yes | List of `"<version> - <change>"` strings, newest last |

Body conventions:

- Sections use the catalog headings from `references/sections.md`, in catalog order.
- Slots use `{{NAME}}`; every slot appears in `variables` and every variable appears in the body.
- Guidance for the Architect goes in HTML comments starting with `<!-- architect:` and is removed when the template is specialized. Keep these comments short and actionable ("remove this section for read-only hosts").
- Everything not in a slot or a comment is real prompt text that should survive into most specialized prompts.
- Keep templates between roughly 50 and 120 lines. Longer templates are a sign of generic content that should be pruned.

Skeleton:

```markdown
---
name: example-agent
version: 1.0.0
status: candidate
category: software
purpose: One sentence.
complexity: 3
recommended_use: When to use it.
autonomy_default: A3
risk_default: MEDIUM
variables: [OBJECTIVE, CONTEXT, REQUIREMENTS, CONSTRAINTS, RESOURCES]
required_tools: [file read, file edit, shell]
changelog:
  - "1.0.0 - Initial version."
---

<!-- architect: How to specialize this template in one or two sentences. -->

## Objective
{{OBJECTIVE}}

## Context
{{CONTEXT}}

## Requirements
{{REQUIREMENTS}}
<!-- architect: MUST / SHOULD / MAY / MUST NOT. Always include a scope-bounding MUST NOT. -->

...
```

## Specializing a template at compile time

1. Fill every slot with concrete content from the request. If a slot has nothing to fill, remove the section (or the line) rather than leaving the placeholder.
2. Prune sections and rules that do not apply to this task or this host. A rule about running tests is removed when the host cannot run tests, and replaced with "list the tests the user should run".
3. Add task-specific requirements, decision rules, and checkpoints. The template supplies the skeleton; the request supplies the specifics.
4. Keep the safety rules whenever the risk level warrants them; strengthen them for HIGH and CRITICAL.
5. Remove all `<!-- architect: -->` comments.
6. Run the review stage on the result as if it were composed from scratch.

The output must read as a prompt written for this task, not as a filled form.

## Versioning

- PATCH: wording fixes that do not change behavior.
- MINOR: added or changed rules, sections, or workflow steps that keep the template's purpose.
- MAJOR: changed purpose, output contract, or autonomy default.
- Every change adds a changelog line and, when behavior changes, updates or adds a test case in `tests/cases/`.
- Status moves `candidate -> draft -> tested -> stable` as test coverage and usage accumulate; a MAJOR change resets status to `draft`.

## Registering

Run `python scripts/check_templates.py --write-index` to validate frontmatter and regenerate `templates/INDEX.md`. The check fails when a variable is declared but unused, used but undeclared, a required key is missing, or the file name and `name` differ.

## Quality bar

Before a template leaves `candidate`:

- The workflow is specific to the task type and orders inspection before change and verification after.
- Safety boundaries match the domain's real risks, not a generic block.
- The output contract matches what users of this task type actually need.
- Completion criteria are checkable.
- Failure handling covers the blocked states this task type actually hits.
- Every instruction affects task success; nothing is decorative.
- At least one test case in `tests/cases/` expects this template.

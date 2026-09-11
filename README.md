# Prompt Architect

Connect this folder to a capable agent and it becomes a compiler: describe what you need in
plain language, and it returns the **prompt**, or the installable **skill**, most likely to
make a model complete that task correctly - classified, reviewed, and validated.

It is a project, not a plugin. A Claude Code plugin is one of four ways to load it, and the
agent reading the folder is the point:

| Load it by | How |
| --- | --- |
| Pointing any agent at the folder | It reads [AGENTS.md](AGENTS.md), then `skills/prompt-architect/SKILL.md` |
| Claude Code plugin | `claude plugin install` - see [Install](#install) |
| Plain skill directory | Clone into `~/.claude/skills/prompt-architect` |
| A single file, no filesystem needed | Paste [dist/prompt-architect.portable.md](dist/prompt-architect.portable.md) as a system prompt |

It behaves like a compiler with quality control rather than a prompt rewriter:

```text
request -> understand -> choose the artifact (prompt | template | skill)
        -> classify (domain, risk, mode, autonomy, runtime, model tier)
        -> discover what the runtime can actually do -> analyze the gaps
        -> extract requirements and assumptions -> ask only if it matters
        -> select a template (prompt templates by domain, skill templates by kind)
        -> apply your own references from skill-upgrader/
        -> compose -> critique -> adversarial review -> optimize -> validate
        -> prompt, or skill files written to disk
```

Two things it will not do: assume a capability the target does not have, or write for a
frontier model when a 3B one is going to run the result.

The specification is [plan.md](plan.md) plus [references/planextention.md](references/planextention.md), which adds capability awareness. The packaging follows [i-have-adhd](https://github.com/ayghri/i-have-adhd); the skill safety rules follow [NVIDIA SkillSpector](https://github.com/NVIDIA/SkillSpector); several business templates are adapted from [ai-business-skills](https://github.com/minhnv0807/ai-business-skills). See [references/README.md](references/README.md) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Install

Claude Code, as a plugin:

```bash
claude plugin marketplace add packtryer-design/Skil
claude plugin install prompt-architect@prompt-architect
```

Claude Code, as a skills-directory plugin (no marketplace):

```bash
git clone https://github.com/packtryer-design/Skil ~/.claude/skills/prompt-architect
```

For one session without installing: `claude --plugin-dir /path/to/Skil`. For claude.ai: zip `skills/prompt-architect/` and upload it as a skill.

Any other agent needs no install step: point it at the folder and it reads [AGENTS.md](AGENTS.md) (Cursor and Copilot also pick up the entry points under `.cursor/` and `.github/`); an agent that cannot read files gets [dist/prompt-architect.portable.md](dist/prompt-architect.portable.md) as its system prompt. Details for every path are in [INSTALL.md](INSTALL.md).

## Use

```text
/prompt-architect I need Claude to add Cognito OIDC authentication to my existing Next.js app without breaking the current login system.
/prompt-architect Make me a skill so my manager updates come out as executive briefs: decision first, three bullets max, then the ask.
/prompt-architect Review this prompt: "You are a world-class engineer. Help the user with their code. Be thorough."
/prompt-architect Is this skill safe to install? ./downloaded-skill
/prompt-architect I run Qwen 2.5 7B in Open WebUI. Make me a skill that answers our support macros in the house voice.
/prompt-architect Upgrade ./skills/release-notes to follow the conventions in my skill-upgrader folder.
```

When installed as a plugin the command is namespaced (`/prompt-architect:prompt-architect`); as a skills-directory plugin or a plain skill it is `/prompt-architect`.

### What comes back

```text
## Compilation Summary
- Objective: ...            one-sentence normalized objective
- Artifact: ...             prompt | template | skill (<kind>, tier <1-3>)
- Domain: ...               software, security, research, documents, data, business, content, meta
- Risk: ...                 LOW | MEDIUM | HIGH | CRITICAL
- Mode: ...                 ANALYST -> ARCHITECT -> ENGINEER -> REVIEWER (or a single mode)
- Autonomy: ...             A0 explain, A1 recommend, A2 produce, A3 execute with checkpoints, A4 autonomous within boundaries
- Level: ...                1 Quick, 2 Standard, 3 Advanced, 4 Expert
- Target: ...               the named runtime the artifact will run in
- Capabilities: ...         what that runtime can actually do, or "none required"
- Gaps: ...                 a required capability that is missing, and what was done about it
- Model: ...                frontier | mid | small | tiny - the capability of the model that will run it
- Template: ...             template used, with version
- Upgrades: ...             which of your skill-upgrader references were applied, or none
- Assumptions: ...          high-impact inferred or unknown items
- Review: ...               what the self-review changed (Level 3 and 4)
- Questions: ...            none, or the questions below

## Prompt                   (prompts) the compiled prompt in a four-backtick fence
## Skill                    (skills)  "Written to: <dir>" then each file as "### <path>" plus a fence
## Notes                    what to supply, conflicts resolved, how to try or install
```

Behavior worth knowing:

- **Questions are rare.** The Architect asks only about intent that changes the artifact materially and that no inspection can reveal, at most three questions with defaults, and it stops there. Execution details (which library, how to treat edge cases, thresholds) become safe defaults plus checkpoints inside the artifact. Research and review requests are compiled with the most likely reading stated, not asked.
- **Complexity follows the task.** "Explain OAuth" gets a ten-line prompt; a production authentication change gets checkpoints, testing, safety boundaries, failure handling, and completion criteria.
- **Autonomy is separate from role**, and the prompt states what Claude may do alone and the exact triggers that require confirmation.
- **Prompts are sized to the model that will run them.** Name a 3B local model, Ollama, a Raspberry Pi, or Haiku-for-cost, and the artifact changes shape: fewer rules and sections, short imperative sentences, MUST and MUST NOT only, a literal output template, and worked examples that carry the specification. Say nothing about the model and you get the frontier
  default, unchanged.
- **Skills are written to disk** in Claude Code (`.claude/skills/<name>/` by default, a new `<plugin>/` directory for shareable plugins) and validated with the bundled checker before they are returned.
- **Reviews.** Paste a prompt for a scored review with an optimized version; point at a skill for a security review with an APPROVE, CAUTION, or REJECT verdict.

## How to ask

Every line of that summary is a decision. The ones you state are the ones the Architect does not have to guess.

It deliberately asks very little: at most three questions, only about intent that no amount of inspection could reveal, and then it stops. Everything else becomes a stated assumption rather than a question. That keeps it out of your way, but it means what you put in the request is what drives the result.

One sentence is a perfectly good request. `Write me a prompt that reviews SQL for performance problems` compiles cleanly. The list below is what to add when you care about the answer.

### The eight things that change the result

| Say this | Why it changes the result | If you leave it out |
| --- | --- | --- |
| **The goal, and what done looks like** | Separates "explain this to me" from "hand me something I can run" | Inferred from your verbs, which is usually right and occasionally not |
| **Prompt, skill, or template** | A skill is installed and fires again and again; a prompt is one job. Say "skill", "slash command", "every time I…", "make Claude always…" | Prompt, unless the request sounds repeatable. It offers the skill in Notes |
| **Where it will run** | A runtime with no shell cannot run your tests. This is what decides which instructions are even legal | The current environment if it is compiling for here; otherwise a named profile with its documented defaults |
| **Which model will run it** | A 3B local model needs worked examples, a literal output template, and six sections; a frontier model does not | `frontier`, recorded as an assumption |
| **What it may touch, and what it must not** | Becomes the MUST NOT list and the checkpoints. The single highest-value thing to state | A scope boundary is inferred from the task, which is the weakest kind |
| **How far it may act alone** | Recommend, produce an artifact, or execute with checkpoints | From the task shape: repository changes default to executing with checkpoints |
| **What material it gets** | Repository, pasted files, uploads, nothing. Determines whether it inspects or asks | Inspected when reachable; otherwise the prompt leaves a marked slot for you to paste into |
| **Who reads the output, in what shape** | A person skimming, a teammate reviewing, or a program parsing are three different contracts | A sensible shape for the task, which may not be your shape |

Anything that makes failure expensive is worth one clause: production, authentication, payments, customer data, anything irreversible. That raises the risk level, which adds checkpoints, validation, and a rollback path.

### What you do not need to say

As useful as the list above, because volunteering these wastes your time:

- **Your stack, file layout, schema, dependencies, or test setup.** If the material is reachable, it inspects rather than asks. Telling it the framework when it can read `package.json` adds nothing.
- **Execution details** - hard delete or soft delete, which threshold, which library. These become safe reversible defaults, recorded under Assumptions and placed at a checkpoint where you can override them. It will not ask you about them, by design.
- **How to write the prompt.** Section lists, tone, length, "be detailed": the compiler decides structure from the task, and asking for detail usually produces padding.

### A skeleton, if you want one

Optional. Blanks become stated assumptions, not questions.

```text
Goal:       what it should accomplish, and what counts as done
Artifact:   prompt | skill | template          (omit to let it choose)
Runs in:    Claude Code | Open WebUI | Ollama | an API | a chat window
Model:      the model that will run it, if it is not a frontier one
May touch:  paths, files, systems
Must not:   the boundary that actually matters
Material:   what you will supply, or where it should look
Output:     who reads it and in what shape
```

### What the extra sentence buys you

Two real examples from [examples/](skills/prompt-architect/examples/).

**Naming the runtime.** "Help me keep my repo healthy — find failing tests and error-handling problems and fix them" compiles for the environment it is running in: execute with checkpoints, run the suite, edit the files. Add *"I'm running Qwen 2.5 7B locally through Open WebUI"* and [the same request](skills/prompt-architect/examples/gap-local-openwebui.md) compiles into a different artifact:

```text
- Autonomy: A1 (diagnose and recommend; the user runs and applies everything)
- Capabilities: files.read=yes, files.write=no, shell=no, code.run=no, web.search=no (open-webui profile, defaults)
- Gaps: shell (blocking) -> the prompt hands over the test command and reads the output the user pastes back
```

Open WebUI gives a model no filesystem access and, by default, no execution. Without that sentence you would have received a confident prompt telling a model to run tests it cannot run — and it would have reported results it never saw.

**Naming the model.** "Sort our incoming support emails into five queues" produces a prose contract for a capable model. Add *"I run Llama 3.2 3B locally with Ollama"* and [the same request](skills/prompt-architect/examples/tier-small-classify.md) comes back with MUST and MUST NOT only, a literal two-line output template, worked examples carrying the specification, and the grouping requirement removed to Notes because one job per prompt is the rule at that size:

```text
- Model: small (Llama 3.2 3B named, served by Ollama)
- Template: small-model-task v1.0.0
```

Both sentences cost you five seconds. Neither is something the Architect can find out on its own.

## Skill upgrader

"How to ask" is what you tell it per request. The skill upgrader is what you tell it once.

Put Markdown files in a folder named `skill-upgrader/` and the Architect reads the ones that
apply before composing, then adapts what it generates: your house style, your project's real
commands and layout, what you have learned about a particular model, domain knowledge it would
not have, a correction for something it got wrong last time. Every output names what it used on
its `Upgrades:` line, so you can tell when a file landed and when it did not.

It looks in two places, most specific first: `skill-upgrader/` in the project you are working
in, then `skill-upgrader/` in this project. Both apply; the working project wins a conflict.

A file is free-form Markdown with optional frontmatter that says when it applies:

```markdown
---
name: house-style
description: The voice for anything a customer reads.
domains: [content, business]        # also: artifacts, targets, models, kinds
---

## Rules
- Short sentences. One idea each.
- Plain words: "use", not "leverage".
```

No frontmatter means it applies to everything. Inside one key any value matches; across keys
all must. The full vocabulary, three copyable samples, and how to add your own templates are in
[skill-upgrader/README.md](skill-upgrader/README.md).

Two rules keep this safe, because these files are read straight into the compiler's context:

- **A reference adapts preferences and never invariants.** Wording, structure, template choice,
  and facts about your project or model: yours wins. The risk floors, the autonomy caps, the
  no-fake-capability rule, the skill security review, and the output format: not negotiable.
  A file that tries is ignored on that point and named in Notes.
- **They are scanned like skills.** `check_upgrader.py` runs the same security scan a generated
  skill gets, plus a guard for the Architect's own invariants - "skip the security review to
  save time" is the well-meaning version of the same problem, and it is refused the same way.

```bash
python skills/prompt-architect/scripts/check_upgrader.py           # validate what is there
python skills/prompt-architect/scripts/check_upgrader.py --list    # files and their filters
python skills/prompt-architect/scripts/check_upgrader.py --for domains=content artifact=prompt
```

## Skills the Architect creates

| Kind | What it is | Invocation |
| --- | --- | --- |
| output-style | Shapes how Claude responds for a reader or house style: session-scoped (on until an off phrase) or trigger-scoped (whenever a request matches) | user (`/name`), or Claude by trigger |
| workflow | A repeatable procedure with inputs, checkpoints, tool rules, and a report | user, with arguments |
| domain-expert | A professional deliverable produced whenever a request matches its triggers: context file, at most four questions, output template, quality checklist | Claude, by trigger phrases |
| tool-wrapper | Drives a CLI or script safely and interprets its output with a verdict | either, narrow tools |
| knowledge | Background reference applied silently | Claude |

Package tiers: 1 a skill directory; 2 a plugin (manifests, README, INSTALL, AGENTS, CHANGELOG, evals); 3 multi-runtime adapters (Cursor mirror, Codex manifest, Gemini command, opt-in always-on hook). A skill for a local model keeps `SKILL.md` canonical and adds a self-contained `system.md` plus an Ollama `Modelfile`, with nothing that depends on a Claude Code host.

Every generated skill follows the Agent Skills specification, declares the capabilities it needs (`capabilities-required`, `-recommended`, `-optional` in `metadata`) so a different runtime can check compatibility, and must pass `check_skill.py` with zero errors: no prompt injection or hidden text, no anti-refusal wording, no credential access or exfiltration, no unpinned or piped installs, no persistence outside the session, no destructive commands without confirmation, no trigger abuse, and a `system.md` that stands on its own.

Existing skills get the same treatment in reverse: paste one for a security review with an APPROVE, CAUTION, or REJECT verdict, or ask for it to be upgraded to your conventions and the Architect applies your [skill-upgrader](#skill-upgrader) references and returns the complete updated files.

## Model tiers

The Architect classifies the model that will *execute* the artifact, separately from the host, and writes for it. The governing principle is that a weaker model gets **fewer** rules, sections, and tools plus worked examples and a literal output template, not a longer prompt: small models have short effective context and lose track of instructions stated far above.

| Tier | Capability | Illustrative models | Autonomy cap | Sections | Examples |
| --- | --- | --- | --- | --- | --- |
| `frontier` | Nuanced instructions, inferred intent, planned tool use | Opus/Sonnet 5, GPT-5 class, Gemini Pro class | A4 | full catalog | when unusual |
| `mid` | Explicit structure followed reliably | Haiku 4.5, Llama 3.3 70B, Qwen 2.5 32B, mini and flash tiers | A3 | 10 | when non-obvious |
| `small` | Short explicit rules, one job at a time | Llama 3.2 3B, Qwen 2.5 3B-7B, Phi-4-mini, Gemma 2 9B | A2 | 6 | required |
| `tiny` | Pattern completion; the examples are the specification | Llama 3.2 1B, Qwen 2.5 0.5-1.5B, quantized 3B | A1 | 3 | required |

Detected from parameter counts, model names, runtimes (Ollama, LM Studio, llama.cpp, vLLM), quantization, offline or single-board hardware, and cost cues. The default is `frontier`; the Architect asks about the tier in exactly one case, when you mention a local model without a size and the work is A2 or above. At `small` and `tiny` a forbidden operation has to be made impossible rather than prohibited, since a model at those tiers does not reliably police itself, and HIGH or CRITICAL risk caps autonomy at A1 with a human verification step.

A skill compiled for a local model keeps `SKILL.md` canonical so it still works in Claude Code, and adds a self-contained `system.md` plus an Ollama `Modelfile`. See [tier-small-classify.md](skills/prompt-architect/examples/tier-small-classify.md) for a worked small-tier prompt.

## What the runtime can do

Model tier is half the picture. The other half is what the environment actually provides, and
the two are independent: Claude Code can be running Haiku, and an API pipeline can be running
Opus. Before composing, the Architect settles fifteen capabilities - `files.read`,
`files.write`, `shell`, `code.run`, `web.search`, `web.fetch`, `browser`, `db`, `git`,
`vision`, `audio`, `image.gen`, `structured.output`, `mcp`, `network` - as `yes`, `no`, or
`unknown`, from the strongest evidence available: inspection, then what you told it, then a
saved profile, then the built-in profile for the named runtime, then documentation, then
`unknown`.

| Runtime | Out of the box |
| --- | --- |
| `claude-code`, `coding-agent` | Files, shell, execution, version control |
| `claude-ai` | Reads attachments, writes nothing to your machine |
| `open-webui` | **No filesystem and no execution.** Uploads become context; code execution and web search are opt-in |
| `ollama`, `lm-studio` | Serves the model and provides no tools. Tool calling is a protocol your program must implement |
| `api-no-tools` | Nothing, and no human in the loop |
| `custom-agent` | Unknown until you say |

Defaults only; every one of these is configurable, and a declaration or an inspection beats
the table. Full profiles in
[runtime-profiles.md](skills/prompt-architect/references/runtime-profiles.md).

Three rules follow, and they are why this layer exists:

- **Nothing is faked.** No "run the tests" without execution, no "search the web" without web
  access, no "edit the file" without write access. A capability that is `unknown` is written
  conditionally; one that is `no` is replaced.
- **Capability caps autonomy**, alongside model tier, and the lower cap wins. Nothing to
  execute with means no acting autonomously, whatever the task asks for.
- **Gaps degrade rather than fail.** No shell becomes "here is the exact command, paste the
  output back". The `## Compatibility` section says what was lost and what would restore it.

It inspects only when the target is the environment it is running in. Compiling *for*
somewhere else, it uses the profile and what you told it - reporting your Claude Code
capabilities for a prompt destined for Open WebUI would be confidently wrong, which is worse
than admitting it does not know. [gap-local-openwebui.md](skills/prompt-architect/examples/gap-local-openwebui.md)
is a worked example of a blocking gap.

## Running it outside Claude Code

The skill assumes a Claude Code host: it opens references on demand, runs its scripts, and writes generated files to disk. `dist/` holds flattened builds that do none of that, for hosts that cannot read files:

```bash
python skills/prompt-architect/scripts/build_portable.py          # regenerate both
python skills/prompt-architect/scripts/build_portable.py --check  # fail if stale (CI does this)
```

| Build | Contents | For |
| --- | --- | --- |
| `dist/prompt-architect.portable.md` | The procedure plus every runtime reference | A frontier model anywhere: claude.ai, ChatGPT, Gemini, a raw API call |
| `dist/prompt-architect.compact.md` | The procedure plus classification, model tiers, requirements, and sections | A mid-tier model or a smaller context budget. Prompts and templates only; it declines skill requests rather than emitting a skill without the security checklist |

Paste one as the system prompt and send the request as the user message. Neither build carries the template library, so both compose from the section catalog and report `Template: none`. The build fails loudly if `SKILL.md` changes in a way that leaves an instruction to run a script the build does not ship.

There is deliberately no `small` or `tiny` build of the Architect itself. It is a multi-stage compiler, and a 3B model cannot run it; such a model is what the Architect compiles **for**, not what it runs **on**.

## Template library

[skills/prompt-architect/templates/INDEX.md](skills/prompt-architect/templates/INDEX.md) lists every template with version, status, defaults, and provenance.

| Category | Templates |
| --- | --- |
| software | repository-agent, codebase-analyst, debugging-agent, code-reviewer, architecture-agent |
| security | security-reviewer, threat-modeler, authentication-reviewer |
| research | research-agent, comparison-agent, fact-checker |
| documents | document-analyst, pdf-analyst, spreadsheet-analyst, multi-document-analyst |
| business | product-architect, requirements-analyst, strategy-analyst, marketing-plan, campaign-brief, competitor-research, customer-insight |
| content | ad-copy, content-calendar |
| data | data-analyst, sql-analyst, visualization-agent |
| meta | prompt-reviewer, prompt-optimizer |
| skill | skill-output-style, skill-workflow, skill-domain-expert, skill-tool-wrapper, skill-plugin-scaffold, skill-local-model |
| local | small-model-task (the flat shape for `small` and `tiny` model tiers) |

Thirty-six templates. Each carries frontmatter (name, version, status, category, purpose, complexity, recommended use, autonomy and risk defaults, variables, required tools, changelog, the model tiers it is written for, and source when adapted) and are validated and indexed by `check_templates.py`. Authoring rules are in [references/template-authoring.md](skills/prompt-architect/references/template-authoring.md).

## Tooling

All scripts live in `skills/prompt-architect/scripts/` so the skill can run them at run time; Python 3.11 or newer, standard library only.

```bash
S=skills/prompt-architect/scripts
python $S/validate_prompt.py output.md              # lint a saved prompt or skill output
python $S/validate_prompt.py output.md --profile-matrix   # would it still be honest on a weaker runtime?
python $S/check_skill.py <skill-dir> [--generated]   # Agent Skills conformance + security scan; --plugin for a whole plugin; --skillspector adds NVIDIA's scanner when installed
python $S/check_templates.py --write-index          # validate templates, regenerate INDEX.md (--check-index for CI)
python $S/check_upgrader.py                          # validate, list, or select skill-upgrader references (--for ...)
python $S/build_portable.py                          # regenerate dist/ single-file builds (--check for CI)
python tests/run_tests.py --list                     # evaluation harness (see below)
```

`check_skill.py` was calibrated on real skills: the i-have-adhd skill, SkillSpector's own inspector skill, and the marketing library pass with zero errors, while injected instructions, credential reads, piped installs, and hidden Unicode are caught. Documentation that must mention forbidden phrases can opt out per file with the marker described in [references/skill-security.md](skills/prompt-architect/references/skill-security.md).

## Evaluation

Prompt and skill quality is judged by results, not appearance.

- `tests/run_tests.py` runs the 40 cases in `tests/cases/*.toml` (simple, medium, complex, high-risk, ambiguous, underspecified, multi-domain, meta, skill, model-tier, capability, upgrader) through the skill and grades deterministically (summary values, sections, files, patterns, lint), optionally with a model judge (`--judge`) and end-to-end task execution (`--execute`). Backends: the local Claude Code CLI (default), the Anthropic API (`--backend api`), or pre-generated outputs (`--from-dir`). Reports land in `tests/results/<run>/`.
- Cases can carry `fixtures`, folders copied into the temporary project before the run; the `upgrader` cases use one to plant a `skill-upgrader/` folder, including a file the Architect must refuse.
- `tests/check_docs.py` verifies that every summary line the README quotes under "How to ask" exists verbatim in a worked example, so the documentation is checked by the same suite as the fixtures.
- `evals/` holds five cases in the native `claude plugin eval` layout (`prompt.md` plus `graders/criteria.md`), for when that command is available on your account.
- `.github/workflows/validate.yml` runs every offline check on each push: script compilation, template validation and index, the plugin and skill-upgrader scans (including a fixture that must be rejected), the portable-build currency check, the README quote check, and the lint plus offline grading of all eight examples.

```bash
python tests/run_tests.py --from-dir skills/prompt-architect/examples   # free, offline
python tests/run_tests.py --category skill --judge                      # live, through your Claude Code login
```

## Repository layout

```text
AGENTS.md                      how an agent loads this project (read this first); repo map for contributors
skills/prompt-architect/
  SKILL.md                     the compilation procedure, output format, and rules
  references/                  classification, model tiers, capabilities, runtime profiles, requirements,
                               sections, workflows, review, skill authoring, skill security, skill upgrader,
                               template authoring
  templates/                   36 templates: prompts by domain, skill-* scaffolds by kind, small-model-task; INDEX.md
  examples/                    8 worked outputs: prompts at each level, a clarification, a skill,
                               a small-tier prompt, a capability gap
  scripts/                     pa_lib.py, pa_skill.py, validate_prompt.py, check_skill.py,
                               check_templates.py, check_upgrader.py, build_portable.py
skill-upgrader/                your own references that adapt generated output (README.md, inert samples in examples/)
dist/                          portable single-file builds (generated by build_portable.py; do not edit)
tests/                         harness (run_tests.py), 40 cases, fixtures, check_docs.py
evals/                         five cases in the native claude plugin eval layout
.claude-plugin/                plugin.json, marketplace.json
.cursor/, .github/             entry points for Cursor and Copilot; the CI workflow
references/                    planextention.md (part of the spec) and third-party projects studied (ignored by git)
plan.md                        the specification; references/planextention.md extends it
CLAUDE.md, CONTRIBUTING.md, INSTALL.md, THIRD_PARTY_NOTICES.md, LICENSE
```

## License

MIT for this repository. Adapted material keeps its upstream license; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

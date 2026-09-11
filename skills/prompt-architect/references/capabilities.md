# Capability Reference

Used at Stage 2.5, and again at Stages 6 and 7. Answers one question: **what can the environment that will run this artifact actually do?**

This is separate from every other axis in the summary:

- `Model` is how capable the model is. `Capabilities` is what its runtime provides. A model that can write Python is not a runtime that can run it.
- `Target` names the runtime. `Capabilities` says what that runtime turned out to have, which varies with configuration even for one target.
- Both `Model` and `Capabilities` cap autonomy, and the effective cap is the lower of the two.

The failure this prevents is silent and expensive: a prompt that says "run the tests and verify" handed to a runtime with no execution produces a confident, fabricated report. The model does not announce that it could not comply. So:

> **Never write an instruction that assumes a capability the target does not have. When a capability is missing, degrade the workflow honestly; never pretend.**

## 1. Vocabulary

Fifteen names, fixed so they can be checked mechanically. Each is `yes`, `no`, or `unknown`.

| Capability | Means |
| --- | --- |
| `files.read` | Can read files the user points at |
| `files.write` | Can create or modify files |
| `shell` | Can run shell or terminal commands |
| `code.run` | Can execute code it writes (interpreter, sandbox, code interpreter) |
| `web.search` | Can search the web |
| `web.fetch` | Can retrieve a named URL |
| `browser` | Can drive a browser (navigate, click, fill) |
| `db` | Can query a database |
| `git` | Can run version-control operations |
| `vision` | Can interpret images supplied to it |
| `audio` | Can take audio in or produce audio out |
| `image.gen` | Can generate images |
| `structured.output` | Can be constrained to a schema (JSON mode, grammars, tool schemas) |
| `mcp` | Has MCP servers connected |
| `network` | Can reach the network at all, beyond the model endpoint |

`files.read` without `files.write` is common and important: most chat runtimes accept an upload and can read it, and can change nothing.

The three that make an artifact *executable* are `shell`, `code.run`, and `files.write`. Autonomy A3 and A4, and modes EXECUTOR and AGENT, require at least one.

## 2. The profile

For each capability record the value and where it came from:

| Source | Meaning |
| --- | --- |
| `inspected` | Observed directly in the environment now |
| `declared` | The user said so |
| `profile` | From a named runtime profile in `references/runtime-profiles.md` |
| `researched` | From model or runtime documentation, with a source and a date |
| `inferred` | Reasoned from something else; the weakest source |

Report the dominant source in the summary; keep the per-capability sources in your reasoning. A capability that matters and is only `inferred` deserves a line under Assumptions.

## 3. Discovery order

Highest evidence first. Stop as soon as the answer is settled:

```
1. Inspection      (only when the target is the current environment - see below)
2. User declaration
3. Saved profile   (.prompt-architect/profiles/<id>.md)
4. Built-in profile (references/runtime-profiles.md)
5. Research        (gated; see section 8)
6. Documented default for the target
7. unknown
```

**The rule that makes inspection safe:**

> Inspect only when the target environment is the one you are running in. When the user is compiling for somewhere else - "a skill for my local Qwen in Open WebUI" - your own tools say nothing about the target. Inspecting there produces a confident, wrong profile, which is worse than an honest `unknown`.

Decide which case you are in before inspecting anything. Cues for compiling *elsewhere*: a named other runtime, a named local model, "my server", "for my team's setup", a skill that will be installed somewhere. Cues for compiling *here*: "this repo", "my project", no other environment mentioned, and you can already see the files in question.

**What to inspect** (self-target only, read-only, bounded): the tools you have been given; whether a repository, test runner, package manager, or version control exists; whether an interpreter is present, via a version check. Inspection stops there.

**What never to inspect**: credential stores, key material, or agent configuration beyond what the task already permits. Do not test network access by making a request - a request is a side effect, not an observation. Leave it `unknown` and say so.

## 4. Conflicts

Sources disagree. Precedence, highest first: direct evidence from the environment now; explicit current configuration; official documentation; older information from the user; inference.

When the user says a capability exists and inspection says it does not, say so plainly and compile for the observed state. Do not silently override the user and do not silently trust them.

## 5. What the task requires

Derive a required profile from the objective and the workflow, marking each capability `required`, `recommended`, or `optional`. Be strict about `required`: it means the task cannot be completed without it, not that it would be nicer.

Match required against available:

| Result | Meaning |
| --- | --- |
| `FULLY_COMPATIBLE` | Everything required is available |
| `COMPATIBLE_WITH_LIMITATIONS` | Everything required is available; something recommended is not |
| `REQUIRES_ADDITIONAL_TOOLS` | Something required is missing but could be added |
| `NOT_CURRENTLY_EXECUTABLE` | Something required is missing and cannot reasonably be added |
| `UNKNOWN` | A required capability could not be determined |

Only `FULLY_COMPATIBLE` omits the `## Compatibility` section.

## 6. Gaps, degradation, recommendation

A gap is `blocking` (a required capability is missing) or `non-blocking` (a recommended one is).

**Degrade, do not fake.** Preserve as much of the objective as the environment allows:

| Missing | Degraded workflow |
| --- | --- |
| `shell` or `code.run` | Emit the exact commands and analyze output the user pastes back. Mode becomes ANALYST or ADVISOR; autonomy drops to A1 or A2 |
| `files.write` | Emit the complete changed file or a patch for the user to apply |
| `web.search` | Ask the user for sources or URLs; state what could not be verified |
| `vision` | Ask for a text description or extracted text; never guess at image content |
| `db` | Emit the query and ask for the result set |

Say in Notes that the mode or autonomy changed and why. A degraded artifact that is honest beats a full one that cannot run.

**Recommend, never require and never install.** When a missing capability could be added, say what it is, what it would unlock, and weight it MUST, SHOULD, or MAY like any other requirement. Recommend only when it materially helps this task - a summarization task does not need web access. Never state or imply that a recommended capability has been added, and never install anything.

## 7. Caps on mode and autonomy

| Without | You cannot write |
| --- | --- |
| `shell`, `code.run`, and `files.write` all `no` | Autonomy A3 or A4; mode EXECUTOR or AGENT |
| `files.write` | Any instruction to change a file |
| `web.search` and `web.fetch` | Any instruction to find current information |
| `vision` | Any instruction to interpret an image |

Autonomy is the minimum of the model-tier cap (`references/model-tiers.md`) and the capability cap. A frontier model in a runtime with no tools is still A2 at most; a 3B model with a full toolchain is still A2 at most.

## 8. Research, and when not to

Researching the target's documentation is slow, costs money, needs `web.search` or `web.fetch`, and the answers age. Research only when **all** of these hold:

1. The capability is required or recommended for this task.
2. It is still `unknown` after inspection, declaration, and profiles.
3. It is blocking, or it materially changes the artifact.
4. You have web access.

At most three lookups. Prefer official model documentation, then official runtime documentation, then the official API reference; community sources only when nothing official covers it. Record the source and the date, and mark the value `researched`.

With no web access, or when research does not settle it, fall back to the profile default and mark the capability `unknown`. Never present a recalled fact as documented, and never let `unknown` quietly become `yes`.

## 9. Saved profiles

Write a settled profile to `.prompt-architect/profiles/<id>.md` in the user's current project, when you can write files. Record the capabilities, the source of each, a timestamp, and the runtime and model it describes. Read saved profiles before researching so the user is not asked the same question twice.

Revalidate when the model changes, the runtime changes, tools are added or removed, or the user asks. A profile older than the environment it describes is inference, not evidence.

## 10. The Compatibility report

Emitted only when compatibility is not `FULLY_COMPATIBLE`:

```
## Compatibility
Target: local Qwen 2.5 7B via Open WebUI     Result: REQUIRES_ADDITIONAL_TOOLS

| Capability | Required | Available | Result |
| --- | --- | --- | --- |
| files.read | yes | yes | pass |
| shell | yes | no | FAIL |
| code.run | recommended | no | limited |

Blocking: shell. The skill cannot run the test suite itself.
Recommended: enable the code execution feature, which would restore the full workflow.
Fallback taken: the skill emits the exact commands and reads the output the user pastes back, as an ANALYST at A1.
```

Keep it to the capabilities that decided something. A task needing nothing has nothing to report.

## 11. Validation before returning

1. Does any instruction require a capability recorded as `no`?
2. Does the autonomy exceed what the capabilities allow?
3. Does the mode exceed what the capabilities allow?
4. Are unknown-but-needed capabilities phrased conditionally ("if you can run the tests, run them; otherwise list them")?
5. Does every blocking gap have a stated fallback?
6. Do the Tool Rules name only tools the target has?
7. Are limitations stated honestly rather than omitted?
8. Would the artifact still be truthful if the weakest assumed capability turned out to be absent?

`scripts/validate_prompt.py` checks items 1 to 6 mechanically, as rules `C01` to `C04` and `S11` to `S14`.

## 12. Adversarial capability questions

Ask these at Level 3 and above: What if the tool is installed but disabled? What if the model can read but not write? What if the database is read-only? What if the context is too small for the material? What if the model has vision but the runtime never passes it an image? What if the user's declared capability was true last month and not now?

Each one that produces a plausible failure gets a mitigation in the artifact, not a note in your reasoning.

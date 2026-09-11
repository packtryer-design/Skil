# Model Tier Reference

Used at Stage 2 to set the `Model:` tier, and at Stages 5-6 to adapt the artifact to it. The tier is the capability of the model that will *execute* the compiled prompt or skill. It is independent of everything else in the summary:

- `Level` is how complex the compilation is. `Model` is how capable the executing model is. A Level 4 task compiled for a 3B model is still Level 4 work; the artifact just comes out differently.
- `Target` is the host (Claude Code, chat, API, agent). `Model` is the model inside it. Claude Code can run Haiku; an API pipeline can run Opus. Decide them separately.

The one rule that governs everything below: **a weaker model does not get a longer prompt.** Small models have short effective context and lose track of earlier instructions. Detail goes into explicitness and worked examples; the number of rules, sections, decisions, and tools goes down. Rules shrink, examples grow, the total stays bounded.

## 1. The tiers

| Tier | Capability | Illustrative models (as of 2026-09; the list ages, the capability column does not) |
| --- | --- | --- |
| frontier | Follows nuanced multi-part instructions, infers intent from context, plans and revises multi-step tool use, holds a long document in working memory | Claude Opus 5 / Sonnet 5, GPT-5-class, Gemini Pro-class |
| mid | Follows explicit structure reliably; executes named steps in order; limited inference beyond what is written; degrades on implicit judgment | Claude Haiku 4.5, Llama 3.3 70B, Qwen 2.5 32B, Mistral Small, "mini" and "flash" tiers |
| small | Follows short explicit rules one task at a time; needs a worked example to produce a format; cannot arbitrate between competing instructions | Llama 3.2 3B, Qwen 2.5 3B-7B, Phi-4-mini, Gemma 2 9B |
| tiny | Pattern-completes rather than follows; the examples carry most of the specification; a second task in the same prompt displaces the first | Llama 3.2 1B, Qwen 2.5 0.5B-1.5B, heavily quantized 3B, TinyLlama |

Quantization moves a model down: a 3B at Q4 behaves closer to `tiny` than to `small` on format compliance. A model served with a 2K context window is `tiny` regardless of parameter count.

## 2. Tiering a model you were not told about

When the user names a model you do not recognize, or gives only a size, tier it by this test rather than by guessing the vendor's marketing tier:

1. Take the single hardest instruction the artifact will contain (usually the output contract or the decision rule).
2. If the model needs a worked example to comply with it, the tier is `small` or below.
3. If it complies from the instruction but only when the instruction is the only one in the prompt, the tier is `small`.
4. If it complies with that instruction alongside eight others, the tier is `mid`.
5. If it also handles the case the instruction did not mention, the tier is `frontier`.

Size heuristic when nothing better is available: 70B+ is `mid`, 3B-30B is `small`, under 3B is `tiny`. Fine-tuned narrow models (a 3B trained for exactly this classification) behave one tier up **on that task only** and at their base tier on everything else; when the user says the model is fine-tuned for the task, compile at the fine-tune's tier but keep the output contract at the base tier.

## 3. Detection cues

| Cue in the request | Tier |
| --- | --- |
| Parameter counts: "3B", "7B", "1B", "0.5B", "8x7B" | map by size, see above |
| Model names: Llama, Qwen, Phi, Gemma, Mistral, TinyLlama, DeepSeek-R1-Distill | look up or apply the size heuristic |
| Runtimes: Ollama, LM Studio, llama.cpp, GGUF, vLLM, Jan, Text Generation WebUI | `small` unless a larger model is named |
| Quantization: "Q4", "Q4_K_M", "quantized", "4-bit" | one tier down from the size heuristic |
| Hardware and offline: "no GPU", "on my laptop", "Raspberry Pi", "edge device", "air-gapped", "offline", "on-device" | `small`, or `tiny` for single-board hardware |
| Cost and volume: "cheap model", "high volume", "per-request cost", "mini", "flash", "Haiku" | `mid` |
| "local model", "self-hosted", "my own model" with no size | `small`, and see the asking rule below |
| Nothing about the model at all | `frontier` |

**Default and asking.** Default to `frontier` and record it as an Inferred assumption. Do not add a Notes line about smaller models unless the request contains a cue. Ask exactly one question only when both hold: the user referred to a local or self-hosted model without a size, **and** autonomy is A2 or above (the artifact will be built or run, so a wrong tier wastes real work). The question is "roughly what size model, or which one?" with the default stated as `small`. For A0-A1 work, never ask: compile at `small`, say so at the top of the prompt, and note what changes at another tier.

## 4. Authoring rules by tier

| Dimension | frontier | mid | small | tiny |
| --- | --- | --- | --- | --- |
| Sections | full catalog per `sections.md` | at most 10, each at most 6 lines | at most 6, from the reduced set below | at most 3: Objective, Output Format, Examples |
| Sentence style | normal prose and bullets | one instruction per sentence, at most 25 words | at most 20 words, imperative, positive form, no subordinate clauses | at most 12 words |
| Priorities | MUST / SHOULD / MAY / MUST NOT | same | MUST and MUST NOT only | none; every line is an instruction |
| Examples | only when the format is unusual | one when the output format is non-obvious | required: at least one full input-to-output pair | required: two or three pairs |
| Output contract | described | literal skeleton with headings | exact template to copy, fixed keys, closed value sets, "output nothing else" | one line, or one JSON object with at most 4 fixed keys |
| Reasoning | native; no instruction needed | "do the steps in order" | steps are given explicitly; if reasoning is needed it goes in a named output field before the answer | none; direct input-to-output mapping |
| Autonomy cap | A0-A4 | A3 | A2 | A1 |
| Tool budget | as the task needs | at most 3, each named | at most 1, with the call shape shown as an example | none |
| Length | level budget | level budget | level budget x1.5 (the examples) | 30 lines total, whatever the level |

Reduced section set for `small`, in this order: Objective, Context (only if facts are needed), Requirements (as MUST / MUST NOT), Workflow (as numbered steps), Output Format, Examples.

### Sentence style

Small and tiny models parse each sentence nearly independently. Write for that:

- One instruction per sentence. Split "Review the query for performance and correctness, then suggest an index" into three sentences.
- Positive form. "Reply with one of the five labels" beats "Do not reply with anything other than a label". Keep MUST NOT only for the one or two boundaries that matter most; every extra prohibition dilutes the others.
- No subordinate clauses, no "unless", "except when", "where relevant", "as appropriate", "if applicable", "use your judgment". Each of these asks the model to arbitrate, which is the capability that is missing. Replace a conditional with a step ("Step 2. If the email mentions a refund, output `billing`. Step 3. Otherwise continue.") or delete it.
- Repeat the exact same noun every time. Do not alternate "the email", "the message", "the ticket", "it". Coreference is where small models drift.
- Numbers and labels are literal and closed. "one of: billing, technical, sales, spam, other" beats "an appropriate category".

### Examples

At `small` and `tiny` the examples are not illustration, they are the specification. Write them as full input-to-output pairs in the exact shape the model must produce, inside an `## Examples` section (`small`) or as the body of the prompt (`tiny`).

- Cover the ordinary case first, then the one boundary the model will otherwise get wrong (the ambiguous input, the empty input, the input that belongs in the catch-all bucket).
- Every example obeys every rule in the prompt. An example that violates the output contract overrides the contract.
- Do not include an example of the wrong output at `small` or `tiny`; bad/good pairs work at `frontier` and `mid` and backfire below, because the model copies the nearest pattern rather than reading the label.
- Use the user's real data shape, not `foo`/`bar`.

### Output contract

Give `small` and `tiny` a template to copy, not a description to satisfy:

```
Category: <one of: billing, technical, sales, spam, other>
Confidence: <high, medium, or low>
```

Then one line: `Output these two lines and nothing else.` Prefer fixed keys over prose, closed value sets over open text, a fixed count over an open list ("exactly three bullets"), and plain text or a flat JSON object over Markdown with nested structure. Do not ask for tables, citations with line numbers, or scores with per-dimension rationale below `mid`.

### Autonomy, tools, and safety

The autonomy caps in the table are hard. Beyond them:

- A `small` or `tiny` model does not reliably self-police, so a forbidden operation must be made **impossible**, not prohibited. Withhold the tool, scope the permission, or route the step to a human. A prose rule saying "never delete files" is not a control at these tiers.
- At `small` or `tiny`, risk HIGH or CRITICAL caps autonomy at A1 and requires an explicit human verification step before anything is acted on. If the task cannot be done that way, say so in Notes and recommend a `mid` or `frontier` model for the risky part.
- Where one tool is allowed at `small`, show the exact call shape as an example. Where no tool is allowed at `tiny`, the prompt must not mention tools at all.

### Decomposition

At `small` and `tiny`, a task needing more than about five steps, or more than one domain, does not become a longer prompt. Compile the single narrowest prompt that delivers the user's primary deliverable, and list the follow-up prompts in Notes so the user can request them separately. One prompt, one job.

## 5. Prohibited asks

These fail at the tier shown and at every tier below it. When the task requires one, either move the tier up or move that part to a human or a separate frontier-model step.

| Ask | Fails at |
| --- | --- |
| Self-critique or revision pass in the same response | small |
| Ranking by several criteria at once, or weighted scoring | small |
| "Cite the file and line", "quote the source" (invented citations) | small |
| Open-ended lists ("list all the issues you find") | small |
| Arithmetic across more than a handful of numbers | small |
| Synthesis across more than one long document | small |
| Holding a rule stated 40 lines earlier | tiny |
| Any conditional branch not written as its own step | tiny |
| Producing nested structure (Markdown sections, nested JSON) | tiny |
| More than one task in one prompt | tiny |

## 6. Adaptation procedure

Apply after selecting and specializing a template, before the review stage.

1. Set the tier from the cues, or `frontier` by default.
2. If the tier is `frontier`, stop. Nothing below applies.
3. Check the caps: autonomy against the table, risk against the safety rule, tool count against the budget. Lower the autonomy or move the risky part out before touching the wording.
4. Cut sections to the tier's limit, keeping the reduced set in catalog order. Merge Constraints into Requirements, and Decision Rules into Workflow steps, rather than dropping their content silently.
5. Rewrite every remaining sentence to the tier's style rule. Split, shorten, flip negatives, remove conditionals, unify the nouns.
6. At `small` and below, reduce priorities to MUST and MUST NOT.
7. Replace the described output contract with a literal template plus "output nothing else".
8. Write the examples: one pair at `small`, two or three at `tiny`, each obeying every rule in the prompt.
9. At `tiny`, cut to three sections: Objective (one or two lines of task), Output Format (the template), Examples (two or three pairs). Everything else is deleted, not compressed. End the prompt on the input slot so the model's next token is the start of the answer.
10. Re-check the length against the tier budget. If it is over, cut rules, never examples.

## 7. Worked contrast

The same objective, compiled at two tiers.

**frontier** (Level 2, about 30 lines, abbreviated here):

```
## Objective
Triage inbound support emails into one of five queues so the on-call engineer sees only what is theirs.

## Requirements
MUST
- Assign exactly one queue per email.
- Use `other` when the email fits none of the four named queues.
SHOULD
- Note when an email plausibly fits two queues, so the routing rules can be improved.
MUST NOT
- Reply to the customer or take any action on the ticket.

## Output Format
For each email: the queue, a one-line reason, and a confidence. Group by queue and order by confidence.
```

**small** (same objective, Llama 3.2 3B):

```
## Objective
Sort one support email into one queue.

## Requirements
MUST: Choose exactly one queue from this list: billing, technical, sales, spam, other.
MUST: Choose `other` if no queue fits.
MUST NOT: Write a reply to the customer.

## Workflow
1. Read the email.
2. Choose the queue.
3. Write the two output lines.

## Output Format
Queue: <billing, technical, sales, spam, or other>
Confidence: <high, medium, or low>

Output these two lines. Output nothing else.

## Examples
Email: "My card was charged twice for the March invoice."
Queue: billing
Confidence: high

Email: "hi"
Queue: other
Confidence: low
```

What changed and why: the SHOULD disappeared (a small model cannot weigh a preference against a requirement); "exactly one queue per email" became "one email" (one job per prompt); the described output became a copyable template; two examples were added, the second covering the empty-ish input that would otherwise be forced into a real queue; the grouping and ordering requirement was dropped because it is a second task. The `small` version is longer in lines and smaller in demands. That is the shape the trade always takes.

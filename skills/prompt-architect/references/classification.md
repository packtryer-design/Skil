# Classification Reference

Used at Stage 2 for Level 2 and above. Covers domains, risk, operating mode, autonomy, complexity level, and target host. The compact versions in `SKILL.md` are authoritative; this file adds the detail needed for borderline cases.

## 1. Domain taxonomy

| Domain | Subdomains | Recognition cues | Base templates |
| --- | --- | --- | --- |
| software | coding, code modification, repository modification, debugging, refactoring, code review, architecture, API, database, DevOps, testing | "add", "fix", "refactor", "my repo", stack names, error messages, "PR", "CI" | repository-agent, codebase-analyst, debugging-agent, code-reviewer, architecture-agent |
| security | security review, threat modeling, authentication and authorization review, session and token handling, secrets, cloud configuration, input validation, prompt injection | "vulnerabilities", "audit", "pentest findings", "OIDC", "OAuth", "IAM", "secrets", "threat model" | security-reviewer, threat-modeler, authentication-reviewer |
| research | technical research, market research, comparison, fact checking, source evaluation, synthesis | "find out", "compare", "which should I buy", "is it true that", "state of the art", "sources" | research-agent, comparison-agent, fact-checker |
| documents | PDF analysis, Word or text document analysis, spreadsheet analysis, multi-document analysis, document generation, document transformation | attached files, "this contract", "these reports", "extract", "summarize the PDF", "convert to" | document-analyst, pdf-analyst, spreadsheet-analyst, multi-document-analyst (generation and transformation: compose from sections) |
| data | data analysis, data cleaning, SQL, statistics, visualization, reporting | "dataset", "CSV", "query", "dashboard", "chart", "trend", "correlation" | data-analyst, sql-analyst, visualization-agent |
| business | product planning, business analysis, requirements, strategy, project planning, customer workflows | "MVP", "roadmap", "should we enter", "user stories", "stakeholders", "pricing" | product-architect, requirements-analyst, strategy-analyst |
| content | writing, rewriting, editing, marketing, documentation, presentation, communication | "write", "rewrite", "edit", "tone", "blog", "email", "slides", "README" | none (compose from sections; usually Level 1-2) |
| meta | prompt creation, prompt review, prompt optimization | "prompt", "system prompt", "instructions for Claude", "make Claude do X reliably" | prompt-reviewer, prompt-optimizer |

Assignment rules:

- The primary domain is the domain of the deliverable. Secondary domains are those that gate the deliverable's quality (security for authentication work, data for a dashboard built from a CSV).
- A task is multi-domain when a second domain changes the workflow, the safety rules, or the output contract. Mentioning a technology is not enough: "write a blog post about Kubernetes" is content, not software.
- For multi-domain tasks, use one primary template and pull the specific sections you need from the secondary domain (for example, the finding format from `security-reviewer` into the review step of `repository-agent`). Do not concatenate two whole templates.
- When supplied documents are the evidence for a comparison or decision ("compare these three contracts and tell me which is best"), the primary template is the document one (`multi-document-analyst` or `document-analyst`, for provenance and coverage rules, since inventing terms is the main failure mode) with the criteria and recommendation sections borrowed from `comparison-agent`. `comparison-agent` as primary is acceptable when it keeps per-document evidence with locations before any synthesis.
- When the phases of a task map to domains, express them as a HYBRID mode sequence in the prompt.

## 2. Risk rubric

Risk is the consequence of a wrong answer or a wrong action, not the difficulty of the task.

| Risk | Definition | Examples | What the prompt gains |
| --- | --- | --- | --- |
| LOW | Wrong output is cheap to notice and redo; no side effects | Explain a concept, draft an email, compare two CPUs | An output contract; nothing else |
| MEDIUM | Wrong output causes rework or guides a moderate decision; changes touch non-production artifacts | Refactor a side project, plan a dashboard, review a query, summarize a report used internally | A scope boundary (MUST NOT), assumptions, validation of the result |
| HIGH | Wrong output changes production behavior, touches authentication, sessions, permissions, data integrity, or drives decisions with real cost; security assessments (false negatives and false positives both cost) | Modify production authentication, review security controls, advise on a purchase above a few thousand dollars, legal or medical content for publication | Checkpoints before high-impact steps, testing and regression checks, evidence rules, rollback consideration, a review step |
| CRITICAL | Wrong action is destructive or irreversible, moves money, exposes secrets, changes privileged access, or tears down infrastructure | Delete or migrate production data, change IAM or firewall rules, rotate keys, run payment operations, `terraform destroy` | Confirmation before each irreversible step, dry run or backup first, a list of forbidden operations, stop-and-report failure handling, never A4 |

Escalators (raise one level when any applies): production environment; no test suite, staging, or rollback path; the user cannot verify the result themselves; the result will be published or acted on by others without review; the task involves personal or regulated data.

De-escalators (lower one level when all apply): sandbox or throwaway environment; result is reviewed by the user before use; fully reversible.

Defaults by task shape: explanations and drafts LOW; analysis of supplied material MEDIUM (a wrong reading misleads); repository changes MEDIUM, HIGH when the code path is production or touches auth, payments, or data migration; security assessments HIGH; anything with destructive operations CRITICAL.

## 3. Operating modes

| Mode | Deliverable | Typical verbs | Output shape |
| --- | --- | --- | --- |
| ADVISOR | A recommendation with options and trade-offs | recommend, should I, which, best way | Recommendation, alternatives, trade-offs, conditions under which the answer changes |
| ANALYST | An accurate account of existing information or a system | analyze, understand, assess, what does this do, review the data | Findings with evidence, structure, risks, open questions |
| RESEARCHER | Evidence gathered, evaluated, and synthesized | research, find out, compare with sources, is it true | Findings, evidence quality, disagreements, confidence, sources, limitations |
| ARCHITECT | A design or specification | design, architecture, spec, plan the system | Recommended design, alternatives, trade-offs, risks, phases |
| ENGINEER | Working code or a technical artifact | implement, build, fix, refactor, add | What changed, why, tests run, remaining issues |
| EXECUTOR | Steps carried out with tools, with side effects | run, migrate, deploy, process these files, convert | Actions taken, results, verification, anything not done |
| REVIEWER | An evaluation of existing work | review, audit, critique, check, find problems | Ranked findings with evidence and recommendations |
| TEACHER | Understanding in the reader | explain, teach, why, how does | Explanation adapted to the audience, examples, common mistakes |
| AGENT | A bounded multi-step task completed autonomously | "just do it", "go through all", batch work | Progress log, results, boundaries respected, exceptions |
| ORCHESTRATOR | Coordination of phases, tools, or roles | pipeline, multi-stage, coordinate, subagents | Plan of phases, hand-offs, consolidated result |

Common HYBRID sequences:

- Repository change: ANALYST -> ENGINEER -> REVIEWER (insert ARCHITECT when a design decision is needed first).
- Debugging: ANALYST -> ENGINEER.
- Purchase or technology decision: RESEARCHER -> ADVISOR.
- Product idea to specification: ANALYST -> ARCHITECT.
- Security assessment: ANALYST -> REVIEWER.
- Data question with reproducible code: ANALYST -> ENGINEER.
- Autonomous multi-role project: ORCHESTRATOR over the modes above.

Anti-patterns: a "senior expert" role standing in for a behavioral specification; ENGINEER when the user wanted a recommendation; AGENT without boundaries; REVIEWER prompts that do not define what counts as evidence.

## 4. Autonomy levels

| Level | Claude does | Claude does not | Prompt wording pattern |
| --- | --- | --- | --- |
| A0 Explain only | Explain, describe, teach | Recommend or act | (usually implicit in the objective) |
| A1 Analyze or recommend | Analyze, review, or evaluate existing material and recommend: findings, options, trade-offs. A long review report is still A1 | Produce an artifact to be run or built later; execute | "Report findings and recommendations; do not change anything." or "Recommend one approach and state when a different choice would be better." |
| A2 Produce | Produce an artifact that will be used or run later: a plan, specification, code (including a standalone script), or query, not run against real systems | Execute against real files, data, or systems; run side-effecting commands | "Produce the plan only. Do not modify files or run commands that change state." or "Deliver the script; it will be run by the user." |
| A3 Execute with checkpoints | Execute, stopping at defined decision points | Continue past a checkpoint without confirmation | "Proceed without asking for X and Y. Stop and report before Z." |
| A4 Execute autonomously within boundaries | Complete the whole task inside explicit boundaries | Leave the boundaries, ask routine questions | "Work autonomously within these boundaries: ... Stop only when ..." |

A checkpoint is a point where Claude stops, reports the current state and the decision to be made, and waits. Define triggers concretely. Common triggers:

- Before modifying authentication, session, authorization, or payment code paths.
- Before schema migrations, data deletion, overwriting files, or force operations.
- Before external calls with side effects (emails, deployments, API writes).
- After the plan and before implementation, for HIGH and CRITICAL risk.
- When inspection contradicts the user's description of the system.
- When the remaining work exceeds the stated scope.

Selection rules:

- Repository changes default to A3.
- A4 requires all of: clear boundaries (allowed paths, forbidden operations, stop conditions), a reversible path (version control, backups), and either an explicit user request or LOW-MEDIUM risk.
- CRITICAL risk never gets A4; every irreversible step gets its own checkpoint.
- If the target host has no tools, cap autonomy at A2 and say so in Notes.
- If the target host has no human in the loop (API pipeline, scheduled job), checkpoints cannot wait for answers: instruct Claude to take the safe path, record what it would have asked, and report it.

## 5. Complexity level selection

| Level | Signals | Plan test categories |
| --- | --- | --- |
| 1 Quick | One deliverable, LOW risk, A0-A1, no tools, no material ambiguity | Simple: explain OAuth, rewrite this paragraph |
| 2 Standard | One domain, LOW-MEDIUM risk, A0-A2, requirements or output structure matter | Medium: review my SQL query, analyze this document, plan a dashboard; compare two CPUs when criteria matter |
| 3 Advanced | Multi-step or tool-using work (A2-A3), MEDIUM-HIGH risk, or multi-domain | Complex: modify a repository, design a production architecture, research a purchasing decision; most multi-domain tasks |
| 4 Expert | HIGH-CRITICAL risk with execution, several phases or roles, significant ambiguity | High-risk: modify production authentication, change infrastructure, review security controls of a live system |

Notes:

- Floors from `SKILL.md` apply: HIGH risk needs Level >= 3, CRITICAL needs Level 4, A3-A4 need Level >= 3, multi-domain needs Level >= 2.
- Ambiguous requests: decide the level from the most likely reading; if the clarification gate says ask, ask before compiling.
- Underspecified but solvable requests: assume, record the assumptions, and compile at Level 2-3. Interrogating the user is a failure.
- A long request is not automatically a high level; a short request is not automatically a low level ("delete stale users from prod" is Level 4).

## 6. Target host detection

| Target | Cues | Consequences for the prompt |
| --- | --- | --- |
| `claude-code` | Repository paths, "my repo", "run the tests", CLI or IDE context, the user is currently in Claude Code | File and shell tools available; A3-A4 possible; output can be files plus a report; checkpoints work |
| `claude-ai` | Attached documents, "in the chat", no repository | Attachments and possibly web search; no shell and no file writing; A2 at most for code; output is the message |
| `coding-agent` | Cursor, Codex, Cline, Continue, "my IDE agent" | Close to `claude-code`, but name capabilities rather than that product's specific tools |
| `open-webui` | "Open WebUI", a self-hosted chat front-end, usually over Ollama | No filesystem and no execution by default; uploads reach the model as context; code execution and web search are opt-in |
| `ollama`, `lm-studio` | "Ollama", "LM Studio", "Jan", "llama.cpp", a served local model | The runtime serves a model and provides no tools; tool calling is a protocol the caller must implement |
| `api-no-tools` | Building an application, "system prompt", batch or pipeline | No tools, no human in the loop; state assumptions instead of asking; machine-friendly output contract |
| `custom-agent` | MCP servers, named tools, "the agent can call X", a harness the user built | Only what the user declared exists; name those tools and nothing else |
| `unknown` | None of the above | Conditional tool rules; autonomy capped at A3; state the assumption in Notes |

The profile's defaults and the switches that change them are in `references/runtime-profiles.md`; what to do with the result is in `references/capabilities.md`.

Never assume a tool the host does not have. When in doubt, write the rule conditionally.

The host and the model tier are orthogonal: Claude Code can be running Haiku, an API pipeline can be running Opus, and a local runtime such as Ollama is a host *and* a strong cue about the model. Decide the host from where the artifact runs and the tier from what will execute it.

## 7. Model tier

Summarized in `SKILL.md` Stage 2; the full rubric, detection cues, per-tier authoring rules, prohibited asks, and adaptation procedure are in `references/model-tiers.md`. Read that file whenever the tier is not `frontier`.

| Tier | Capability | Autonomy cap | Tool budget |
| --- | --- | --- | --- |
| frontier | Nuanced multi-part instructions, inferred intent, planned multi-step tool use | A0-A4 | as needed |
| mid | Explicit structure followed reliably; limited inference | A3 | 3 named tools |
| small | Short explicit rules, one task at a time; needs worked examples | A2 | 1 tool |
| tiny | Pattern completion; the examples carry the specification | A1 | none |

At `small` and `tiny`, risk HIGH or CRITICAL caps autonomy at A1 and requires a human verification step, because a model at these tiers does not reliably self-police: a forbidden operation must be made impossible rather than prohibited in prose.

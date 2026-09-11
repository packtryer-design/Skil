# Requirements Reference

Used at Stages 3-5 for Level 2 and above. Covers intent understanding, normalization, requirement extraction and priorities, the assumption ledger, the clarification gate, context strategy, and conflict resolution.

## 1. Intent understanding

Answer these internally before anything else:

1. What does the user want to exist or know at the end?
2. Why do they want it, when the reason changes the solution? ("so the auditors accept it" changes the deliverable; "because I am curious" does not.)
3. What must Claude produce: an explanation, a recommendation, a plan, an artifact, a change to an existing system, an evaluation, or a mix?
4. What existing material must Claude use: repository, files, data, previous conversation, a URL, a prior prompt?
5. Which activities are needed, in what order: analyze, advise, plan, execute, review?
6. What would the user accept as success, and how could anyone check it?

Keep the user's own terms for their systems, roles, and documents. Drop filler, hedges, and side remarks that do not carry requirements.

## 2. Normalization

Rewrite the request as a clear internal task definition before extracting anything. Two examples:

```text
User: "Make the dashboard way better and add filters."

Objective: Improve the existing analytics dashboard.
Likely work: UI refinement plus filter functionality.
Important unknown: which filters apply to which widgets, and what "better" means to this user.
Likely constraint: do not break existing dashboard behavior.
```

```text
User: "Can you figure out if we should move our Postgres to Aurora? Finance keeps asking."

Objective: Recommend whether to migrate the production Postgres database to Amazon Aurora.
Deliverable: a recommendation with cost, risk, and migration effort, written so a finance stakeholder can follow the cost part.
Important unknowns: current database size, workload profile, and the cost figures finance cares about.
Likely constraint: no downtime beyond what the business tolerates (unknown).
```

Do not lock in assumptions during normalization; record unknowns instead.

## 3. Requirement extraction

Collect requirements from four sources and label where each came from:

- Explicit statements by the user (CONFIRMED).
- Implied by the deliverable (a migration needs a rollback; a dashboard needs a data source) (INFERRED).
- Implied by domain norms (production auth changes need tests; research needs sources) (INFERRED).
- Imposed by the environment (existing framework, deployment platform) (CONFIRMED when stated, otherwise INFERRED).

Categories:

| Category | Examples | Notes |
| --- | --- | --- |
| Objective | The final desired result | One sentence |
| Functional | What the solution must do | Observable behavior |
| Non-functional | Performance, reliability, security, scalability, accessibility, maintainability | Include only those that matter for this task |
| Constraints | Existing architecture, technology limits, budget, compatibility, deployment, "do not rewrite unrelated code" | Constraints bound the solution space; they are not goals |
| Preferences | Nice-to-have choices | Never mandatory unless the user says so |
| Resources | Repository, files, database, API, documentation, existing implementation | Feed the Resources section |
| Success criteria | How success can be verified | Feed Validation and Completion Criteria |

### Priority classes

| Class | Assign when | Wording in the prompt |
| --- | --- | --- |
| MUST | The user stated it as necessary, or the deliverable is wrong without it | "MUST use Amazon Cognito OIDC." |
| SHOULD | Expected by default, may be traded away with a stated reason | "SHOULD preserve the existing login UI." |
| MAY | Adds value, optional | "MAY improve related login UI when touching those files." |
| MUST NOT | Out of scope, forbidden, or protective | "MUST NOT rewrite unrelated authentication code." |

The preference test: if the user would still accept the deliverable without it, it is SHOULD or MAY, not MUST.

Common failures to avoid: requirement inflation (turning every mention into a MUST), vague MUSTs ("high quality", "robust"), missing MUST NOT for scope, non-functional requirements copied from a checklist rather than the task, and constraints written as goals.

Success criteria must be observable: "existing login tests pass and a Cognito login completes end to end" rather than "authentication works well".

## 4. Assumption ledger

| Class | Meaning | Handling in the prompt |
| --- | --- | --- |
| CONFIRMED | Stated by the user or verifiable right now | State as fact in Context |
| INFERRED | Likely, with a stated basis | List under Assumptions as "Inferred: ... (basis)". High-impact ones get a verification step in the workflow when they can be checked |
| UNKNOWN | Cannot be determined from available information | List under Assumptions as "Unknown: ..." with what Claude should do about it (inspect, ask at a checkpoint, or proceed with the safe default) |

Rules:

- Never present an inference as confirmed.
- Never hide a high-impact assumption. High-impact means it changes the architecture, could cause significant rework, or affects safety or security.
- Prefer inspecting available resources before assuming.
- Prefer reversible assumptions: choose the default that is cheapest to undo if wrong.
- Keep low-impact assumptions out of the prompt; they add length without changing behavior.

Verification-step pattern: "Before implementing, confirm that the project uses NextAuth (inferred from the dependency list). If it does not, stop and report the actual authentication mechanism."

## 5. Clarification gate

Ask the minimum number of questions that materially improve the outcome. Ask only when all three conditions hold:

1. Different answers produce materially different prompts.
2. Claude cannot reasonably determine the answer from available context, and the target Claude cannot inspect it either.
3. A wrong assumption would cause significant damage, wasted work, or a wrong result.

Decision table:

| Situation | Action |
| --- | --- |
| The answer is in a repository, file, schema, or document Claude can inspect (stack, layout, data model, dependencies, test setup, where the code lives) | Do not ask. Add an inspection step and, if the decision is high-impact, a checkpoint after inspection |
| The unknown is about how to execute safely (hard or soft delete, edge-case records, thresholds, library choice) and a safe reversible default exists | Do not ask. Compile with the default, record it under Assumptions, put the decision at a checkpoint |
| The answer changes little | Assume the reversible default, record it |
| The unknown is about what the user wants the outcome to be, it changes the prompt materially, and only the user knows it | Ask |
| The user said "just do it" or "do not ask" | Do not ask. Choose the safe default and list the assumptions prominently |
| The target host has no human in the loop | Do not ask. Write the prompt so Claude proceeds on the safe path and reports the assumption |

Intent versus execution: "which filters, applied to which widgets" and "what does better mean" are intent unknowns (ask when material). "Soft delete or hard delete", "what about users who never logged in", "which rate-limit threshold" are execution unknowns: inspect, default safely, checkpoint. If you can state a sensible default for a question, it is usually an execution unknown and should not be asked.

Question quality:

- Specific and easy to answer; ideally a choice between named options.
- Includes the consequence: what changes depending on the answer.
- Includes a default: what you will assume if the user prefers not to answer.
- At most three questions. If you have more, the request needs assumptions, not a questionnaire.

Bad:

```text
What framework? What database? What UI? What language? What deployment? What testing framework?
```

Better:

```text
1. Which identity provider should handle login: Amazon Cognito, Auth0, or your own OIDC server?
   Why it matters: it decides the integration architecture and the libraries used.
   Default if unanswered: Amazon Cognito, because the request mentions AWS.
```

Format for the Questions section: numbered items, each with the question, "Why it matters:", and "Default if unanswered:". Then stop; do not emit a prompt until the user answers or accepts the defaults.

## 6. Context collection strategy

Possible sources: user-provided text, files, repository, images, documents, database schema, existing code, configuration, external research, tool output, earlier conversation context.

For each source relevant to the task, assign one status:

| Status | Meaning | Prompt consequence |
| --- | --- | --- |
| Required | The task cannot be done correctly without it | Claude must inspect it before acting; if it is missing, Claude stops and reports (Failure Handling) |
| Recommended | Materially improves the result | Claude should inspect it when available and say if it was not |
| Optional | Helpful for edge cases | Claude may consult it |
| Unavailable | Known not to exist or not to be accessible | Claude must not assume its contents; state the resulting limitation |

Typical assignments:

- Repository tasks: repository Required; configuration and deployment files Recommended; architecture documentation Optional; production configuration usually Unavailable.
- Document tasks: all supplied documents Required; external references Optional.
- Research tasks: user-provided material Required when supplied; external sources Required for factual claims; earlier conversation Recommended.
- Data tasks: the dataset and its schema Required; a data dictionary Recommended.

Resources section wording: list each source with its status and what Claude should look for, then close with "Use supplied context before making assumptions. If a required resource is missing or contradicts this prompt, say so before proceeding."

## 7. Conflict detection and resolution

Priority hierarchy, highest first:

1. Platform and system constraints (what the host allows, model policies).
2. Safety and security requirements.
3. Explicit user requirements.
4. Task-specific constraints.
5. Preferences.
6. Optional optimizations.

Detect conflicts before composing: a preference that contradicts a MUST, a speed preference that contradicts a testing requirement, "do not ask questions" against a CRITICAL checkpoint, "rewrite everything" against "keep changes minimal".

Resolve by keeping the higher-priority item, removing or weakening the lower one, and stating the resolution in Notes when the user would want to know. If two items at the same level conflict and the choice is material, the clarification gate applies.

Examples:

- "Ship it fast" (preference) versus "no regressions in production" (safety): keep the regression requirement; note that speed was subordinated.
- "Do not ask me anything" (preference) versus deleting production data (CRITICAL): keep the confirmation checkpoint before the deletion step only; make everything else autonomous; say so in Notes.
- "Use the newest library" (preference) versus "follow existing project patterns" (constraint): prefer existing patterns; allow the new library only where no pattern exists.

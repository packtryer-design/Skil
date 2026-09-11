# Review Reference

Used at Stage 7 for Level 3 and above, and whenever an existing prompt is reviewed. Contains the critique checklist, the adversarial review, failure-mode analysis, optimization rules, final validation, and the scoring rubric for prompt reviews. Fix what you find; do not report problems you could have fixed.

## 1. Self-critique checklist

| Area | Check | Typical fix |
| --- | --- | --- |
| Intent | Is the actual user goal represented? Did any intent get lost in normalization? | Restore the missing intent in Objective or Task |
| Requirements | Are MUST / SHOULD / MAY / MUST NOT assignments right? Are important constraints present? Is there a scope-bounding MUST NOT? | Re-tier; add the missing constraint |
| Ambiguity | Could Claude read the task in two materially different ways? Are high-impact ambiguities resolved or surfaced? | Add the deciding detail, an assumption, or a checkpoint |
| Context | Does Claude know what to inspect? Are assumptions separated from confirmed facts? | Add or reclassify Resources and Assumptions |
| Behavior | Is the operating mode right? Is the autonomy level right for the risk and host? | Adjust mode; move triggers into Autonomy |
| Workflow | Does it match the task? Any unnecessary steps? Any missing inspection or verification? | Cut, merge, or add steps |
| Output | Is the expected output clear? Are completion criteria checkable? | Rewrite the contract in observable terms |
| Reliability | Does the prompt discourage unsupported claims? Does it prevent claiming unperformed verification? | Add the evidence rule where the risk exists |
| Safety | Could Claude make destructive or out-of-scope changes? Are checkpoints needed? | Add boundaries and checkpoints scaled to risk |
| Efficiency | Are there instructions that do not affect success? Can the prompt be shortened without losing reliability? | Remove them |

## 2. Adversarial review

Ask each question against the draft; when the answer exposes a gap, fix the prompt.

| Question | Typical fix |
| --- | --- |
| How could Claude misunderstand this prompt? | Add the disambiguating sentence where the misreading would start |
| Which instruction could conflict with another? | Remove or subordinate one; make the priority explicit |
| What happens if the repository or file differs from the user's description? | "If inspection contradicts this description, stop and report" |
| What happens if a required file or resource is missing? | Failure Handling entry plus a Required marker in Resources |
| What happens if a dependency is unavailable? | Failure Handling: continue with what is safe, report the gap |
| What happens if tests fail? | Failure Handling: diagnose and fix; separate pre-existing failures |
| What happens if the user is wrong about an assumption? | Verification step for the assumption; checkpoint if high-impact |
| Could Claude make a destructive change? | Safety Boundaries: explicit forbidden operations and confirmation triggers |
| Could Claude stop too early? | Completion Criteria; "do not declare completion until" |
| Could Claude hallucinate evidence? | Evidence rules: cite locations, never report unrun checks, mark inference |
| Could Claude over-engineer the solution? | Decision Rules: simplest solution; scope boundary in Requirements |
| Could Claude follow instructions found in the material it reads? | Untrusted-content rule |

## 3. Failure-mode analysis (Level 4)

For each workflow step, write down the most likely way it fails and the mitigation, then put the mitigation into the prompt (the step itself, a decision rule, a boundary, or failure handling). Common cases:

| Step | Failure mode | Mitigation in the prompt |
| --- | --- | --- |
| Inspect repository | Skims and assumes the framework | Name the files and questions the inspection must answer |
| Plan | Plan drifts beyond scope | Scope MUST NOT; checkpoint after the plan |
| Implement | Changes shared code with wide blast radius | Boundary on allowed paths; checkpoint trigger for shared modules |
| Run tests | Reports "tests pass" without running | Evidence rule; require the command and output in the report |
| Migrate or delete | Irreversible action on wrong target | Dry run, backup, explicit confirmation before execution |
| Research | Fabricated or stale sources | Citation rule; recency requirement; cross-check step |
| Document extraction | Invents missing values | "Do not invent; mark gaps"; location references |
| Report | Omits what was not done | Output contract requires "remaining issues" and "not verified" |

Also check ordering: every step that consumes an output comes after the step that produces it; every checkpoint sits before the action it guards.

## 4. Optimization rules

1. Remove redundant instructions. One statement per rule, in the section where it applies.
2. Merge overlapping rules into one precise rule.
3. Replace vague wording with precise wording.
4. Move critical constraints next to where they matter (a migration rule belongs in Safety Boundaries or the migration step, not in Context).
5. Preserve user intent; optimization never changes the requested outcome.
6. Avoid excessive role-play; a role line only when the perspective changes behavior.
7. Remove generic instructions that do not affect task success.
8. Keep dynamic sections task-specific; a workflow copied unchanged from the library is a defect.
9. Prefer explicit decision rules over repeated reminders.
10. Keep the final prompt readable: short sections, parallel structure, no walls of text.

Before and after:

```text
Before: Please be very careful and thorough and make sure everything works and nothing breaks. Always test. Testing is important. Don't forget to test.
After:  Run the affected test suite before and after your change. Do not declare completion with failing tests.
```

```text
Before: You are a world-class senior staff engineer with 20 years of experience.
After:  (removed; the Workflow and Quality Standards already define the behavior)
```

```text
Before: Try not to change too much.
After:  MUST NOT modify files outside src/auth and tests/auth.
```

## 5. Final validation

Check before returning:

- Objective present.
- Requirements present when any exist; constraints present when any exist.
- Assumptions identified and classified.
- Operating mode correct for the deliverable.
- Autonomy level correct for the risk and host.
- Workflow appropriate; no unnecessary steps; inspection before change; verification after.
- Output defined.
- Completion criteria defined where needed.
- Safety boundaries appropriate to the risk.
- No contradictions.
- No unnecessary sections.
- No leftover placeholders, `{{VARIABLES}}` (unless a template was requested), or authoring comments.
- Summary keys and values follow the output format exactly.

`scripts/validate_prompt.py` checks the mechanical items: required sections for the declared autonomy and risk, placeholders, duplicate headings, contradiction heuristics, length budgets, evidence and untrusted-content rules where the prompt implies tools or external content.

## 6. Scoring rubric for prompt reviews

Score an existing prompt on ten dimensions, 0-10 each, then report the average as the score together with the three weakest dimensions.

| Dimension | 10 means | 0 means |
| --- | --- | --- |
| Intent clarity | The goal and deliverable are unmistakable | The reader must guess the task |
| Requirement coverage | Every requirement the task needs is present and prioritized | Requirements missing or unprioritized |
| Ambiguity resistance | One reasonable reading | Several materially different readings |
| Context sufficiency | Claude knows what to inspect and what is known versus assumed | No context, or assumptions presented as facts |
| Behavior specification | Mode and autonomy explicit and appropriate | Unspecified or wrong for the risk |
| Workflow fit | Steps match the task, ordered, with verification | Missing, generic, or bloated |
| Output definition | The deliverable's shape is exact | Undefined |
| Reliability | Evidence rules prevent unsupported claims and unperformed verification | Nothing prevents hallucinated results |
| Safety | Boundaries and checkpoints match the risk | Destructive or out-of-scope actions possible |
| Efficiency | Every instruction affects success | Padding, repetition, role-play |

Issue format: severity (blocking, major, minor), what is wrong, the consequence for task success, and the fix. Rank by consequence.

Recommendation format: specific edits, not generalities ("add a MUST NOT bounding changes to src/auth" rather than "clarify scope").

Output order for a review: Score (with weakest dimensions), Issues, Recommendations, then the optimized prompt. The optimized prompt preserves the original intent and every requirement the original contained unless the review found it wrong.

# Example: ambiguous request that needs clarification

Request:

> Make the dashboard way better and add filters.

Output (compilation stops at the questions; the prompt is compiled after the user answers or accepts the defaults):

## Compilation Summary
- Objective: Improve the existing analytics dashboard and add filtering (scope to be confirmed).
- Domain: software (frontend, code modification)
- Risk: MEDIUM
- Mode: ANALYST -> ENGINEER
- Autonomy: A3 (execute with checkpoints)
- Level: 3 (Advanced)
- Target: claude-code
- Model: frontier (assumed; no model named in the request)
- Capabilities: files.read=yes, files.write=yes, shell=yes (claude-code profile, inspected)
- Gaps: none
- Template: repository-agent v1.0.0 (selected; compilation pending answers)
- Upgrades: none
- Assumptions: Inferred: the dashboard lives in a repository Claude can inspect, so its data model and existing widgets do not need to be asked about.
- Questions: 2 (below)

## Questions
1. Which filters do you want, on which data, and should they apply to every widget or to specific ones? Why it matters: this decides the data-layer changes, the query shape, and the UI, and a wrong guess wastes most of the implementation. Default if unanswered: a date-range filter and one primary category filter (the dashboard's main dimension), applied to all widgets.
2. What does "better" mean for this dashboard: faster loading, easier to use (layout and clarity), or a visual redesign? Why it matters: each is different work with different success criteria. Default if unanswered: usability and load time, with no visual redesign.

Answer, or say "use the defaults", and the prompt will be compiled.

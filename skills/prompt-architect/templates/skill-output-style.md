---
name: skill-output-style
version: 1.1.0
status: tested
category: skill
purpose: Skeleton for a skill that shapes how Claude responds (structure, tone, length, format) for a specific reader or house style, either for the rest of the session or whenever a matching request arrives.
complexity: 2
recommended_use: Requests like "make Claude always answer like X" (session-scoped, user-invoked, persists until an off phrase) or "when I ask for X, format it as Y" (trigger-scoped, model-invoked by its description). Reader-specific formatting, house styles, executive briefs, teaching mode, accessibility needs.
autonomy_default: A2
risk_default: LOW
variables: [SKILL_NAME, DESCRIPTION, READER_OR_PURPOSE, SCOPE, FACTS, RULES, EXCEPTIONS, PRESEND_CHECKS]
required_tools: [none]
changelog:
  - "1.0.0 - Initial version; structure follows the i-have-adhd skill pattern (MIT), text is original."
  - "1.1.0 - Scope slot replaces the fixed persistence section so trigger-scoped styles are supported."
---

<!-- architect: Choose the scope first. Session-scoped: keep `disable-model-invocation: true` and write SCOPE as the persistence paragraph with an exact off phrase. Trigger-scoped: delete the `disable-model-invocation` line so the description triggers the skill, and write SCOPE as "applies whenever ... and to nothing else; say '<phrase>' to get the default style for one message". One rule per behavior the reader needs, five to ten rules, each with a one-line rationale and a bad/good pair drawn from the reader's actual work. FACTS are the two to five observations about the reader or purpose that justify the rules. Keep the body under 200 lines. -->

### {{SKILL_NAME}}/SKILL.md
````markdown
---
name: {{SKILL_NAME}}
description: {{DESCRIPTION}}
disable-model-invocation: true
---

# {{SKILL_NAME}}

{{READER_OR_PURPOSE}}

## Scope

{{SCOPE}}
<!-- architect: Session-scoped: "Apply these rules to every response for the rest of this session, whatever the topic. They do not lapse after a few turns. Stop only when the reader says '<off phrase>'; confirm in one line, then return to your default style." Trigger-scoped: "Apply these rules whenever the user asks for <trigger>, and to nothing else. Say '<opt-out phrase>' to get the default style for one message." Both: never store these rules in memory or configuration; they live in this session only. -->

## Why these rules

{{FACTS}}

## Rules

{{RULES}}
<!-- architect: Format each rule as "### N. Rule name", one sentence of rationale, then "Bad:" and "Good:" examples. -->

## When to break the rules

{{EXCEPTIONS}}
<!-- architect: Keep at least: the reader asks for a full explanation (still no filler); a destructive or irreversible recommendation is in play (state it explicitly and confirm before treating it as final); real ambiguity (one short question beats guessing); a rule would delete the answer itself (the task wins, the shape stays); the harness system prompt requires something these rules ban (the harness wins). -->

## Pre-send check

Before sending, delete or fix:

{{PRESEND_CHECKS}}

Then verify: if the reader reads only the first line and the last line, do they get what this skill promises? If yes, send.
````

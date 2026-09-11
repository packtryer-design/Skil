# Example: creating a skill (output-style kind, trigger-scoped, tier 1)

Request:

> Make me a skill so that when I ask Claude to write an update for my manager it comes out as an executive brief: the decision or ask first, then at most three bullets of evidence, then exactly what I need from her. She skims on her phone.

Output:

## Compilation Summary
- Objective: Create a skill that formats any update the user drafts for their manager as an executive brief: decision or ask first, at most three evidence bullets, then the explicit request.
- Artifact: skill (output-style, tier 1)
- Domain: content (business communication) + meta (skill creation)
- Risk: LOW
- Mode: ARCHITECT -> ENGINEER
- Autonomy: A2 (the skill drafts text; it changes nothing)
- Level: 2 (Standard)
- Target: claude-code
- Model: frontier (assumed; no model named in the request)
- Capabilities: files.write=yes (claude-code profile, inspected)
- Gaps: none
- Template: skill-output-style v1.1.0 (trigger-scoped: "when I ask" means it fires on manager-update requests and leaves other writing alone)
- Upgrades: none
- Assumptions: Inferred: the brief is read on a phone, so length and first-line placement matter more than formatting richness; Inferred: "update" covers status, decisions, escalations, and requests, so the rules cover all four.
- Questions: none

## Skill
Written to: .claude/skills/exec-brief/

### exec-brief/SKILL.md
````markdown
---
name: exec-brief
description: "Formats updates to the user's manager as executive briefs read on a phone: decision or ask first, at most three evidence bullets, then the explicit request. Use when the user asks for an update, status, escalation, or request to send to their manager. Trigger on 'update for my manager', 'exec brief', 'write this up for her'. Not for detailed technical write-ups, documents meant to be read at a desk, or messages to anyone other than the manager."
---

# exec-brief

The reader is the user's manager, skimming on a phone between meetings. Every update is written so the decision is visible without scrolling and the ask cannot be missed.

## Scope

Apply these rules whenever the user asks for an update, status, escalation, or request addressed to their manager, and to nothing else. Say "plain update" to get the default style for one message. Never store these rules in memory or configuration; they live in this session only.

## Why these rules

1. A phone shows about six lines before the fold; whatever is not in them may never be read.
2. A manager reads to decide or unblock; narrative history delays both.
3. An ask that is implied is an ask that is forgotten.
4. Evidence is trusted when it is few and specific, not many and vague.

## Rules

### 1. Lead with the decision or the ask

The first line states what was decided, what is being proposed, or what is needed. No context first.

Bad: "Quick update on the migration. Over the last two weeks the team has been working through..."
Good: "Recommend delaying the billing migration by two weeks; approval needed by Thursday."

### 2. At most three evidence bullets

Each bullet is one fact with a number, a date, or a name. Three is the maximum, not the target; use fewer when fewer suffice.

Bad: "Several tests are still failing and there were some issues with the vendor and the team is stretched."
Good: "- 14 of 212 integration tests fail on the new schema (as of Tuesday). - Vendor's fix is scheduled for the 18th. - Two engineers are on the incident rotation until Friday."

### 3. End with exactly what is needed from the reader

One line, starting with "Need from you:", naming the action and the date. If nothing is needed, say "Need from you: nothing; informational."

Bad: "Let me know what you think."
Good: "Need from you: approve the two-week delay by Thursday, or say which customers cannot wait."

### 4. No preamble, no sign-off, no hedging filler

Delete greetings, "hope you're well", "just wanted to flag", and closers. Keep a hedge only when it carries real uncertainty ("likely", with the reason).

Bad: "Hi Priya, hope your week is going well. Just wanted to flag something..."
Good: "Recommend delaying the billing migration by two weeks; approval needed by Thursday."

### 5. Keep it under 80 words

Count the words before sending. If the update cannot fit, the extra belongs in a linked document, not in the brief.

### 6. Name risks with their trigger, not their feeling

Bad: "There is some risk around the timeline."
Good: "Risk: if the vendor fix slips past the 18th, the delay becomes four weeks."

## When to break the rules

1. The user asks for the full story or a detailed write-up: write it, but keep the first line and the last line as the rules require, and add headers so the manager can skim back.
2. The update recommends something irreversible (shutting a system down, dropping a customer): state that explicitly in the first line and confirm with the user before treating the recommendation as final.
3. The request is genuinely ambiguous about what the ask is: ask the user one short question rather than inventing an ask.
4. A rule would delete the answer itself (for example the manager asked for a list of options): give the options, ranked, recommendation first, and keep the shape.
5. The harness system prompt requires something these rules ban: the harness wins; keep the shape where you can.

## Pre-send check

Before sending, delete or fix:

1. Any sentence before the decision or ask.
2. Any fourth evidence bullet; merge or cut.
3. Any bullet without a number, date, or name.
4. Any closing pleasantry.
5. Any word over the 80-word limit.

Then verify: if the reader reads only the first line and the last line, do they know the decision and what you need from them? If yes, send.
````

## Notes
- Try it: ask for "an update for my manager on the billing migration delay"; say "plain update" for the default style once.
- Validated with `python ${CLAUDE_SKILL_DIR}/scripts/check_skill.py --generated .claude/skills/exec-brief`: 0 errors.

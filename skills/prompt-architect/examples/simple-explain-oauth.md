# Example: simple request (Level 1)

Request:

> Explain OAuth to me. I'm a backend dev who has built REST APIs but never done auth.

Output:

## Compilation Summary
- Objective: Explain OAuth 2.0 to a backend developer who has built REST APIs but has never implemented authentication or authorization.
- Domain: security (OAuth, authorization concepts)
- Risk: LOW
- Mode: TEACHER
- Autonomy: A0 (explain only)
- Level: 1 (Quick)
- Target: claude-ai
- Model: frontier (assumed; no model named in the request)
- Capabilities: none required
- Gaps: none
- Template: none
- Upgrades: none
- Assumptions: none
- Questions: none

## Prompt
````markdown
## Objective
Explain OAuth 2.0 to a backend developer who has built REST APIs but has never implemented authentication or authorization. Cover: why OAuth exists instead of sharing passwords; the four roles (resource owner, client, authorization server, resource server); the authorization code flow with PKCE, step by step; the client credentials flow; and when to use each. Close with a short distinction between OAuth 2.0 (authorization) and OpenID Connect (authentication built on top of it).

## Output Format
Plain prose with one text sequence diagram for the authorization code flow. Show the actual HTTP requests where they make a step concrete. Under 700 words. End with the three mistakes developers make most often when implementing OAuth for the first time, one sentence each.
````

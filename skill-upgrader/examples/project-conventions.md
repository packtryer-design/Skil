---
name: project-conventions
description: How this repository is built, tested, and reviewed, so generated prompts use the real commands.
domains: [software]
targets: [claude-code, coding-agent]
---

## Facts

- Package manager: pnpm. Never npm or yarn; the lockfile is pnpm's.
- Tests: `pnpm test` runs the unit suite; `pnpm test:e2e` needs the dev server on port 3000.
- Lint and types: `pnpm lint` and `pnpm typecheck`; both must pass before a change is done.
- Layout: application code under `src/`, tests beside the code as `*.test.ts`, shared types in `src/types/`.
- Branches: feature work on `feat/<ticket>`; `main` is protected.

## Rules

- A change is not complete until `pnpm lint`, `pnpm typecheck`, and `pnpm test` have been run in this session and their output recorded.
- New code follows the pattern of the nearest existing module before introducing a new one.
- Anything touching `src/auth/` gets a checkpoint before the first edit.

## Review checklist

Before reporting done: no new dependency without saying why; no `any` in TypeScript; every new branch of logic has a test beside it.

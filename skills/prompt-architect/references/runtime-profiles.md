# Runtime Profiles

Starting capability profiles for the runtimes an artifact is most often compiled for. Used at Stage 2.5 when the target is not the current environment and so cannot be inspected. Read with `references/capabilities.md`, which defines the vocabulary and the discovery order.

These are **defaults, not facts about the user's install**. Every one of these runtimes can be configured to have more or less than the table says, and the columns below describe the out-of-the-box state as of 2026-09. A profile is the starting point; a user declaration or an inspection beats it, and anything still material and uncertain is `unknown`, not a guess.

## The distinction these tables exist to preserve

> A model that can request a tool call is not a runtime that has tools.

Most local runtimes support the tool-calling *protocol*: the model emits a structured request and the runtime hands it to the caller's program. If nobody implemented that program, no tool exists. Ollama, LM Studio, llama.cpp and vLLM are all in this position by default. Writing "use the file tool to read the config" for one of them produces a model that emits a tool call into a void, and then reports success.

The same distinction runs the other way: a runtime can provide a capability the model handles badly. Capability means available, not reliable.

## claude-code

Coding agent in a terminal or IDE, with the user's project mounted.

| Capability | Default | Notes |
| --- | --- | --- |
| `files.read` `files.write` | yes | Scoped to the working directory and what permissions allow |
| `shell` `code.run` | yes | Subject to the permission prompt and `allowed-tools` |
| `git` | yes | Through `shell` |
| `web.search` `web.fetch` | yes | Can be disabled by configuration or policy |
| `browser` `db` | no | Unless an MCP server provides them |
| `vision` | yes | Images can be supplied |
| `structured.output` | yes | |
| `mcp` | unknown | Per install; inspect rather than assume |

This is the one profile you can usually inspect instead of assuming, because it is normally the environment the Architect is running in.

## claude-ai

The chat product, in a browser or desktop app.

| Capability | Default | Notes |
| --- | --- | --- |
| `files.read` | yes | Attachments and connected sources only; no access to the user's filesystem |
| `files.write` | no | Output is the message, plus artifacts the user copies |
| `shell` | no | |
| `code.run` | unknown | A sandboxed analysis tool may be available; it cannot reach the user's machine |
| `web.search` `web.fetch` | yes | Can be off for the account |
| `vision` `image.gen` | yes / no | |
| `db` `git` `browser` | no | Unless a connector provides them |
| `mcp` | unknown | Connectors vary per account |

The trap here is `files.write`. The user can see a file in the conversation and assume the model changed it; it did not.

## coding-agent

Cursor, Codex, Cline, Continue, Copilot agent mode and similar: an agent with the repository open.

| Capability | Default | Notes |
| --- | --- | --- |
| `files.read` `files.write` | yes | The open workspace |
| `shell` `code.run` | yes | Often behind an approval prompt |
| `git` | yes | |
| `web.search` `web.fetch` | unknown | Varies by product and settings |
| `browser` `db` | no | Unless an extension or MCP server provides them |
| `vision` | unknown | Varies by the selected model |
| `mcp` | unknown | Widely supported, rarely configured by default |

Close enough to `claude-code` that the same artifact usually ports. Do not name Claude Code's specific tools in an artifact aimed here; describe the capability instead.

## open-webui

Self-hosted browser front-end, usually over Ollama. **The most commonly misjudged profile**, because it looks like a full agent and starts as a chat box.

| Capability | Default | Notes |
| --- | --- | --- |
| `files.read` | partial | Documents the user uploads are put into context or retrieved from; the model has **no** access to the user's filesystem |
| `files.write` | no | |
| `shell` | no | |
| `code.run` | no | A code interpreter feature exists and is off until enabled |
| `web.search` `web.fetch` | no | Built-in web search exists and is off until configured with a provider |
| `browser` `db` `git` | no | |
| `vision` | depends | On the served model, not on Open WebUI |
| `structured.output` | depends | On the backend serving the model |
| `mcp` | no | Tool servers can be added; none by default |
| `network` | server-side | The server can reach the network; that is not the model having web access |

Compile for the default unless the user says which features they enabled, and ask if it is blocking. "Documents are in context" is `files.read` for one conversation, never `files.write`, and never a live view of a directory.

## ollama

The local runtime itself, through `ollama run` or its API.

| Capability | Default | Notes |
| --- | --- | --- |
| everything except the two below | no | It serves a model; it provides no tools |
| `structured.output` | yes | Schema-constrained output is supported |
| `vision` | depends | On the model |

Tool calling is supported as a protocol for models that emit it, but the caller implements every tool. Unless the user has written that program, treat all tools as absent. Context window is whatever `num_ctx` is set to, and the default is small enough to truncate a long system prompt silently.

## lm-studio

Also covers Jan, Msty and similar desktop apps serving an OpenAI-compatible endpoint.

| Capability | Default | Notes |
| --- | --- | --- |
| everything except the two below | no | Same position as Ollama: it serves the model |
| `structured.output` | yes | |
| `vision` | depends | On the model |

Some of these apps add document attachment or a plugin system; treat those as `unknown` until the user says otherwise.

## api-no-tools

A program calling a model endpoint directly, with no tool layer.

| Capability | Default | Notes |
| --- | --- | --- |
| everything | no | The program may have capabilities; the model does not |
| `structured.output` | yes | |
| `vision` | depends | On the model |

Two consequences beyond the capability table: there is no human in the loop, so the artifact must state assumptions and take the safe path instead of asking; and the consumer is usually a program, so the output contract has to be exact.

## custom-agent

Anything the user built themselves.

| Capability | Default |
| --- | --- |
| everything | unknown |

Nothing can be assumed. Use the declared capabilities, name only tools the user named, and write every uncertain capability conditionally. If a required capability is unknown and the work is A2 or above, that is a legitimate clarification question under the Stage 4 gate.

## Confirming a profile you cannot inspect

When the target is elsewhere and a capability is both required and uncertain, the cheapest resolution is a probe the user runs once, not a research detour:

- Execution: ask the target to run the smallest real command and report the exact output. A runtime without execution will describe what the output would be, which is the failure this whole reference exists to prevent.
- File access: ask it to print the first line of a named file.
- Web: ask it for something that changes daily and cannot be recalled.
- Vision: supply an image and ask for something only visible in it.

Record the answer as `inspected` in a saved profile so the probe is not needed again.

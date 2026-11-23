# Claude Code execution adapter

Read only in Claude Code. Apply the shared runtime contract and skill protocol.

## Skill loader and questions

Use the `Skill` tool with `skill: lorestrom:<name>` and the original arguments.
Do not shadow the loaded skill's behavior. Use `AskUserQuestion` for required
user decisions when available, otherwise ask directly and wait.

## Lorestrom tools

A connected Lorestrom MCP server's tools appear as `mcp__<server>__<tool>`, where `<server>`
is whatever name the user gave it (for example `mcp__lorestrom__find_docs`). Find the server
by its tools, as the storage contract says, never by its name alone. If no such tools are
listed, they may be deferred: search the tool list for `find_docs` before deciding that no
server is connected. Connecting one is the user's step:
`claude mcp add --transport http --client-id <client id> --callback-port 53682 lorestrom https://www.lorestrom.com/mcp/o/<org id>`,
then `/mcp` to authenticate, with the client id from their organization's Lorestrom setup
instructions.

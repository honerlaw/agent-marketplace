# Codex execution adapter

Read only in local Codex app, CLI or IDE sessions. Apply the shared runtime contract and
skill protocol. The helper needs Git, Python 3.9+ and a POSIX shell.

## Skill loader and questions

Use the available skill-loading capability if provided. Otherwise read the named
`skills/<name>/SKILL.md` from this loaded plugin root, then its required references, and
execute its protocol in the current agent with the original arguments. User-facing examples
use `$lorestrom:<name>`; use the actual qualified name exposed by the skill selector if a
host renders the namespace differently.

Use an available question tool when appropriate to the current collaboration mode, otherwise
ask the required question directly and wait. Respect prior user authorization and sandbox
approvals. A fallback answer is not permission.

## Lorestrom tools

Call a connected Lorestrom MCP server's tools by the names the storage contract uses, through
however the host exposes MCP tools. Find the server by its tools, never by its name alone.
Connecting one is the user's step, following their organization's Lorestrom setup
instructions for the endpoint `https://www.lorestrom.com/mcp/o/<org id>`.

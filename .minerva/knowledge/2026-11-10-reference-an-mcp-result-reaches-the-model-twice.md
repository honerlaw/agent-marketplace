# An MCP tool result reaches the client twice, so a size cap on the body is not a cap on context

**Date**: 2026-11-10
**Type**: reference
**Theme**: mcp-servers
**Summary**: mcp 2.x returns a dict result as structured content and a pretty-printed text copy, about 3x the compact JSON size
**Context**: .minerva/work/2026-11-10-add-clerk-mcp-server (see git history if the worktree has been cleaned up)

## Context
`mcp/clerk/` cut a response body at 256 KiB of compact JSON so a large user page could not flood
the model's context.

## Finding
Under `mcp` 2.3.0, a tool returning a dict comes back as `structured_content` **and** as a
`TextContent` holding the same value pretty-printed. The code review measured a 260,177-character
compact body arriving as 559,230 characters of text plus the structured copy, so roughly three
times the cap reached the client, and the cap's "ask for less" note never fired below it.

## Implications
- Size a body cap at about a third of the context budget you intend (`mcp/clerk/` uses 64 KiB),
  and say in the README what the cap counts.

## Related
- [[2026-09-25-reference-mcp-python-sdk-2x-server-facts]] — the other SDK facts these servers rely on
- [[2026-11-10-reference-clerk-backend-api-facts-for-mcp-servers]] — the server where it was measured

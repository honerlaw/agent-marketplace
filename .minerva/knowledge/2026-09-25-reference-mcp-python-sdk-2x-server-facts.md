# MCP Python SDK 2.x server facts that shaped the first mcp/ server

**Date**: 2026-09-25
**Type**: reference
**Summary**: mcp 2.x renamed FastMCP to MCPServer, uses httpx2, caps HTTP bodies at 4 MiB
**Context**: .minerva/work/2026-09-25-add-openai-mcp-server (see git history if the worktree has been cleaned up)

## Context
`mcp/openai/` was built on `mcp` 2.2.0 under `mypy --strict` and 100% branch coverage. Most
examples online still target 1.x.

## Finding
- `FastMCP` is gone. Importing `mcp.server.fastmcp` raises; use
  `from mcp.server.mcpserver import MCPServer`. Tool errors are
  `mcp.server.mcpserver.exceptions.ToolError` and come back to the client as `is_error` results.
- The SDK's HTTP stack is `httpx2` (pydantic's httpx successor, a hard dependency). Using it for
  outbound calls avoids a second HTTP library. `httpx2.MockTransport` works for tests.
- `mcp.Client` connects to an `MCPServer` instance in-process, to a `StdioServerParameters`
  subprocess, or to `streamable_http_client(url, http_client=httpx2.AsyncClient(headers=...))` for
  authenticated HTTP. All three are usable in pytest (anyio marker).
- `streamable_http_app()` caps request bodies at 4 MiB by default (`max_request_body_size`),
  which silently bounds base64 uploads. It auto-enables DNS-rebinding protection only when bound to
  localhost.
- `custom_route` is an untyped decorator, so `mypy --strict` rejects the decorator syntax.
  Register the route by calling it: `server.custom_route(path, methods=[...])(handler)`.
- Tool closures defined inside one builder count toward that function's McCabe complexity. Split
  registration into small functions to stay under a limit of 5.

## Implications
- New servers under `mcp/` should copy `mcp/openai/`'s patterns rather than 1.x tutorials.

## Related
- [[2026-09-25-decision-mcp-servers-expose-generic-spec-driven-tools]] — the server these facts come from

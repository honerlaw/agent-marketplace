# MCP servers for large APIs expose a few generic, spec-driven tools, not one tool per endpoint

**Date**: 2026-09-25
**Type**: decision
**Summary**: API-wrapping MCP servers expose generic request tools plus OpenAPI discovery, not per-endpoint tools
**Context**: .minerva/work/2026-09-25-add-openai-mcp-server (see git history if the worktree has been cleaned up)

## Context
The first server under `mcp/` had to give an LLM "full control" of the OpenAI REST API (352
operations on the current spec). Three shapes were weighed by a 3/3 panel: one generated tool per
OpenAPI operation, a hand-curated subset, or a handful of generic tools.

## Finding
Five generic tools reach every endpoint: a JSON request tool, a multipart upload tool, a binary
download tool, and two discovery tools that list and describe operations from the vendor's
published OpenAPI spec (loaded lazily, so requests still work when the spec is unreachable).
Per-operation tools were rejected because hundreds of tools exceed client tool limits (~100–128 in
several clients) and flood context every turn. A curated subset fails "full control" and goes stale
as the vendor adds endpoints.

## Implications
- A future `mcp/<name>/` server wrapping a large or fast-moving API should start from this shape
  (see `mcp/openai/`). Curated tools are only right when the goal is a narrow capability.
- Discovery output must be sized for context: expand `$ref`s shallowly by default and let the
  model ask for more ([[2026-09-25-reference-openai-openapi-spec-source-and-size]]).
- Generic tools make the path argument a security boundary. Every path-taking tool has to share one
  validator, and the tests have to cover each tool, not just one.

## Related
- [[2026-09-25-pattern-a-server-local-path-argument-is-a-remote-file-primitive]] — the security consequence of generic file arguments
- [[2026-09-25-reference-openai-openapi-spec-source-and-size]] — the spec the discovery tools read
- [[2026-08-11-decision-ci-runs-the-whole-suite]] — why `mcp.yml` discovers servers by glob rather than a list

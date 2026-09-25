# OpenAI's OpenAPI spec: use the main branch, and expand $refs one level at a time

**Date**: 2026-09-25
**Type**: reference
**Summary**: openai-openapi main branch lists 352 operations; manual_spec is stale; deep $ref expansion reaches megabytes
**Context**: .minerva/work/2026-09-25-add-openai-mcp-server (see git history if the worktree has been cleaned up)

## Context
The OpenAI MCP server's discovery tools read OpenAI's published OpenAPI spec from the
`openai/openai-openapi` GitHub repository.

## Finding
- `main/openapi.yaml` is current (OpenAPI 3.1, 352 operations as of 2026-09-25) and parses with
  PyYAML's `CSafeLoader` in under a second. The `manual_spec` branch was last updated
  2025-04-29 and lists 148 operations, missing `/conversations`, `/videos` and `/containers`.
- Schemas are deeply nested and self-referential. Inlining `$ref`s for `POST /responses`
  gives about 16 KB at depth 1, about 55 KB at depth 2, about 165 KB at depth 4, and over 1 MB at
  depth 6. `POST /chat/completions` is about 21 KB at depth 1. Listing every operation as one
  line each is about 22 KB.

## Implications
- Default discovery to depth 1, leaving unexpanded refs as markers, and let the caller ask deeper.
  A recursion bound is mandatory because schemas reference themselves.
- Point spec URLs at `main`, and re-check that assumption if discovery ever returns suspiciously
  few operations.

## Related
- [[2026-09-25-decision-mcp-servers-expose-generic-spec-driven-tools]] — the discovery tools that read this spec
- [[2026-09-25-reference-reddit-ads-api-v3-facts-for-mcp-servers]] — see also

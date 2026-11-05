# When every API path is a fixed literal, an MCP server dispatches by operation name and takes no path

**Date**: 2026-11-05
**Type**: decision
**Theme**: mcp-servers
**Summary**: Fixed-path APIs get an operation-name request tool; no caller path, host or header, so no validator
**Context**: .minerva/work/2026-11-05-add-microsoft-ads-mcp-server (see git history if the worktree has been cleaned up)

## Context
The earlier generic ads servers (openai-ads, reddit-ads, google-ads, meta-ads) take a caller
`path` (and sometimes headers) and guard it with a validator, because their APIs put ids in the
path. Microsoft Advertising v13 REST has 291 operations whose paths are all fixed literals with
no path parameters (`/CampaignManagement/v13/Campaigns/QueryByAccountId`); ids travel in the
JSON body or in identity headers.

## Decision
`microsoft_ads_request(operation, body?, customer_id?, account_id?)` takes an operation **name**,
resolved case- and underscore-insensitively (and with an optional `Service.` prefix) against the
committed catalog. The catalog supplies the method and path, and a fixed per-environment table
supplies the host. The caller supplies no path, host, query or header; the two per-call ids are
digit-checked before they become headers. Approach review weighed "path + validator" (option C)
and found it dominated: equal reach, strictly more attack surface.

The decision constrains the request tool's *shape*, not the generic-tools decision it sits
under: the server still exposes a few generic tools plus catalog discovery
(`list_operations`, `describe_operation`, `describe_type`), not one tool per endpoint.

## Consequences
- There is no path validator to get wrong; the security boundary (`safety.py`) is only the id
  check and the download-URL allowlist.
- An operation Microsoft adds after the catalog pin cannot be called until a re-pin; a new field
  on an existing operation can, because bodies pass through as written.
- The catalog's operation names must be unique after normalization; the builder refuses a
  collision rather than letting one shadow another.

## Related
- [[2026-09-25-decision-mcp-servers-expose-generic-spec-driven-tools]] — the decision this narrows the request tool's shape under
- [[2026-09-25-decision-mcp-server-tool-shape-follows-api-size-and-stability]] — why the tool count stays small for a 291-operation API
- [[2026-11-05-reference-microsoft-advertising-api-facts-for-mcp-servers]] — the fixed-path facts that made this possible

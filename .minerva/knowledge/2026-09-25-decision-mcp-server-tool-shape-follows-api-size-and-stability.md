# An MCP server's tool shape follows its API's size and stability

**Date**: 2026-09-25
**Type**: decision
**Summary**: Small, stable APIs get one typed MCP tool per operation; large or fast-moving APIs get generic tools
**Context**: .minerva/work/2026-09-25-add-google-search-console-mcp-server (see git history if the worktree has been cleaned up)

## Context
The second server under `mcp/` wraps the Google Search Console API, which has 10 live operations
and has added one resource in about four years. The first server (`mcp/openai/`) wraps a
352-operation API with generic request tools plus OpenAPI discovery. A 3/3 panel weighed three
shapes for the new server: copy the generic shape, one typed tool per operation, or typed tools
plus a generic escape hatch.

## Finding
Typed per-operation tools were chosen for Search Console. This applies the "narrow capability"
carve-out in the generic-tools decision rather than reversing it. The generic shape exists to
stay under client tool limits (about 100–128) and to keep up with a vendor that adds endpoints
often, and neither pressure applies to a 10-operation API. The typed shape has three advantages
here:
- The tool schema carries the API's field names and enums, so the model needs no discovery turns.
- The server builds every URL from a fixed template. Callers never supply a path, so there is no
  path validator to get wrong.
- Values that must be percent-encoded into the path (a `siteUrl` such as
  `https://example.com/`) are encoded by the server. A generic path tool would make the model
  encode them itself, and `mcp/openai`'s `check_path` rejects an encoded `://`.

The generic escape hatch was rejected because it would bring back a caller-controlled path for
endpoints that don't exist yet.

## Implications
- For a new `mcp/<name>/` server, count the API's live operations and look at how often it adds
  endpoints. Tens of stable operations point to typed tools; hundreds, or frequent additions,
  point to the generic shape. `mcp/README.md`'s "Adding a server" states this rule.
- The cost of typed tools is staleness: a new endpoint needs a code change. Record the
  discovery or spec revision the tools were built against (the Search Console README does), and
  revisit the shape if the API grows materially.
- Typed tools still need the path-segment guard described in
  [[2026-09-25-pattern-percent-encoding-does-not-confine-a-dot-segment]].

## Related
- [[2026-09-25-decision-mcp-servers-expose-generic-spec-driven-tools]] — builds on
- [[2026-09-25-pattern-percent-encoding-does-not-confine-a-dot-segment]] — the guard typed tools still need
- [[2026-08-22-pattern-a-denylist-safety-guard-fails-open]] — why server-built URLs beat validating caller paths

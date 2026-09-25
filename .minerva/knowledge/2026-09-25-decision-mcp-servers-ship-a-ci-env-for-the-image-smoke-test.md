# Every MCP server ships a ci.env, so the image smoke test names no server's variables

**Date**: 2026-09-25
**Type**: decision
**Summary**: mcp.yml's docker smoke test runs each image with --env-file mcp/<server>/ci.env
**Context**: .minerva/work/2026-09-25-add-reddit-ads-mcp-server (see git history if the worktree has been cleaned up)

## Context
`.github/workflows/mcp.yml` discovers servers by globbing `mcp/*/pyproject.toml`, so a new
server needs no workflow edit. But its `docker` job started every image with hard-coded
`-e OPENAI_API_KEY=sk-ci -e MCP_AUTH_TOKEN=ci`. A server that refuses to start without its own
credentials would fail `/healthz`, as the Reddit Ads server does without Reddit credentials.
The Google Search Console server passed only because it can start without credentials.
A 3/3 panel chose the fix over two alternatives: listing each server's variables in the
workflow, or letting servers start without credentials.

## Finding
Each server ships `mcp/<name>/ci.env` holding dummy, non-secret values that let its image start.
The smoke step runs `docker run --env-file "${{ matrix.server }}/ci.env"`. A server without the
file fails the job loudly. `openai`, `google-search-console` and `reddit-ads` all have one. No
server calls its vendor at startup, so dummy values are enough for `/healthz`. The file is not
copied into the image, because each Dockerfile copies only `pyproject.toml`, `README.md` and
`src`.

## Implications
- Adding a server means adding its `ci.env`, as `mcp/README.md`'s contract and "Adding a server"
  steps now say. The workflow stays server-agnostic.
- Keep config validation fail-fast. Don't relax a server's startup checks to satisfy CI; give it
  dummy values instead.
- Never put a real secret in `ci.env`, because it is committed.

## Related
- [[2026-08-11-decision-ci-runs-the-whole-suite]] — builds on
- [[2026-08-11-pattern-the-enumeration-is-what-fails]] — the hard-coded variable list was an enumeration waiting to fail
- [[2026-09-25-decision-mcp-servers-expose-generic-spec-driven-tools]] — see also

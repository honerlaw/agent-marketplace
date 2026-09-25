# Proposal: add-reddit-ads-mcp-server

**Date**: 2026-09-25
**Status**: Draft

## Goal

Add a second server to `mcp/`: `mcp/reddit-ads/`, an MCP server that gives an LLM client **full
control of the Reddit Ads API v3** (`https://ads-api.reddit.com/api/v3`) using the operator's
Reddit OAuth app credentials. Build it the same way as `mcp/openai/`: a few generic tools driven by
the spec, strict quality gates, and three ways to run (stdio, streamable HTTP, Docker, including
GHCR publishing through the existing `mcp.yml`).

## Why

The user asked for "a reddit ads mcp server similar to how we implemented the openai one". Knowledge
`2026-09-25-decision-mcp-servers-expose-generic-spec-driven-tools` says a server wrapping a large or
fast-moving API should start from that shape. The Ads API has 108 operations across 80 paths
(campaigns, ad groups, ads, posts, audiences, pixels, reports, targeting, CAPI, …) and changes
often. For example, `conversion_pixel_id` becomes required for campaign budget optimization
campaigns starting July 13th, 2026, per the spec's own operation description. Reddit publishes an official machine-readable spec at
`https://ads-api.reddit.com/api/v3/openapi.json` (OpenAPI 3.1, about 1 MB, no auth needed), so
spec-driven discovery works here just as it does for OpenAI. The existing open-source Reddit Ads
MCP servers are all hand-written tool subsets.

## Approach

**Layout.** `mcp/reddit-ads/` is a Python package `reddit_ads_mcp` (console script
`reddit-ads-mcp`, GHCR image `ghcr.io/<owner>/reddit-ads-mcp`). It has the same files as
`mcp/openai/`: `pyproject.toml` with the strict gate configuration copied verbatim, `Makefile`,
`Dockerfile`, `docker-compose.yml`, `.env.example`, `.dockerignore`, `README.md` and `tests/`. It
uses the same stack: `mcp>=2.2,<3` (`MCPServer`), `httpx2`, `uvicorn` and hatchling. `pyyaml` is
dropped because the spec is JSON. Code is **copied and adapted** from `mcp/openai/`, not shared:
the `mcp/README.md` contract makes each server self-contained, with its own Docker build context
and CI matrix entry. `mcp/README.md` and the root `README.md` "MCP servers" table each gain a row.

**Tool surface: four tools.**
1. `reddit_ads_request(method, path, query?, body?, headers?)` sends any JSON request relative to
   the base URL. `method` is one of GET/POST/PATCH/DELETE, the only methods the spec uses: POST for creates and
   for query-style reads (`/query`, `/reports`, `/history`, estimates), PATCH for updates and DELETE for deletes. The result contains:
   - the status
   - an allowlist of response headers: `content-type`, `ratelimit`, `ratelimit-policy` and
     `retry-after` (Reddit's rate-limiting guide documents the IETF `RateLimit` headers, not `x-ratelimit-*`; the spec itself
     declares no response headers)
   - the JSON body, or text

   Body envelopes (`{"data": …}`) are passed through untouched.
2. `reddit_ads_follow_page(url, method="GET", body?)` follows a `pagination.next_url` or
   `previous_url` from an earlier response. The spec says these URLs "should be followed directly"
   and warns against rebuilding them from their query parameters. `page.token` is a shared query
   parameter on 36 operations, but its encoding inside the URL is Reddit's to change. Four paginated
   endpoints are POSTs: `/ad_accounts/{id}/reports`, `/ad_accounts/{id}/history`,
   `/businesses/{id}/ad_accounts/query` and `/businesses/{id}/funding_instruments/query`. Each
   declares `page.token` as a query parameter alongside its JSON body. So the tool takes
   `method` (`GET` or `POST`) and, for POST, the original request `body` re-sent unchanged. The tool
   description says exactly that, and adds that re-sending the body is inferred from the spec's shape
   rather than confirmed against the live API.
   `reddit_ads_request`'s `path` keeps refusing absolute URLs, so this separate tool accepts one
   absolute URL, validated by its own allowlist guard in `safety.py`, `check_page_url`. It
   parses the URL with `urlsplit` and requires:
   - scheme and netloc exactly equal to `REDDIT_ADS_BASE_URL`'s, so no userinfo, port or host
     change is possible
   - a path under the base path, whose base-relative remainder passes the same `check_path`
   - no fragment

   It then sends the request to the relative path plus the URL's query string verbatim, so the
   access token only ever goes to the base URL.
3. `reddit_ads_list_endpoints(text_filter?)` returns `METHOD /path — summary` lines from the spec
   (about 6.7 KB for all 108 operations).
4. `reddit_ads_describe_endpoint(method, path, depth=1)` returns parameters, request body, 2xx
   responses and the **required OAuth scope** (from the operation's `security`, or `null` when no requirement is
   declared, whether the key is absent or empty; one operation has no `security` key at all, `GET /targeting/communities/suggestions`), with `$ref`s
   inlined `depth` levels (clamped to 1–6). Reddit's operation descriptions embed a rendered HTML
   rate-limit panel with inline SVG, so describe strips HTML tags and collapses whitespace in
   `description` fields. That takes a description from 2.8 KB to 1.2 KB. POST
   `/ad_accounts/{id}/campaigns` is about 14 KB at depth 1 and 37 KB fully expanded.

There are **no multipart or download tools**. Every request and response body in the spec is
`application/json`. Creative uploads are URL-based: Reddit fetches `media.url` and the client polls
the upload. So there are no server-local path arguments at all, which removes the whole class of
risk in `2026-09-25-pattern-a-server-local-path-argument-is-a-remote-file-primitive`.

The spec is loaded lazily and cached, from `REDDIT_ADS_OPENAPI_PATH` (a local file) or else
`REDDIT_ADS_OPENAPI_URL` (default `https://ads-api.reddit.com/api/v3/openapi.json`). If the spec is
unavailable, the discovery tools return a clear error and requests still work.

**Auth: OAuth2 token manager.** Unlike OpenAI's static key, Reddit issues short-lived bearer
tokens.
- **Refresh mode** (default) needs `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` and
  `REDDIT_REFRESH_TOKEN`.
  - The server POSTs `grant_type=refresh_token` to `REDDIT_TOKEN_URL` (default
    `https://www.reddit.com/api/v1/access_token`), form-encoded, with HTTP Basic
    `client_id:client_secret`.
  - It caches the access token until 60 s before `expires_in`. Reddit sends either 3600 or
    86400 seconds.
  - If the response includes a new `refresh_token`, it replaces the old one in memory.
  - A lock makes concurrent tool calls share one refresh.
  - On a 401 from the API it refreshes and retries **once**.
  - If the token endpoint rejects the credentials, the tool error names the problem and does not
    echo any secret.
- **Static mode**: `REDDIT_ACCESS_TOKEN` is sent as-is and never refreshed. This covers a CAPI
  conversion access token or a token minted elsewhere.

Exactly one mode must be configured, or startup fails with a `ConfigError`.

Every request carries `User-Agent: REDDIT_USER_AGENT`. Reddit requires the form
`<platform>:<app id>:<version> (by /u/<username>)` and heavily rate-limits generic agents. The
default `python:reddit-ads-mcp:0.1.0 (by /u/unset)` carries a visible placeholder username so it
is obviously not production-ready. `.env.example`, the README configuration table and the setup
snippets all set `REDDIT_USER_AGENT` explicitly. The
README documents the one-time authorization-code flow for obtaining a permanent refresh token:
authorize URL with `duration=permanent` and a scope list, then a `curl` code exchange. It lists
all four scopes the spec declares (`adsread`, `adsedit`, `adsconversions` and `adsdatadeletion`),
says which operations need each, and recommends requesting only what the agent needs. Full control
needs all four.

**Safety.**
- `path` goes through the same allowlist-of-shape validator as OpenAI's `check_path` (copied): a
  single leading `/`, no scheme or host, no `..`, `//`, `?`, `#` or `\`, checked after
  percent-decoding. Requests only go to `REDDIT_ADS_BASE_URL`.
- The client secret and refresh token are only ever sent to `REDDIT_TOKEN_URL`. The access token is
  only sent to the base URL.
- Callers cannot override `Authorization`, `Host` or `User-Agent`.
- HTTP mode keeps the same bearer-auth middleware, closed-by-default startup, `/healthz`,
  `MCP_MAX_REQUEST_BYTES` and opt-in `MCP_STATELESS` behavior (copied `http_app.py`).
- **Accepted risk:** any authorized caller can do anything the token's scopes allow, including
  spending money (launching campaigns, raising budgets). There is no server-side spend guard in v1.
  The README tells operators to grant only the scopes they need (for example only `adsread` for a
  reporting agent) and to use Reddit's account-level spend controls.

**Configuration.**
- Reddit: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_REFRESH_TOKEN`,
  `REDDIT_ACCESS_TOKEN`, `REDDIT_USER_AGENT`, `REDDIT_TOKEN_URL`, `REDDIT_ADS_BASE_URL`,
  `REDDIT_TIMEOUT_SECONDS`, `REDDIT_ADS_OPENAPI_PATH` and `REDDIT_ADS_OPENAPI_URL`.
- MCP: `MCP_TRANSPORT`, `MCP_HOST`, `MCP_PORT`, `MCP_AUTH_TOKEN`, `MCP_ALLOW_UNAUTHENTICATED`,
  `MCP_MAX_REQUEST_BYTES` and `MCP_STATELESS`, all identical to openai.

**CI contract change (cross-cutting).** The `docker` smoke job in `.github/workflows/mcp.yml`
currently hard-codes `-e OPENAI_API_KEY=sk-ci -e MCP_AUTH_TOKEN=ci`. The reddit container would
exit on missing credentials and fail `/healthz`. The fix is for each server to ship a
`ci.env` of dummy, non-secret values that lets its image start. The smoke job runs
`docker run --env-file "<server>/ci.env"` instead of enumerating variables. `mcp/openai/ci.env` is
added, and `mcp/README.md`'s per-server contract lists `ci.env`. This keeps the rule that "a new
server needs no workflow edit", and a server without `ci.env` fails the job loudly. No startup step
calls Reddit, so dummy credentials are enough for `/healthz`. The `publish` job needs no change:
the image name derives from the directory.

**Gate feasibility.** The token manager has no openai analogue and branches the most. It is
split into small single-purpose functions (freshness check, refresh, single send, and send with
one 401 retry) so each stays under complexity 5, 6 branches and 2 nested blocks.

**Tests.** They use `httpx2.MockTransport` with no network. The fake routes the token URL and the
API separately, so tests can assert where each credential went. Coverage:
- path validation and protected headers
- JSON and text responses and the header allowlist
- `reddit_ads_follow_page`: it follows a base-URL `next_url` with its query intact and the bearer
  token attached, both as a GET and as a POST re-sending the given body, and it refuses another host, scheme or port, userinfo, a path outside the base
  path, a `..` segment and a fragment
- token refresh: first-use fetch, cache hit, refresh on expiry, refresh-token rotation, a single
  retry on 401 and no infinite loop on a second 401, token-endpoint failure, and secrets sent only
  to the token URL
- static-token mode
- config errors: no mode, both modes, partial refresh credentials
- list and describe against a small fixture spec, including the scope (and `null` when undeclared), HTML stripping, depth
  clamping and the unreachable-spec error
- HTTP auth middleware, stateless mode and `/healthz`
- an in-process client listing exactly the four tools
- a stdio subprocess handshake

The gates are the same four as openai (ruff ALL with complexity 5, format, mypy --strict, and
pytest at 100% line and branch coverage) through `make check`, and CI discovers the server by glob.

**Alternatives considered.**
- **A. Generic spec-driven tools (chosen).** This is knowledge-backed, stays current as Reddit
  changes the API, and needs four tools.
- **Pagination by copying `page.token` into `query`.** Rejected: the spec says not to
  rebuild pagination from `next_url`'s query parameters.
- **B. One tool per operation** (108 tools). Rejected: close to the ~100–128 tool limits of several
  clients, floods context, and was already rejected in the knowledge decision.
- **C. Hand-curated tools** (campaigns, reports, …), like the existing OSS servers. Rejected: it
  fails "full control" and goes stale.
- **D. A shared `mcp/common` package** reused by both servers. Rejected: it breaks the
  self-contained-directory contract and each server's Docker build context, which would need a
  repo-root context or vendoring. At two servers, duplication is cheaper than coupling. Revisit at
  a third.
- **CI alternatives:**
  - Add the Reddit variables to the `docker run` line. Rejected: it enumerates servers inside the
    workflow.
  - Let the server start without credentials. Rejected: it weakens fail-fast config validation.

## Success criteria

- `mcp/reddit-ads/` contains `pyproject.toml` (gate config identical to openai's), `Makefile`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `ci.env`, `.dockerignore`, `README.md`, the `reddit_ads_mcp` package and `tests/`.
- An in-process MCP client test lists exactly `reddit_ads_request`, `reddit_ads_follow_page`, `reddit_ads_list_endpoints`, `reddit_ads_describe_endpoint`.
- Tests show `reddit_ads_request` rejects absolute URLs, `..` segments, `//`, `?` and percent-encoded variants, and rejects overrides of `Authorization`, `Host` and `User-Agent`. Tests show `reddit_ads_follow_page` follows a base-URL `next_url` with its query string intact, as a GET and as a POST carrying the given body, and refuses a different host, scheme or port, userinfo, a path outside the base path, a `..` segment and a fragment.
- Tests show refresh mode fetches a token with HTTP Basic client credentials from the token URL, reuses it until near expiry, refreshes after expiry, adopts a rotated refresh token, retries exactly once on a 401, and never sends the client secret or refresh token to the API base URL.
- Tests show static-token mode sends `REDDIT_ACCESS_TOKEN` with no token-endpoint call, and config refuses zero modes, both modes, or incomplete refresh credentials.
- Tests show every API request carries the configured `User-Agent` and that `ratelimit`/`ratelimit-policy`/`retry-after` headers are returned.
- Tests show list/describe work from a fixture spec via `REDDIT_ADS_OPENAPI_PATH`, describe includes the required scope (`null` when undeclared) and HTML-stripped descriptions, and an unreachable spec yields a clear error.
- Tests show HTTP mode refuses to start without `MCP_AUTH_TOKEN` unless explicitly allowed, rejects bad bearer tokens, serves `/healthz` unauthenticated, completes an authenticated tool call, and serves stateless mode without sessions; a stdio subprocess test completes a handshake and lists four tools.
- In `mcp/reddit-ads/`, `make check` passes: ruff check, ruff format --check, mypy --strict, pytest with 100% line and branch coverage.
- `docker build mcp/reddit-ads` succeeds and the container started with `--env-file mcp/reddit-ads/ci.env` answers `GET /healthz` with 200. The same holds for `mcp/openai` with its new `ci.env`.
- `.github/workflows/mcp.yml`'s docker job uses `--env-file <server>/ci.env` and names no server-specific variables. `mcp/README.md` and root `README.md` list `reddit-ads`; `mcp/README.md` adds `ci.env` to the per-server contract.
- `mcp/reddit-ads/README.md` documents:
  - stdio setup for Claude Code and Claude Desktop, and HTTP/Docker usage
  - every environment variable
  - the refresh-token bootstrap and scopes
  - the User-Agent requirement
  - pagination via `reddit_ads_follow_page`
  - all four OAuth scopes and which operations need each
  - the security model, including the accepted spend risk and scope minimization
  - rate limits
- `make check` in `mcp/openai` still passes, and root `pytest tests/` still passes.

## Open Questions

- Refresh-token persistence across restarts when Reddit rotates the token. v1 keeps it in memory only. If Reddit invalidates the old token on rotation, a restart would need re-authorization. This is documented; the fix is deferred until rotation is observed.
- A `reddit-ads-mcp-auth` helper CLI for the code exchange. Deferred; the README documents the `curl` flow.
- A server-side spend guard (for example a read-only mode that refuses non-GET requests except query POSTs). Deferred; v1 relies on OAuth scopes.
- POST pagination re-sends the original body to `next_url`. This is inferred from the spec's shape: each
  of the four POST paginators declares `page.token` as a query parameter next to its JSON body. It
  has not been confirmed against the live API. The README says so, and tests can only use mocks.
- CAPI v2.0 (`/api/v2.0/conversions/events/…`) is outside the v3 base URL. It is deprecated, and v3 `/pixels/{id}/conversion_events` covers it.

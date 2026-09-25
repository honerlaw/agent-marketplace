# Proposal: add-google-search-console-mcp-server

**Date**: 2026-09-25
**Status**: Draft

## Goal
Add `mcp/google-search-console/`: an MCP server that gives an LLM full access to the Google
Search Console API (Search Analytics, Sites, Sitemaps, URL Inspection) using the operator's Google
credentials. It follows the same server contract as `mcp/openai/`: Python package with console
script, stdio + bearer-guarded streamable HTTP, `MCP_STATELESS`, `/healthz`, non-root Dockerfile,
`make check` with the strict ruff/mypy/100%-branch-coverage gates, discovered and published by the
existing `.github/workflows/mcp.yml` with no workflow edit.

## Why
The user asked for "a Google Search Console API MCP server similar to the OpenAI one we created".
`mcp/README.md` defines a per-server contract and CI already discovers servers by glob, so the
second server should reuse that contract. The Search Console API is small (11 operations in the
v1 discovery document, revision 20260923; one of them, the Mobile-Friendly Test, belongs to a tool
Google retired in Dec 2023, to be confirmed during implementation) and stable (the `webmasters/v3` resources plus the 2022 URL Inspection
addition).

## Approach
One typed MCP tool per live API operation (10 tools), talking to `https://searchconsole.googleapis.com/`
through `httpx2`, with credentials from `google-auth`:

- **Sites:** `gsc_list_sites()`, `gsc_get_site(site_url)`, `gsc_add_site(site_url)`*, `gsc_delete_site(site_url)`*
- **Sitemaps:** `gsc_list_sitemaps(site_url, sitemap_index?)`, `gsc_get_sitemap(site_url, feedpath)`,
  `gsc_submit_sitemap(site_url, feedpath)`*, `gsc_delete_sitemap(site_url, feedpath)`*
- **Search Analytics:** `gsc_query_search_analytics(site_url, query: SearchAnalyticsQuery)` — a pydantic
  model mirroring `SearchAnalyticsQueryRequest` (dates, dimensions, type, dimensionFilterGroups,
  aggregationType, rowLimit, startRow, dataState), serialized to camelCase
- **URL Inspection:** `gsc_inspect_url(site_url, inspection_url, language_code?)`

(* mutating.)

**Why typed tools here, not `mcp/openai/`'s generic shape.** This is the "narrow capability" carve-out
that [[2026-09-25-decision-mcp-servers-expose-generic-spec-driven-tools]] already allows, not a reversal
of it. That decision chose generic tools for a *large or fast-moving* API (352 OpenAI operations, over
client tool limits). Search Console has 10 live operations and has added one resource in about four
years, so typed tools covering the whole surface stay well under tool limits and give up no coverage.
A generic `gsc_request` plus discovery tools (3 tools; GSC has no upload or binary-download surface, so
openai's multipart and download tools have no counterpart) was rejected: the model would have to
percent-encode `siteUrl` itself, and openai's `check_path` rejects an encoded `https://` siteUrl, so it
would need a new, looser path validator. A generic escape hatch on top of typed tools was rejected: it
brings back a caller-controlled path for endpoints that do not exist yet. **Staleness mitigation:** the
README records the discovery revision the tools were built against; if Google's discovery document
grows materially, revisit the generic shape. Promote records this size/stability split as a knowledge
entry so future `mcp/<name>/` servers know which shape applies.

The server builds every URL itself, and each tool carries its own full path because the API mixes
two prefixes: sites, sitemaps and Search Analytics live under `webmasters/v3/sites/{siteUrl}/…`, while
URL Inspection is `POST v1/urlInspection/index:inspect` with `siteUrl` and `inspectionUrl` as JSON
body fields (no path parameters). Path parameters (`site_url`, `feedpath`) are percent-encoded as
single path segments (`quote(value, safe="")`), so callers never supply a path and there is no
path-validation boundary to defend. Non-2xx responses raise `ToolError` with the HTTP status and
Google's `error.message`; 2xx responses return the parsed JSON (empty bodies return `{"status": <code>}`).

**Credentials** are resolved lazily on the first tool call (so the container starts and answers
`/healthz` without Google credentials, which keeps CI's generic docker smoke test unchanged):
`GSC_CREDENTIALS_JSON` (inline service-account or authorized-user JSON, via
`google.auth.load_credentials_from_dict`) if set, otherwise Application Default Credentials
(`GOOGLE_APPLICATION_CREDENTIALS`, `gcloud auth application-default login`, GCP metadata). Token
refresh runs in a worker thread via `google-auth[requests]`. Scope is `webmasters`;
`GSC_READ_ONLY=true` requests `webmasters.readonly` instead and does not register the four mutating
tools. This keeps the credential surface minimal: an operator who only needs reporting gets a server
that cannot change properties or sitemaps. The guarantee is the unregistered tools; the narrower
OAuth scope is defence in depth whose effect depends on the credential type (the README says so).

**Shared plumbing is copied, not shared** (per `mcp/README.md`'s self-contained contract): config
loading (`MCP_TRANSPORT`, `MCP_HOST/PORT`, `MCP_AUTH_TOKEN`, `MCP_ALLOW_UNAUTHENTICATED`,
`MCP_MAX_REQUEST_BYTES`, `MCP_STATELESS`, `GSC_TIMEOUT_SECONDS`), `BearerAuth` middleware,
`/healthz`, `main()`, Makefile, Dockerfile, `.env.example`, `.dockerignore`, docker-compose, and the
`pyproject.toml` quality block verbatim.

Files: `mcp/google-search-console/{pyproject.toml,Makefile,Dockerfile,docker-compose.yml,.env.example,.dockerignore,README.md}`,
`src/google_search_console_mcp/{__init__,__main__,main,config,credentials,api,server,http_app}.py`,
`tests/*`, plus a row in both server tables: `mcp/README.md` and the root `README.md`'s "MCP servers" section.

## Success criteria
1. `make install && make check` passes in `mcp/google-search-console/` (ruff ALL, format check,
   mypy --strict, 100% line+branch coverage) with the `[tool.ruff]`/`[tool.mypy]` quality config
   copied from `mcp/openai/pyproject.toml` unchanged except package names.
2. The server registers exactly the 10 tools above; with `GSC_READ_ONLY=true` it registers only the
   6 read tools and requests the `webmasters.readonly` scope — both asserted by tests.
3. Tests show `site_url` values `https://example.com/` and `sc-domain:example.com`, and a feedpath
   containing `../` and `?`, are sent as single encoded path segments under
   `/webmasters/v3/sites/`, and a test shows `gsc_inspect_url` sends `POST /v1/urlInspection/index:inspect`
   with `siteUrl`, `inspectionUrl` and (when given) `languageCode` in the JSON body.
4. HTTP mode refuses to start without `MCP_AUTH_TOKEN` unless `MCP_ALLOW_UNAUTHENTICATED=true`; a
   request without the bearer gets 401; `/healthz` is open; `MCP_STATELESS=true` is honored — tests.
5. Credentials: tests cover `GSC_CREDENTIALS_JSON`, ADC fallback, a clear `ToolError` when no
   credentials exist, and token refresh when the token is invalid — without network.
6. The Docker image builds and answers `/healthz` when run with only `MCP_AUTH_TOKEN` set (checked
   locally if Docker is available; always by the CI `docker` job, with no edit to `mcp.yml`).
7. `mcp/google-search-console/README.md` documents tools, credential setup (including adding a
   service account as a user on the Search Console property), configuration, security model (including
   that read-only mode's guarantee is the unregistered tools, with the narrower scope as defence in
   depth) and limitations; `mcp/README.md` and the root `README.md` both list the new server.

## Open Questions
- None blocking. The Mobile-Friendly Test operation is excluded as retired; if the endpoint still
  answers, adding it later is a one-tool change.

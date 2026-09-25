# Proposal: add-google-search-console-mcp-server

**Date**: 2026-09-25
**Status**: Shipped (2026-09-25)

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
Google retired on 1 December 2023, together with its API) and stable (the `webmasters/v3` resources plus the 2022 URL Inspection
addition).

## Approach
One typed MCP tool per live API operation (10 tools), talking to `https://searchconsole.googleapis.com/`
through `httpx2`, with credentials from `google-auth`:

- **Sites:** `gsc_list_sites()`, `gsc_get_site(site_url)`, `gsc_add_site(site_url)`*, `gsc_delete_site(site_url)`*
- **Sitemaps:** `gsc_list_sitemaps(site_url, sitemap_index?)`, `gsc_get_sitemap(site_url, feedpath)`,
  `gsc_submit_sitemap(site_url, feedpath)`*, `gsc_delete_sitemap(site_url, feedpath)`*
- **Search Analytics:** `gsc_query_search_analytics(site_url, query: SearchAnalyticsQuery)` — a pydantic
  model (`models.py`) mirroring `SearchAnalyticsQueryRequest` (dates, dimensions, type,
  dimensionFilterGroups, aggregationType, rowLimit, startRow, dataState). The schema uses the API's
  camelCase names and also accepts snake_case. The deprecated `searchType` is accepted as an alias
  for `type`, and unknown fields are rejected (`extra="forbid"`), so a misspelled option fails
  instead of being silently dropped
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
grows materially, revisit the generic shape. The size/stability rule is recorded in
[[2026-09-25-decision-mcp-server-tool-shape-follows-api-size-and-stability]] and as one line in
`mcp/README.md`'s "Adding a server".

The server builds every URL itself, and each tool carries its own full path because the API mixes
two prefixes: sites, sitemaps and Search Analytics live under `webmasters/v3/sites/{siteUrl}/…`, while
URL Inspection is `POST v1/urlInspection/index:inspect` with `siteUrl` and `inspectionUrl` as JSON
body fields (no path parameters). Callers never supply a path. Each path parameter (`site_url`,
`feedpath`) becomes exactly one segment in `api.segment`: it is percent-encoded
(`quote(value, safe="")`), and `""`, `.` and `..` are refused. Encoding alone was not enough.
Review found that httpx2 resolves dot segments, so `gsc_delete_sitemap(feedpath="..")` was sending
DELETE on the site itself
([[2026-09-25-pattern-percent-encoding-does-not-confine-a-dot-segment]]). Responses:
- Non-2xx raises `ToolError` with the HTTP status and Google's `error.message`, falling back to the body.
- 2xx returns the parsed JSON object. An empty body returns `{"status": <code>}`, and a non-JSON
  body returns `{"status", "text"}`.
- Transport errors and timeouts raise `ToolError` naming the exception.

**Credentials** are resolved lazily on the first tool call (so the container starts and answers
`/healthz` without Google credentials, which keeps CI's generic docker smoke test unchanged):
`GSC_CREDENTIALS_JSON` if set, otherwise Application Default Credentials
(`GOOGLE_APPLICATION_CREDENTIALS`, `gcloud auth application-default login`, GCP metadata). Inline
JSON must be `service_account` or `authorized_user` and goes through that type's own constructor.
The draft planned `google.auth.load_credentials_from_dict`, but that loader also accepts
`external_account` configs, which can make the server fetch URLs or run executables, so every
other type is refused
([[2026-09-25-pattern-a-generic-credential-loader-is-a-fetch-and-exec-primitive]]). Token refresh
runs in a worker thread under an `anyio.Lock`, via `google-auth[requests]`. google-auth's
unannotated functions get commented per-call `type: ignore[no-untyped-call]`, so the copied
`[tool.mypy]` block stays unchanged. Scope is `webmasters`;
`GSC_READ_ONLY=true` requests `webmasters.readonly` instead and does not register the four mutating
tools. This keeps the credential surface minimal: an operator who only needs reporting gets a server
that cannot change properties or sitemaps. The guarantee is the unregistered tools; the narrower
OAuth scope is defence in depth whose effect depends on the credential type (the README says so).

**Shared plumbing is copied, not shared** (per `mcp/README.md`'s self-contained contract): config
loading (`MCP_TRANSPORT`, `MCP_HOST/PORT`, `MCP_AUTH_TOKEN`, `MCP_ALLOW_UNAUTHENTICATED`,
`MCP_MAX_REQUEST_BYTES`, which defaults to the SDK's 4 MiB because there are no uploads, `MCP_STATELESS`,
`GSC_TIMEOUT_SECONDS`), `BearerAuth` middleware,
`/healthz`, `main()`, Makefile, Dockerfile, `.env.example`, `.dockerignore`, docker-compose, and the
`pyproject.toml` quality block verbatim.

Files: `mcp/google-search-console/{pyproject.toml,Makefile,Dockerfile,docker-compose.yml,.env.example,.dockerignore,README.md}`,
`src/google_search_console_mcp/{__init__,__main__,main,config,credentials,api,models,server,http_app}.py`,
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
- None. The Mobile-Friendly Test was confirmed retired (tool, report and API shut down on 1 December
  2023) and is excluded.

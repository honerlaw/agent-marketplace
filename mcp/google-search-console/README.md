# google-search-console-mcp

An MCP server that gives an LLM **full access to the Google Search Console API** with your
Google credentials: search performance, properties, sitemaps and URL inspection.

The API is small (ten live operations), so each operation gets its own typed tool. Tool
schemas carry the API's field names and enums, so the model doesn't need a separate
discovery step. The `openai-ads` and `reddit-ads` servers take the opposite approach because
their APIs have around a hundred operations each and add endpoints often.

| Tool | API operation |
|---|---|
| `gsc_list_sites()` | `GET webmasters/v3/sites`: properties you can access, with permission level |
| `gsc_get_site(site_url)` | `GET webmasters/v3/sites/{siteUrl}` |
| `gsc_add_site(site_url)` ✎ | `PUT webmasters/v3/sites/{siteUrl}` |
| `gsc_delete_site(site_url)` ✎ | `DELETE webmasters/v3/sites/{siteUrl}` |
| `gsc_list_sitemaps(site_url, sitemap_index?)` | `GET …/sites/{siteUrl}/sitemaps` |
| `gsc_get_sitemap(site_url, feedpath)` | `GET …/sites/{siteUrl}/sitemaps/{feedpath}` |
| `gsc_submit_sitemap(site_url, feedpath)` ✎ | `PUT …/sites/{siteUrl}/sitemaps/{feedpath}` |
| `gsc_delete_sitemap(site_url, feedpath)` ✎ | `DELETE …/sites/{siteUrl}/sitemaps/{feedpath}` |
| `gsc_query_search_analytics(site_url, query)` | `POST …/sites/{siteUrl}/searchAnalytics/query`: clicks, impressions, CTR, position |
| `gsc_inspect_url(site_url, inspection_url, language_code?)` | `POST v1/urlInspection/index:inspect`: index status of one URL |

✎ changes your account. These four tools are not registered when `GSC_READ_ONLY=true`.

A `site_url` is a property exactly as Search Console lists it: `https://www.example.com/`
(URL-prefix property, trailing slash included) or `sc-domain:example.com` (domain property).
A `feedpath` is a sitemap's full URL. `query` mirrors
[`SearchAnalyticsQueryRequest`](https://developers.google.com/webmaster-tools/v1/searchanalytics/query),
e.g. `{"startDate": "2026-09-01", "endDate": "2026-09-07", "dimensions": ["QUERY"], "rowLimit": 25}`.
Use `type` for the search type; the deprecated `searchType` is also accepted. Unknown fields
are rejected, so a misspelled option fails instead of being ignored.

The tools cover the Search Console discovery document at revision `20260923`, except the
Mobile-Friendly Test (`urlTestingTools.mobileFriendlyTest.run`), which Google retired on
1 December 2023. If Google adds operations, add a tool for each one. If the API grows large
or changes quickly, switch to the generic approach used by [`../openai-ads`](../openai-ads/).

## Credentials

The server uses Google OAuth. The **first tool call** resolves credentials, not startup, so
the server starts and answers `/healthz` before any credentials exist. It tries, in order:

1. `GSC_CREDENTIALS_JSON`: an inline service-account key or authorized-user JSON. No other
   credential types are accepted.
2. [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials):
   `GOOGLE_APPLICATION_CREDENTIALS` (a key file path), `gcloud auth application-default login`,
   or the metadata server when running on Google Cloud.

**Service account (recommended for servers):**

1. In Google Cloud, enable the **Google Search Console API** and create a service account
   with a JSON key.
2. In Search Console, open **Settings → Users and permissions** for each property, and add the
   service account's email as a user. **Restricted** is enough for reporting. Writes need
   more: Google's [permission table](https://support.google.com/webmasters/answer/2451999)
   lists which actions need Full or Owner.
3. Pass the key as `GSC_CREDENTIALS_JSON`, or point `GOOGLE_APPLICATION_CREDENTIALS` at the file.

**Your own account (handy locally):**

```bash
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/webmasters,https://www.googleapis.com/auth/cloud-platform
```

If Google refuses gcloud's built-in OAuth client for this scope, create your own OAuth client
(Desktop app) and add `--client-id-file=<its JSON>`.

## Run locally (stdio)

```bash
cd mcp/google-search-console
make install            # creates .venv with the server and dev tools
```

Claude Code:

```bash
claude mcp add search-console \
  --env GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/key.json -- \
  /absolute/path/to/mcp/google-search-console/.venv/bin/google-search-console-mcp
```

Claude Desktop / other clients (`mcpServers` JSON):

```json
{
  "mcpServers": {
    "search-console": {
      "command": "/absolute/path/to/mcp/google-search-console/.venv/bin/google-search-console-mcp",
      "env": { "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/key.json" }
    }
  }
}
```

## Run over HTTP / Docker

```bash
cd mcp/google-search-console
cp .env.example .env    # set GSC_CREDENTIALS_JSON and MCP_AUTH_TOKEN (openssl rand -hex 32)
docker compose up --build
```

The MCP endpoint is `http://<host>:8000/mcp`, and clients must send
`Authorization: Bearer <MCP_AUTH_TOKEN>`. `GET /healthz` is unauthenticated for
load balancers. For Claude Code:

```bash
claude mcp add --transport http search-console http://localhost:8000/mcp \
  --header "Authorization: Bearer <MCP_AUTH_TOKEN>"
```

Pushes to `main` publish the image as `ghcr.io/<owner>/google-search-console-mcp` (see
[`../README.md`](../README.md)). Put it behind TLS: the bearer token is only as private as the
connection carrying it.

Without Docker: `MCP_TRANSPORT=http MCP_AUTH_TOKEN=... .venv/bin/google-search-console-mcp`.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `GSC_CREDENTIALS_JSON` | unset | Inline service-account or authorized-user JSON; unset means ADC |
| `GOOGLE_APPLICATION_CREDENTIALS` | unset | Key file path, read by ADC |
| `GSC_READ_ONLY` | `false` | `true` requests the `webmasters.readonly` scope and hides the ✎ tools |
| `GSC_TIMEOUT_SECONDS` | `120` | Per-request timeout |
| `MCP_TRANSPORT` | `stdio` (`http` in Docker) | `stdio` or `http` |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `8000` (`0.0.0.0` in Docker) | HTTP bind address |
| `MCP_AUTH_TOKEN` | unset | Bearer token; **required** in http mode |
| `MCP_ALLOW_UNAUTHENTICATED` | `false` | Set `true` to run http mode without a token |
| `MCP_MAX_REQUEST_BYTES` | `4194304` (4 MiB) | Largest HTTP request body |
| `MCP_STATELESS` | `false` | Set `true` to serve http mode without sessions (no `mcp-session-id`; a fresh transport per request). Use it on hosts that stop idle instances, or with several replicas behind a load balancer |

## Security model

- **Callers never supply a URL path.** Every tool builds its URL from a fixed template, and
  `site_url` and `feedpath` each become exactly one path segment. They are percent-encoded,
  so `/`, `?` and `#` can't split them. The empty string, `.` and `..` are refused outright,
  because URL resolution would collapse them into a different path (for example turning
  "delete sitemap `..`" into "delete site"). Requests only go to
  `https://searchconsole.googleapis.com`.
- **Only two credential types are accepted inline.** `GSC_CREDENTIALS_JSON` must be a
  `service_account` or `authorized_user` object. `external_account` configurations are refused
  because they can make the server fetch URLs or run programs.
- **HTTP mode is closed by default.** The server won't start without `MCP_AUTH_TOKEN` unless
  you set `MCP_ALLOW_UNAUTHENTICATED=true`. Tokens are compared in constant time.
- **Read-only mode.** With `GSC_READ_ONLY=true` the four ✎ tools are never registered, so the
  model can't call them no matter what the credentials allow. That is the guarantee. The
  server also asks Google for the `webmasters.readonly` scope, but that is defence in depth
  only: a service account gets exactly the requested scope, while user credentials keep
  whatever scope they were granted at consent time.
- **Accepted risk: anything the credentials can do, the client can do.** In read-write mode
  that includes removing properties and sitemaps. Give the service account the least
  Search Console permission you need, per property.

## Limitations

- **Quotas are Google's.** URL Inspection allows about 2,000 calls a day per property, and
  Search Analytics has per-site and per-project load limits. A quota error comes back as the
  tool's error message.
- **Search Analytics returns at most 25,000 rows per call.** Page through larger result sets
  with `startRow`. Dates are in Pacific time, and the last few days may be incomplete unless
  `dataState` is `ALL`.
- **Network failures and timeouts** come back as tool errors naming the exception.
- **Adding a property doesn't verify it.** `gsc_add_site` only registers the property.
  Ownership verification happens outside this API.

## Development

The code is held to strict gates, configured in `pyproject.toml` and run identically in CI
(`.github/workflows/mcp.yml`):

- `ruff check`: every rule family on, McCabe complexity ≤ 5, ≤ 5 arguments, ≤ 6 branches,
  ≤ 25 statements, ≤ 4 returns, ≤ 2 nested blocks
- `ruff format --check`
- `mypy --strict` over source and tests. google-auth ships `py.typed` but leaves some
  functions unannotated, so each call to one carries a commented `type: ignore[no-untyped-call]`
- `pytest` with 100% line and branch coverage (no network: the API is a mock transport,
  Google credentials are faked, and HTTP and stdio are exercised with real servers)

```bash
make install
make check
```

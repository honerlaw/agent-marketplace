# reddit-ads-mcp

An MCP server that gives an LLM **full access to the Reddit Ads API (v3)** using
your Reddit credentials. Instead of one tool per endpoint, it exposes four generic
tools that together reach all 108 operations: campaigns, ad groups, ads, posts,
audiences, pixels and conversions, reports, targeting and more. Because the tools
read Reddit's published OpenAPI spec, they don't go stale when Reddit adds
endpoints.

| Tool | What it does |
|---|---|
| `reddit_ads_request(method, path, query?, body?, headers?)` | Any call, e.g. `GET /me`, `POST /ad_accounts/{id}/campaigns`, `PATCH /ads/{id}` |
| `reddit_ads_follow_page(url, method?, body?)` | Fetches the next page: pass `pagination.next_url` exactly as returned |
| `reddit_ads_list_endpoints(text_filter?)` | Lists operations from Reddit's OpenAPI spec |
| `reddit_ads_describe_endpoint(method, path, depth?)` | Parameters, body schema, success responses and **required OAuth scope** of one operation |

Paths are relative to the base URL (`https://ads-api.reddit.com/api/v3`), so
`/me` means `https://ads-api.reddit.com/api/v3/me`. Request bodies use Reddit's
envelope, `{"data": {...}}`, and updates are `PATCH`.

## Getting a refresh token

The server holds a long-lived **refresh token** and exchanges it for short-lived
access tokens as needed. You get one once:

1. Create an app at [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
   with a redirect URI you control, e.g. `http://localhost:8080`. Note its client
   ID and secret. Your Reddit account needs access to the ad accounts you want to
   manage.
2. Open this URL in a browser, approve, and copy the `code` from the redirect:

   ```
   https://www.reddit.com/api/v1/authorize?client_id=<CLIENT_ID>&response_type=code&state=any&redirect_uri=<REDIRECT_URI>&duration=permanent&scope=adsread,adsedit,adsconversions,adsdatadeletion
   ```

3. Within 10 minutes, exchange the code (it works once):

   ```bash
   curl -X POST https://www.reddit.com/api/v1/access_token \
     -u '<CLIENT_ID>:<CLIENT_SECRET>' \
     -A 'server:my-ads-agent:1.0 (by /u/your_username)' \
     -d 'grant_type=authorization_code&code=<CODE>&redirect_uri=<REDIRECT_URI>'
   ```

   The response's `refresh_token` is your `REDDIT_REFRESH_TOKEN`.

**Request only the scopes the agent needs.** `describe_endpoint` reports each
operation's scope.

| Scope | Grants |
|---|---|
| `adsread` | Every read, plus reports, history, estimates and bid suggestions (71 operations) |
| `adsedit` | Creating and changing campaigns, ad groups, ads, posts, audiences, and so on (32 operations) |
| `adsconversions` | Sending Conversions API events (`POST /pixels/{id}/conversion_events`) |
| `adsdatadeletion` | Data-deletion jobs (3 operations) |

A reporting agent needs only `adsread`. Full control needs all four.

## Run locally (stdio)

```bash
cd mcp/reddit-ads
make install            # creates .venv with the server and dev tools
```

Claude Code:

```bash
claude mcp add reddit-ads \
  --env REDDIT_CLIENT_ID=... --env REDDIT_CLIENT_SECRET=... --env REDDIT_REFRESH_TOKEN=... \
  --env "REDDIT_USER_AGENT=server:my-ads-agent:1.0 (by /u/your_username)" \
  -- /absolute/path/to/mcp/reddit-ads/.venv/bin/reddit-ads-mcp
```

Claude Desktop / other clients (`mcpServers` JSON):

```json
{
  "mcpServers": {
    "reddit-ads": {
      "command": "/absolute/path/to/mcp/reddit-ads/.venv/bin/reddit-ads-mcp",
      "env": {
        "REDDIT_CLIENT_ID": "...",
        "REDDIT_CLIENT_SECRET": "...",
        "REDDIT_REFRESH_TOKEN": "...",
        "REDDIT_USER_AGENT": "server:my-ads-agent:1.0 (by /u/your_username)"
      }
    }
  }
}
```

## Run over HTTP / Docker

```bash
cd mcp/reddit-ads
cp .env.example .env    # set the Reddit values and MCP_AUTH_TOKEN (openssl rand -hex 32)
docker compose up --build
```

Or pull the published image, `ghcr.io/<owner>/reddit-ads-mcp:latest`.

The MCP endpoint is `http://<host>:8000/mcp`, and clients must send
`Authorization: Bearer <MCP_AUTH_TOKEN>`. `GET /healthz` is unauthenticated for
load balancers. For Claude Code:

```bash
claude mcp add --transport http reddit-ads http://localhost:8000/mcp \
  --header "Authorization: Bearer <MCP_AUTH_TOKEN>"
```

Put the server behind TLS: the bearer token is only as private as the connection
carrying it.

## Configuration

Set **either** the three refresh values **or** `REDDIT_ACCESS_TOKEN`. The server
refuses to start with neither, both, or an incomplete set.

| Variable | Default | Meaning |
|---|---|---|
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | — | Your Reddit app; sent only to the token URL |
| `REDDIT_REFRESH_TOKEN` | — | Permanent refresh token; sent only to the token URL |
| `REDDIT_ACCESS_TOKEN` | — | A ready-made token used as-is and never refreshed, e.g. a Conversions API access token |
| `REDDIT_USER_AGENT` | `python:reddit-ads-mcp:0.1.0 (by /u/unset)` | **Set this.** Reddit requires `<platform>:<app id>:<version> (by /u/<username>)` and rate-limits generic agents |
| `REDDIT_ADS_BASE_URL` | `https://ads-api.reddit.com/api/v3` | API base URL; every request stays on it |
| `REDDIT_TOKEN_URL` | `https://www.reddit.com/api/v1/access_token` | Where access tokens are refreshed |
| `REDDIT_TIMEOUT_SECONDS` | `120` | Per-request timeout |
| `REDDIT_ADS_OPENAPI_PATH` | unset | Local spec file for discovery (offline / restricted egress) |
| `REDDIT_ADS_OPENAPI_URL` | `https://ads-api.reddit.com/api/v3/openapi.json` | Spec URL used when no path is set |
| `MCP_TRANSPORT` | `stdio` (`http` in Docker) | `stdio` or `http` |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `8000` (`0.0.0.0` in Docker) | HTTP bind address |
| `MCP_AUTH_TOKEN` | unset | Bearer token; **required** in http mode |
| `MCP_ALLOW_UNAUTHENTICATED` | `false` | Set `true` to run http mode without a token |
| `MCP_MAX_REQUEST_BYTES` | `4194304` (4 MiB) | Largest HTTP request body |
| `MCP_STATELESS` | `false` | Set `true` to serve http mode without sessions. Use it on hosts that stop idle instances, or with several replicas behind a load balancer |

## Security model

- **Each credential goes to one place.** The client secret and refresh token go
  only to `REDDIT_TOKEN_URL`. The access token goes only to the API base URL.
- **Nothing leaves the base URL.** `path` must be a plain relative path (no
  scheme, host, `//`, `..`, query or fragment), so a prompt-injected model can't
  send your token to another host.
  - A pagination URL is accepted only if its scheme, host and port equal the
    base URL's exactly, its path sits under the base path, and it has no
    userinfo or fragment.
  - Callers can't override `Authorization`, `Host` or `User-Agent`.
- **HTTP mode is closed by default.** The server won't start without
  `MCP_AUTH_TOKEN` unless you set `MCP_ALLOW_UNAUTHENTICATED=true`. Tokens are
  compared in constant time.
- **No server filesystem access.** Every Reddit Ads endpoint takes and returns
  JSON, and creative uploads are by URL (Reddit fetches `media.url`). So no tool
  takes a local file path.
- **Accepted risk: anything the token can do, the client can do.** With
  `adsedit` that includes spending money, by launching campaigns or raising
  budgets. There's no server-side spend guard, so bound the risk with the
  **narrowest scopes** that do the job and Reddit's account-level spend controls.

## Pagination

List responses carry `pagination.next_url` and `pagination.previous_url`. Reddit
says to follow these URLs directly, not to rebuild them from their query
parameters. Pass the URL to `reddit_ads_follow_page` unchanged.

For lists that come from a **POST** (`/ad_accounts/{id}/reports`,
`/ad_accounts/{id}/history`, `/businesses/{id}/ad_accounts/query`,
`/businesses/{id}/funding_instruments/query`), call it with `method: "POST"` and
the same `body` as the original request. Re-sending the body is inferred from the
spec: each of those endpoints takes `page.token` as a query parameter alongside
its JSON body. It has not been confirmed against the live API.

## Rate limits

Reddit pools limits per endpoint group and per user. Examples are 400
reads/min, 200 writes/min and 60 reports/min. Every result includes Reddit's
`ratelimit`, `ratelimit-policy` and `retry-after` headers when they're sent, and
a `429` is returned to the model as-is. The server doesn't retry it, so back off
and try again later. Each operation's description (via `describe_endpoint`) names
its limit group.

## Limitations

- **The refresh token lives in memory.** If Reddit rotates it, the server uses
  the new one until it restarts. If Reddit then refuses the original, repeat
  "Getting a refresh token".
- **Discovery follows the published spec**, which may briefly lag new endpoints.
  `reddit_ads_request` works for any endpoint whether or not it's listed.
- **Conversions API v2.0** (`/api/v2.0/conversions/...`) is outside the v3 base
  URL. Use v3's `POST /pixels/{pixel_id}/conversion_events`.

## Development

The code is held to the same strict gates as every server in `mcp/`, configured
in `pyproject.toml` and run identically in CI (`.github/workflows/mcp.yml`):
`ruff check` with every rule family on and complexity ≤ 5, `ruff format --check`,
`mypy --strict`, and `pytest` with 100% line and branch coverage. The tests make
no network calls: Reddit is a mock transport, and HTTP and stdio are exercised
with real servers.

```bash
make install
make check
```

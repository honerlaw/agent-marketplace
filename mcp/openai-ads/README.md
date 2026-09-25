# openai-ads-mcp

An MCP server that lets an LLM manage **ChatGPT advertising through the OpenAI Ads
(Advertiser) API**: ad accounts, campaigns, ad groups, ads, creative uploads, custom
audiences, product feeds, conversion tracking and insights. It uses your ad account's
Advertiser API key. Instead of one tool per endpoint it exposes four generic tools that
together reach every endpoint, so it keeps working as OpenAI adds endpoints.

| Tool | What it does |
|---|---|
| `openai_ads_request(method, path, query?, body?, headers?)` | Any JSON call, e.g. `POST /campaigns`, `GET /ad_groups`, `POST /ads/{ad_id}/activate` |
| `openai_ads_multipart_request(path, files, fields?)` | File uploads, e.g. a creative image to `/upload` |
| `openai_ads_list_endpoints(text_filter?)` | Lists operations from OpenAI's published Ads OpenAPI spec |
| `openai_ads_describe_endpoint(method, path, depth?)` | Parameters and schemas of one operation |

Paths are relative to the base URL (`https://api.ads.openai.com/v1`), so `/campaigns`
means `https://api.ads.openai.com/v1/campaigns`.

The structure is **ad account → campaign → ad group → ad**. Campaigns hold the objective,
budget, schedule and targeting. Ad groups hold bidding, context hints and product sets. Ads
hold the creative and destination URL. Money amounts are **micros** of the account currency
(`50000000` is 50.00). The server's instructions tell the model to create everything
`paused`, send an `Idempotency-Key` on creates, and confirm with you before activating
anything or changing budgets, bids or spend limits.

## Get an API key

In [Ads Manager](https://developers.openai.com/ads/api-overview), open **Settings** and
create an Advertiser API key. Each key belongs to one ad account. To check it:

```bash
curl https://api.ads.openai.com/v1/ad_account -H "Authorization: Bearer $OPENAI_ADS_API_KEY"
```

## Run locally (stdio)

```bash
cd mcp/openai-ads
make install            # creates .venv with the server and dev tools
```

Claude Code:

```bash
claude mcp add openai-ads --env OPENAI_ADS_API_KEY=... -- \
  /absolute/path/to/mcp/openai-ads/.venv/bin/openai-ads-mcp
```

Claude Desktop / other clients (`mcpServers` JSON):

```json
{
  "mcpServers": {
    "openai-ads": {
      "command": "/absolute/path/to/mcp/openai-ads/.venv/bin/openai-ads-mcp",
      "env": { "OPENAI_ADS_API_KEY": "..." }
    }
  }
}
```

## Run over HTTP / Docker

```bash
cd mcp/openai-ads
cp .env.example .env    # set OPENAI_ADS_API_KEY and MCP_AUTH_TOKEN (openssl rand -hex 32)
docker compose up --build
```

The MCP endpoint is `http://<host>:8000/mcp`, and clients must send
`Authorization: Bearer <MCP_AUTH_TOKEN>`. `GET /healthz` is unauthenticated for
load balancers. For Claude Code:

```bash
claude mcp add --transport http openai-ads http://localhost:8000/mcp \
  --header "Authorization: Bearer <MCP_AUTH_TOKEN>"
```

CI publishes the image as `ghcr.io/<owner>/openai-ads-mcp` (see `../README.md`). Deploy it
anywhere that runs containers, behind TLS: the bearer token is only as private as the
connection carrying it.

Without Docker: `MCP_TRANSPORT=http MCP_AUTH_TOKEN=... OPENAI_ADS_API_KEY=... .venv/bin/openai-ads-mcp`.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `OPENAI_ADS_API_KEY` | — (required) | Advertiser API key sent with every request |
| `OPENAI_ADS_BASE_URL` | `https://api.ads.openai.com/v1` | API base URL; every request stays on it |
| `OPENAI_ADS_TIMEOUT_SECONDS` | `120` | Per-request timeout |
| `OPENAI_ADS_OPENAPI_PATH` | unset | Local JSON spec file for discovery (offline / restricted egress) |
| `OPENAI_ADS_OPENAPI_URL` | `https://developers.openai.com/ads/openapi.json` | Spec URL used when no path is set |
| `MCP_TRANSPORT` | `stdio` (`http` in Docker) | `stdio` or `http` |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `8000` (`0.0.0.0` in Docker) | HTTP bind address |
| `MCP_AUTH_TOKEN` | unset | Bearer token; **required** in http mode |
| `MCP_ALLOW_UNAUTHENTICATED` | `false` | Set `true` to run http mode without a token |
| `MCP_MAX_REQUEST_BYTES` | `67108864` (64 MiB) | Largest HTTP request body, which bounds base64 uploads |
| `MCP_STATELESS` | `false` | Set `true` to serve http mode without sessions (no `mcp-session-id`; a fresh transport per request). Use it on hosts that stop idle instances, or with several replicas behind a load balancer, where an in-memory session would be lost or land on the wrong instance |

## Security model

- **The key never leaves the base URL.** `path` must be a plain relative path (no
  scheme, host, `//`, `..`, query or fragment), so a prompt-injected model can't
  send your key to another host. Callers can't override `Authorization` or `Host`.
- **HTTP mode is closed by default.** The server won't start without
  `MCP_AUTH_TOKEN` unless you set `MCP_ALLOW_UNAUTHENTICATED=true`. Tokens are
  compared in constant time.
- **No server filesystem access over HTTP.** `local_path` uploads work only over
  stdio, where the client already runs as you on your machine. Over HTTP they are
  refused, so a remote caller can't read the server's files (such as its environment).
- **Accepted risk: anything the key can do, the client can do.** That includes
  activating campaigns, raising budgets and bids, creating API keys and changing
  ad-account spend limits, all of which spend real money. The server's instructions
  ask the model to confirm before spending, but the server does not enforce it. Bound
  the risk with the ad account's own spend limits (`/ad_account/daily_spend_limit`,
  `/ad_account/spend_limit_windows`).

## Limitations

- **API key only.** The partner OAuth flow (`auth.openai.com`, scopes
  `ads.admin.all.read|write`) is not supported. Use one server per ad account.
- **Discovery follows the published spec**, which may briefly lag new endpoints.
  `openai_ads_request` works for any endpoint whether or not it's listed.
- **Array parameters** are passed as lists, e.g. `query={"include[]": ["serving_issues"]}`.
- **Response headers are an allowlist:** `content-type`, `x-request-id`,
  `openai-processing-ms`, `openai-version`, `retry-after`, and any `x-ratelimit-*` or
  `ratelimit*` header. The rate-limit header names are not documented, so both common
  spellings are forwarded.

## Development

The code is held to strict gates, configured in `pyproject.toml` and run
identically in CI (`.github/workflows/mcp.yml`):

- `ruff check`: every rule family on, McCabe complexity ≤ 5, ≤ 5 arguments, ≤ 6
  branches, ≤ 25 statements, ≤ 4 returns, ≤ 2 nested blocks
- `ruff format --check`
- `mypy --strict` over source and tests
- `pytest` with 100% line and branch coverage (no network: the Ads API is a
  mock transport, and HTTP and stdio are exercised with real servers)

```bash
make install
make check
```

Keep functions small enough to pass these gates without per-line ignores. An
ignore needs a comment saying why.

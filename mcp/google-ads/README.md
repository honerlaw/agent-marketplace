# google-ads-mcp

An MCP server that gives an LLM **full access to the Google Ads API** (REST, v26) with your
Google credentials: GAQL reporting, and creating and changing campaigns, ad groups, ads,
assets, budgets and everything else the API can do. Instead of one tool per endpoint (there
are 175), it exposes four generic tools that read Google's published Discovery document, so
they don't go stale when Google adds endpoints.

| Tool | What it does |
|---|---|
| `google_ads_request(method, path, query?, body?, headers?)` | Any call, e.g. `GET /customers:listAccessibleCustomers`, `POST /customers/1234567890/googleAds:search`, `POST /customers/1234567890/campaigns:mutate` |
| `google_ads_list_endpoints(text_filter?)` | Lists operations as `METHOD /template — summary` |
| `google_ads_describe_endpoint(method, path, depth?)` | Parameters, request schema and response schema of one operation |
| `google_ads_describe_schema(name, depth?)` | One schema, by the name a `$ref` marker gives |

Paths are relative to `https://googleads.googleapis.com/v26`, so `/customers/123/googleAds:search`
means `https://googleads.googleapis.com/v26/customers/123/googleAds:search`. Customer ids are
digits without dashes. Templates are printed in one spelling, `/customers/{customerId}/...`:
pass a template to the describe tool exactly as the list tool prints it, and a real path, with
ids filled in, to the request tool.

Google Ads messages nest deeply. The ad group's Shorts setting sits five schemas below
`adGroups:mutate`, so open nested types one at a time with `google_ads_describe_schema`
instead of raising `depth`. A few schemas are very large at any depth (`Metrics`,
`Segments`, `ErrorCode`, up to about 280 KB). To find GAQL fields, ask the API's own field
service instead: `POST /googleAdsFields:search` with a GAQL `query`.

## Reading: GAQL

```json
{"method": "POST", "path": "/customers/1234567890/googleAds:search",
 "body": {"query": "SELECT campaign.id, campaign.name, metrics.clicks FROM campaign WHERE segments.date DURING LAST_7_DAYS", "pageSize": 1000}}
```

A page comes back with `nextPageToken`. Send the same body with `"pageToken"` set to it for the
next page. Prefer `googleAds:search` to `googleAds:searchStream`, which returns every row in one
response. A response larger than `GOOGLE_ADS_MAX_RESPONSE_BYTES` (2 MiB) is not returned at all:
the tool says so and asks for a smaller page or a narrower query.

## Changing things: mutates

Every `*:mutate` takes `"validateOnly": true`. Google then checks the request without applying it,
which makes a free dry run. `POST /customers/{id}/googleAds:mutate` takes a list of operations of
different types in one atomic request. Within it, a new resource can be referred to before it
exists by a **temporary id**, a negative number in its resource name, e.g.
`customers/1234567890/campaignBudgets/-1`.

### Worked example: a YouTube Shorts campaign

**Unverified against a live account.** The field names come from the v26 Discovery
document. The sequence has not yet been run against a real account, and the schema does not
show whether a Shorts-only channel selection is accepted for every account. Run each step with
`validateOnly` first.

Shorts ads run as a **Demand Gen** campaign whose ad group serves only on YouTube Shorts. Standard
Video campaigns can't be used: the API can only read and report on them. Before you start:

- The video must already be on YouTube, public or unlisted. You need its video id.
- A logo image goes in as base64 inside the JSON body. Each HTTP request is capped at
  `MCP_MAX_REQUEST_BYTES` (4 MiB), so keep images small.

One `googleAds:mutate` body, with `1234567890` as the customer id:

```json
{"validateOnly": true, "mutateOperations": [
  {"campaignBudgetOperation": {"create": {
    "resourceName": "customers/1234567890/campaignBudgets/-1",
    "name": "Shorts budget", "amountMicros": "10000000",
    "deliveryMethod": "STANDARD", "explicitlyShared": false}}},
  {"campaignOperation": {"create": {
    "resourceName": "customers/1234567890/campaigns/-2",
    "name": "Shorts", "advertisingChannelType": "DEMAND_GEN", "status": "PAUSED",
    "campaignBudget": "customers/1234567890/campaignBudgets/-1",
    "maximizeConversions": {},
    "containsEuPoliticalAdvertising": "DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING"}}},
  {"adGroupOperation": {"create": {
    "resourceName": "customers/1234567890/adGroups/-3",
    "name": "Shorts only", "campaign": "customers/1234567890/campaigns/-2", "status": "ENABLED",
    "demandGenAdGroupSettings": {"channelControls": {"selectedChannels": {
      "youtubeShorts": true, "youtubeInStream": false, "youtubeInFeed": false,
      "discover": false, "gmail": false, "display": false, "maps": false}}}}}},
  {"assetOperation": {"create": {
    "resourceName": "customers/1234567890/assets/-4",
    "name": "Shorts video", "youtubeVideoAsset": {"youtubeVideoId": "<video id>"}}}},
  {"assetOperation": {"create": {
    "resourceName": "customers/1234567890/assets/-5",
    "name": "Logo", "imageAsset": {"data": "<base64 of a square logo>"}}}},
  {"adGroupAdOperation": {"create": {
    "adGroup": "customers/1234567890/adGroups/-3", "status": "ENABLED",
    "ad": {"name": "Shorts ad", "finalUrls": ["https://example.com/"],
      "demandGenVideoResponsiveAd": {
        "videos": [{"asset": "customers/1234567890/assets/-4"}],
        "logoImages": [{"asset": "customers/1234567890/assets/-5"}],
        "headlines": [{"text": "Short headline"}],
        "longHeadlines": [{"text": "A longer headline"}],
        "descriptions": [{"text": "What it is"}],
        "businessName": {"text": "Example"}}}}}}
]}
```

When Google accepts it, send it again without `validateOnly`. The campaign starts `PAUSED`.
Enabling it is the step that starts spending: a `campaignOperation` with `update` setting
`"status": "ENABLED"` and `"updateMask": "status"`.

## Credentials

Set `GOOGLE_ADS_CREDENTIALS_JSON` to one JSON object of either kind. Without it the server
uses Application Default Credentials. The OAuth scope is always
`https://www.googleapis.com/auth/adwords`.

- **A service account.** Create one in your Google Cloud project and download a JSON key.
  In Google Ads, as an administrator, open **Admin > Access and security**, then **Users**,
  then **+**, and add the service account's email with an access level ("Email only" is not
  supported). That access level is what the server can do. The value of the variable is the
  key file as-is (`"type": "service_account"`).
- **An OAuth user.** Create an OAuth client (Desktop) in the same project, consent once with
  the `adwords` scope (for example with Google's installed-app flow), and keep the refresh
  token. The value is
  `{"type": "authorized_user", "client_id": "...", "client_secret": "...", "refresh_token": "..."}`.
  Publish the OAuth consent screen ("In production"): refresh tokens issued while it is in
  Testing expire after 7 days.

**No developer token.** Google sunset developer tokens on 2026-09-09. API access now follows
the Google Cloud project that issued the credentials, at its access level (Test, Explorer,
Basic or Standard; see Google's "Access levels" page to apply for more). The server sends no
developer token and has no setting for one. A project with only Test access gets
`CLOUD_PROJECT_NOT_APPROVED_FOR_PRODUCTION` against a real account.

To act on a client account through a **manager account**, set
`GOOGLE_ADS_LOGIN_CUSTOMER_ID` to the manager's id, or pass a `login-customer-id` header on
one call.

## Run locally (stdio)

```bash
cd mcp/google-ads
make install            # creates .venv with the server and dev tools
```

Claude Code:

```bash
claude mcp add google-ads \
  --env "GOOGLE_ADS_CREDENTIALS_JSON=$(cat key.json)" \
  -- /absolute/path/to/mcp/google-ads/.venv/bin/google-ads-mcp
```

Claude Desktop / other clients (`mcpServers` JSON):

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "/absolute/path/to/mcp/google-ads/.venv/bin/google-ads-mcp",
      "env": {"GOOGLE_ADS_CREDENTIALS_JSON": "{\"type\": \"service_account\", ...}"}
    }
  }
}
```

## Run over HTTP / Docker

```bash
cd mcp/google-ads
cp .env.example .env    # set GOOGLE_ADS_CREDENTIALS_JSON and MCP_AUTH_TOKEN (openssl rand -hex 32)
docker compose up --build
```

Or pull the published image, `ghcr.io/<owner>/google-ads-mcp:latest`.

The MCP endpoint is `http://<host>:8000/mcp`, and clients must send
`Authorization: Bearer <MCP_AUTH_TOKEN>`. `GET /healthz` is unauthenticated for load
balancers. For Claude Code:

```bash
claude mcp add --transport http google-ads http://localhost:8000/mcp \
  --header "Authorization: Bearer <MCP_AUTH_TOKEN>"
```

Put the server behind TLS: the bearer token is only as private as the connection carrying it.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `GOOGLE_ADS_CREDENTIALS_JSON` | unset (ADC) | Service-account key or `authorized_user` JSON |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | unset | Manager account to act through; dashes are stripped |
| `GOOGLE_ADS_API_VERSION` | `v26` | The only version setting: the base URL and the Discovery URL both follow it |
| `GOOGLE_ADS_DISCOVERY_PATH` | unset | Local copy of the Discovery document (offline / restricted egress) |
| `GOOGLE_ADS_TIMEOUT_SECONDS` | `120` | Per-request timeout |
| `GOOGLE_ADS_MAX_RESPONSE_BYTES` | `2097152` (2 MiB) | Largest API response returned to the model |
| `MCP_TRANSPORT` | `stdio` (`http` in Docker) | `stdio` or `http` |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `8000` (`0.0.0.0` in Docker) | HTTP bind address |
| `MCP_AUTH_TOKEN` | unset | Bearer token; **required** in http mode |
| `MCP_ALLOW_UNAUTHENTICATED` | `false` | Set `true` to run http mode without a token |
| `MCP_MAX_REQUEST_BYTES` | `4194304` (4 MiB) | Largest HTTP request body |
| `MCP_STATELESS` | `false` | Set `true` to serve http mode without sessions. Use it on hosts that stop idle instances, or with several replicas behind a load balancer |

Bumping the API version is a one-line change to the default, plus re-cutting the test fixture
(see Development). Google ships a major version about every quarter and sunsets old ones.

## Security model

- **The token only goes to Google.** There is no base-URL setting. Requests go to
  `https://googleads.googleapis.com/<version>`, and the Discovery document comes from the same
  host. `path` must be a plain relative path (no scheme, host, `//`, `..`, query or fragment),
  so a prompt-injected model can't send your token elsewhere.
  - Callers can't override `Authorization`, `Host` or `User-Agent`.
  - `login-customer-id` and `linked-customer-id` must be customer ids.
- **Only two credential types load.** google-auth's generic loader also accepts
  `external_account` configurations, which can make the server fetch URLs or run programs.
  They are refused.
- **HTTP mode is closed by default.** The server won't start without `MCP_AUTH_TOKEN` unless you
  set `MCP_ALLOW_UNAUTHENTICATED=true`. Tokens are compared in constant time.
- **No server filesystem access.** No tool takes a local file path. Images go in as base64.
- **Accepted risk: anything the credential's Google Ads access level allows, a caller can do.**
  That includes spending money: launching campaigns, raising budgets and bids. The server has
  no spend guard and no read-only switch, on purpose: the limit is the credential. Give the
  service account or user the **narrowest access level** that does the job (Read only for
  reporting, Standard to manage campaigns), and set budgets and account spending limits in
  Google Ads. The tool descriptions ask the model to confirm spending actions with the user and
  to use `validateOnly` first. Neither is enforced.

## Limitations

- **No live calls in the tests.** Request shapes are checked against the Discovery document,
  and the Shorts example above has not yet been run against a real account.
- **Errors come back as results.** A Google error is returned with its status and body (and a
  `request-id` header to quote to Google support), not as a tool error. The server does not
  retry, so back off on `RESOURCE_EXHAUSTED`.
- **Discovery follows the published document**, which can briefly lag a release.
  `google_ads_request` works for any endpoint whether or not it is listed.
- **Two catch-all templates are shared.** `GET /{name}` is both `operations.get` and
  `operations.list`, so the describe tool returns both, each with its Discovery `id`.

## Development

The code is held to the same strict gates as every server in `mcp/`, configured in
`pyproject.toml` and run identically in CI (`.github/workflows/mcp.yml`): `ruff check` with
every rule family on and complexity ≤ 5, `ruff format --check`, `mypy --strict`, and `pytest`
with 100% line and branch coverage. The tests make no network calls: Google is a mock
transport, credentials are fakes, and HTTP and stdio are exercised with real servers.

`tests/fixtures/discovery.json` is cut from the real Discovery document (its `version` and
`revision` record which one) by `tests/cut_discovery.py`. It keeps a handful of methods,
including `adGroups:mutate`, and the schemas down to the Shorts channel setting. To re-cut it:

```bash
curl -sS -o /tmp/v26.json 'https://googleads.googleapis.com/$discovery/rest?version=v26'
.venv/bin/python -m tests.cut_discovery /tmp/v26.json tests/fixtures/discovery.json
```

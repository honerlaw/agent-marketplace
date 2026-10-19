# meta-ads-mcp

An MCP server that gives an LLM **full access to Meta's Marketing API** (the Graph API,
`v26.0`) for your own ad accounts, using a Meta system-user token. Instead of one tool per
endpoint, it exposes six generic tools that reach every Graph operation the token allows:
ad accounts, campaigns, ad sets, ads, creatives, images, audiences, insights and more. The
discovery tools read Meta's own machine-readable endpoint specs, so the model can look up
any endpoint's parameters and enum values before calling it.

| Tool | What it does |
|---|---|
| `meta_ads_request(method, path, query?, body?, body_format?)` | Any call, e.g. `GET /me/adaccounts`, `POST /act_<id>/campaigns`, `POST /<id>` (update), `DELETE /<id>` |
| `meta_ads_follow_page(url)` | Fetches the next or previous page: pass `paging.next` exactly as returned |
| `meta_ads_list_endpoints(text_filter?)` | Lists all 1,503 operations as `METHOD /{Node}/edge → Return` |
| `meta_ads_describe_endpoint(method, path)` | Parameters of one operation, with enum values |
| `meta_ads_describe_type(name)` | Fields of one object type (`Campaign`, `AdsInsights`, ...), with enum values, and its endpoints |
| `meta_ads_token_status()` | Whether the token is valid, its scopes, and when it (and its data access) expire |

Paths are relative to `https://graph.facebook.com/v26.0`. Templates name the object type in
braces: `/{AdAccount}/campaigns` is called as `/act_<account id>/campaigns`, `/me` is the
system user, and a bare numeric id is whatever object it was read as.

## Reading

Choose fields with the `fields` query parameter and page with `meta_ads_follow_page`:

```json
{"method": "GET", "path": "/act_123/campaigns",
 "query": {"fields": "name,status,objective,daily_budget", "limit": 50}}
```

Performance comes from the `insights` edge (`GET /act_123/insights` with `fields`,
`date_preset` or `time_range`, and `level`); `meta_ads_describe_type AdsInsights` lists its
fields. List and object query values are sent as JSON, as Graph expects:
`{"effective_status": ["ACTIVE"], "time_range": {"since": "2026-10-01", "until": "2026-10-18"}}`.
Graph's multi-object read (`GET /?ids=1,2,3`) is not available, because the bare `/` path is
refused (it is also the batch endpoint); read objects one at a time.

## Changing things

Create with `POST` to an edge, update with `POST` to the object, delete with `DELETE`. Bodies
are JSON by default. `body_format: "form"` sends form fields instead (nested values as JSON),
which is how an image goes to `POST /act_<id>/adimages` as base64 `bytes`. Videos go to
`POST /act_<id>/advideos` with a public `file_url`. Budgets are in the account currency's
minor units (cents for USD).

### Worked example: a paused campaign, ad set and ad

**Unverified against a live write**: the tests check the request shapes against mocks only.
Create everything `PAUSED`, read it back, and activate it only once a person has checked it.

1. `POST /act_<id>/campaigns` with `{"name": "...", "objective": "OUTCOME_TRAFFIC",
   "status": "PAUSED", "special_ad_categories": []}`.
2. `POST /act_<id>/adsets` with the campaign id, `daily_budget`, `billing_event`,
   `optimization_goal`, `targeting` (e.g. `{"geo_locations": {"countries": ["US"]}}`) and
   `"status": "PAUSED"`.
3. Upload an image: `POST /act_<id>/adimages`, `body_format: "form"`, `{"bytes": "<base64>"}`;
   keep the returned `hash`.
4. `POST /act_<id>/adcreatives` with an `object_story_spec` naming your Page and a
   `link_data` using the image hash.
5. `POST /act_<id>/ads` with the ad set id, `{"creative": {"creative_id": "<id>"}}` and
   `"status": "PAUSED"`.
6. Activate with `POST /<ad set id>` and `POST /<campaign id>` setting `"status": "ACTIVE"`.
   This spends money.

`meta_ads_describe_endpoint POST /{AdAccount}/adsets` lists every parameter and its enum
values.

## Getting a system-user token

1. **App.** At developers.facebook.com, create an app of type Business, add the **Marketing
   API** product, and note the App ID and App Secret (App settings → Basic). Development mode
   is enough for your own ad accounts.
2. **System user.** In Business Settings → Users → System users, add one (Admin for full
   access).
3. **Assets.** Select the system user → Assign assets: your ad account(s) with full control,
   the Facebook Page your ads run from, the app, and any Instagram account, pixel or catalog
   you use.
4. **Token.** Select the system user → Generate new token → your app → expiration
   **Never** if offered → permissions `ads_management`, `ads_read`, `business_management`,
   `pages_show_list`, `pages_read_engagement` (plus `pages_manage_ads` or
   `catalog_management` if you use them). Copy the token: Meta shows it once.

The token reaches exactly the assets you assigned and the permissions you granted. Grant
`ads_read` alone for a reporting-only agent.

**Token lifetime.** Meta offers never-expiring system-user tokens and 60-day ones, and makes
some businesses use the 60-day kind. `meta_ads_token_status` reports `expires_at` ("never" or
a date) and `data_access_expires_at`, the separate clock on reading user data. A 60-day token
must be refreshed before it lapses:

```
GET https://graph.facebook.com/v26.0/oauth/access_token?grant_type=fb_exchange_token
    &client_id=<app id>&client_secret=<app secret>&set_token_expires_in_60_days=true
    &fb_exchange_token=<current token>
```

Deploy the new token, then revoke the old one. The server does not refresh tokens itself: it
keeps no state, so a refreshed token would be lost on restart.

## Run locally (stdio)

```bash
cd mcp/meta-ads
make install            # creates .venv with the server and dev tools
make specs              # fetches and verifies Meta's endpoint specs into ./specs
```

Claude Code:

```bash
claude mcp add meta-ads \
  --env META_ADS_ACCESS_TOKEN=... --env META_APP_ID=... --env META_APP_SECRET=... \
  --env META_ADS_SPEC_PATH=/absolute/path/to/mcp/meta-ads/specs \
  -- /absolute/path/to/mcp/meta-ads/.venv/bin/meta-ads-mcp
```

Without `META_ADS_SPEC_PATH` the server fetches the same pinned specs from GitHub on first
use and checks them the same way.

## Run over HTTP / Docker

```bash
cd mcp/meta-ads
cp .env.example .env    # set the META_* values and MCP_AUTH_TOKEN (openssl rand -hex 32)
docker compose up --build
```

Or pull the published image, `ghcr.io/<owner>/meta-ads-mcp:latest`. The image carries the
specs, so a running container talks only to `graph.facebook.com`. Building it fetches them
from `codeload.github.com`, so the build is not hermetic.

The MCP endpoint is `http://<host>:8000/mcp`, and clients must send
`Authorization: Bearer <MCP_AUTH_TOKEN>`. `GET /healthz` is unauthenticated for load
balancers. Put the server behind TLS.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `META_ADS_ACCESS_TOKEN` | unset | The system-user token; tools that call Meta fail without it |
| `META_APP_ID` / `META_APP_SECRET` | unset | Set both or neither; with them every call is signed with `appsecret_proof` and `meta_ads_token_status` works |
| `META_ADS_API_VERSION` | `v26.0` | The only version setting; the base URL follows it |
| `META_ADS_SPEC_PATH` | unset (`/app/specs` in Docker) | Directory of Meta's spec files; unset, they are fetched on first use |
| `META_ADS_TIMEOUT_SECONDS` | `120` | Timeout for each phase of a request |
| `META_ADS_MAX_RESPONSE_BYTES` | `2097152` (2 MiB) | Largest API response, or discovery output, returned to the model |
| `MCP_TRANSPORT` | `stdio` (`http` in Docker) | `stdio` or `http` |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `8000` (`0.0.0.0` in Docker) | HTTP bind address |
| `MCP_AUTH_TOKEN` | unset | Bearer token; **required** in http mode |
| `MCP_ALLOW_UNAUTHENTICATED` | `false` | Set `true` to run http mode without a token |
| `MCP_MAX_REQUEST_BYTES` | `4194304` (4 MiB) | Largest HTTP request body (and so the largest upload) |
| `MCP_STATELESS` | `false` | Set `true` to serve http mode without sessions |

**Versions.** Bumping the Graph version is a one-line change to the default. The endpoint
specs are pinned separately (`SPEC_COMMIT` and `SPEC_CONTENT_HASH` in
`src/meta_ads_mcp/spec_fetch.py`); Meta's codegen repository is not versioned per Graph
version, so the catalog describes the API as the SDK saw it on the pinned commit (2026-09-17,
which targets `v26.0`) and can differ slightly from the live API. Meta retires Graph versions
about two years after release.

## Security model

- **The token only goes to Meta.** There is no base-URL setting. The token travels in the
  `Authorization` header to `https://graph.facebook.com/<version>`, never in a URL, with one
  exception: `meta_ads_token_status` sends it as `debug_token`'s `input_token` query
  parameter, the only way Graph accepts it there; `path` must
  be a plain relative path (no scheme, host, `//`, query, fragment, or `.`/`..` segment,
  including percent-encoded and double-encoded forms).
- **The server owns the credential parameters.** A caller may not set `access_token`,
  `appsecret_proof`, `batch`, `adbatch`, `method`, `suppress_http_code` or `callback` in the
  query or the body (compared after normalizing case, `.` and spaces to `_`, and `[...]`
  suffixes), and may set no headers at all. `batch` and `adbatch` (the async batch edge) would
  carry unguarded relative URLs and bodies, and `method` silently changes the verb. Graph batch
  requests, sync and async, and the bare `/` path are therefore refused.
- **Pagination URLs are checked.** `meta_ads_follow_page` accepts only `https` on
  `graph.facebook.com` under the configured version, with no userinfo, port or fragment; Meta's
  own credential parameters are dropped and the server's re-added.
- **Credentials never reach the model.** Every result and every error is scrubbed: the token,
  the app secret and the proof are replaced wherever they appear; `paging` URLs lose Meta's
  credential parameters; any JSON field named `access_token`, and any string shaped like a Meta
  access token (`EAA` and a long alphanumeric run, which catches aliased fields such as
  `fields=access_token.as(x)`), is redacted. Bodies that parse as JSON are treated as JSON
  whatever their content type, so the key rule always applies. Page tokens and minted tokens
  can't be obtained through this server, by design: the system user already holds the assets.
- **Logs carry no credential.** The HTTP client libraries log full request URLs at INFO, and
  every URL carries `appsecret_proof` (`debug_token`'s carries the token), so the server holds
  those loggers at WARNING.
- **`appsecret_proof`.** With the app secret set, every call carries HMAC-SHA256 of the token
  (key: app secret), so a leaked token alone is less useful.
- **HTTP mode is closed by default**, and no tool takes a local file path.
- **Accepted risk: anything the token allows, a caller can do**, including spending money. There
  is no read-only switch, on purpose: the limit is the token's assigned assets and permissions
  and the ad account's spending limit. The tool descriptions ask the model to create things
  `PAUSED` and to confirm spending with the user. Neither is enforced.

## Limitations

- **No batch requests** (sync or async), no `GET /?ids=` multi-read, and no chunked video upload (that runs on `graph-video.facebook.com`);
  use `file_url` for videos.
- **Writes are unverified live**: request shapes are tested against mocks; JSON bodies on every
  write endpoint are assumed (use `body_format: "form"` if one refuses JSON).
- **Errors come back as results**, with Meta's status, body and `x-fb-trace-id`. The server does
  not retry. Rate limits are Graph errors 4, 17, 613 and 80000-80014, and the
  `x-business-use-case-usage` / `x-ad-account-usage` headers show how close you are. A new app
  starts on Meta's rate-limited development tier.
- **Any `access_token` field, and any token-shaped string, in a response is redacted**,
  including page tokens.

## Development

The code is held to the same strict gates as every server in `mcp/` (see `mcp/README.md`).
The tests make no network calls: Meta is a mock transport with sentinel credentials, and HTTP
and stdio are exercised with real servers. `tests/test_secrets.py` checks that no tool
result, error or log line carries a credential.

`tests/fixtures/specs/` is cut from the pinned specs by `tests/cut_specs.py` (five object types
whole, and the enums they use), and `tests/fixtures/specs.sha256` is its own content hash,
which the tests pin. To re-cut after a re-pin:

```bash
.venv/bin/meta-ads-fetch-specs /tmp/meta-specs
.venv/bin/python -m tests.cut_specs /tmp/meta-specs
```

The specs come from
[facebook/facebook-business-sdk-codegen](https://github.com/facebook/facebook-business-sdk-codegen)
under its own licence, which the image carries as `/app/specs/LICENSE`.

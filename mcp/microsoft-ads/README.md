# microsoft-ads-mcp

An MCP server that gives an LLM **read and write access to the Microsoft Advertising API**
(Bing Ads API v13, its JSON REST interface) for your own accounts. It can create, change,
pause and delete campaigns, ad groups, ads, keywords and budgets, and run reports.

It does not have one tool per endpoint. Instead it exposes five generic tools that reach
every operation in the catalog: 291 operations across Campaign Management, Bulk,
Reporting, Ad Insight, Customer Management and Customer Billing. The model calls an
operation **by name**. The server looks up the operation's fixed method, host and path in
a catalog built from Microsoft's own Python SDK, so the model never supplies a URL.

| Tool | What it does |
|---|---|
| `microsoft_ads_request(operation, body?, customer_id?, account_id?)` | Calls one operation by name, e.g. `AddCampaigns` or `GetAdGroupsByCampaignId`, with a JSON body |
| `microsoft_ads_list_operations(text_filter?)` | Lists the operations as `Service.Name — METHOD /path → RequestType` |
| `microsoft_ads_describe_operation(operation)` | Shows request and response fields by wire name, the fields of the types they name, and enum values |
| `microsoft_ads_describe_type(name, service?)` | Shows a type's fields (inherited ones included) and its subtypes with the `"Type"` each needs, or an enum's values |
| `microsoft_ads_download_file(url)` | Downloads a report or bulk result file and returns its CSV/TSV text, with no credentials sent |

Things the model needs to know (also in the tool descriptions):
- **Ids are JSON strings**, e.g. `"AccountId": "123"`.
- **Money is in the account currency, not micros:** `"DailyBudget": 25` means 25.00.
- **Polymorphic objects need a `"Type"`.** An ad is `{"Type": "ResponsiveSearch", ...}` and
  a text asset is `{"Type": "TextAsset", "Text": "..."}`. `microsoft_ads_describe_type Ad`
  lists every subtype with the value to send.
- **Every read is a POST.** Add is POST, Update is PUT, and Delete is DELETE with a JSON
  body. The server picks the verb; the model only names the operation.

## Reading

```json
{"operation": "GetCampaignsByAccountId",
 "body": {"AccountId": "123", "CampaignType": "Search"}}
```

Most `Get…` operations are **not paged**. `GetKeywordsByAdGroupId`, for example, returns the
whole ad group in one response. For a large account, download the entities instead with
`DownloadCampaignsByAccountIds` (Bulk), poll `GetBulkDownloadStatus`, and read the file with
`microsoft_ads_download_file`. A response larger than `MICROSOFT_ADS_MAX_RESPONSE_BYTES`
(2 MiB by default) is refused, not truncated.

**Reports** run asynchronously:
1. `SubmitGenerateReport` with a `ReportRequest` whose `"Type"` names the report, e.g.
   `CampaignPerformanceReportRequest`, with `Columns`, `Scope` and `Time`.
2. `PollGenerateReport` until `ReportRequestStatus.Status` is `Success`.
3. `microsoft_ads_download_file` on `ReportDownloadUrl` within **five minutes**. If the link
   expires, poll again for a fresh one. A null URL means there was no data.

The zip is unpacked and the CSV returned as text.

## Changing things

Writes **change live campaigns and spend real money**:
- Create campaigns, ad groups and ads with `"Status": "Paused"`.
- Confirm enabling them, and any budget or bid increase, with the person you are working
  for.

Add, Update and Delete can **partly succeed**: ids come back `null` where an item failed,
with a `PartialErrors` list. Per call you can send at most 100 campaigns, 1,000 ad groups,
50 ads or 1,000 keywords.

When Microsoft throttles you it returns error code 117 `CallRateExceeded` (Campaign
Management and Ad Insight, 60-second window), 207 (Reporting) or 4204 (Bulk). Wait before
retrying; the server does not retry for you.

### Worked example: a paused search campaign, ad group, keywords and ad

Each step is `microsoft_ads_request` with the operation and body shown. This sequence has not
yet been run against a live account (see [Limitations](#limitations)).

1. `AddCampaigns`, which returns `CampaignIds`:
   ```json
   {"AccountId": "123", "Campaigns": [{"Name": "Spring sale", "CampaignType": "Search",
     "BudgetType": "DailyBudgetStandard", "DailyBudget": 25, "TimeZone": "PacificTimeUSCanadaTijuana",
     "Languages": ["English"], "Status": "Paused"}]}
   ```
2. `AddAdGroups`, which returns `AdGroupIds`:
   ```json
   {"CampaignId": "<campaign id>", "AdGroups": [{"Name": "Shoes", "Status": "Paused",
     "CpcBid": {"Amount": 0.75}}]}
   ```
3. `AddKeywords`:
   ```json
   {"AdGroupId": "<ad group id>", "Keywords": [
     {"Text": "running shoes", "MatchType": "Phrase", "Bid": {"Amount": 0.9}}]}
   ```
4. `AddAds`, a responsive search ad, which needs at least 3 headlines and 2 descriptions:
   ```json
   {"AdGroupId": "<ad group id>", "Ads": [{"Type": "ResponsiveSearch", "Status": "Paused",
     "FinalUrls": ["https://example.com/shoes"],
     "Headlines": [{"Asset": {"Type": "TextAsset", "Text": "Running Shoes"}},
                   {"Asset": {"Type": "TextAsset", "Text": "Free Shipping"}},
                   {"Asset": {"Type": "TextAsset", "Text": "Spring Sale"}}],
     "Descriptions": [{"Asset": {"Type": "TextAsset", "Text": "Shoes for every run."}},
                      {"Asset": {"Type": "TextAsset", "Text": "Order today."}}]}]}
   ```
5. Review the setup with the person you are working for, then enable it with
   `UpdateCampaigns` and `UpdateAdGroups`, sending `{"Id": "...", "Status": "Active"}`.

To undo, call `DeleteCampaigns` with `{"AccountId": "123", "CampaignIds": ["<id>"]}`.

## Credentials

The API takes four things: an OAuth access token for a Microsoft Advertising user, a
**developer token**, and the `CustomerId` and `CustomerAccountId` of the account being used.
The server refreshes access tokens itself from a refresh token. Microsoft offers only
**user-delegated** OAuth, with no client-credentials (app-only) flow, so you sign in once as
a user who can manage the accounts.

1. **Register an app** in the Microsoft Entra admin center: App registrations, then New
   registration.
   - Supported account types: "Accounts in any organizational directory and personal
     Microsoft accounts" (tenant `common`), unless you only use work accounts.
   - Choose one kind of app:
     - **Web**, with a client secret (Certificates & secrets). Microsoft recommends this for
       a server: the refresh token is bound to the secret.
     - **Mobile and desktop** (a public client), with no secret. Leave
       `MICROSOFT_ADS_CLIENT_SECRET` empty, because a public client must not send one.
   - Redirect URI: e.g. `https://localhost/callback` (Web) or
     `https://login.microsoftonline.com/common/oauth2/nativeclient` (public).
2. **Get a refresh token** once, in a browser, signed in as a user with access to the
   accounts:
   1. Open
      `https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=<client id>&response_type=code&redirect_uri=<redirect uri>&response_mode=query&scope=https%3A%2F%2Fads.microsoft.com%2Fmsads.manage%20offline_access&state=x`
   2. Copy the `code` from the redirect.
   3. Exchange it:
      ```sh
      curl -s https://login.microsoftonline.com/common/oauth2/v2.0/token \
        -d client_id=<client id> -d client_secret=<secret, Web apps only> \
        -d grant_type=authorization_code -d code=<code> -d redirect_uri=<redirect uri> \
        -d scope="https://ads.microsoft.com/msads.manage offline_access"
      ```
   4. The `refresh_token` in the response is `MICROSOFT_ADS_REFRESH_TOKEN`.
3. **Developer token:** sign in to the Microsoft Advertising Developer Portal
   (`https://developers.ads.microsoft.com`) and request one under Account. For the sandbox,
   use the universal sandbox token `BBD37VB98`.
4. **Ids:** with only the credentials set, call `GetUser` with `{"UserId": null}`. That
   returns your user and `CustomerRoles`. Then call `SearchAccounts` to find account ids.
   Put them in `MICROSOFT_ADS_CUSTOMER_ID` / `MICROSOFT_ADS_ACCOUNT_ID`, or pass
   `customer_id` / `account_id` per call.

### Refresh-token rotation

**Microsoft returns a new refresh token every time the server refreshes an access token**
(about hourly while in use). The server uses the new one for its next refresh, but keeps it
**only in memory**. After a restart it starts again from `MICROSOFT_ADS_REFRESH_TOKEN`.

Microsoft does not revoke the old token when it issues a new one. It does expire refresh
tokens: they have no fixed lifetime ("e.g. 90 days" for public clients), and can be
invalidated at any time, for example by a password change or an admin.

When the configured one stops working, every call fails with a message naming
`invalid_grant`. Run the consent flow above again and update the variable. Plan to re-issue
it well inside 90 days. Persisting rotated tokens would need durable storage, which this
server does not have.

### Sandbox

Set `MICROSOFT_ADS_ENVIRONMENT=sandbox` to send every call to the
`*.api.sandbox.bingads.microsoft.com` hosts and request the sandbox scope
`https://si.ads.microsoft.com/msads.manage`. That scope is the msads SDK's default; older
documentation names others.
- A sandbox needs its own sandbox account (sign up at `https://ads.sandbox.microsoft.com`)
  and the sandbox developer token `BBD37VB98`.
- Sandbox writes spend nothing, which makes the sandbox the safe place to try the worked
  example.
- Sandbox sign-in has not yet been verified against a live sandbox call.

## Run locally (stdio)

```sh
make install
MICROSOFT_ADS_CLIENT_ID=... MICROSOFT_ADS_REFRESH_TOKEN=... MICROSOFT_ADS_DEVELOPER_TOKEN=... \
  .venv/bin/microsoft-ads-mcp
```

Or add it to an MCP client:

```json
{"mcpServers": {"microsoft-ads": {
  "command": "/path/to/mcp/microsoft-ads/.venv/bin/microsoft-ads-mcp",
  "env": {"MICROSOFT_ADS_CLIENT_ID": "...", "MICROSOFT_ADS_CLIENT_SECRET": "...",
          "MICROSOFT_ADS_REFRESH_TOKEN": "...", "MICROSOFT_ADS_DEVELOPER_TOKEN": "...",
          "MICROSOFT_ADS_CUSTOMER_ID": "...", "MICROSOFT_ADS_ACCOUNT_ID": "..."}}}}
```

The discovery tools work with no credentials at all.

## Run over HTTP / Docker

```sh
cp .env.example .env   # fill it in, including MCP_AUTH_TOKEN
docker compose up --build
```

The image serves streamable HTTP on port 8000 at `/mcp`. Clients must send
`Authorization: Bearer $MCP_AUTH_TOKEN`. `/healthz` is open. CI publishes the image as
`ghcr.io/<owner>/microsoft-ads-mcp`.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `MICROSOFT_ADS_CLIENT_ID` | — | Entra app (client) id. Needed for API calls |
| `MICROSOFT_ADS_CLIENT_SECRET` | — | Web apps only; leave unset for a public client |
| `MICROSOFT_ADS_REFRESH_TOKEN` | — | From the consent flow. Needed for API calls |
| `MICROSOFT_ADS_DEVELOPER_TOKEN` | — | Sent as `DeveloperToken`. Needed for API calls |
| `MICROSOFT_ADS_CUSTOMER_ID` / `MICROSOFT_ADS_ACCOUNT_ID` | — | Default `CustomerId` / `CustomerAccountId` (digits). The header is omitted when unset |
| `MICROSOFT_ADS_ENVIRONMENT` | `production` | `production` or `sandbox`: picks the API hosts and the OAuth scope |
| `MICROSOFT_ADS_TENANT` | `common` | `common`, `organizations`, `consumers`, a tenant GUID or a domain |
| `MICROSOFT_ADS_DOWNLOAD_HOSTS` | `blob.core.windows.net,bingads.microsoft.com` | Domains `microsoft_ads_download_file` may fetch from (see below) |
| `MICROSOFT_ADS_TIMEOUT_SECONDS` | `120` | Per-request timeout |
| `MICROSOFT_ADS_MAX_RESPONSE_BYTES` | `2097152` | Largest API response, downloaded file (once unpacked) or discovery output returned |
| `MCP_TRANSPORT` | `stdio` (`http` in Docker) | `stdio` or `http` |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `8000` | HTTP bind address |
| `MCP_AUTH_TOKEN` | — | Bearer token HTTP clients must send. Required in http mode |
| `MCP_ALLOW_UNAUTHENTICATED` | `false` | Allow http mode without `MCP_AUTH_TOKEN` |
| `MCP_MAX_REQUEST_BYTES` | `4194304` | Largest MCP request body |
| `MCP_STATELESS` | `false` | Serve http without sessions |

The credentials are not needed to start: the server starts, answers `/healthz` and serves the
discovery tools without them. An API call without them fails with a message naming the
missing variables. Values that are set are checked at start.

## Security model

- **Fixed hosts, no caller URLs.** `microsoft_ads_request` takes an operation **name**. The
  method and path come from the committed catalog, and the host from a fixed table for the
  configured environment (`campaign`, `bulk`, `reporting`, `adinsight` or `clientcenter` on
  `.api[.sandbox].bingads.microsoft.com`). The caller supplies no path, host, query or
  header, so there is no path validator to get wrong.
- **Fixed token URL.** There is no base-URL or token-URL setting. Credentials can reach only
  `login.microsoftonline.com/<tenant>` and the Microsoft Advertising hosts.
- **Per-call ids are validated** as digits before they become headers.
- **Credentials never reach the model.** Every tool result and error has every credential
  literal replaced with `[redacted]`: the client secret, the developer token, the configured
  refresh token, and each access and refresh token issued since start. No credential is
  ever put in a URL, and the HTTP client libraries' loggers are held at WARNING.
- **Result-file downloads carry no credentials.** `microsoft_ads_download_file` fetches
  Microsoft's self-authorizing report and bulk URLs:
  - It sends no `Authorization` or `DeveloperToken` header and follows no redirects.
  - It accepts only `https` URLs with no userinfo, port or fragment, whose host equals an
    allowlisted domain or ends in `.` plus one. So `evilbingads.microsoft.com` is refused.
  - **The default allowlist is provisional and broad.** `blob.core.windows.net` matches every
    Azure customer's storage account, not only Microsoft's. A prompt-injected model could
    therefore fetch an attacker's blob, pulling untrusted text into its context and sending
    whatever it puts in the URL to that host. No secret can leak this way, because none is
    sent.
  - The real report host has not been measured yet. Once you have seen it, narrow
    `MICROSOFT_ADS_DOWNLOAD_HOSTS` to that storage account, e.g.
    `<account>.blob.core.windows.net`.
- **No filesystem arguments**, so nothing can read or write server-local files over HTTP.
- **HTTP mode requires a bearer token** unless you explicitly opt out.
- **No read-only switch, on purpose.** The bound on what the model can do is the OAuth user's
  access to accounts and each account's own budgets. Give the server a user whose access
  matches what you want it to touch.

**Egress hosts:**
- `login.microsoftonline.com`;
- `campaign`, `bulk`, `reporting`, `adinsight` and `clientcenter`, each under
  `.api.bingads.microsoft.com` (or `.api.sandbox.bingads.microsoft.com`);
- the download allowlist.

Building or running the image fetches nothing else. `make catalog` alone downloads the msads
sdist from `files.pythonhosted.org`.

## The operation catalog

Microsoft publishes no OpenAPI document. The catalog comes from Microsoft's official Python
SDK, `msads`:
- Pinned version: **13.0.30.1**, sdist sha256
  `6d3c0fd82595750bd19d1ea4cb91f6bf31775f31b9cdcee75028428ba7ff801d`.
- The SDK's generated REST client (`openapi_client/`) is read with Python's `ast`. It is
  never imported or run, and it is not a dependency.
- The result is committed as `src/microsoft_ads_mcp/catalog.json`, holding for each
  operation its method, path, and request and response types, plus every type's fields and
  every enum's values.
- The SDK's MIT licence ships beside it as `catalog.LICENSE`.
- The catalog's `source` records the version and sha, and a test ties them to the pin in
  `catalog_build.py`. Hand edits to the rest of the file are caught only by review.

To re-pin, change `VERSION`, `SDIST_SHA256` and `SDIST_URL` in `catalog_build.py` and run
`make catalog`. The builder refuses a download with another hash, and fails loudly on any
SDK code shape it does not recognise rather than skipping it. Then update the per-service
counts in `tests/test_discovery.py`.

Polymorphic types are described with the `"Type"` value to send:
- The value listed in the subtype's own `Type` enum is marked `documented`. Microsoft's REST
  examples send that short form, e.g. `"ResponsiveSearch"`.
- Other spellings the SDK also parses are listed as `sdk_aliases`.
- `documented: false` means no enum confirms the value: it is the one value the SDK
  dispatches on.

## Limitations

- **Not yet run against a live account.** The live smoke run (`GetUser`,
  `GetCampaignsByAccountId`, a one-day report download) and a live zero-spend write are pending
  credentials. Every path, reads and writes, is tested against a mock of Microsoft only, so
  sign-in, the sandbox scope and the request shapes are as documented, not as observed.
- **Downloads are unverified live.** The report download path is tested the same way, and the
  default download allowlist is a guess (see the security model).
- **11 operations have no Microsoft Learn reference page.** They are in the SDK, but their REST
  behaviour is unverified: GetConfigValue, GetCampaignSizesByAccountId, GetCurrentUser,
  GetAccessibleCustomer, GetPilotFeaturesCountries, AddPrepayAccount, UpdatePrepayAccount,
  MapAccountIdToExternalAccountIds, MapCustomerIdToExternalCustomerId,
  UpgradeCustomerToAgency, UploadEntityRecords. Ad Insight's PutMetricData is in neither the
  docs nor the SDK, so it is not in the catalog.
- **No bulk upload.** Bulk upload POSTs a multipart file **with credentials** to a URL the API
  returns, so it is left out. Bulk download works.
- **The catalog is a snapshot** of msads 13.0.30.1. An operation Microsoft adds later needs a
  re-pin. A field added later can still be sent, because bodies pass through as written.
- **Unpaged reads** return whole collections. Use Bulk download for big accounts.
- **Refresh tokens rotate and are kept in memory only.** See
  [Refresh-token rotation](#refresh-token-rotation).
- **One known SDK quirk:** `AuditPointResult.Details` is mistyped in the SDK and is shown as
  `object`.

## Development

```sh
make install   # once
make check     # ruff, ruff format --check, mypy --strict, pytest with 100% line+branch coverage
make catalog   # re-download the pinned msads sdist and regenerate catalog.json
```

The tests need no network. They run against the committed catalog, a small fixture sdist
built in memory, and a mock of Microsoft's token and API hosts.

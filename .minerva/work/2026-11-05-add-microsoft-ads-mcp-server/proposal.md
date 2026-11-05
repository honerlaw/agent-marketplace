# Proposal: add-microsoft-ads-mcp-server

**Date**: 2026-11-05
**Status**: Shipped (2026-11-05)

## Goal
`mcp/microsoft-ads/`: an MCP server that gives an LLM read and write access to the Microsoft
Advertising API (Bing Ads API **v13**, its JSON **REST** interface) for the operator's own
accounts, so it can create, change, pause and delete campaigns, ad groups, ads, keywords and
budgets, and run reports. It reaches the API through a few generic tools driven by an operation
catalog. It has the same layout, gates and image contract as `mcp/google-ads/` and `mcp/meta-ads/`,
and keeps the operator's credentials out of the model's context.

"Full" means every operation in the pinned SDK catalog: 291 operations across the six services
(Campaign Management, Bulk, Reporting, Ad Insight, Customer Management, Customer Billing). It has
these limitations:
- **11 operations have no Learn reference page.** They are in the SDK but unverified on REST, and
  the README lists them: GetConfigValue, GetCampaignSizesByAccountId, GetCurrentUser,
  GetAccessibleCustomer, GetPilotFeaturesCountries, AddPrepayAccount, UpdatePrepayAccount,
  MapAccountIdToExternalAccountIds, MapCustomerIdToExternalCustomerId, UpgradeCustomerToAgency,
  UploadEntityRecords. A twelfth WSDL operation, Ad Insight's PutMetricData, has neither a Learn
  page nor an SDK entry, so it is not in the catalog.
- no bulk **upload**: it would send credentials to a URL the API returns;
- no operation absent from the pinned catalog (a re-pin adds it);
- no client-credentials flow, because Microsoft offers only user-delegated OAuth.

Two paths stay **unverified live until their manual criteria run**:
- **Writes** are built and tested against mocks. The first live write is criterion 9, a manual,
  owner-approved step.
- **Report and bulk-file downloads** use a provisional host allowlist. Criterion 7 measures the real
  host. Until then an operator may need `MICROSOFT_ADS_DOWNLOAD_HOSTS`, and a follow-up that pins the
  default to the measured host is expected.

## Why
The owner wants Microsoft Advertising behind the same MCP setup as Google, Meta, Reddit and OpenAI
ads, with full campaign control. Microsoft's own hosted MCP server
(`https://partner.api.bingads.microsoft.com/ext/mcp/vnext`, Learn guide updated 2026-10-20) is live
but documented as read and reporting only. It also needs per-user Entra OAuth, so it cannot create
or change campaigns.

Facts, measured 2026-11-05 unless marked "docs":
- **REST covers all six services.** All 280 documented operation pages give a REST URL.
  - Paths are fixed literals with **no path parameters**, e.g. `POST /CampaignManagement/v13/Campaigns`
    (AddCampaigns) and `POST /CampaignManagement/v13/Campaigns/QueryByAccountId`. Ids travel in the
    JSON body.
  - Verbs: Add = POST, Update = PUT, Delete = DELETE **with a JSON body**, and every Get/Query = POST.
    GET to a resource path returns 405.
- **Hosts.** Each service has its own host; the sandbox inserts `.sandbox`.

  | Service | Host |
  |---|---|
  | Campaign Management | `campaign.api.bingads.microsoft.com` |
  | Bulk | `bulk.api.bingads.microsoft.com` |
  | Reporting | `reporting.api.bingads.microsoft.com` |
  | Ad Insight | `adinsight.api.bingads.microsoft.com` |
  | Customer Management | `clientcenter.api.bingads.microsoft.com` |
  | Customer Billing | `clientcenter.api.bingads.microsoft.com` |

  - The sandbox form is `<x>.api.sandbox.bingads.microsoft.com`.
  - The first path segment names the service.
- **Microsoft publishes no OpenAPI document.**
  - The SOAP WSDLs list 292 operations but carry no REST paths or verbs.
  - The official Python SDK `msads` 13.0.30.1 (PyPI, **MIT**, uploaded 2026-10-14) ships an
    OpenAPI-Generator client, `openapi_client/`. It holds `method=` and `resource_path=` literals for
    **291 operations** (POST 222, PUT 36, DELETE 33) and Pydantic v2 models with wire-name aliases.
  - The sdist is `msads-13.0.30.1.tar.gz`: 675,518 bytes, sha256
    `6d3c0fd82595750bd19d1ea4cb91f6bf31775f31b9cdcee75028428ba7ff801d`. PyPI files are immutable, so
    the bytes themselves are pinnable.
  - A prototype that reads the sdist with `ast` (no import) produced 291 operations, 1,286 object
    types and 214 enums. Serialized compactly, that catalog is about 344 KB.
  - 39 type names repeat across services.
  - Polymorphic types (`Ad`, `AdExtension`, criteria and others) carry a `"Type"` discriminator.
    The generated `from_dict` maps discriminator values to subclasses. Some subclasses have two
    values, e.g. `ResponsiveSearch` and `ResponsiveSearchAd`.
  - The Learn REST example for AddAds sends the short form, `"Type": "AppInstall"`, which is the
    `AdType` enum value. So the documented spelling is the one in the base type's `Type` enum.
  - Normalized operation names (lowercase, `_` removed) are unique across all 291 operations. Paths
    are not unique: one path serves POST, PUT and DELETE.
- **Auth (docs).**
  - OAuth 2.0, user-delegated only. The token endpoint is
    `https://login.microsoftonline.com/<tenant>/oauth2/v2.0/token` (default tenant `common`).
  - The scope is `https://ads.microsoft.com/msads.manage offline_access`. The SDK's sandbox default
    is `https://si.ads.microsoft.com/msads.manage`.
  - A client secret is needed only for a Web (confidential) app; a public client must not send one.
  - Refresh tokens rotate: a new one comes back on each refresh, and the old one is "not revoked"
    but should be discarded. They have no fixed lifetime ("e.g. 90 days" for public clients) and
    can return `invalid_grant` at any time.
  - Every REST call carries `Authorization: Bearer`, `DeveloperToken`, `CustomerId` and
    `CustomerAccountId`. The sandbox developer token is `BBD37VB98`.
- **Limits (docs).**
  - Money is in account-currency units as decimals, not micros. Long ids are JSON **strings**.
  - Most Get operations are **unpaged**: GetKeywordsByAdGroupId returns everything. About 11
    operations take `PageInfo {Index, Size}`.
  - Per-call caps: 100 campaigns, 1,000 ad groups, 50 ads, 1,000 keywords.
  - Throttling: `117 CallRateExceeded` (60 s window), `207` (Reporting), `4204` (Bulk). No
    `Retry-After` header.
- **Errors (measured unauthenticated, plus docs).** There are two body shapes.
  - Auth faults: HTTP 401 with `AdApiFaultDetail {Errors:[{Code, ErrorCode, Message}]}`.
  - Service faults: `ApiFaultDetail {BatchErrors, OperationErrors}`.
  - Add, Update and Delete succeed partially: ids come back null at failed positions, plus
    `PartialErrors`.
  - Responses carry a `TrackingId` field and an `x-ms-trackingid` header.
- **Reports and bulk downloads (docs).**
  - Flow: SubmitGenerateReport, then PollGenerateReport, then `ReportDownloadUrl`. The URL is valid
    for **5 minutes**, is a zip of CSV/TSV, and is null when there is no data.
  - The SDK GETs it with no credentials, so it is a self-authorizing URL. The docs say not to
    depend on its domain; the real host is not yet measured.
  - Bulk download works the same way.
  - Bulk **upload** POSTs multipart to a returned URL **with** auth headers, and the docs and the
    SDK disagree on the header names.
- **Versions.** v13 is current with no v14 announced. SOAP is deprecated on 2027-01-31, and REST is
  the migration target.

## Approach
Copy the strict blocks and contract from `mcp/openai-ads/` (as `mcp/README.md` says) and the layout
of `mcp/google-ads/` and `mcp/meta-ads/`, adapted as follows.

**A committed operation catalog, built from the pinned `msads` sdist.**
- `src/microsoft_ads_mcp/catalog_build.py` (console script `microsoft-ads-build-catalog
  <sdist.tar.gz> <package dir>`) builds it, with the extraction itself in `catalog_extract.py`.
  - It reads the sdist **as a tarball in memory with `ast`**; it never imports or executes SDK
    code, and the SDK is not a dependency.
  - It verifies the sdist's sha256 against the pinned constant.
  - It writes `src/microsoft_ads_mcp/catalog.json`, plus `catalog.LICENSE` copied from the sdist's
    `LICENSE`, which keeps the MIT notice.
- `make catalog` downloads the pinned sdist from `files.pythonhosted.org` (curl), checks it and runs
  the builder. A re-pin changes the version, URL and sha in one place (`catalog_build.py`) and
  regenerates.
- The catalog is **committed** and loaded with `importlib.resources`. The image build and the
  running server make no request for it, and tests read the real catalog with no network.
- Catalog contents, sorted for stable diffs:
  - **source**: `{package, version, sdist_sha256}`, written by the builder from its pinned
    constants. A test asserts that these equal the constants in `catalog_build.py`, which ties the
    committed file to the pin. Hand edits beyond that are guarded by review only, and the README
    says so.
  - **operations**: name (PascalCase, e.g. `AddCampaigns`, taken from the request model minus
    `Request`, else the response model minus `Response`; 16 operations take or return a bare
    `object`), service, HTTP method, path, request type, response type. The **operation name is the key**,
    because a path is shared across verbs.
  - **types**: per service, fields as wire name and type text, base type, and subtypes with their
    `Type` discriminator values (taken from the base's `from_dict` branches). The value that
    appears in the base's `Type` enum is listed as the documented one; any other value is marked as
    an SDK alias.
  - **enums**: per service, values; `Flag` enums are marked and carry the wire names from the
    SDK's `_to_str` mapping.
  - The committed file is 621,261 bytes (indent 1, sorted keys): 1,228 types and 272 enums.
- The builder fails loudly on an unexpected shape. That covers an operation without a literal
  method or path, a field without an alias, and **two operations whose normalized names collide**.
  It does not skip, because silent skips are how an enumeration goes dark.
- The `ast` extractor is the largest code risk under McCabe ≤ 5 and 100% branch coverage. It is
  written as small per-node functions, each covered through the fixture sdist.

**Requests address an operation by name, never a URL.**
- `microsoft_ads_request(operation, body, customer_id?, account_id?)` looks `operation` up in the
  catalog. The match ignores case and `_`, so `AddCampaigns`, `add_campaigns` and `addcampaigns`
  are the same.
- The server takes method, host and path from that entry. The host comes from a fixed
  service → host table for the configured environment.
- The caller supplies no path, host, query or headers, so there is no path validator to get wrong
  (the server-built-URL preference in the tool-shape decision).
- An unknown name is a `ToolError` that names `microsoft_ads_list_operations`.
- The body is sent as JSON for every verb, DELETE included (`client.request("DELETE", url, json=…)`).
- The tool returns the HTTP status, `TrackingId` / `x-ms-trackingid`, and the body as `json` (or
  `text`).
- Microsoft's error bodies pass through. There are no retries. The description names 117, 207 and
  4204, says backing off is the caller's job, and says Add/Update/Delete can succeed partially
  (check for null ids and `PartialErrors`).
- An over-limit body is abandoned mid-stream with a `ToolError` that suggests a narrower call or a
  bulk download.

**Credentials and identity** (`config.py`, `auth.py`):
- Credentials:
  - `MICROSOFT_ADS_CLIENT_ID`;
  - `MICROSOFT_ADS_CLIENT_SECRET` (optional: a confidential Web app sends it, a public app does
    not);
  - `MICROSOFT_ADS_REFRESH_TOKEN`;
  - `MICROSOFT_ADS_DEVELOPER_TOKEN`.

  All are required at the first API tool call, not at start, so discovery works without
  credentials and CI's smoke test starts with only `ci.env`. Values present at start are
  shape-checked at start.
- `MICROSOFT_ADS_TENANT` defaults to `common` and must be `common`, `organizations`, `consumers`, a
  GUID or a domain-shaped name. It is the only knob on the token URL, whose host is fixed.
- `MICROSOFT_ADS_ENVIRONMENT` is `production` (default) or `sandbox`. It selects the host table and
  the OAuth scope (`ads.microsoft.com` or `si.ads.microsoft.com`).
- There is no base-URL or token-URL override, so credentials can only reach Microsoft.
- `MICROSOFT_ADS_CUSTOMER_ID` and `MICROSOFT_ADS_ACCOUNT_ID` are optional defaults for the
  `CustomerId` and `CustomerAccountId` headers. The tool's `customer_id` / `account_id` arguments
  override them per call, as digits only. An operation that needs neither (e.g. GetUser) works
  without them, and a header with no value is omitted.
- `auth.py` follows `mcp/reddit-ads/auth.py`:
  - a lazy, locked refresh; a form-encoded refresh-token grant to the fixed token URL;
  - `client_secret` in the form only when it is set;
  - the expiry margin; the rotated refresh token kept **in memory**;
  - one re-refresh and retry, only when the response is HTTP 401 **and** its body is an
    `AdApiFaultDetail` whose first error code is 105 (`InvalidCredentials`) or 109 (expired
    token), and the rejected token is more than a minute old. 105 also means an inactive account
    or developer token, which no refresh fixes, so a brand-new token is not refreshed. Any other
    401 is returned as is. Concurrent rejections share one refresh (`invalidate` compares
    before dropping).
- A `invalid_grant` refusal says to re-run the consent flow in the README.
- The README states the operational fact: Microsoft returns a new refresh token on **every**
  refresh, and the server keeps it only in memory. After a restart it uses the env refresh token
  again, so the operator must re-issue that token before Microsoft expires it. Persisting a rotated
  token needs durable state and is out of scope.
- **Secret scrub.** Every tool output and every `ToolError` / exception text has exact-literal
  occurrences of the access token, refresh token, client secret and developer token replaced with
  `[redacted]`, as meta-ads does. Every rotated refresh token joins the set when it arrives and
  stays (Microsoft does not revoke old ones); each issued access token stays until it expires.
  Empty or unset values are never in the set.
- No secret is ever in a URL. Tokens go only in headers or the token POST body.
- `main.py` raises `httpx` / `httpcore` (and httpx2's) loggers to WARNING, as meta-ads does
  (the seekless httpx-logs-URLs constraint).

**Result files** (`download.py`):
- `microsoft_ads_download_file(url)` fetches a `ReportDownloadUrl` or bulk download `ResultFileUrl`
  **with no credentials** and `follow_redirects=False`.
- The URL must be printable ASCII with no spaces (`urlsplit` silently drops tabs and newlines
  that httpx2 rejects), use `https`, and have no userinfo, port or fragment. Its hostname, lower-cased, must
  equal an allowlisted domain or end with `.` plus that domain. That is a dot-boundary match, so
  `evilbingads.microsoft.com` and `x.blob.core.windows.net.evil.com` fail.
  - The provisional default is `blob.core.windows.net` and `bingads.microsoft.com`.
    `MICROSOFT_ADS_DOWNLOAD_HOSTS` overrides it as operator config, never a tool argument.
  - **The blob suffix is broad.** It matches every Azure customer's storage account, so a
    prompt-injected model could fetch an attacker's blob, pulling untrusted text into context and
    leaking whatever it encodes in the URL to that host.
  - No credential is ever sent on this path. The README states this risk and recommends narrowing
    the variable to the measured host. Once criterion 7 measures it, the default is narrowed to that
    host's storage account, in this unit if measured before ship, else as an expected follow-up.
- The body is read bounded. A zip must hold exactly one member, read with a decompressed-size cap;
  a gzip is read with a cap. A corrupt, encrypted or unsupported archive is a clear `ToolError`.
  The result is the decoded text with its BOM stripped, refused (not truncated) over
  `MICROSOFT_ADS_MAX_RESPONSE_BYTES`, with a message to narrow the report or bulk download, or
  raise the limit.
- The API client and the downloader share one capped stream reader (`transfer.py`).
- The real download host is unverified until criterion 7 runs. The README says so, and says how to
  widen the allowlist.

**Discovery tools** (all read the committed catalog, so none can fail on the network):
- `microsoft_ads_list_operations(text_filter?)`: one line per operation,
  `Service.Operation — METHOD /path → RequestType`, 291 lines unfiltered, under the response cap.
- `microsoft_ads_describe_operation(operation)`: the request and response types' own fields, plus
  the fields of each object type those fields name. A list's element type counts as the named
  type, so `AddCampaignsRequest.Campaigns` → `Campaign`'s fields. Deeper types stay as names for
  `describe_type`. Enum values are shown inline, using wire names so the body can be written from
  it. Item caps are in the request tool's description.
- `microsoft_ads_describe_type(name, service?)`: a type's fields including inherited ones, enum
  values, and its subtypes with their discriminator values.
  - A bare name resolves when it is unique. Otherwise the error lists the services that define it.
  - An enum name resolves to its values.
  - Output over the cap is refused with a message, not truncated.

**Server and instructions.** As google-ads: stdio or streamable HTTP, `/healthz`, `MCP_*`
settings. The instructions and the request tool description say:
- ids are JSON strings;
- money is in currency units, not micros;
- polymorphic objects need `"Type"`;
- create campaigns and ads with `"Status": "Paused"` as the safe default;
- DELETE takes a body;
- writes change live campaigns and spend real money, so confirm them with the user. This is in the
  tool description because a gateway may drop server instructions.

**No read-only switch, on purpose** (as google-ads and meta-ads). The owner asked for full campaign
control. The bound is the OAuth user's account access and the accounts' own budgets; the README
says so.

**Files.**
- `Dockerfile`: non-root, `/healthz`, no build-time fetch because the catalog is committed.
- `ci.env`: a dummy `MCP_AUTH_TOKEN` only.
- `Makefile`: includes `catalog`.
- `.env.example` and `docker-compose.yml`.
- `README.md` covers:
  - the tools;
  - registering an Entra app (Web vs native), the consent URL and code exchange to get a refresh
    token, and the developer token;
  - sandbox setup;
  - configuration;
  - the security model: fixed hosts, operation-name dispatch, no caller headers, scrub, download
    allowlist;
  - egress hosts;
  - limitations: no bulk upload; refresh-token re-issue; unpaged Gets, with bulk download for large
    accounts; catalog staleness and re-pin;
  - a worked Paused campaign (inline daily budget) → ad group → keywords → RSA sequence, then
    enabling all three levels, unverified against a live write.
- A row in `mcp/README.md`.

**Knowledge followed:**
- the tool-shape decisions: the generic shape for 291 operations, and server-built URLs. The
  generic-tools decision constrains the tool *shape* (a few generic tools plus discovery), not
  whether the caller supplies a path. Operation-name dispatch is that shape with no caller path,
  the first such server, which is worth a decision entry at promote;
- `ci.env`;
- the server-local-path and generic-credential-loader patterns: no tool takes a filesystem path,
  and credentials are explicit env values, not a dispatching loader;
- the mock-transport-lock entry, for the token-refresh concurrency test;
- the meta-ads scrub and log precedent.

**Knowledge written** (Theme `mcp-servers`):
- `2026-11-05-reference-microsoft-advertising-api-facts-for-mcp-servers` — the Microsoft facts;
- `2026-11-05-decision-mcp-servers-dispatch-by-operation-name-when-every-path-is-fixed`;
- `2026-11-05-pattern-validate-a-url-with-the-parser-that-fetches-it` — from code review.

**Tests** run with no network:
- the builder over a small fixture sdist (a tar.gz built in the test from trimmed generated files,
  with the sha passed in);
- the real committed catalog, for counts and named entries;
- an httpx2 mock transport;
- 100% line and branch coverage;
- HTTP and stdio exercised with real servers, as the siblings do;
- a concurrency test for the token refresh that actually overlaps callers.

### Alternatives considered
- **B. Typed tools for core operations (campaigns, ad groups, ads, keywords, budgets, reports),
  ~25 tools.** Rejected because 291 operations is the generic shape under the standing decision,
  and a curated subset fails "full". A generic escape hatch beside it was rejected by the same
  decision.
- **C. Generic `request(method, path)` with a path validator**, like the siblings. Rejected because
  every path here is a fixed literal, so operation-name dispatch reaches the same set with no
  caller-controlled path. It strictly dominates on safety at equal reach.
- **D. Depend on `msads` at runtime and introspect its Pydantic models.** Rejected for three
  reasons: it pulls `requests`, `urllib3`, `enum34` and the SOAP `bingads` package; it executes
  vendor code; and the HTTP the guards must see would be hidden if its client were used.
- **E. Build the catalog at image-build time** (meta-ads' pattern). Rejected because:
  - it is non-hermetic;
  - CI tests could not read the real catalog without network;
  - local stdio would need a runtime fetch or a `make` step;
  - at about 600 KB, committing is cheap, and a re-pin shows up as a reviewable diff.
- **F. Proxy Microsoft's hosted MCP server.** Rejected because it is read and reporting only, which
  fails the goal.
- **G. Parse the WSDLs instead of `msads`.** Rejected because they carry no REST paths or verbs, so
  a second source would still be needed for them.
- **H. Bulk upload in v1.** Deferred: it sends credentials to an API-returned URL, the docs and SDK
  disagree on its headers, and it needs multipart.

## Success criteria
1. `mcp/microsoft-ads/` meets the `mcp/README.md` contract: a pyproject whose `[tool.ruff]`,
   `[tool.mypy]` and `[tool.pytest]` blocks match `openai-ads/pyproject.toml`'s apart from the
   package name; a second console script for the builder is allowed. It also has a non-root
   Dockerfile with `/healthz`, `ci.env`, a Makefile, a README and tests.
   - `make check` passes on Python 3.11 and 3.13 with 100% line and branch coverage.
   - The PR's `mcp.yml` `check` and `docker` jobs include `microsoft-ads` and pass.
2. The committed `catalog.json`:
   - was produced by `make catalog` from the pinned sdist (sha256 verified), with the run recorded
     in the scratchpad;
   - has a `source` that a test shows equals the builder's pinned version and sha256;
   - holds 291 operations: 195 Campaign Management, 39 Customer Management, 33 Ad Insight,
     16 Customer Billing, 6 Bulk, 2 Reporting. These are the pin's counts, updated with a re-pin;
   - tests assert that `AddCampaigns` is `POST /CampaignManagement/v13/Campaigns`, `DeleteCampaigns`
     is `DELETE` on the same path, `GetCampaignsByAccountId` is
     `POST /CampaignManagement/v13/Campaigns/QueryByAccountId`, and `SubmitGenerateReport` is
     `POST /Reporting/v13/GenerateReport/Submit`;
   - lists `ResponsiveSearchAd` under `Ad`'s subtypes with discriminator `ResponsiveSearch`;
   - ships `catalog.LICENSE` with the MIT notice.

   Over a fixture sdist, the builder refuses a wrong sha256, an operation without a literal path,
   and two operations whose normalized names collide.
3. Over a mock transport, tests show:
   - each operation goes to the host for its service, both production and sandbox, with its
     catalog method and path, and a DELETE carries its JSON body;
   - every request carries `Authorization: Bearer`, `DeveloperToken`, and `CustomerId` /
     `CustomerAccountId` from config or the per-call override, omitted when unset;
   - a non-digit id override is refused;
   - an unknown operation is refused, and names in other case or underscore spellings resolve;
   - no tool takes a path, host, URL (except `download_file`), header or filesystem argument;
   - the request tool's description carries the spend warning and `Paused` default;
   - an over-limit body raises the size error.
4. Auth tests show:
   - the refresh POSTs to `login.microsoftonline.com/<tenant>/oauth2/v2.0/token` with the right
     scope for each environment, and `client_secret` only when configured;
   - a rotated refresh token is used for the next refresh;
   - two concurrent first calls trigger one refresh (with callers that actually overlap);
   - a 401 `AdApiFaultDetail` with code 105 or 109 triggers exactly one re-refresh and retry
     (when the token is not brand new), while a 401 with another body is returned without a retry;
   - `invalid_grant` gives the re-consent message;
   - a malformed tenant or environment is refused at start.
5. **Secret containment.** For every tool, over mock responses of each shape (success, both fault
   shapes, a body echoing the token, the developer token or the refresh token, a token-endpoint
   error, and a transport exception whose message embeds secrets), no output and no `ToolError`
   text contains any configured or rotated secret, asserted by substring. With the loggers as
   `main.py` configures them, a captured log of those calls contains none either. With no client
   secret configured (a public client), outputs are unchanged apart from real secrets: nothing is
   redacted for an empty value.
6. `download_file`:
   - refuses `http`, userinfo, a port, an unlisted host, the suffix-confusion hosts
     `evilbingads.microsoft.com` and `x.blob.core.windows.net.evil.com`, and a redirect;
   - accepts an exact allowlisted domain and a subdomain of one;
   - sends no `Authorization` or `DeveloperToken` header;
   - unzips a single-member zip and a gzip;
   - refuses a multi-member zip, an over-cap decompressed size and an over-cap text;
   - strips a BOM.

   Discovery against the real catalog:
   - an unfiltered `list_operations` returns 291 lines, under the default
     `MICROSOFT_ADS_MAX_RESPONSE_BYTES` of 2 MiB;
   - `describe_operation AddCampaigns` lists `Campaigns` and, one named type down, the `Campaign`
     fields `DailyBudget` and `BudgetType`;
   - `describe_type Ad` lists `ResponsiveSearchAd` with documented discriminator `ResponsiveSearch`
     (and `ResponsiveSearchAd` marked as an SDK alias);
   - an ambiguous bare type name names its services;
   - each of those outputs is under 50 KB, a test budget below the 2 MiB product cap.
7. **Manual evidence, outside CI.** A live read-only smoke run with the owner's credentials (values
   never printed, output in the scratchpad):
   - `GetUser` (Customer Management) answers;
   - `GetCampaignsByAccountId` returns the account's campaigns with no secret in the output;
   - a one-day report submitted, polled and downloaded through `download_file` records the real
     download host.

   If the owner has no credentials yet, record this as pending and say so in the README.

   **Outcome: pending.** No credentials were available at ship; the README's Limitations says so.
8. The README documents:
   - the Entra app registration, consent and refresh-token steps, and the developer token;
   - sandbox setup;
   - refresh-token rotation and re-issue;
   - the security model, including the breadth of the provisional download allowlist;
   - egress hosts;
   - limitations, including the 11 operations with no Learn page and the unverified write and
     download paths;
   - the Paused-first sequence. `mcp/README.md` lists the server. A `reference` knowledge entry with
   Theme and Summary records the Microsoft facts.
9. **Manual, owner-approved** (asked for at the time; if declined, recorded as unverified): one
   zero-spend live write. Create a `Paused` campaign (sandbox if the owner has a sandbox account,
   otherwise production), read it back, delete it, and put the output in the scratchpad.

   **Outcome: unverified.** Asked at completion; the owner chose to record it as unverified.

## Open Questions
- The real host of `ReportDownloadUrl` (criterion 7). The default allowlist is a guess from Azure
  blob conventions.
- Whether the sandbox OAuth scope `si.ads.microsoft.com` is current. The server uses the SDK's
  default; the README notes that older documentation names others, and sandbox auth stays
  unverified until a sandbox call succeeds.

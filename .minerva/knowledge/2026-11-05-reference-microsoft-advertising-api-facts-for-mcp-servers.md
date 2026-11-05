# Microsoft Advertising API v13: REST by operation name, rotating refresh tokens, and an SDK-built catalog

**Date**: 2026-11-05
**Type**: reference
**Theme**: mcp-servers
**Summary**: No OpenAPI spec (catalog from the msads SDK's REST client), fixed literal paths, refresh tokens rotate, 5-minute report links
**Context**: .minerva/work/2026-11-05-add-microsoft-ads-mcp-server (see git history if the worktree has been cleaned up)

## Context
`mcp/microsoft-ads/` wraps the Microsoft Advertising (Bing Ads) API v13 JSON REST interface with
generic tools. The facts below shaped it. They were read from Microsoft Learn and from the
`msads` 13.0.30.1 sdist on 2026-11-05; **none was measured against a live account** (no
credentials were available), so treat the auth and download facts as documented, not observed.

## Finding
- **No OpenAPI document.** The WSDLs describe SOAP and carry no REST paths. The official Python
  SDK `msads` (PyPI, MIT) ships a generated REST client under `openapi_client/` whose
  `_<op>_serialize` methods hold literal `method` / `resource_path` values and whose pydantic
  models hold wire names as `Field(alias=...)`. Reading it with `ast` (never importing it)
  yields 291 operations: Campaign Management 195, Customer Management 39, Ad Insight 33,
  Customer Billing 16, Bulk 6, Reporting 2. Ad Insight's PutMetricData is in neither.
- **Every path is a fixed literal with no path parameters**: `/<Service>/v13/<Noun>[/<qualifier>]` (e.g. `/CustomerManagement/v13/Account`)
  on a per-service host — `campaign`, `bulk`, `reporting`, `adinsight`, `clientcenter`
  (Customer Management and Billing share it) under `.api.bingads.microsoft.com` or
  `.api.sandbox.bingads.microsoft.com`. Add = POST, Update = PUT, Delete = DELETE **with a JSON
  body**, and every Get/Query/Search = POST. So a server can dispatch by operation name and take
  no caller path at all.
- **SDK quirks:** 16 operations (e.g. SetAccountProperties, DeleteUser) take or return a bare
  `object` (a dict), so name an operation from its request model, falling back to its response; one annotation is `StrictDict[str, Str]` (a generator bug)
  and must map to `object`.
- **Headers:** `Authorization: Bearer <access token>`, `DeveloperToken`, `CustomerId`,
  `CustomerAccountId`. Ids are JSON strings; money is in account currency (not micros).
- **Polymorphism** uses a `"Type"` field. The SDK's `from_dict` accepts several spellings; the
  one in each subclass's own `Type` enum (e.g. `ResponsiveSearch`) is what Learn's REST examples
  send. Some subtypes (e.g. `CampaignPerformanceReportRequest`) have no such enum.
- **OAuth is user-delegated only** (no client-credentials flow): Entra v2 at
  `login.microsoftonline.com/<tenant>/oauth2/v2.0/token`, scope
  `https://ads.microsoft.com/msads.manage offline_access` (sandbox, per the SDK default:
  `https://si.ads.microsoft.com/msads.manage`). **Every refresh returns a new refresh token**;
  refresh tokens have no fixed lifetime and can be revoked at any time. A Web app sends its
  client secret; a public client must not. Error codes 105/109 mean the access token was
  rejected. The universal sandbox developer token is `BBD37VB98`.
- **Errors:** `AdApiFaultDetail` (`Errors[{Code, Message}]`) or `ApiFaultDetail`
  (`BatchErrors` / `OperationErrors`); writes partly succeed with `PartialErrors` and `null` ids.
  Throttling: 117 (Campaign/Ad Insight), 207 (Reporting), 4204 (Bulk).
- **Reports and bulk downloads** are asynchronous: SubmitGenerateReport → PollGenerateReport →
  `ReportDownloadUrl`, a self-authorizing link valid for five minutes, usually a zip. The
  host is documented only loosely (Azure blob storage); it was not observed.

## Implications
- Dispatch by operation name from a pinned, sha-checked catalog; refuse caller paths, hosts and
  headers.
- Keep rotated refresh tokens in the scrub set as well as the configured one; persisting them
  needs storage a stateless server lacks, so document re-issue instead.
- Fetch result files without credentials, behind a host allowlist; narrow it once a real report
  host has been seen.

## Related
- [[2026-10-18-reference-meta-marketing-api-facts-for-mcp-servers]] — the sibling ads server's facts, and the scrub precedent
- [[2026-10-18-reference-google-ads-api-facts-for-mcp-servers]] — another spec-driven ads server

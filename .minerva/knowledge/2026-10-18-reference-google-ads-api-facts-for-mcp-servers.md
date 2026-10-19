# Google Ads API v26: a Discovery document, no developer token, GAQL paging, Shorts as Demand Gen

**Date**: 2026-10-18
**Type**: reference
**Theme**: mcp-servers
**Summary**: Google Ads REST publishes a 3.3 MB Discovery doc (175 methods); dev tokens sunset 2026-09-09; Shorts = Demand Gen channel controls
**Context**: .minerva/work/2026-10-18-add-google-ads-mcp-server (see git history if the worktree has been cleaned up)

## Context
`mcp/google-ads/` wraps the Google Ads REST API with generic tools driven by Google's own
API description. The facts below shaped it. They were measured on 2026-10-18 against v26
(released 2026-10-14) unless marked as read from Google's docs.

## Finding
- **Spec:** `https://googleads.googleapis.com/$discovery/rest?version=v26` needs no auth. It is
  Google **Discovery** format, not OpenAPI: 3.3 MB of JSON, 175 methods (POST 162, GET 12,
  DELETE 1), 1,497 schemas, one scope `https://www.googleapis.com/auth/adwords`.
  - Methods sit in nested `resources`. Each has a `path` with the version and reserved
    expansion (`v26/customers/{+customerId}/googleAds:search`) and a `flatPath` with different
    parameter names (`customers/{customersId}/...`).
  - Some paths are catch-alls: `v26/{+name}` is both `operations.get` and `operations.list`
    (GET), and `v26/{+resourceName}` serves several resources. A concrete path can fit several
    templates, and two methods can share one (method, template) pair.
  - Schemas are referenced by bare name, often with a sibling `description` next to the `$ref`.
  - Parsing the whole document takes about 0.02 s. Most schemas at one level of expansion are a
    few KB, but `Common__Metrics` (~114 KB), `Common__Segments` (~70 KB) and
    `Errors__ErrorCode` (~280 KB) are large at any depth.
- **Reads are GAQL.** `POST /customers/{id}/googleAds:search` takes `query`, `pageToken`,
  `pageSize`, `validateOnly`. The next page is the same POST with `pageToken` set to the
  response's `nextPageToken`, so no follow-a-URL tool is needed. `googleAds:searchStream`
  returns every row at once. `POST /googleAdsFields:search` finds GAQL fields.
- **Every mutate takes `validateOnly: true`**, a dry run. `googleAds:mutate` takes mixed
  operation types in one atomic request, and new resources can be linked by temporary ids
  (negative numbers in resource names).
- **Developer tokens were sunset on 2026-09-09** (Google's dev-token page, read 2026-10-18, not
  proven by a call). Access levels follow the Google Cloud project that issued the OAuth
  credentials. A sent token is "optional and ignored", and a future major version will reject
  one. A Test-access project gets `CLOUD_PROJECT_NOT_APPROVED_FOR_PRODUCTION` (v25+) against a
  real account.
- **Credentials:** a service account can be added directly as a Google Ads user (Admin >
  Access and security > Users, any level except "Email only"), or an OAuth user's refresh
  token works. A manager account needs a `login-customer-id` header of 10 digits, no dashes.
- **YouTube Shorts is a Demand Gen campaign.** The API cannot create or update standard Video
  campaigns ("only supports fetching and reporting"). The Shorts-only switch is
  `AdGroup.demandGenAdGroupSettings.channelControls.selectedChannels.youtubeShorts`, five
  schemas below `adGroups:mutate`, with `YoutubeVideoAsset {youtubeVideoId}` and
  `DemandGenVideoResponsiveAdInfo` for the ad. Schema presence does not show that a Shorts-only
  selection is accepted for every account. As of this entry it was not yet tried live.

## Implications
- A Discovery-driven server needs its own reader: walk `resources`, strip the version
  prefix, drop the `+` of reserved expansion, and describe by exact template rather than
  matching a concrete path to catch-alls.
- Describing one schema at a time, by the name a `$ref` marker gives, keeps deep message types
  readable. Expanding a whole request tree floods context.
- Treat the developer-token sunset as unverified until a live call succeeds without one.

## Related
- [[2026-09-25-decision-mcp-servers-expose-generic-spec-driven-tools]] — the tool shape this API was wrapped in
- [[2026-09-25-reference-reddit-ads-api-v3-facts-for-mcp-servers]] — the sibling ads-API reference
- [[2026-09-25-reference-google-auth-and-mcp-client-facts-for-mcp-servers]] — the credentials module this server reuses

# OpenAI Ads API: a public JSON spec, one API key per ad account, and cursor pagination

**Date**: 2026-09-25
**Type**: reference
**Summary**: OpenAI Ads API v1 publishes openapi.json; per-account bearer keys; cursor pagination; micros; two upload endpoints
**Context**: .minerva/work/2026-09-25-refocus-openai-mcp-on-ads-api (see git history if the worktree has been cleaned up)

## Context
`mcp/openai-ads/` wraps OpenAI's Advertiser API (ChatGPT ads) with generic, spec-driven tools.
The facts below came from the vendor's spec, its developer docs and one unauthenticated probe on
2026-09-25. They shaped the server, and most are not in third-party write-ups.

## Finding
- **Base URL and spec.** The base URL is `https://api.ads.openai.com/v1`. The spec is at
  `https://developers.openai.com/ads/openapi.json`.
  - It needs no auth and is OpenAPI 3.1 JSON, about 310 KB, with 87 operations: POST 50, GET 34,
    PATCH 2, DELETE 1, no PUT.
  - Updates are POSTs to the resource path, as are state changes (`/activate`, `/pause`,
    `/archive`). Deletes of spend-limit windows are POSTs too.
  - `api.ads.openai.com/v1/openapi.json` and `developers.openai.com/ads/openapi.yaml` return 404.
- **Auth.** `Authorization: Bearer <Advertiser API key>`, with **one key per ad account**,
  created in Ads Manager > Settings. `GET /ad_account` verifies a key.
  - A partner OAuth flow also exists: `auth.openai.com/api/accounts/authorize` and `.../oauth/token`,
    with scopes `ads.admin.all.read`, `ads.admin.all.write` and `offline_access`.
- **Pagination** uses cursor query parameters (`limit` up to 500, `after`, `before`, `order`) on
  the same path. Responses carry `has_more`, `first_id` and `last_id`. There are no absolute
  next-page URLs, unlike Reddit Ads.
- **Array query parameters.** The spec names them without brackets (`include`, `campaign_ids`,
  `fields`, and others). OpenAI's own curl examples spell one as `include[]=serving_issues`.
  Which spelling the server accepts has not been checked with a live key.
- **Uploads.** There are two upload endpoints.
  - `POST /upload` takes an image as multipart `file` or as JSON `{"image_url": ...}`, and returns
    a `file_id` for creatives.
  - `POST /uploads` takes multipart only (`file`, `purpose`), for custom-audience files
    (`purpose: custom_audience`).
  - All 87 success responses are `application/json`, so there is nothing to download.
- **Money and state.**
  - Amounts are **micros** of the account currency (`50000000` is 50.00).
  - `status` (`active` or `paused`) is **required** on campaign create, alongside `name` and
    `budget`.
  - Creating an ad submits it for review. Activating a campaign, ad group or ad starts spend.
  - Ten create operations accept an `Idempotency-Key` header.
- **Rate limits** are 600 requests/min per endpoint and 1,200/min overall, enforced per ad account
  and per IP. The spec declares no response headers.
  - A live 401 carried `x-request-id`, `openai-version` and `openai-processing-ms`, plus Cloudflare
    `set-cookie` and `cf-ray`.
  - The names of the rate-limit headers are undocumented.
- The changelog shows frequent additions (Aug 25 and Sep 9–10, 2026 alone).

## Implications
- The generic request tool covers pagination; no follow-URL tool is needed.
- A multipart tool must refuse an empty file list. Otherwise httpx sends
  `application/x-www-form-urlencoded`, which neither upload endpoint accepts.
- Forward a response-header allowlist that includes both rate-limit spellings (`x-ratelimit-*`,
  `ratelimit*`) and `retry-after`, and never cookies.
- Schemas are small: a depth-3 `$ref` expansion is at most about 13 KB. Depth-1 discovery defaults
  are cheap here, unlike the general OpenAI spec.
- Re-derive the operation counts from the live spec before quoting them, because they drift.

## Related
- [[2026-09-25-decision-mcp-servers-expose-generic-spec-driven-tools]] — the tool shape this API was wrapped in
- [[2026-09-25-reference-reddit-ads-api-v3-facts-for-mcp-servers]] — see also: the sibling ads-API reference, which paginates by URL instead
- [[2026-09-25-reference-openai-openapi-spec-source-and-size]] — see also: the general OpenAI API spec this server no longer reads
- [[2026-09-25-decision-mcp-openai-server-refocused-on-the-ads-api]] — the decision these facts informed

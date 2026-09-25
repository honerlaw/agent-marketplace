# Reddit Ads API v3: a public OpenAPI spec, refresh-token OAuth, and pagination by URL

**Date**: 2026-09-25
**Type**: reference
**Summary**: Reddit Ads v3 publishes openapi.json; OAuth refresh tokens; follow next_url; four POST paginators
**Context**: .minerva/work/2026-09-25-add-reddit-ads-mcp-server (see git history if the worktree has been cleaned up)

## Context
`mcp/reddit-ads/` wraps the Reddit Ads API v3 with generic, spec-driven tools. The facts below
came from the vendor's spec and docs and shaped the server. Most third-party write-ups and the
existing open-source Reddit Ads MCP servers don't record them.

## Finding
- **Spec:** `https://ads-api.reddit.com/api/v3/openapi.json` needs no auth. It is OpenAPI 3.1,
  about 1 MB of JSON, with 108 operations on 80 paths.
  - Methods are GET 63, POST 27, PATCH 13 and DELETE 5, with no PUT. Every body is
    `application/json`, so no multipart or download tools are needed. Creatives upload by URL.
  - `/docs/v3/openapi.json` and the other guessed spec paths return 404.
  - WebFetch is blocked on the host, but plain `curl` works.
- **Descriptions:** most operation descriptions embed a rendered HTML rate-limit panel with inline
  SVG. Stripping the tags takes a depth-1 describe of POST `/ad_accounts/{id}/campaigns` from
  about 14 KB to 10 KB and leaves readable "Policy Slug / Window / Quota" text.
- **Scopes:** each operation declares its scope in `security`: `adsread` 71, `adsedit` 32,
  `adsdatadeletion` 3, `adsconversions` 1. `GET /targeting/communities/suggestions` declares none,
  and there is no global default.
- **Auth:** `POST https://www.reddit.com/api/v1/access_token`, form-encoded, HTTP Basic
  `client_id:client_secret`, `grant_type=refresh_token`.
  - `expires_in` is 3600 or 86400. The response may carry a new `refresh_token`.
  - The endpoint can answer **HTTP 200 with `{"error": "invalid_grant"}`**, so check for
    `access_token`, not the status.
  - A permanent refresh token comes from `duration=permanent` on the authorize URL.
- **User-Agent:** Reddit requires `<platform>:<app id>:<version> (by /u/<username>)` and heavily
  rate-limits generic agents.
- **Rate limits:** headers follow the IETF draft (`RateLimit`, `RateLimit-Policy`), not
  `x-ratelimit-*`. The spec declares no response headers; this comes from the docs.
- **Pagination:** `pagination.next_url` and `previous_url` are full URLs, and the spec says to
  "follow directly", not to rebuild them from query parameters.
  - `page.token` is a shared parameter on 36 operations.
  - Four paginators are **POSTs** with a JSON body: `/ad_accounts/{id}/reports`,
    `/ad_accounts/{id}/history`, `/businesses/{id}/ad_accounts/query` and
    `/businesses/{id}/funding_instruments/query`. The next page is the same POST, with the same
    body, to `next_url`. This is inferred from the spec's shape and has not been confirmed live.

## Implications
- A generic request tool whose `path` refuses absolute URLs needs a separate, same-origin-checked
  "follow this URL" tool for pagination. That tool must support POST with a body.
- Treat the token endpoint's JSON as the source of truth and keep refresh failures free of
  secrets. A 429 or 5xx from it is an outage, not bad credentials.
- The operation and scope counts drift. Re-derive them from the live spec before quoting them.

## Related
- [[2026-09-25-decision-mcp-servers-expose-generic-spec-driven-tools]] — the tool shape this API was wrapped in
- [[2026-09-25-decision-mcp-server-tool-shape-follows-api-size-and-stability]] — Reddit Ads is the "large, fast-moving" case
- [[2026-09-25-reference-openai-openapi-spec-source-and-size]] — the sibling spec-source reference for OpenAI
- [[2026-09-25-reference-google-auth-and-mcp-client-facts-for-mcp-servers]] — see also

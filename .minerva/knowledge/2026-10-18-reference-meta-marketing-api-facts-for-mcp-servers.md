# Meta Marketing API v26.0: system-user tokens, codegen specs, and credentials in paging URLs

**Date**: 2026-10-18
**Type**: reference
**Theme**: mcp-servers
**Summary**: No OpenAPI spec (codegen specs), credentials in paging URLs, DCR refused for Meta's hosted MCP
**Context**: .minerva/work/2026-10-18-add-meta-ads-mcp-server (see git history if the worktree has been cleaned up)

## Context
`mcp/meta-ads/` wraps Meta's Marketing API (the Graph API) with generic tools. The facts below
shaped it. They were measured on 2026-10-18 with a real system-user token (values never
printed) unless marked as read from Meta's docs.

## Finding
- **Meta's hosted MCP server is closed to unknown clients.** `mcp.facebook.com/ads`'s dynamic
  client registration (`/.well-known/register/ads`) answers `invalid_client_metadata:
  "Dynamic registration is not available for this client."` for every redirect URI tried
  (Cloudflare portal callbacks, localhost), so only Meta's pre-approved clients can use it;
  a gateway or other proxy cannot.
- **Auth.** A Business Manager **system-user token** works with `Authorization: Bearer <token>`
  on `graph.facebook.com/v26.0`, with `appsecret_proof` (HMAC-SHA256, key = app secret,
  message = token, hex) as a query parameter; the app did not require the proof but accepted
  it. `GET /debug_token?input_token=<token>` with `Bearer <app_id>|<app_secret>` returns
  validity, type `SYSTEM_USER`, scopes, `granular_scopes`, and `expires_at` / 
  `data_access_expires_at` (0 = never). Per Meta's docs, system-user tokens are "Never
  expires" or 60 days, some businesses must use the 60-day kind, and a 60-day token is
  refreshed with `fb_exchange_token` + `set_token_expires_in_60_days=true`.
- **Credentials leak through responses.** Graph builds `paging.next` / `previous` as full URLs
  carrying `access_token` (and `appsecret_proof`); `/me/accounts` and similar return page
  tokens as `access_token` fields, and `fields=access_token.as(x)` can alias them. Tokens start
  with `EAA`.
- **No OpenAPI spec.** `facebook/facebook-business-sdk-codegen`'s `api_specs/specs/` describes
  1,103 node types and 1,503 operations (`#get`/`#update`/`#delete` node operations, edges, and
  6 `basePath` operations), with `enum_types.json` (975 enums) linked by exact type name. It is
  not versioned per Graph version. GitHub regenerates archives on demand, so pin the extracted
  content's hash, not the tarball's. Licence: use and distribution "in connection with" Meta's
  APIs, copyright notice kept.
- **Query encoding.** List and object query values go as JSON (`effective_status=["ACTIVE"]`),
  not repeated keys (repeated keys are last-wins); JSON-array filters return 200.
- **Rate limits.** A new app is on `ads_api_access_tier: development_access`
  (`x-business-use-case-usage`); limit errors are 4, 17, 613 and 80000-80014.
- **Control parameters.** Graph honours `batch` (root `/` endpoint), `adbatch`
  (`async_batch_requests`), `method` (verb override), `suppress_http_code` and `callback`; none
  is a Marketing API parameter in the specs (`access_token` appears only on two Instagram
  token-exchange operations), so a server can refuse them all.

## Implications
- An MCP server for Meta should hold a system-user token itself rather than proxy Meta's hosted
  server.
- Scrub responses by credential value, by `access_token` key and by token shape, and drop
  credentials from paging URLs; refuse the control parameters in query and body.
- Re-pinning the specs changes the commit and the content hash together; a version bump is
  separate.

## Related
- [[2026-10-18-reference-google-ads-api-facts-for-mcp-servers]] — the sibling ads server's facts
- [[2026-09-25-reference-reddit-ads-api-v3-facts-for-mcp-servers]] — the paging-URL pattern this extends

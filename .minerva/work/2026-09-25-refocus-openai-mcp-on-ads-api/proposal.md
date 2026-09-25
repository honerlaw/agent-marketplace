# Proposal: refocus-openai-mcp-on-ads-api

**Date**: 2026-09-25
**Status**: Shipped (2026-09-25)

## Goal
Turn the MCP server under `mcp/openai/` into a server that lets an LLM manage ChatGPT
advertising through OpenAI's Advertiser API: create and manage campaigns, ad groups, ads,
creative uploads, custom audiences, product feeds, conversion tracking and insights. The server
moves to `mcp/openai-ads/` and stops wrapping the general OpenAI REST API (`api.openai.com/v1`:
responses, files, models, and so on).

## Why
The user asked: "This server should be focused on their advertisement API so that we can
create campaigns / ads / ad groups / etc." Today the server targets the general OpenAI API
and can't do anything with ads.

**The trade-off:** this removes general OpenAI REST API access (`/responses`, `/files`,
`/models`, ...) from the repo's maintained servers. The last `ghcr.io/<owner>/openai-mcp`
image stays pullable but frozen. A repo-wide grep found nothing else that uses `mcp/openai/`
apart from its own files, two READMEs and a cross-link in the Google Search Console README.
The user's wording ("this server should be focused on their advertisement API") asks for this
refocus. If general access is wanted again later, it can come back as its own server.

### Facts gathered (2026-09-25)
- Base URL `https://api.ads.openai.com/v1`. Auth is `Authorization: Bearer <Advertiser API key>`,
  with one key per ad account, created in Ads Manager > Settings. A partner OAuth flow also
  exists (`auth.openai.com`, scopes `ads.admin.all.read|write`).
- The OpenAPI 3.1 spec is public and needs no auth: `https://developers.openai.com/ads/openapi.json`
  (about 310 KB of JSON). It has 87 operations: POST 50, GET 34, PATCH 2, DELETE 1, and no PUT.
  They cover the ad account (plus spend limits and insights), campaigns, ad groups, ads (plus
  preview), activate/pause/archive state changes, uploads (`/upload`, `/uploads`), custom
  audiences (plus async operations), feeds, conversions, lead sync subscriptions, audit logs, geo
  lookup, sandbox eligibility jobs, partner data uploads, API keys, ad account creation sessions,
  and `/me`.
- All 87 success responses are `application/json`. Two request bodies are `multipart/form-data`;
  `/upload` also accepts JSON `{"image_url": ...}`. There are no binary download endpoints.
- Pagination uses cursor query parameters (`limit`, `after`, `before`, `order`) on the same path.
  Responses carry `has_more`, `first_id` and `last_id`. There are no absolute next-page URLs.
- Ten create operations accept an `Idempotency-Key` header. `status` is required on create
  (`CreateCampaignBody` requires `name`, `status`, `budget`).
- Rate limits are 600 requests/min per endpoint and 1,200/min overall, applied per ad account
  and per IP.
- The spec declares no response headers. A live 401 returned `x-request-id`, `openai-version`
  and `openai-processing-ms`. The rate-limit header names are not documented.
- Money is in micros (`daily_spend_limit_micros: 50000000` is $50). Creating an ad submits it for
  review. Activating a campaign, ad group or ad starts spend.
- The changelog shows frequent additions (Aug 25 and Sep 9–10, 2026 alone).

## Approach
Rename the server to `mcp/openai-ads/` with `git mv`, so file history follows, and point it at
the Ads API. A 3/3 panel chose this over (A) repurposing `mcp/openai/` under its old name and
(C) adding a sibling server while keeping the general one:
- C doesn't make *this* server ads-focused.
- A would silently change what the `openai-mcp` image and client configs point at.
- The `-ads` name follows the `reddit-ads` precedent.

The server keeps its generic, spec-driven shape, per
[[2026-09-25-decision-mcp-servers-expose-generic-spec-driven-tools]] and
[[2026-09-25-decision-mcp-server-tool-shape-follows-api-size-and-stability]]. With 87 operations
and frequent additions, the Ads API gets the generic shape.

- **Names:** the distribution (`[project] name`), console script and GHCR image are all
  `openai-ads-mcp`. The import package / module directory is `src/openai_ads_mcp`.
- **Tools (4):**
  - `openai_ads_request(method, path, query?, body?, headers?)` with method GET, POST, PATCH or
    DELETE.
  - `openai_ads_multipart_request(path, files, fields?)` for `/upload` (creative images) and
    `/uploads` (custom-audience files, `purpose: custom_audience`). It refuses an empty `files`
    list, because httpx would otherwise send a urlencoded form, and points `image_url` uploads at
    `openai_ads_request`.
  - `openai_ads_list_endpoints(text_filter?)`.
  - `openai_ads_describe_endpoint(method, path, depth?)`.

  `openai_download` is dropped because the spec has no binary endpoints.
- **Config:**
  - `OPENAI_ADS_API_KEY` (required).
  - `OPENAI_ADS_BASE_URL` (default `https://api.ads.openai.com/v1`).
  - `OPENAI_ADS_OPENAPI_URL` (default `https://developers.openai.com/ads/openapi.json`) or
    `OPENAI_ADS_OPENAPI_PATH` (a local JSON file).
  - `OPENAI_ADS_TIMEOUT_SECONDS`, default 120 s. The old 600 s default existed for long model
    generations on the general API; Ads calls are CRUD and reporting.
  - The existing `MCP_*` transport, auth and stateless variables, unchanged.

  `OPENAI_ORG_ID`, `OPENAI_PROJECT_ID` and `OPENAI_MCP_MAX_BINARY_BYTES` are dropped.
- **Responses:** JSON bodies come back as `json`. Every other body comes back as `text`. The
  base64 branch and its size cap are removed, since the spec has no binary responses.
- **Spec loading:** switch to `json.loads` and drop the `pyyaml` / `types-PyYAML` dependencies.
  Discovery keeps `$ref` expansion at depth 1 by default, and `HTTP_METHODS` drops the unused PUT.
- **Safety:**
  - The shared `check_path` guard stays on both request tools.
  - `Authorization` and `Host` remain non-overridable; the org/project entries leave
    `PROTECTED_HEADERS`.
  - `Idempotency-Key` passes through.
  - Forwarded response headers are `content-type`, `x-request-id`, `openai-processing-ms`,
    `openai-version`, `retry-after` (if present) and any `x-ratelimit-*` / `ratelimit*` header.
    The rate-limit names are defensive because they aren't documented.
- **Instructions** (the `MCPServer` instructions string, which clients read as `Client.instructions`) cover:
  - the account > campaign > ad group > ad hierarchy
  - amounts in micros of the account currency
  - creating resources with `status: "paused"`
  - sending an `Idempotency-Key` on creates
  - confirming with the user before activating anything or changing budgets and spend limits
  - which upload endpoint takes which file, and that list endpoints page with `limit`/`after`/`before`

  The README tells the model to pass array query parameters under the name
  `openai_ads_describe_endpoint` shows, sent as repeated keys. The spec says `include`, while
  OpenAI's own curl examples write `include[]`.
- **Packaging/docs:**
  - Dockerfile, docker-compose, `.env.example`, `ci.env`, Makefile and pyproject are renamed,
    and the server README is rewritten.
  - The root `README.md` row is updated.
  - `mcp/README.md`: the table row, the strict-gates source link, the GHCR naming example, the
    "Adding a server" copy-from pointer and the generic-shape example all move to `openai-ads/`.
  - `mcp/google-search-console/README.md`'s `../openai` cross-link is updated.
  - CI needs no edit, because it globs `mcp/*/pyproject.toml`.
- **Out of scope:** the partner OAuth flow (API key only), a read-only mode, and typed
  per-resource tools.

## Success criteria
1. `mcp/openai-ads/` exists and `mcp/openai/` does not. The move is a `git mv`, so git reports
   the files as renames. (Git detects 20 files as renames. The 7 most heavily rewritten ones fall under its
   50% similarity threshold and show as delete+add, even though they were moved with `git mv`.)
   `make check` passes in the new directory (ruff ALL, format,
   `mypy --strict`, 100% line and branch coverage).
2. The server registers exactly four tools: `openai_ads_request`,
   `openai_ads_multipart_request`, `openai_ads_list_endpoints` and `openai_ads_describe_endpoint`.
   A test asserts this.
3. The defaults are `https://api.ads.openai.com/v1` and
   `https://developers.openai.com/ads/openapi.json`. A test using a JSON fixture spec lists and
   describes a campaigns operation; this test is the enforced pass condition. Best effort, when
   network access is available: a manual run against the live spec lists `POST /campaigns`,
   `POST /ad_groups` and `POST /ads`, recorded in the scratchpad.
4. `OPENAI_ADS_API_KEY` is required and sent as a Bearer token. Overrides of `Authorization`
   and `Host` are refused, `Idempotency-Key` passes through, and a `retry-after` response header
   is forwarded. Tests cover each.
5. Both path-taking request tools reject unsafe paths, with tests for each tool.
6. The server instructions state the hierarchy, micros, create-paused, Idempotency-Key-on-create
   and confirm-before-activating-or-changing-budgets guidance. A test checks for each element.
7. The Docker image builds and `/healthz` answers when started with `--env-file ci.env`.
   This runs locally if Docker is available, otherwise in CI.
8. Outside `.minerva/`, `git grep` finds none of these: `openai_mcp`, `openai-mcp`,
   `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_ORG_ID`, `OPENAI_PROJECT_ID`,
   `OPENAI_TIMEOUT_SECONDS`, `OPENAI_OPENAPI_PATH`, `OPENAI_OPENAPI_URL`,
   `OPENAI_MCP_MAX_BINARY_BYTES`. Every remaining `openai` hit from
   `git grep -n openai -- ':!.minerva'` is a reference to `openai-ads` or to OpenAI the vendor.
   Checking each hit by reading it catches relative links such as `../openai/`.
9. These docs describe or link the Ads server:
   - the server README
   - `mcp/README.md`: table row, strict-gates link, GHCR example, "Adding a server" copy-from
     pointer, generic-shape example
   - the root `README.md`
   - `mcp/google-search-console/README.md`

## Open Questions
- None blocking. The GHCR `openai-ads-mcp` package starts private, and the owner has to make it
  public once. This is already documented for every new package in `mcp/README.md`.

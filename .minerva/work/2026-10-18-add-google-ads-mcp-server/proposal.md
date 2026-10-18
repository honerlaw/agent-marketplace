# Proposal: add-google-ads-mcp-server

**Date**: 2026-10-18
**Status**: Draft

## Goal

A new server `mcp/google-ads/` (`google-ads-mcp`) that gives an LLM full access to the Google Ads
API (REST, v26) through a few generic, spec-driven tools, built to the same contract and strict
gates as `mcp/reddit-ads/` and `mcp/google-search-console/`, and published by `mcp.yml` as
`ghcr.io/honerlaw/google-ads-mcp`. The owner's driving use case is launching **YouTube Shorts**
ads: a Demand Gen campaign whose ad group's `demandGenAdGroupSettings.channelControls.selectedChannels`
enables only `youtubeShorts`, with a `DemandGenVideoResponsiveAd` over a `YoutubeVideoAsset`. Every
piece of that is a plain JSON mutate, so the generic tools reach it with no special-case tool.

Non-goals: wiring it into the seekless MCP gateway (a separate seekless work unit, once the image
is published); standard Video campaigns (the API itself cannot create or update them: "The Google
Ads API only supports fetching and reporting on existing Video campaigns"); any server-side spend
guard or read-only switch (see Approach); a developer-token setting.

## Why

The owner asked to manage Google Ads, specifically YouTube Shorts, from agents through the seekless
gateway, and chose (2026-10-18) to have it as an agent-marketplace server like `reddit-ads` and
`openai-ads` rather than a third-party server: "I would prefer all of the servers are in
agent-marketplace's mcp folder and then we only utilize them in here." Google's own MCP server is
read-only; the open-source write-capable ones (mharnett/mcp-google-ads, burnr8, ...) lack Shorts
channel controls and/or YouTube video asset creation, are single-maintainer, and would be built
from third-party source.

## Facts that shape the design (measured 2026-10-18)

- **API surface.** `https://googleads.googleapis.com/$discovery/rest?version=v26` (no auth, 200,
  3.3 MB JSON, Google **Discovery** format, not OpenAPI): 175 methods (POST 162, GET 12,
  DELETE 1), 1,497 schemas, one OAuth scope `https://www.googleapis.com/auth/adwords`. v26 is
  current (released 2026-10-14; v25 still served). Each method has a `path` with reserved
  expansion and the version prefix, e.g. `v26/customers/{+customerId}/googleAds:search`, and a
  `flatPath` with different names (`customers/{customersId}/...`). Some paths are catch-alls
  (`v26/{+resourceName}`, `v26/{+name}`), so a concrete path can fit several templates.
- **Shorts is reachable as JSON.** Schemas present in v26:
  `AdGroup.demandGenAdGroupSettings.channelControls.selectedChannels` with `youtubeShorts`,
  `youtubeInStream`, `youtubeInFeed`, `discover`, `gmail`, `display`, `maps`;
  `Common.YoutubeVideoAsset {youtubeVideoId, youtubeVideoTitle}`;
  `Common.DemandGenVideoResponsiveAdInfo` (videos, headlines, long headlines, descriptions,
  logo images, call to actions, business name). Schema presence does not prove the API accepts a
  Shorts-only selection for every account; that is proven live in the seekless unit.
- **Reads are GAQL.** `POST /customers/{id}/googleAds:search` takes `{query, pageToken, pageSize,
  validateOnly, searchSettings}`; pages come back with `nextPageToken` and the next page is the same
  POST with `pageToken` in the body, so no "follow this URL" tool is needed (unlike reddit-ads).
  `googleAds:searchStream` returns every row in one response, which can be far larger than a
  model's context.
- **Mutates support `validateOnly: true`** (Google validates without applying), a dry run the tool
  description points the model at. It is not enforced.
- **Developer tokens were sunset 2026-09-09** (Google's dev-token page, read 2026-10-18, not proven
  by a call): access levels now follow the Google Cloud project that issued the OAuth credentials;
  a sent token "is optional and ignored", and a future major version will reject one. So the server
  sends none and has no setting for one. A Cloud project with only Test access gets
  `CLOUD_PROJECT_NOT_APPROVED_FOR_PRODUCTION` (v25+) against a real account.
- **Manager accounts** need a `login-customer-id` header (digits, no dashes) naming the manager when
  acting on a client account through it.
- **Credentials.** Google Ads accepts OAuth user credentials (client id/secret + refresh token) or a
  service account added as a user of the Ads account. `mcp/google-search-console/credentials.py`
  loads exactly `service_account` or `authorized_user` JSON (refusing `external_account`, which can
  fetch URLs or run executables), refreshes off the event loop under a lock, and falls back to
  Application Default Credentials. It takes gsc's `Settings` and picks a scope from its `read_only`
  flag, so it is adapted, not copied byte for byte; its three `type: ignore[no-untyped-call]`
  comments carry over.
- **In-repo precedents.** Tool shape: `2026-09-25-decision-mcp-servers-expose-generic-spec-driven-tools`
  and `2026-09-25-decision-mcp-server-tool-shape-follows-api-size-and-stability`. Security:
  reddit-ads `safety.py` (`check_path`, `check_headers`, `PROTECTED_HEADERS`), the local-path
  pattern. SDK: `2026-09-25-reference-mcp-python-sdk-2x-server-facts` (mcp 2.x `MCPServer`, httpx2,
  a 4 MiB cap on HTTP **request** bodies, which bounds base64 image assets). CI discovers
  `mcp/*/pyproject.toml` by glob and publishes on `main` to `ghcr.io/<owner>/<dir>-mcp`; a new
  package starts private.
- **Size.** reddit-ads is ~1,800 lines of source and tests; this adds a Discovery reader and
  credentials, so expect ~2,000-2,500. One PR is still right: no independent subsystem.

## Approach

Copy `mcp/reddit-ads/`'s layout and gates, with `mcp/google-search-console/`'s credentials module:

- `src/google_ads_mcp/`:
  - `config.py`: `GOOGLE_ADS_CREDENTIALS_JSON` (service_account or authorized_user JSON; else ADC),
    `GOOGLE_ADS_LOGIN_CUSTOMER_ID` (optional; dashes stripped, digits required),
    `GOOGLE_ADS_API_VERSION` (default `v26`, the **only** version setting: the base URL
    `https://googleads.googleapis.com/<version>` and the Discovery URL are derived from it, with no
    base-URL or Discovery-URL override, so the bearer can only go to Google),
    `GOOGLE_ADS_DISCOVERY_PATH` (optional local copy, offline use), `GOOGLE_ADS_TIMEOUT_SECONDS`,
    `GOOGLE_ADS_MAX_RESPONSE_BYTES` (default 2 MiB), and the shared `MCP_*` transport settings
    (bearer required in http mode, `MCP_STATELESS`, `MCP_MAX_REQUEST_BYTES`).
  - `credentials.py`: gsc's loader and `TokenSource`, adapted to this `Settings`, adwords scope.
  - `safety.py`: reddit-ads' `check_path` and `check_headers` with `authorization`, `host`,
    `user-agent` protected; a caller's `login-customer-id` / `linked-customer-id` (matched
    case-insensitively) is normalized like the config value (dashes stripped, digits required) and
    replaces the configured default.
  - `api.py`: one request function: bearer from `TokenSource`, default `login-customer-id`, JSON
    in/out, returns status, `request-id` and the body; Google error bodies passed through; no retries.
    A response body over `GOOGLE_ADS_MAX_RESPONSE_BYTES` is not returned: the body is read as a
    stream and abandoned once it passes the limit (so memory stays bounded), and the tool raises a
    `ToolError` saying so and to use `googleAds:search` with a modest `pageSize` and `pageToken`, or
    a narrower query. Loud, never truncated.
  - `spec.py`: a lazy, cached Discovery reader (not OpenAPI). **One template spelling** everywhere:
    each method's `path` with the `<version>/` prefix stripped, a leading `/` added and `{+x}`
    written `{x}`, e.g. `/customers/{customerId}/adGroups:mutate`. `list_endpoints` prints that
    form; `describe_endpoint` takes a template **exactly as listed** (as reddit-ads' does, and its
    description says to copy it from `list_endpoints`), so no concrete-path matching and no
    catch-all tie-breaking exist; `google_ads_request` sends concrete paths and needs no template.
    Describe expands `$ref` schemas to a bounded depth (default 1); a ref left unexpanded is shown
    as its schema name. Google Ads bodies nest deeply (the Shorts flag sits about six refs below
    `MutateAdGroupsRequest`), so `describe_schema` reads one named schema at a time instead of
    expanding a whole tree into the model's context.
  - `server.py` / `http_app.py` / `main.py`: as reddit-ads (stdio or streamable HTTP, `/healthz`).
- Tools (four):
  - `google_ads_request(method, path, query?, body?, headers?)`: any call, e.g.
    `GET /customers:listAccessibleCustomers`, `POST /customers/123/googleAds:search` with a GAQL
    `query`, `POST /customers/123/campaigns:mutate`. The description names GAQL search,
    `pageToken` paging, preferring `search` to `searchStream`, and `validateOnly` as a dry run.
  - `google_ads_list_endpoints(text_filter?)`
  - `google_ads_describe_endpoint(method, path, depth?)`
  - `google_ads_describe_schema(name, depth?)`: one Discovery schema by the name `describe_*`
    printed for an unexpanded ref.
- **Version bumps** are a one-line change to the `GOOGLE_ADS_API_VERSION` default plus a fixture
  re-cut; the README says so.
- **No read-only switch, on purpose.** gsc has `GSC_READ_ONLY`; this server does not. The owner's
  standing policy for the gateway this server is built for is to expose every tool and bound it by
  the credential (a recorded owner feedback, 2026-09-25, which named `GSC_READ_ONLY` as the
  example not to repeat). The bound is the Google Ads user role of the service account or user
  (Read only / Standard / Admin) and the account's budgets; the README says so.
- Tests with no network: a trimmed Discovery fixture, an httpx2 mock transport, gsc-style
  credential fakes; 100% line and branch coverage; HTTP and stdio exercised with real servers as the
  siblings do. The fixture records the source version and Discovery `revision`, and the README's
  Development section states how it was cut (the methods kept plus the closure of schemas they
  reference, including the Shorts path).
- `Dockerfile`, `ci.env` (dummy `MCP_AUTH_TOKEN` only; credentials resolve on first tool call),
  `Makefile`, `.env.example`, `docker-compose.yml`, `README.md` (tools, getting credentials both
  ways, configuration, security model, limitations, and the Shorts launch as a worked sequence
  labelled **unverified against a live account** until the seekless unit runs it: budget →
  campaign (Demand Gen) → ad group with Shorts-only channel controls → `YoutubeVideoAsset` for a
  video already uploaded to YouTube as public or unlisted → logo image asset (base64, inside the 4 MiB request cap) → video
  responsive ad, each mutate first with `validateOnly`), and a row in `mcp/README.md`.
- Knowledge: a `reference` entry (Theme/Summary format) with the Google Ads API facts above.

Alternatives considered:
- **B. One typed tool per operation** (175): over client tool limits and stale as versions ship
  every ~quarter; rejected by the standing tool-shape decision.
- **C. Two hand-written tools, GAQL search + generic mutate, no discovery**: a Demand Gen launch
  needs exact nested mutate schemas the model cannot guess. C plus a describe tool is A.
- **D. Wrap mharnett/mcp-google-ads** (TypeScript, stdio-only, 40-odd typed tools): the owner chose
  agent-marketplace-native over third-party; it also lacks Shorts channel controls.

## Success criteria

1. `mcp/google-ads/` meets the `mcp/README.md` contract (pyproject with the copied strict
   `[tool.ruff]`/`[tool.mypy]`/`[tool.pytest]` blocks unchanged, Dockerfile non-root with
   `/healthz`, `ci.env`, Makefile, README, tests) and `make check` passes on Python 3.11 and 3.13
   with 100% line and branch coverage; the PR's `mcp.yml` `check` and `docker` jobs include
   `google-ads` and pass (the docker job starts the image with only `ci.env` and gets `/healthz`).
2. Over a mock transport, tests show: `google_ads_request` sends `Authorization: Bearer <token>` and
   every request's URL host is `googleads.googleapis.com` under `/<version>/` (asserted on the
   recorded request), the default `login-customer-id` is sent when configured, a caller's
   (any-case, dashed) `login-customer-id` or `linked-customer-id` is sent normalized (replacing the
   default for `login-customer-id`) and a non-numeric one is refused,
   `authorization`/`host`/`user-agent` overrides are refused, `/customers/1/googleAds:search` and
   `/customers:listAccessibleCustomers` pass the path guard while each reddit-ads guard case
   (scheme, `//`, `..`, `?`, `#`, `\`, and their percent-encoded forms) is refused, an over-limit
   response raises the size error, and credentials JSON of any type but
   `service_account`/`authorized_user` is refused.
3. A changed `GOOGLE_ADS_API_VERSION` moves both the request base URL and the Discovery URL (test).
4. Against the real v26 Discovery document (a one-off local run with `GOOGLE_ADS_DISCOVERY_PATH`
   pointing at a saved copy, its output and the first-load time kept in the scratchpad),
   `list_endpoints` reports 175 operations in the `/customers/{customerId}/...` form, and starting
   from `describe_endpoint POST /customers/{customerId}/adGroups:mutate` at default depth, following
   printed schema names with `describe_schema` reaches `selectedChannels.youtubeShorts`, with no
   single output over 50 KB; the trimmed test fixture is cut from that document.
5. Over HTTP the server refuses requests without the bearer and starts only when `MCP_AUTH_TOKEN` is
   set or `MCP_ALLOW_UNAUTHENTICATED=true`; no tool takes a filesystem path.
6. `README.md` documents both credential routes (OAuth refresh token as `authorized_user` JSON;
   service account added as a user in Google Ads), the role and budgets as the spend bound and why
   there is no read-only switch, the dev-token sunset, the Shorts sequence labelled unverified, and
   the accepted risk: anything the credential's Google Ads role allows, a caller can do, including
   spending money.
7. `mcp/README.md` lists the server; a knowledge `reference` entry records the API facts.

Post-merge check (outside the unit's pass/fail): `mcp.yml`'s `publish` job pushes
`ghcr.io/honerlaw/google-ads-mcp:<sha>` with its digest in the job summary. The owner then makes the
package public once, which the seekless unit needs before it can pull the image; the PR body says so.

## Open Questions

- **No live call is made in this unit.** There are no Google Ads credentials yet; the first real
  `listAccessibleCustomers` and the Shorts sequence run in the seekless wiring unit, once the owner
  has credentials in Doppler. Request shapes are checked against the Discovery document only, and
  the dev-token sunset is read from Google's docs, not proven by a call. **A fix-forward unit here is
  an expected outcome, not a surprise**: if the live run finds a wrong header, auth detail or
  Discovery assumption, the fix is a new agent-marketplace PR and a new published digest, which the
  seekless unit then pins.
- Whether a service account can be added directly as a Google Ads user for this account type is
  owner-side; the README documents both routes so either works.
- Hand-off to the seekless unit: it pins the image by tag + digest as `reddit-ads` does, and records
  the spend bound (role, budgets) in its credential-scope table.

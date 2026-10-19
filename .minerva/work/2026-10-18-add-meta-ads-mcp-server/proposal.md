# Proposal: add-meta-ads-mcp-server

**Date**: 2026-10-18
**Status**: Draft

## Goal
`mcp/meta-ads/`: an MCP server that gives an LLM full read and write access to Meta's Marketing API
(the Graph API, version `v26.0`) for the operator's own ad accounts, through a few generic,
spec-driven tools, with the same layout, gates and image contract as `mcp/reddit-ads/` and
`mcp/google-ads/`, while keeping the operator's credentials out of the model's context. Its first
consumer is the seekless MCP gateway, which will run it as a container (a separate seekless unit).
"Full" covers every Graph call the token allows except the stated limitations (no batch requests in
v1, no chunked video upload, and no page or minted tokens: any `access_token` field is redacted by
design). Writes are built and tested against mocks; the first live write is a manual, owner-approved
step (criterion 9), unverified until it runs.

## Why
The owner wants Meta Ads behind the seekless MCP gateway with full campaign control. Meta's own hosted
MCP server (`mcp.facebook.com/ads`) cannot sit behind the gateway: measured 2026-10-18, its dynamic
client registration answers `invalid_client_metadata: "Dynamic registration is not available for this
client."` for every redirect URI tried (Cloudflare's dashboard and shared callbacks, the gateway's own,
and localhost). The Marketing API takes a **system-user access token**, which a server can hold.

Facts, measured 2026-10-18 with the owner's real credentials (values never printed):
- `GET /v26.0/debug_token?input_token=<token>` with `Authorization: Bearer <app_id>|<app_secret>`
  → 200: `is_valid: true`, `type: SYSTEM_USER`, `expires_at: 0` (never), `data_access_expires_at: 0`,
  scopes `ads_management ads_read business_management pages_show_list pages_read_engagement
  pages_manage_ads catalog_management threads_business_basic public_profile`.
- `GET /v26.0/me/adaccounts` with `Authorization: Bearer <token>` **and** `appsecret_proof` → 200
  (one account, USD); `GET /v26.0/me` with the bearer and no proof → 200. So header auth works and the
  proof is accepted with it (this app does not require the proof; the server sends it anyway).
- Graph pagination answered with `paging.cursors` only (opaque `before`/`after`, not secrets) on that
  call; other edges return `paging.next` / `previous` as full URLs, which Meta builds with an embedded
  `access_token` query parameter.

Facts from sources:
- Meta publishes no OpenAPI spec. `facebook/facebook-business-sdk-codegen`'s `api_specs/specs/`
  describes 1,103 node types (pinned commit `8420be6d5752c568a4f01dd608fa3cce6b2db960`, 2026-09-17;
  tarball 1.2 MB; 1,104 `*.json` files, 2.67 MB; **content hash**
  `618ff17fe424d41c681e0a92ace962fac839413c0e9a837aedf601f78f0970f4` = sha256 over the files in
  order of their basenames, each as `basename \0 bytes \0`; the definition is the code in
`spec_fetch.content_hash` (basenames sorted as Python `str`, case-sensitive, UTF-8 encoded). GitHub regenerates archives on demand, so the
  tarball's own bytes are not pinned; the extracted content is; `enum_types.json`, 975 enums). Each node has `fields` (name, type) and `apis`
  (1,503 entries): node operations `#get` / `#update` / `#delete` (404), edges with an `endpoint`
  (1,029 unnamed plus 64 named `gen*`), and 6 `gen*` entries with a `basePath` instead
  (`IntegrityAppeal` ×5, `AdCampaignPlacement` ×1) whose path is not under a node id.
- The codegen specs are not versioned per Graph version: the pinned commit is the SDK's state on
  2026-09-17, whose templates name `v26.0`, so the catalog describes v26.0 as the SDK saw it then;
  mismatches with live v26.0 are possible and the README says so.
- Its licence permits use, copy and distribution "in connection with the web services and APIs
  provided by Facebook", with the copyright notice kept.
- System-user tokens: "Never expires" or 60 days; refresh call documented (README only).

## Approach
Copy the strict blocks and contract from `mcp/openai-ads/` (as `mcp/README.md` says) and the layout of
`mcp/google-ads/`, adapted to the Graph API:

- `src/meta_ads_mcp/`:
  - `config.py`: `META_ADS_ACCESS_TOKEN` (required at the first tool call, not at start, so the CI
    smoke test starts with only `ci.env`), `META_APP_ID` + `META_APP_SECRET` (both or neither;
    with them every call carries `appsecret_proof` and `meta_ads_token_status` works),
    `META_ADS_API_VERSION` (default `v26.0`, must match `v<digits>.<digits>`; the base URL
    `https://graph.facebook.com/<version>` is derived from it, with no base-URL override),
    `META_ADS_SPEC_PATH` (directory of codegen `*.json` specs; operator config, never a tool argument;
    the image sets it), `META_ADS_TIMEOUT_SECONDS`, `META_ADS_MAX_RESPONSE_BYTES` (default 2 MiB), the
    shared `MCP_*` settings. Numeric settings positive and finite.
  - `safety.py` (the security boundary):
    - `check_path`: reddit-ads' guard (single leading `/`; no scheme, `//`, `?`, `#`, `\`; printable
      ASCII) extended per the dot-segment knowledge entry: no `.` or `..` segment after decoding once
      **and** twice (`%252e%252e`). The bare path `/` is refused (Graph's root is the batch and
      `?ids=` multi-read endpoint; batch is out of v1).
    - `check_params`: one check for `query`, `body` and a pagination URL's query: refuses, at the top
      level and case-insensitively, `access_token`, `appsecret_proof`, `batch`, `method`,
      `suppress_http_code`, `callback`, and the same names with a bracket suffix
      (`access_token[0]`). Graph reads these as top-level parameter names only. A scan of the pinned
      specs (2026-10-18) found none of them as a Marketing API parameter (`access_token` only on two
      Instagram token-exchange `#get`s), so nothing legitimate is blocked. `ids=` (multi-node read)
      and `include_headers` are allowed: both only shape a read of nodes the token can already reach. Credential keys would override or leak the configured token;
      `batch` carries unguarded relative URLs; `method` silently turns a request into another verb;
      `suppress_http_code` / `callback` change response semantics.
    - No caller headers at all: the request tool takes no `headers` argument (no Graph call needs
      one), which also closes `X-HTTP-Method-Override`-style verb overrides.
    - `check_page_url`: parsed exactly: scheme `https`, hostname equal to `graph.facebook.com`, no
      userinfo, no port, no fragment, path under `/<version>/` passing `check_path` after removing the
      prefix, query passing `check_params` once Meta's own `access_token` / `appsecret_proof` are
      stripped (they are re-added from config, never reused).
  - `scrub.py`: applied to every tool output **and** every `ToolError` / exception text (the app
    token `<app_id>|<app_secret>` is covered by the secret literal):
    (1) exact-literal replacement of the configured token, app secret and computed proof with
    `[redacted]` in every string, including JSON-encoded strings; (2) under any `paging` object,
    `access_token` and `appsecret_proof` query parameters are removed from URL values (structural,
    only there, so ad data such as a creative `link` is never rewritten); (3) a JSON key named
    `access_token` anywhere in a response has its value replaced with `[redacted]`. (3) is a
    deliberate choice: page tokens (`/me/accounts`) and minted tokens are credentials too, and the
    system user already holds the assets, so the model never needs one; the README says so.
  - `api.py`: one request function. The token goes in `Authorization: Bearer <token>` (never in the
    URL); `appsecret_proof` (HMAC-SHA256, key = app secret, message = access token, hex digest) is
    added as a query parameter when the app secret is set. Request size is bounded by
    `MCP_MAX_REQUEST_BYTES` (4 MiB) on the MCP side; there is no separate outbound body cap. `body_format`:
    `json` (default; Graph accepts JSON bodies on POST) or `form` (top-level keys form-encoded, nested
    values JSON-encoded, Graph's convention; needed for `POST /act_<id>/adimages` with a base64
    `bytes`). Returns the status, `x-fb-trace-id` / `x-fb-request-id`, Meta's usage headers
    (`x-business-use-case-usage`, `x-ad-account-usage`, `x-app-usage`) and the scrubbed body; Meta error
    bodies pass through scrubbed; no retries (the description names the rate-limit codes 4, 17, 613,
    80000–80014 and says backing off is the caller's job). Over-limit bodies are abandoned mid-stream
    with a `ToolError`.
  - Spec modules, split to stay within the complexity gates: `spec_fetch.py` (download the pinned
    tarball with its own client and no `Authorization` header, read `api_specs/specs/*.json` from it
    in memory with a decompressed-size cap of 16 MiB, verify the **content hash**, and, as
    `python -m meta_ads_mcp.spec_fetch <dir>`, write the files plus the tarball's top-level codegen
    `LICENSE` (not hashed; required present and non-empty) to a directory, which the Dockerfile
    uses), `spec_catalog.py` (a lazy, cached, single-flight load from `META_ADS_SPEC_PATH`, else
    `spec_fetch` in memory; the content hash is checked on both paths against an expected hash that
    is a constructor argument defaulting to the pinned constant: `build_server` passes it through,
    so tests pass the trimmed fixture's own hash (written by `tests/cut_specs.py` beside the fixture)
    exactly as they inject the HTTP transport. There is no environment knob to skip or change it) and
    `spec_render.py`
    (templates, list lines, describe output). A load failure is a `ToolError` on the discovery tools
    only; `meta_ads_request` never touches the spec. **Template spelling**: a node operation is
    `METHOD /{NodeType}` (`GET /{Campaign}`, `POST /{Campaign}` for `#update`, `DELETE /{Campaign}`);
    an edge (unnamed or `gen*` with an `endpoint`) is `METHOD /{NodeType}/<edge>`; a `basePath` entry
    is its literal path (`GET /integrity/appeals/ads/eligibility`). **One line per spec entry**:
    `list_endpoints` counts exactly 1,503 lines for the pinned specs, and where two entries share a
    method and template `describe_endpoint` returns every match. `list_endpoints` prints `METHOD template → Return`;
    `describe_endpoint` takes a template exactly as listed (a concrete path such as `/act_1/campaigns`
    matches nothing and the error says to copy a template from `meta_ads_list_endpoints`) and prints params (name, type, required),
    enum values from `enum_types.json`; `describe_type` prints a node's fields with enum values.
    The tool descriptions say how to map concrete paths: `act_<id>` is an `AdAccount`, `/me` a `User`,
    a bare numeric id is whatever object it was read as. Any discovery output over
    `META_ADS_MAX_RESPONSE_BYTES` is refused with a message to narrow the filter, never truncated.
    The unfiltered list (1,503 short lines, about 0.1 MB) is under the default cap; a large
    `describe_type` (e.g. `AdAccount`'s fields with enum values) is what the cap guards.
  - `token_status.py`: `meta_ads_token_status` calls `GET /debug_token?input_token=<token>` with
    `Authorization: Bearer <app_id>|<app_secret>` and returns only `is_valid`, `type`, `app_id`,
    `expires_at` ("never" for 0, else ISO), `data_access_expires_at` (same), `scopes` and
    `granular_scopes` (which assets each scope reaches); scrubbed like everything else. Without app
    id and secret it returns `{"available": false, "reason": "set META_APP_ID and META_APP_SECRET"}`
    and makes no call.
  - **Logs**: `main.py` raises the `httpx`/`httpcore` loggers (and httpx2's, whatever names it uses,
    found in work) to WARNING before serving, because they log full request URLs at INFO and
    `appsecret_proof` is in every URL and the token in `debug_token`'s
    (seekless knowledge `2026-10-13-constraint-httpx-logs-the-query-string-so-a-url-key-reaches-the-logs`). Without app id/secret it says so.
  - `server.py` / `http_app.py` / `main.py`: as google-ads (stdio or streamable HTTP, `/healthz`).
- Tools (six): `meta_ads_request(method, path, query?, body?, body_format?)`,
  `meta_ads_follow_page(url)`, `meta_ads_list_endpoints(text_filter?)`,
  `meta_ads_describe_endpoint(method, path)`, `meta_ads_describe_type(name)`,
  `meta_ads_token_status()`. The request tool's description names `fields=`, cursor paging,
  `status=PAUSED` on create as the safe default, budgets in the currency's minor units, the
  rate-limit codes, and that writes change live campaigns and spend real money (in the tool
  description, since a gateway may drop server instructions).
- **The spec ships in the image.** After installing the package, the Dockerfile runs
  `python -m meta_ads_mcp.spec_fetch /app/specs` (Python only: the slim base has no curl), which
  fails the build on a content-hash mismatch, adds the codegen `LICENSE`, and sets
  `META_ADS_SPEC_PATH=/app/specs`, so a running container makes no request to GitHub. This build step
  is a deliberate divergence from the siblings' Dockerfiles. The commit and content hash live in one
  place, `spec_fetch.py`; a re-pin changes both there. Local stdio use either sets
  `META_ADS_SPEC_PATH` (a `make specs` target fetches and verifies the same tarball) or falls back to
  the verified runtime fetch.
- **No read-only switch, on purpose** (as google-ads): the owner asked for full campaign access, and the
  gateway's policy bounds a server by its credential. The bound is the system user's assigned assets,
  the token's permissions and the ad account's spend limit; the README says so.
- **Version drift**: the spec is pinned independently of `META_ADS_API_VERSION`; the README says a
  version bump is a one-line default change plus a re-pinned spec commit and sha, that Meta retires
  Graph versions about two years after release, and that the catalog describes the pinned spec, not
  necessarily an overridden version.
- **Token lifetime.** A never-expiring token (the owner's, measured) needs nothing. A 60-day token is
  visible through `meta_ads_token_status`; the README gives the refresh call and rotation. Automatic
  refresh needs durable state, so it is out of scope.
- Limitations (README and Goal): no batch requests; any JSON key named `access_token` in a response
  is redacted (page tokens included); chunked video upload (`graph-video.facebook.com`,
  multipart) out of reach by construction; video by `file_url` and images by base64 `bytes`
  (`body_format: form`) work.
- README security model also says the httpx/httpx2 loggers are held at WARNING and why; that
  `ids=` reads several nodes at once outside the edge catalog; and that building the image fetches
  from `codeload.github.com`, so the build is not hermetic.
- Knowledge followed: the generic-tools tool-shape decision, `ci.env`, dot segments, server-local
  paths, the mock-transport-lock entry, and seekless's httpx-logs-URLs constraint. The strict pyproject
  blocks are copied with only the package name changed.
- Tests with no network: a trimmed spec fixture cut from the pinned commit by `tests/cut_specs.py`
  (including an `IntegrityAppeal` `basePath` entry, `AdsInsights`, `AdAccount`, `Campaign` and their
  enums), an httpx2 mock transport; 100% line and branch coverage; HTTP and stdio exercised with real
  servers as the siblings do; a concurrency test for the single-flight load that actually overlaps
  callers (per the mock-transport-lock knowledge entry).
- `Dockerfile` (non-root, `/healthz`, the spec stage), `ci.env` (dummy `MCP_AUTH_TOKEN` only),
  `Makefile` (incl. `specs`), `.env.example`, `docker-compose.yml`, `README.md` (tools; system-user
  token steps incl. app mode and asset assignment; `data_access_expires_at` explained; configuration;
  security model: header auth, proof, scrub, refused keys, no batch; egress hosts: `graph.facebook.com`
  only, plus `codeload.github.com` only for the runtime spec fallback; limitations; a worked campaign
  → ad set → creative → ad sequence created `PAUSED`, unverified against a live write), a row in
  `mcp/README.md`.
- Knowledge: a `reference` entry (Theme/Summary) with the Meta facts above.

Alternatives considered:
- **B. One typed tool per operation** (1,503): rejected by the standing tool-shape decision.
- **C. Wrap the `facebook-business` Python SDK**: a large dependency mirroring the same specs; hides
  the HTTP the guards must see.
- **D. Proxy Meta's hosted MCP server**: DCR refused (measured).
- **E. Fetch specs file by file**: 1,103 requests.
- **F′. Runtime tarball fetch only** (the first draft): every cold start of a stateless container
  needs GitHub egress; F (bake into the image, runtime fetch kept as a verified fallback) dominates.
- **Batch support in v1**: each item's `relative_url`, `body` string and headers would need the same
  guards and its JSON-string `body` responses the scrub; deferred, refused until then.

## Success criteria
1. `mcp/meta-ads/` meets the `mcp/README.md` contract (pyproject with the strict blocks copied
   with only the package name changed, non-root Dockerfile with `/healthz`, `ci.env`, Makefile, README, tests) and `make check`
   passes on Python 3.11 and 3.13 with 100% line and branch coverage; the PR's `mcp.yml` `check` and
   `docker` jobs include `meta-ads` and pass (the image build fetches the specs and verifies the
   content hash; the image holds `/app/specs` with the 1,104 `*.json` files plus the codegen
   `LICENSE`).
2. Over a mock transport, tests show: every request goes to `https://graph.facebook.com/v26.0/...` with
   `Authorization: Bearer <token>` and no `access_token` in the URL; `appsecret_proof` equals
   HMAC-SHA256(token, secret) when the secret is set and is absent otherwise; each refused key
   (`access_token`, `appsecret_proof`, `batch`, `method`, `suppress_http_code`, `callback`, any case,
   and with a `[...]` suffix) is refused in `query`, in `body` and in a `follow_page` URL, while a
   nested key (`{"fields": {"access_token": 1}}`), `ids` and `include_headers` pass; the request
   tool has no `headers` argument and its description carries the spend warning and the
   `status=PAUSED` default; each reddit-ads path-guard case, bare `.`/`..` segments, the double-encoded form and the
   bare `/` are refused while `/act_1/campaigns`, `/123` and `/me/adaccounts` pass; `follow_page`
   refuses another host, userinfo, a port, `http`, another version, and re-adds credentials;
   `body_format: form` form-encodes with nested values JSON-encoded; an over-limit body raises the size
   error.
3. **Secret containment**: for every tool, over mock responses of each shape (success, Graph error
   body, `paging.next` with `access_token=` and `appsecret_proof=`, a nested string and a JSON-string
   containing the token, a `/me/accounts`-style `access_token` field, a transport exception whose
   message embeds the full request URL with the proof, and a `debug_token` call), no output and no
   `ToolError` text contains the token, the app secret or the proof (asserted by substring over the
   serialized output); with the loggers as `main.py` configures them, a captured log of those calls
   contains none of the three either; a creative `link` containing `access_token=` outside
   `paging` is returned unchanged.
4. A changed `META_ADS_API_VERSION` moves the request base URL; a malformed version is refused (tests).
   The spec loader refuses content with the wrong hash (expected hash injected as in the other tests)
   or over the size cap, and two concurrent first calls trigger one fetch (tests).
5. Against the real pinned specs (one-off local run with `META_ADS_SPEC_PATH`, output and load time in
   the scratchpad, loaded through the real pinned hash): `list_endpoints` with an empty filter returns
   exactly 1,503 lines, under the default cap; `describe_endpoint POST /{AdAccount}/campaigns` lists `objective` with its enum
   values; `describe_type Campaign` lists `daily_budget`; `describe_endpoint GET
   /integrity/appeals/ads/eligibility` resolves; each of these named describe outputs is under 50 KB
   (a test budget, not a product limit); a duplicate (method, template) pair in the fixture returns
   every match; `token_status` without app credentials returns the unavailable answer and an unfiltered
   list over the cap is refused with the narrow-the-filter message.
6. Over HTTP the server refuses requests without the bearer and starts only when `MCP_AUTH_TOKEN` is
   set or `MCP_ALLOW_UNAUTHENTICATED=true`; no tool takes a filesystem path.
7. **Manual evidence, outside CI**: a live read-only smoke run (one-off, the owner's token from Doppler injected, values never printed;
   output in the scratchpad): `meta_ads_token_status` reports `never`, and `meta_ads_request GET
   /me/adaccounts` returns the account with no secret in the output.
8. `README.md` documents the token steps, both expiry kinds and rotation, the security model, egress
   hosts, limitations and the PAUSED-first sequence; `mcp/README.md` lists the server; a `reference`
   knowledge entry with Theme/Summary records the Meta facts.
9. **Manual, owner-approved** (asked for at the time; if declined, recorded as unverified): one
   zero-spend live write: create a `PAUSED` campaign, read it back, delete it, output in the
   scratchpad.

## Open Questions
- Whether every write endpoint accepts a JSON body; `body_format: form` is the fallback either way,
  and the README says JSON writes are unverified until the first live write.

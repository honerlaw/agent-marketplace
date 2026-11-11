# Proposal: 2026-11-10-add-clerk-mcp-server

**Date**: 2026-11-10
**Status**: Proposed

## Goal
`mcp/clerk/`: an MCP server that gives an LLM read and write access to the **Clerk Backend API**
(`https://api.clerk.com/v1`) for one Clerk instance, authenticated with that instance's secret key.
The first use is reading Seekless's production users ("who signed up recently"). It reaches the API
through three generic, spec-driven tools, has the same layout, gates and image contract as
`mcp/openai-ads/`, and keeps the **configured secret key** out of every result. Credentials that
Clerk itself returns by design (sign-in, actor, testing and M2M tokens, OAuth application and
machine secrets, API key secrets, users' provider access tokens) come back as Clerk sends them.

"Full" means every operation in Clerk's published Backend API spec, version **2026-08-20**:
264 operations over 184 paths, of which `clerk_request` can send the **261 JSON** ones (users, organizations, sessions, invitations, allowlists,
JWT templates, OAuth applications, domains, webhooks and more). It has these limitations:
- **No multipart uploads.** Three operations take `multipart/form-data`:
  `POST /users/{user_id}/profile_image`, `PUT /organizations/{organization_id}/logo` and
  `PUT /oauth_applications/{oauth_application_id}/logo`. They only set images, and sending a file
  through a tool argument is bounded by the 4 MiB MCP body cap. The README lists them.
- **One API version.** Every request carries the pinned version; moving to a newer version is a
  re-pin PR.
- **One instance per deployment.** The secret key decides the instance (`sk_live_…` production,
  `sk_test_…` development).

## Why
The owner asked to read users who recently signed up through the MCP gateway. Clerk's hosted MCP
server (`mcp.clerk.com`), added to the gateway as an OAuth upstream in seekless #3671, refuses the
gateway: after the owner's sign-in, `whoami` returned "This MCP client cannot use authenticated Clerk
tools. Authenticated access is limited to the OAuth application this server is configured with."
The owner then chose option B: our own server over the Backend API with a production secret key,
in agent-marketplace like every other gateway server, with seekless only pinning its image.

Facts (from Clerk's spec and docs, read 2026-11-10; no live call was made — an unauthenticated
probe of `api.clerk.com` was refused by this session's permission check):
- **Spec.** `github.com/clerk/openapi-specs` (MIT, default branch `main`, pushed 2026-11-10) holds
  `bapi/<version>.yml` for 2021-02-05, 2024-10-01, 2025-03-12, 2025-04-10, 2025-11-10, 2026-05-12
  and 2026-08-20. `bapi/2026-08-20.yml` is OpenAPI 3.0.3, 836,785 bytes as YAML and about 630 KB as
  compact JSON: 184 paths, 264 operations, 187 component schemas, server
  `https://api.clerk.com/v1`, one security scheme `bearerAuth` ("Secret key, obtained under API
  Keys in the Clerk Dashboard", format `sk_<environment>_<secret value>`). No operation declares a
  header parameter. Three request bodies are multipart; the rest are JSON.
- **Versions (docs, clerk.com/docs/versioning/available-versions).** A caller picks a version with
  the `Clerk-API-Version` header **or** the `__clerk_api_version` query parameter, never both: both,
  or an invalid version, is an invalid request. The docs do not say what an unversioned request
  gets. 2026-08-20 changed only the Frontend API; its Backend API equals 2026-05-12.
- **Reach of a secret key.** A Clerk secret key is not scoped: it can do everything the Backend API
  can on its instance, including deleting and banning users, minting sign-in tokens
  (`POST /sign_in_tokens`) and impersonation actor tokens (`POST /actor_tokens`), and changing
  instance settings. The server cannot narrow that; the gateway's Access policy (owner only) and
  each client's permission settings are the bounds.
- **Pagination.** List endpoints take `limit` and `offset` (e.g. `GET /users`, up to 500 per page,
  with `order_by` such as `-created_at`); `GET /users/count` returns a total. No follow-a-URL
  paging, so no paging tool is needed.

## Approach
Copy `mcp/openai-ads/`'s contract, strict blocks and layout (`config.py`, `safety.py`, `api.py`,
`spec.py`, `server.py`, `http_app.py`, `main.py`, `__main__.py`, Dockerfile, Makefile), plus a
small `scrub.py`, adapted as follows. Package `clerk_mcp`, console script `clerk-mcp`, image
`ghcr.io/<owner>/clerk-mcp` (published by `mcp.yml`'s existing glob; no workflow edit).

**A vendored, pinned spec.** `src/clerk_mcp/bapi.json` is `bapi/2026-08-20.yml` from
`clerk/openapi-specs` at commit `af85fe9443c550f6de08634ab26abe95d78e6f7e` (the file's last change,
2026-11-05; blob `c57d7c31…`, sha256 `95287228…4ab4e0`, both recorded in full in `bapi.LICENSE`
and the README), converted to compact JSON, with `bapi.LICENSE` carrying
Clerk's MIT notice (the `catalog.json` + `catalog.LICENSE` precedent in `mcp/microsoft-ads/`). It is
loaded lazily with `importlib.resources`. `CLERK_API_VERSION = "2026-08-20"` is one constant, and a
test asserts it equals the vendored spec's `info.version`, so the spec and the version header cannot
drift. The README gives the re-pin recipe: download the YAML at a commit,
convert with `uv run --with pyyaml python -I -c …` (PyYAML only at re-pin time, never a package
dependency), record the new commit, blob and sha256. Dated spec files are edited after release
(this one on 2026-11-05), which is another reason to vendor rather than fetch.
**Fallback if Clerk rejects the header:** 2026-08-20 changed only the Frontend API, so its Backend
API equals 2026-05-12. If the wiring unit's smoke call shows the header refused, re-pin to
`bapi/2026-05-12.yml` with `CLERK_API_VERSION = "2026-05-12"`; the equality test keeps the two in
step either way. Vendoring beats fetching at runtime: no PyYAML
dependency, no startup dependency on GitHub, and the spec cannot change under a running image.

**Three tools** (the gateway prefixes them `clerk_`):
- `clerk_request(method, path, query=None, body=None)` — any JSON operation. `method` is a
  plain string in the tool schema (its description lists GET, POST, PUT, PATCH, DELETE); the server
  upper-cases it, so `get` is GET, and refuses any other method with no request sent. A `Literal`
  would make the schema reject `get` before the server could normalize it.
  `(method, path)` is deliberately **not** checked against the spec: discovery is advisory, and a
  new Clerk endpoint stays reachable before a re-pin. `path` is relative to
  `/v1` (e.g. `/users`). Returns status, the response headers `content-type`, `retry-after` and any
  `x-ratelimit-*` / `ratelimit*` (never `set-cookie`), and the JSON or text body. No retries: a 429
  comes back as a result with its `retry-after`.
- `clerk_list_endpoints(text_filter=None)` — one line per operation: method, path, summary.
- `clerk_describe_endpoint(method, path, depth=1)` — parameters, request body and responses with
  `$ref`s inlined `depth` levels (clamped to 1..6), as in `openai-ads`.

**Safety, all tested at the tool level with an assertion that no request went out:**
- The base URL is the constant `https://api.clerk.com/v1`; no env override.
- `path` must start with one `/` and is refused if it contains `://`, `?`, `#`, `\`, **`%`**, any
  whitespace or non-printable character, or any empty, `.` or `..` segment. Refusing `%` outright
  (Clerk's path ids and slugs never need it) means no encoded form (`%2e`, `%2f`, `%5c`, `%252e`) can
  reach the client, so there is no "decoded or raw?" question
  (`2026-09-25-pattern-percent-encoding-does-not-confine-a-dot-segment`,
  `2026-11-05-pattern-validate-a-url-with-the-parser-that-fetches-it`). Tests assert on the URL the
  client actually sent: host `api.clerk.com`, prefix `/v1`.
- Redirects are never followed (`follow_redirects=False`, asserted by a test), so the bearer key
  cannot travel to another host; a 3xx comes back as a result.
- A result's body is capped at `MAX_BODY_CHARS` (256 KiB of text), applied **after** the key is
  scrubbed so a cut can never leave part of the key. Past it the body is cut and the result says so
  with the full length, so a 500-user page cannot flood the model's context; the
  README recommends small `limit`s.
- Callers cannot send headers; the tool takes none. The server sets `Authorization: Bearer <key>`
  and `Clerk-API-Version` itself.
- A query key `__clerk_api_version`, compared case-insensitively, is refused, so the pinned
  version always applies.
- Every string in a result, JSON keys and values alike, is scrubbed of the secret key before it
  returns (`scrub.py` is
  `mcp/microsoft-ads/`'s `Scrubber`, reduced to one fixed literal), so even an error that echoes a request cannot leak
  it.
- HTTP mode requires `MCP_AUTH_TOKEN` (bearer, `hmac.compare_digest`), `/healthz` stays open, as
  every server here.

**Reach, stated on purpose.** The owner's rule is to expose every tool and bound by credential, but
a Clerk secret key is unscoped, so here the credential bounds nothing on its instance. The server
therefore does **not** silently drop endpoints: the credential-minting and secret-returning
operations, for example (`/sign_in_tokens`, `/actor_tokens` (impersonation), `/testing_tokens`, `/m2m_tokens`,
`/sessions/{id}/tokens`, `/api_keys/{id}/secret`, `/machines/{id}/secret_key`,
`/users/{id}/oauth_access_tokens/{provider}`, `rotate_secret`) stay reachable, and the README names
them as examples, not an exhaustive list. Two things bound it instead:
- **An opt-in `CLERK_READ_ONLY=true`** that refuses every method but GET before any request goes
  out. It is off by default (the expose-everything rule). The README says plainly that GET still
  reads secrets (`/api_keys/{id}/secret`, `/machines/{id}/secret_key`, `GET /m2m_tokens`, users'
  provider tokens), and that reads sent as POST (`/users/{id}/verify_password`, `verify_totp`, the
  `*/verify` endpoints) are refused in this mode.
- **The deployment decision.** Whether the production key runs read-only or read-write is an
  explicit owner decision carried to the seekless wiring unit, not made here.

The README also says that production user records (emails, names, metadata) are **personal data**
that flows into the model's context and the client's logs, and names the **prompt-injection** path: user records (names, metadata) are
user-controlled text, and the same session holds write tools. Clients should never auto-allow
`clerk_request`.

**Config.** `CLERK_SECRET_KEY` is required and must start with `sk_`. `CLERK_READ_ONLY` is optional
(`true`/`false`, default `false`). The standard `MCP_*` variables
as in `openai-ads`. `ci.env` holds dummy values (`CLERK_SECRET_KEY=sk_test_ci`).

**Discovery marks the gaps.** `clerk_list_endpoints` and `clerk_describe_endpoint` mark the three
multipart operations as not callable through `clerk_request`.

**Docs.** `mcp/clerk/README.md` (tools, configuration, the secret key's full reach and the
secret-bearing endpoints, read-only mode, prompt injection, the three multipart operations not
covered, a note that the Backend API in 2026-08-20 equals 2026-05-12, re-pin recipe, examples such as the 20 most recent sign-ups:
`GET /users?order_by=-created_at&limit=20`) and a row in `mcp/README.md`'s table.

Considered and rejected:
- **Fetch the YAML spec at runtime** (like `openai-ads` fetches its JSON): adds PyYAML and a GitHub
  dependency at first use, and lets the spec move away from the pinned version header.
- **Typed per-operation tools for users only** (like `google-search-console`): 264 operations is
  "large", per `2026-09-25-decision-mcp-server-tool-shape-follows-api-size-and-stability`, and the
  owner asked for the general server, not a narrow capability.
- **Statically refusing the credential-minting endpoints.** It contradicts the owner's
  expose-everything rule, and an opt-in read-only mode plus the owner's deployment decision bound the
  same risk without hiding tools.

**Out of this unit:** the seekless wiring (a `container_servers.clerk` entry pinned by tag and
digest, a `moved` block from the OAuth `clerk` server, the credentials-map line, Doppler keys set by
the owner, docs). It is a separate unit in the seekless repo that starts once this image is
published, because it needs the digest.

## Success criteria
1. `make install && make check` in `mcp/clerk/` passes: `ruff check` (ALL), `ruff format --check`,
   `mypy --strict`, pytest with 100% line and branch coverage.
2. Tests show, each at the tool level: the request carries `Authorization: Bearer <key>` and
   `Clerk-API-Version: 2026-08-20` and the URL actually sent is `https://api.clerk.com/v1<path>`;
   paths with `..`, `.`, an empty segment, `://`, `?`, `#`, `\`, `%` (including `%2e%2e`, `%2f`,
   `%5c`, `%252e`) or whitespace are refused with no request sent; no path template in the vendored
   spec contains a character the guard refuses; a `__clerk_api_version` query key (any case) is
   refused with no request sent; a method outside GET/POST/PUT/PATCH/DELETE is refused and a
   lower-case `get` is sent as GET; a 3xx response is returned, not followed; a body over
   `MAX_BODY_CHARS` comes back cut and marked with its full length; with `CLERK_READ_ONLY=true` a
   non-GET is refused with no request sent and a GET (including lower-case `get`) goes out; a
   response or error that contains the secret key, in a JSON key or value or straddling the
   `MAX_BODY_CHARS` cut, comes back with it scrubbed; `set-cookie` is never forwarded; HTTP mode refuses a missing or wrong bearer and serves
   `/healthz` without one.
3. A test asserts the vendored spec's `info.version` equals `CLERK_API_VERSION`;
   `clerk_list_endpoints` over the vendored spec lists 264 operations, 3 of them marked multipart
   (not callable); the built wheel contains `bapi.json` and `bapi.LICENSE`; `bapi.LICENSE` records
   the source commit, blob and sha256.
4. `docker build` of `mcp/clerk/` succeeds and the image answers `/healthz` with `--env-file
   mcp/clerk/ci.env` (CI's `docker` job, green on the PR).
5. `mcp/clerk/README.md` exists with the sections above, `bapi.LICENSE` carries the MIT notice, and
   `mcp/README.md`'s table has a `clerk` row.
6. After merge, `mcp.yml`'s `publish` job pushes `ghcr.io/<repository-owner>/clerk-mcp` (today
   `honerlaw`) tagged with the merge SHA and `latest`; the digest is read from the job summary and handed to the seekless wiring unit
   (post-merge by construction).

## Open Questions
- **For the seekless wiring unit (owner decision):** run the production key read-write, or start
  with `CLERK_READ_ONLY=true`. Recommendation: start read-only, since the stated use (recent sign-ups)
  is a pure read, and flip it when a write is wanted.
- None blocking here. Live behaviour (an unversioned request's default, real response sizes) is first
  measured by the seekless wiring unit's smoke call, once the owner has set the key.

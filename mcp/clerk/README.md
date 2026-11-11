# clerk-mcp

An MCP server that lets an LLM read and manage **one Clerk instance through the Clerk
Backend API** (`https://api.clerk.com/v1`). That covers users, organizations, sessions,
invitations, allowlists and blocklists, JWT templates, OAuth applications, domains,
webhooks and more. It authenticates with the instance's **secret key**. Instead of one
tool per endpoint, it exposes three generic tools that together reach every JSON endpoint
in Clerk's published spec.

| Tool | What it does |
|---|---|
| `clerk_request(method, path, query?, body?)` | Any JSON call, e.g. `GET /users`, `PATCH /users/{user_id}`, `POST /users/{user_id}/ban` |
| `clerk_list_endpoints(text_filter?)` | Lists the operations in the vendored Backend API spec |
| `clerk_describe_endpoint(method, path, depth?)` | Parameters and schemas of one operation |

Paths are relative to `https://api.clerk.com/v1`, so `/users` means
`https://api.clerk.com/v1/users`. `method` is `GET`, `POST`, `PUT`, `PATCH` or `DELETE`, in
any case. Lists page with `limit` (1–500, default 10) and `offset`. Keep `limit` small:
user records are large, and a result's body is cut at 64 KiB of compact JSON.

## Reading users

The 20 most recent sign-ups:

```json
{"method": "GET", "path": "/users", "query": {"order_by": "-created_at", "limit": 20}}
```

More examples:
- `GET /users/count` gives the total.
- `GET /users/{user_id}` returns one user.
- `GET /users` takes filters such as `email_address`, `query`, `created_at_after` and
  `last_active_at_since`. See `clerk_describe_endpoint("GET", "/users")` for the full list.

## Get the secret key

In the [Clerk Dashboard](https://dashboard.clerk.com), open the application, then **API
Keys**, and copy the **Secret key**. Which key you use decides the instance:
- `sk_live_…` is **production**: real users.
- `sk_test_…` is development.

Use one server per instance.

## The key's reach (read this before deploying)

**A Clerk secret key is not scoped.** It can do everything the Backend API can on its
instance, so the key bounds nothing. This server exposes all of it, on purpose. Nothing
is hidden, and these operations are reachable too:

- **Operations that mint credentials or act as someone else.** Examples:
  - `POST /sign_in_tokens`: sign in as any user.
  - `POST /actor_tokens`: impersonation.
  - `POST /testing_tokens`
  - `POST /m2m_tokens`
  - `POST /sessions/{session_id}/tokens`
  - `POST /oauth_applications/{id}/rotate_secret`
- **Reads that return secrets.** Examples:
  - `GET /api_keys/{id}/secret`
  - `GET /machines/{id}/secret_key`
  - `GET /m2m_tokens`
  - `GET /users/{user_id}/oauth_access_tokens/{provider}`: a user's Google or other
    provider token.
- **Destructive changes.** Deleting or banning users and organizations, and changing
  instance settings, domains, redirect URLs and OAuth applications.

These lists are examples, not exhaustive. `clerk_list_endpoints` shows everything.

What bounds it:

- **`CLERK_READ_ONLY=true`.** Refuses every method except `GET` before anything is sent.
  It is off by default. GET still returns secrets (see above). Reads that Clerk models as
  POST are refused in this mode: `POST /users/{user_id}/verify_password`, `verify_totp`,
  and the `*/verify` endpoints.
- **Who can reach the server.** Use HTTP mode with `MCP_AUTH_TOKEN`, behind TLS, for one
  operator.
- **Your client's permission settings.** Never auto-allow `clerk_request`.

**Personal data and prompt injection.** User records hold emails, names, phone numbers and
metadata. They reach the model's context and the client's logs. Names and metadata are
user-written text, so a hostile sign-up can carry instructions. The session that reads them
also holds the write tools. The server's instructions tell the model to treat that text as
data and to confirm before any write. The server enforces neither, except through
`CLERK_READ_ONLY`.

## Run locally (stdio)

```bash
cd mcp/clerk
make install            # creates .venv with the server and dev tools
claude mcp add clerk --env CLERK_SECRET_KEY=sk_test_... --env CLERK_READ_ONLY=true -- \
  /absolute/path/to/mcp/clerk/.venv/bin/clerk-mcp
```

## Run over HTTP / Docker

```bash
cd mcp/clerk
cp .env.example .env    # set CLERK_SECRET_KEY and MCP_AUTH_TOKEN (openssl rand -hex 32)
docker compose up --build
```

The MCP endpoint is `http://<host>:8000/mcp`, and clients must send
`Authorization: Bearer <MCP_AUTH_TOKEN>`. `GET /healthz` needs no authentication, so load
balancers can call it. CI publishes the image as `ghcr.io/<owner>/clerk-mcp` (see
`../README.md`).

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `CLERK_SECRET_KEY` | — (required) | The instance's secret key, sent with every request. Surrounding whitespace is stripped; it must then be `sk_live_` or `sk_test_` followed by letters and digits, or the server will not start |
| `CLERK_READ_ONLY` | `false` | Set `true` to refuse every method except GET. Like every switch here it accepts `true`/`false`, `1`/`0`, `yes`/`no`, `on`/`off`; any other value stops the server at startup, so a typo cannot quietly mean "off" |
| `CLERK_TIMEOUT_SECONDS` | `60` | Per-request timeout |
| `MCP_TRANSPORT` | `stdio` (`http` in Docker) | `stdio` or `http` |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `8000` (`0.0.0.0` in Docker) | HTTP bind address |
| `MCP_AUTH_TOKEN` | unset | Bearer token. **Required** in http mode |
| `MCP_ALLOW_UNAUTHENTICATED` | `false` | Set `true` to run http mode without a token |
| `MCP_MAX_REQUEST_BYTES` | `4194304` (4 MiB) | Largest HTTP request body |
| `MCP_STATELESS` | `false` | Set `true` to serve http mode without sessions, for hosts that stop idle instances or for several replicas |

## Security model

- **The key only goes to `api.clerk.com`.**
  - The base URL is a constant, and redirects are never followed. A 3xx comes back as a
    result.
  - `path` must start with `/` and use only letters, digits and `/-._~:@!$&'()*+,;=`.
    So it cannot contain a scheme, a query, a fragment, a backslash, whitespace, non-ASCII
    or **any `%`**. With `%` refused, no encoded form (`%2e`, `%2f`, `%252e`) can reach the
    HTTP client.
  - Empty, `.` and `..` segments are refused.
  - Callers cannot send headers.
- **The API version is pinned.** Every request sends `Clerk-API-Version: 2026-08-20`. A
  query key `__clerk_api_version` (any case) is refused, because Clerk treats both
  together as an invalid request.
- **The key is scrubbed** from every result and error: JSON keys and values, forwarded
  headers and text. Scrubbing happens before the 64 KiB cut, so no fragment of the key
  survives. Credentials that Clerk returns by design are not scrubbed (see above).
- **Response headers are an allowlist.** Only `content-type`, `retry-after` and any
  `x-ratelimit-*` or `ratelimit*` header come through. `set-cookie` never does. There are
  no retries: a 429 comes back with its `retry-after`.
- **HTTP mode is closed by default.** The server won't start without `MCP_AUTH_TOKEN`
  unless `MCP_ALLOW_UNAUTHENTICATED=true`. Tokens are compared in constant time.

## The vendored spec

The discovery tools read `src/clerk_mcp/bapi.json`. It is Clerk's
`bapi/2026-08-20.yml` from [clerk/openapi-specs](https://github.com/clerk/openapi-specs)
(MIT), converted to compact JSON with its content unchanged. `bapi.LICENSE` records the
source commit, blob and sha256. The spec has 264 operations. `clerk_request` can send 261
of them; the other three are multipart uploads (see Limitations).

The version every request sends is the spec's own version. A test holds
`CLERK_API_VERSION` (in `spec.py`) equal to the spec's `info.version`, so the two move
together. The Backend API in `2026-08-20` is the same as `2026-05-12`: that release changed
only Clerk's Frontend API.

The spec is vendored rather than fetched, because Clerk edits dated spec files after
release (this one last changed on 2026-11-05).

**To re-pin** to `<version>` at `<commit>` (PyYAML is needed only here, never by the
package):

```bash
curl -sSfL -o /tmp/bapi.yml \
  https://raw.githubusercontent.com/clerk/openapi-specs/<commit>/bapi/<version>.yml
shasum -a 256 /tmp/bapi.yml
uv run --with pyyaml python -I -c 'import json, sys, yaml; \
  json.dump(yaml.safe_load(open(sys.argv[1])), open(sys.argv[2], "w"), separators=(",", ":"), ensure_ascii=False)' \
  /tmp/bapi.yml src/clerk_mcp/bapi.json
```

Then update `bapi.LICENSE` (commit, blob from `git hash-object /tmp/bapi.yml`, sha256),
`CLERK_API_VERSION`, and the counts and `VENDORED_SHA256` in `tests/test_spec.py`.

If Clerk ever refuses the `2026-08-20` header for Backend API calls, re-pin to
`2026-05-12`. Its Backend API is the same.

## Limitations

- **No multipart uploads.** `POST /users/{user_id}/profile_image`,
  `PUT /organizations/{organization_id}/logo` and
  `PUT /oauth_applications/{oauth_application_id}/logo` take `multipart/form-data`. They
  only set images, and the discovery tools mark them as not callable.
- **One API version and one instance per server.**
- **The body cap counts the compact body.** MCP clients get each result twice (structured
  content and a pretty-printed text copy), so a capped result can reach the model at about three
  times 64 KiB.
- **Discovery is advisory.** `clerk_request` does not check `(method, path)` against the
  spec, so an endpoint Clerk adds after the pin is still reachable.
- **Not measured live when written.** The request shape follows Clerk's spec and docs.
  The first live call was left to the deployment.

## Development

The code is held to strict gates, configured in `pyproject.toml` and run identically in
CI (`.github/workflows/mcp.yml`):

- `ruff check`, with every rule family on, McCabe complexity ≤ 5, and the pylint limits
- `ruff format --check`
- `mypy --strict`
- `pytest` at 100% line and branch coverage

```bash
make install
make check
```

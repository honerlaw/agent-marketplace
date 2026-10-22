# r2-uploads-mcp

An MCP server that lets an agent **host a local file temporarily in a Cloudflare R2 bucket** and
get back a link another service can fetch it from. It's for APIs that take a file by URL, such
as TikTok's `UPLOAD_BY_URL` video upload, Meta's `advideos` `file_url` and Reddit's `media.url`.

The server never receives file bytes, so it works when it is deployed remotely, behind a
gateway, while the file is on the agent's machine. It hands out short-lived presigned URLs (and,
if the deployment connects a public custom domain, a plain `public_url`), and the agent's own
shell does the upload:

```
agent                               r2-uploads-mcp                       R2 bucket
  │ r2_create_upload(path)               │                                   │
  │ ────────────────────────────────────▶│                                   │
  │ ◀── key, upload_command, download_url│                                   │
  │ curl --upload-file <path> <presigned PUT URL> ─────────────────────────▶│
  │ hand download_url to TikTok / Meta / … ── they GET the presigned URL ──▶│
```

| Tool | What it does |
|---|---|
| `r2_create_upload(path)` | Picks a new key (`<date>/<random>/<file name>`) and returns a presigned PUT `upload_url`, a ready-to-run `upload_command` (`curl --fail --upload-file …`), and a presigned GET `download_url`, with their expiry times. With a public hostname configured, also an unsigned `public_url`. No network call. |
| `r2_list_uploads(prefix?)` | Lists up to 1,000 objects (`ListObjectsV2`), each with its size, time and a fresh `download_url` (and `public_url` when configured). `prefix` narrows it, e.g. `2026-10-19/` |

### Which link to hand over

- **`download_url`** is a presigned GET. It expires at `download_expires_at` and answers **GET only**:
  a signature covers one HTTP method, so a `HEAD` request to it is refused with 403. Fine for a
  service that downloads the file straight away with a GET (for example TikTok's `UPLOAD_BY_URL`).
- **`public_url`** is present only when the deployment sets `R2_PUBLIC_BASE_URL`. It is the
  object's plain URL on the bucket's public custom domain: no signature, so it answers `HEAD`
  and `GET` (with ranges) until the bucket's lifecycle rule deletes the object. Use it for a
  service that checks a link with `HEAD` first, or that fetches the file later (for example a
  social scheduler that downloads the video when the post goes out).

`path` is the file's local path. Only its base name, reduced to `A-Z a-z 0-9 . _ -`, goes into
the key. The full path goes into `upload_command`, shell-quoted.

## Configuration

Nothing about the bucket is built in. The deployment supplies all of it:

| Variable | Default | Meaning |
|---|---|---|
| `R2_ACCOUNT_ID` | **required** | The Cloudflare account id (32 hex characters). The endpoint is `https://<id>.r2.cloudflarestorage.com` |
| `R2_BUCKET` | **required** | The bucket. Use one dedicated to this server |
| `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | **required** | An R2 API token's S3 credentials, scoped to that one bucket (Object Read & Write) |
| `R2_UPLOAD_EXPIRES_SECONDS` | `900` (15 min) | How long an upload URL works, 1 s to 7 days |
| `R2_DOWNLOAD_EXPIRES_SECONDS` | `86400` (24 h) | How long a download URL works, 1 s to 7 days |
| `R2_PUBLIC_BASE_URL` | unset | The bucket's public custom domain as `https://<host>` (nothing after the host). When set, both tools add `public_url = <base>/<key>`. It only names the domain: the bucket is public as soon as the custom domain is connected, set or not |
| `R2_TIMEOUT_SECONDS` | `30` | Timeout of the listing request |
| `MCP_TRANSPORT` | `stdio` (`http` in Docker) | `stdio` or `http` |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `8000` (`0.0.0.0` in Docker) | HTTP bind address |
| `MCP_AUTH_TOKEN` | unset | Bearer token; **required** in http mode |
| `MCP_ALLOW_UNAUTHENTICATED` | `false` | Set `true` to run http mode without a token |
| `MCP_MAX_REQUEST_BYTES` | `4194304` (4 MiB) | Largest HTTP request body |
| `MCP_STATELESS` | `false` | Set `true` to serve http mode without sessions, for hosts that stop idle instances or run several replicas |

### The bucket

1. Create a private bucket. Don't enable an `r2.dev` URL. By default every link this server
   hands out is presigned. If a consumer needs a plain URL (one that answers `HEAD`, or lasts
   until the file is deleted), connect a **custom domain** to the bucket and set
   `R2_PUBLIC_BASE_URL` to it. That makes **every object in the bucket** readable by anyone who
   knows its key, so use a bucket that holds only files meant to be published anyway.
2. Add a lifecycle rule that deletes objects after a day or a few. That is what makes the
   hosting temporary. The server never deletes anything.
3. Create an R2 API token with **Object Read & Write** on that bucket only, and pass its S3
   access key id and secret.

## Run

```bash
cd mcp/r2-uploads
make install
cp .env.example .env    # fill in the R2_* values and MCP_AUTH_TOKEN (openssl rand -hex 32)
docker compose up --build
```

The MCP endpoint is `http://<host>:8000/mcp`, and clients send
`Authorization: Bearer <MCP_AUTH_TOKEN>`. `GET /healthz` is unauthenticated. Pushes to `main`
publish the image as `ghcr.io/<owner>/r2-uploads-mcp` (see [`../README.md`](../README.md)).

Locally over stdio, for Claude Code:

```bash
claude mcp add r2-uploads --env R2_ACCOUNT_ID=… --env R2_BUCKET=… \
  --env R2_ACCESS_KEY_ID=… --env R2_SECRET_ACCESS_KEY=… -- \
  /absolute/path/to/mcp/r2-uploads/.venv/bin/r2-uploads-mcp
```

## Security model

- **The bucket key pair never leaves the server.** Clients get presigned URLs, each good for one
  method on one object until it expires. An upload URL can't read, list or overwrite anything
  else. A download URL can't write.
- **Callers never name a host or a bucket.** Every URL is built for the configured account's
  endpoint and bucket, and the key or prefix is percent-encoded into it. `R2_ACCOUNT_ID` must be
  exactly 32 hex characters, because it becomes part of the hostname.
- **A new key every upload.** Keys carry 64 random bits, so an upload never replaces an earlier
  file. That is also why a leaked download link exposes one file, not the bucket.
- **HTTP mode is closed by default.** The server won't start without `MCP_AUTH_TOKEN` unless
  you set `MCP_ALLOW_UNAUTHENTICATED=true`. Tokens are compared in constant time. The secret
  and the token are left out of the settings' `repr`.
- **No URL reaches the logs.** The HTTP client libraries log full request URLs at INFO, and the
  listing URL is presigned, so their loggers are held at WARNING.
- **Accepted risk: anyone with an upload URL can store any file of any size at that key** until
  it expires (15 minutes by default). Presigned PUTs can't cap the size on R2. The lifecycle
  rule removes it.
- **Accepted risk: a download URL is a bearer link.** Anyone it is shared with can fetch the file
  until the URL expires, and so can anyone they pass it on to.
- **With `R2_PUBLIC_BASE_URL` set, the bucket is public by key.** Anyone who has an object's key
  or `public_url` can fetch it until the lifecycle rule deletes it (and a CDN may keep serving a
  cached copy for its cache lifetime after that); `download_url`'s expiry then bounds nothing for
  that object. Nothing can be listed through the custom domain, and the key's 64 random bits make
  a URL unguessable. Only disconnecting the custom domain makes the bucket private again; unsetting
  `R2_PUBLIC_BASE_URL` just stops the server from printing `public_url`.

## Limitations

- **One upload is one PUT**, so a file can be at most 5 GiB, R2's single-request limit. There is no
  multipart upload.
- **The listing stops at 1,000 objects** and says so with `truncated: true`. Narrow it with
  `prefix`. With a lifecycle rule the bucket stays small.
- **A download URL lasts at most 7 days**, the Signature Version 4 limit. Ask
  `r2_list_uploads` for a fresh one.
- **A download URL answers GET only.** A presigned signature covers one method, so a fetcher
  that probes with `HEAD` first gets 403. Give such a fetcher `public_url`.
- **The shell running `upload_command` must reach `*.r2.cloudflarestorage.com`.** A sandbox that
  blocks it makes `curl` fail, and the command exits non-zero.

## Development

The code is held to the same strict gates as every server here (see
[`../README.md`](../README.md)): Ruff with every rule, complexity ≤ 5, `mypy --strict` and 100%
line and branch coverage. Signing is checked against AWS's published presigned-URL example, and
R2 is a mock transport in the tests.

```bash
make install
make check
```

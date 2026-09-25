# Proposal: add-openai-mcp-server

**Date**: 2026-09-25
**Status**: Draft

## Goal

Add a top-level `mcp/` directory to this repo that houses custom MCP (Model Context Protocol)
servers, one self-contained subdirectory per server. Ship the first one, `mcp/openai/`: an MCP
server that gives an LLM client **full control of the OpenAI REST API** using the operator's
OpenAI API key, and that runs three ways — locally over stdio (Claude Code / Claude Desktop /
Codex MCP config), locally over streamable HTTP, and as a Docker container deployable anywhere.

The code is held to **extremely strict lint, static-analysis and test gates** that force simple,
readable, low-complexity code (user requirement, 2026-09-25).

## Why

The user wants a home for custom MCP servers in this marketplace repo, and wants an LLM to be able
to drive the entire OpenAI API (responses, chat, embeddings, images, audio, files, batches,
fine-tuning, vector stores, assistants, moderation, models, uploads, evals, admin endpoints if the
key allows, …) — not a curated subset. The API surface is large and changes often, so hand-written
per-endpoint tools would be both incomplete and perpetually stale. The user also asked that every
server here be forced toward the simplest, most readable code possible via tooling, not goodwill.

## Approach

**Layout.** `mcp/README.md` indexes servers and states the per-server contract: each server is
its own directory with `pyproject.toml`, `Dockerfile`, `README.md`, `tests/`, and the shared strict
quality configuration. `mcp/openai/` is a Python package (`openai_mcp`) built on the official MCP
Python SDK (`mcp>=2.2,<3`, `MCPServer`; verified on PyPI — 2.2.0 is current) and `httpx`, with a
`hatchling` build backend. This is the repo's **first `pyproject.toml` and first Dockerfile**, so
`mcp/README.md` names that as a new convention rather than implying continuity. The root
`README.md` gains a short "MCP servers" section pointing at `mcp/`. Python matches the rest of the
repo's tooling. Security-critical logic (path/header validation, bearer-auth middleware) lives in
its own small modules so review can target it.

**Tool surface — generic, spec-driven, small (approach A).** Instead of one tool per endpoint,
expose five tools that together reach every endpoint:

1. `openai_request(method, path, query?, body?, headers?)` — any JSON request against the
   configured base URL (`/v1`). Returns status, an allowlist of response headers (`content-type`,
   `x-request-id`, `openai-processing-ms`, `openai-organization`, `openai-version`,
   `x-ratelimit-*`), and the JSON body
   (or text; binary responses base64-encoded up to `OPENAI_MCP_MAX_BINARY_BYTES`, default
   20 MiB, beyond which the tool returns an error pointing at `openai_download`). `stream: true`
   is supported but **buffered**: the raw SSE text is returned once the stream completes (a stated
   v1 limitation).
2. `openai_multipart_request(path, fields, files)` — multipart uploads (`/files`,
   `/uploads/{id}/parts`, `/audio/transcriptions`, `/audio/translations`, `/images/edits`, …).
   Each file is base64 content, or a local file path. **Local paths resolve on the server's
   filesystem**, so they are useful only when client and server share a filesystem (stdio, or a
   mounted volume); remote HTTP/Docker clients send base64.
3. `openai_list_endpoints(filter?)` — lists `METHOD /path — summary` from OpenAI's published
   OpenAPI spec, filterable by substring.
4. `openai_describe_endpoint(method, path)` — the operation's parameters and request/response
   schemas from the spec, with `$ref`s resolved to a bounded depth (default 6; deeper refs are left as `$ref` markers).
5. `openai_download(path, save_to?)` — fetches binary content (e.g. `/files/{id}/content`,
   generated audio) and writes it to a server-local path, or returns base64 under the size cap.
   **`save_to` writes on the server's filesystem**, so in HTTP/Docker mode without a mounted volume
   a binary larger than the cap is not retrievable by a remote client (a stated v1 limitation,
   mirroring the upload-side one; the operator raises the cap or mounts a volume).

The OpenAPI spec is loaded lazily on first discovery call from `OPENAI_OPENAPI_PATH` (a local
file, for offline / egress-restricted deployments) or else `OPENAI_OPENAPI_URL` (default
`https://raw.githubusercontent.com/openai/openai-openapi/manual_spec/openapi.yaml`), and cached in
memory. The default URL is an **accepted egress dependency on GitHub** and tracks a mutable
branch; spec unavailability only degrades the two discovery tools with a clear error — requests
still work.

**Safety of the key.** `path` must be a relative API path (starts with `/`, no scheme/host, no
`..` segments, no `//`); requests only ever go to `OPENAI_BASE_URL`, so a prompt-injected model
cannot send the `Authorization` header elsewhere. Caller-supplied headers may not override
`Authorization`, `Host`, `OpenAI-Organization` or `OpenAI-Project`. **Accepted risk:** by design any
caller authorized to reach the server can trigger any operation the key permits, including
cost-bearing ones (fine-tunes, batches, image/audio generation) — there is no rate or spend limit
in v1; the operator bounds risk with a scoped OpenAI project key and project spend limits,
documented in the README.

**Configuration (env vars).** `OPENAI_API_KEY` (required), `OPENAI_BASE_URL` (default
`https://api.openai.com/v1`), `OPENAI_ORG_ID`, `OPENAI_PROJECT_ID`, `OPENAI_TIMEOUT_SECONDS`,
`OPENAI_MCP_MAX_BINARY_BYTES`, `OPENAI_OPENAPI_PATH`, `OPENAI_OPENAPI_URL`, `MCP_TRANSPORT`
(`stdio` | `http`, default `stdio`), `MCP_HOST`, `MCP_PORT`, `MCP_AUTH_TOKEN`,
`MCP_ALLOW_UNAUTHENTICATED`, `MCP_MAX_REQUEST_BYTES` (HTTP request-body cap; default 64 MiB, raised
from the SDK's 4 MiB so base64 uploads fit). In `http` mode the server **refuses to start without
`MCP_AUTH_TOKEN`** (bearer-token check, constant-time compare, on every request except `/healthz`)
unless `MCP_ALLOW_UNAUTHENTICATED=true` is set explicitly — a deployed server holding an OpenAI
key must not be open by default.

**Docker.** `mcp/openai/Dockerfile` (slim Python base, non-root user, `MCP_TRANSPORT=http`,
`EXPOSE 8000`, healthcheck on unauthenticated `GET /healthz`), plus `docker-compose.yml` and
`.env.example`.

**Strict quality gates (user requirement).** Configured in `mcp/openai/pyproject.toml` and
enforced in CI; none may be loosened per-file without an inline justification comment:
- **Ruff lint** with `select = ["ALL"]`, ignoring only rules that conflict with each other or the
  formatter (e.g. `D203`/`D213`, `COM812`, `ISC001`), plus McCabe `max-complexity = 5` and
  pylint limits `max-args = 5`, `max-branches = 6`, `max-statements = 25`, `max-returns = 4`,
  `max-nested-blocks = 2`.
- **Ruff format** check (no diff allowed).
- **mypy `--strict`** over the package and tests (no `Any` leaking from our own code; untyped
  third-party imports are the only permitted overrides).
- **pytest** with **100% line and branch coverage** (`--cov-fail-under=100 --cov-branch`).
A single `make check` (or equivalent script) runs all four locally, identically to CI.

**Tests.** `mcp/openai/tests/` uses pytest with `httpx.MockTransport` (no network, no API key):
path validation, header protection, JSON/binary/multipart/SSE handling, the size cap, spec
listing/describe against a small fixture spec and its unreachable-spec error, auth-middleware
accept/reject over the HTTP app (including a multipart call over HTTP), startup refusal without a
token, an in-process MCP client listing exactly the five tools, and a stdio smoke test that
spawns the server as a subprocess and completes an MCP handshake over real pipes (catching stray
non-protocol bytes on stdout, which in-process tests cannot).

**CI — tests cannot go dark.** Per knowledge `2026-08-11-decision-ci-runs-the-whole-suite`
("collection is the enumeration"), `.github/workflows/mcp.yml` runs on **every** PR and push to
main (no `paths:` filter — accepting the extra CI minutes), discovers servers by glob
(`mcp/*/pyproject.toml`) rather than an enumerated list, and for each runs the four quality gates
plus `docker build`; pytest exit code 5 (no tests collected) fails the job. Matrix: Python 3.11 and
3.13, matching `evals.yml`. Root `pytest tests/` stays as is because servers carry dependencies the
root job does not install. Marking the new workflow a required status check is a repository
setting outside this diff; the final report surfaces it.

**Alternatives considered.**
- **B — one MCP tool per OpenAPI operation** (~200+ tools). Rejected: exceeds client tool limits
  (~100–128 in several clients), floods context every turn, and still needs the spec at startup.
- **C — hand-curated tools for popular endpoints.** Rejected: fails "full control" and goes stale.
- **TypeScript SDK.** Rejected: the repo's tooling, tests and CI are Python.
- **Phasing** (safety core first, discovery/Docker/CI later). Rejected: the phases are not
  independently mergeable — the CI and auth middleware must land with the code they guard.

## Success criteria

- [ ] `mcp/README.md` documents the one-directory-per-server convention, the shared strict-quality contract, and lists `openai`.
- [ ] `mcp/openai/` contains `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `README.md`, the `openai_mcp` package and `tests/`.
- [ ] An in-process MCP client test lists exactly the five tools named in Approach.
- [ ] Tests show `openai_request`, `openai_multipart_request` and `openai_download` each reject absolute URLs, `..` segments and `//`, and that protected-header overrides are rejected.
- [ ] A stdio smoke test spawns the server with `MCP_TRANSPORT=stdio`, completes an MCP handshake over real pipes and lists the five tools.
- [ ] Tests exercise JSON, binary (under and over the size cap), SSE-buffered and multipart requests against `httpx.MockTransport`.
- [ ] Tests show the discovery tools list and describe operations from a fixture spec (via `OPENAI_OPENAPI_PATH`) and return a clear error when the spec is unreachable.
- [ ] Tests show HTTP mode refuses to start without `MCP_AUTH_TOKEN` unless `MCP_ALLOW_UNAUTHENTICATED=true`, rejects missing/wrong bearer tokens, serves `/healthz` unauthenticated, and completes an authenticated multipart tool call over HTTP.
- [ ] In `mcp/openai/`: `ruff check`, `ruff format --check`, `mypy --strict` and `pytest` at 100% line+branch coverage all pass, with the rule set and limits stated in Approach.
- [ ] `docker build mcp/openai` succeeds and the running container answers `GET /healthz` with 200.
- [ ] `.github/workflows/mcp.yml` has no `paths:` filter, discovers servers by glob, runs all four gates plus `docker build`, and fails on zero collected tests.
- [ ] Root `README.md` points to `mcp/`; root `pytest tests/` still passes.
- [ ] `mcp/openai/README.md` documents stdio config for Claude Code / Claude Desktop, HTTP/Docker usage, every env var, the security model including the accepted cost risk, the buffered-streaming limitation, and the server-local-path limitation for uploads and downloads in HTTP/Docker mode.

## Open Questions

- Per-request OpenAI key override (multi-tenant) — deferred; single operator key for now.
- Server-side rate / spend limits — deferred; v1 relies on OpenAI project-level limits.
- Remote retrieval of binaries larger than the cap in HTTP/Docker mode (e.g. chunked download) — deferred; documented limitation.

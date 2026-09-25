# openai-mcp

An MCP server that gives an LLM **full access to the OpenAI REST API** using your
API key. Instead of one tool per endpoint, it exposes five generic tools that
together reach every endpoint, so it doesn't go stale when OpenAI adds endpoints.

| Tool | What it does |
|---|---|
| `openai_request(method, path, query?, body?, headers?)` | Any JSON call, e.g. `POST /responses`, `GET /models`, `DELETE /files/{id}` |
| `openai_multipart_request(path, files, fields?)` | File uploads: `/files`, `/uploads/{id}/parts`, `/audio/transcriptions`, `/images/edits`, … |
| `openai_download(path, save_to?)` | Binary content, e.g. `/files/{id}/content`, returned as base64 or written to a file |
| `openai_list_endpoints(text_filter?)` | Lists operations from OpenAI's published OpenAPI spec |
| `openai_describe_endpoint(method, path, depth?)` | Parameters and schemas of one operation |

Paths are relative to the base URL (`https://api.openai.com/v1`), so
`/chat/completions` means `https://api.openai.com/v1/chat/completions`.

## Run locally (stdio)

```bash
cd mcp/openai
make install            # creates .venv with the server and dev tools
```

Claude Code:

```bash
claude mcp add openai --env OPENAI_API_KEY=sk-... -- \
  /absolute/path/to/mcp/openai/.venv/bin/openai-mcp
```

Claude Desktop / other clients (`mcpServers` JSON):

```json
{
  "mcpServers": {
    "openai": {
      "command": "/absolute/path/to/mcp/openai/.venv/bin/openai-mcp",
      "env": { "OPENAI_API_KEY": "sk-..." }
    }
  }
}
```

## Run over HTTP / Docker

```bash
cd mcp/openai
cp .env.example .env    # set OPENAI_API_KEY and MCP_AUTH_TOKEN (openssl rand -hex 32)
docker compose up --build
```

The MCP endpoint is `http://<host>:8000/mcp`, and clients must send
`Authorization: Bearer <MCP_AUTH_TOKEN>`. `GET /healthz` is unauthenticated for
load balancers. For Claude Code:

```bash
claude mcp add --transport http openai http://localhost:8000/mcp \
  --header "Authorization: Bearer <MCP_AUTH_TOKEN>"
```

Deploy the image anywhere that runs containers. Put it behind TLS: the bearer
token is only as private as the connection carrying it.

Without Docker: `MCP_TRANSPORT=http MCP_AUTH_TOKEN=... OPENAI_API_KEY=... .venv/bin/openai-mcp`.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `OPENAI_API_KEY` | — (required) | Key sent with every request |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | API base URL; every request stays on it |
| `OPENAI_ORG_ID` / `OPENAI_PROJECT_ID` | unset | Sent as `OpenAI-Organization` / `OpenAI-Project` |
| `OPENAI_TIMEOUT_SECONDS` | `600` | Per-request timeout |
| `OPENAI_MCP_MAX_BINARY_BYTES` | `20971520` (20 MiB) | Largest binary returned inline as base64 |
| `OPENAI_OPENAPI_PATH` | unset | Local spec file for discovery (offline / restricted egress) |
| `OPENAI_OPENAPI_URL` | openai-openapi `manual_spec` on GitHub | Spec URL used when no path is set |
| `MCP_TRANSPORT` | `stdio` (`http` in Docker) | `stdio` or `http` |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `8000` (`0.0.0.0` in Docker) | HTTP bind address |
| `MCP_AUTH_TOKEN` | unset | Bearer token; **required** in http mode |
| `MCP_ALLOW_UNAUTHENTICATED` | `false` | Set `true` to run http mode without a token |
| `MCP_MAX_REQUEST_BYTES` | `67108864` (64 MiB) | Largest HTTP request body, which bounds base64 uploads |

## Security model

- **The key never leaves the base URL.** `path` must be a plain relative path (no
  scheme, host, `//`, `..`, query or fragment), so a prompt-injected model can't
  send your key to another host. Callers can't override `Authorization`, `Host`,
  `OpenAI-Organization` or `OpenAI-Project`.
- **HTTP mode is closed by default.** The server won't start without
  `MCP_AUTH_TOKEN` unless you set `MCP_ALLOW_UNAUTHENTICATED=true`. Tokens are
  compared in constant time.
- **Accepted risk: anything the key can do, the client can do.** This includes
  cost-bearing operations (fine-tunes, batches, image and audio generation) and
  admin endpoints if you use an admin key. There's no server-side rate or spend
  limit, so bound the risk with a **project-scoped key** and OpenAI project
  budget limits.

## Limitations

- **Streaming is buffered.** With `"stream": true` the raw server-sent events are
  returned once the stream finishes, not incrementally.
- **Local paths are server-local.** `local_path` uploads and `save_to` downloads
  use the server's filesystem. Remote HTTP/Docker clients send uploads as base64.
  They can only retrieve downloads inline, up to `OPENAI_MCP_MAX_BINARY_BYTES`,
  unless you mount a volume or raise the limit.
- **Discovery follows the published spec.** The spec tracks a branch of
  `openai/openai-openapi` and may lag new endpoints. `openai_request` works for
  any endpoint whether or not it's listed.

## Development

The code is held to strict gates, configured in `pyproject.toml` and run
identically in CI (`.github/workflows/mcp.yml`):

- `ruff check`: every rule family on, McCabe complexity ≤ 5, ≤ 5 arguments, ≤ 6
  branches, ≤ 25 statements, ≤ 4 returns, ≤ 2 nested blocks
- `ruff format --check`
- `mypy --strict` over source and tests
- `pytest` with 100% line and branch coverage (no network: the OpenAI API is a
  mock transport, and HTTP and stdio are exercised with real servers)

```bash
make install
make check
```

Keep functions small enough to pass these gates without per-line ignores. An
ignore needs a comment saying why.

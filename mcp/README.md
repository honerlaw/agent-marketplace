# MCP servers

Custom [Model Context Protocol](https://modelcontextprotocol.io) servers, one per
directory. Each server is self-contained and can run locally over stdio or be
deployed as a container.

| Server | What it gives an LLM |
|---|---|
| [`openai-ads`](openai-ads/) | Manage ChatGPT ads through the OpenAI Ads (Advertiser) API via four generic, spec-driven tools |
| [`google-search-console`](google-search-console/) | Full access to the Google Search Console API via ten typed tools, one per operation (optional read-only mode) |
| [`reddit-ads`](reddit-ads/) | Full access to the Reddit Ads API (v3) via four generic, spec-driven tools, with OAuth token refresh |

## Contract for every server

Each `mcp/<name>/` directory has:

- `pyproject.toml`: a Python package (hatchling build backend) with a console
  script entry point, plus the **strict quality configuration** below
- `Dockerfile` (non-root, `/healthz` health check) and, where useful,
  `docker-compose.yml` and `.env.example`
- `ci.env`: dummy, non-secret environment values that let the image start, so
  CI's `/healthz` smoke test can run it without naming any server's variables
- `Makefile` with `make install` and `make check`
- `README.md`: tools, configuration, security model, limitations
- `tests/`: collected by CI automatically

These are the repo's first `pyproject.toml` and `Dockerfile` files. The rest of the
repo is scripts and skills without packaging.

### Strict quality gates

Every server copies the `[tool.ruff]`, `[tool.mypy]` and `[tool.pytest]`
configuration from [`openai-ads/pyproject.toml`](openai-ads/pyproject.toml):

- Ruff with `select = ["ALL"]`. Only rules that contradict another rule or the
  formatter are ignored.
- McCabe complexity ≤ 5, and pylint limits on arguments, branches, statements,
  returns and nesting
- `ruff format --check`
- `mypy --strict`
- 100% line **and** branch coverage

The point is to force simple, readable code. If a gate fails, simplify the code
instead of loosening the rule.

## CI

[`.github/workflows/mcp.yml`](../.github/workflows/mcp.yml) runs on every PR and
push to `main`. It discovers servers by globbing `mcp/*/pyproject.toml`, so a new
server needs no workflow edit. For each server it runs `make check` on Python 3.11
and 3.13, builds the Docker image, and starts it with `--env-file <server>/ci.env`
to check `/healthz`. A server with no collected tests, or no `ci.env`, fails the
job. Tests must never be able to go dark.

On a push to `main` only (never on a pull request), once `check` and `docker` have
both passed, a `publish` job builds each server's image for `linux/amd64` and
`linux/arm64` and pushes it to GitHub Container Registry as
`ghcr.io/<repository-owner>/<server-dir>-mcp`, for example
`ghcr.io/<owner>/openai-ads-mcp`. Each image is tagged with the full commit SHA and
`latest`, and the pushed digest is written to the job summary. The job signs in
with the workflow's `GITHUB_TOKEN`, so no secret is needed. A new package starts
private: make it public once, under the package's settings on GitHub, before
anyone can pull it without signing in.

## Adding a server

1. Copy `openai-ads/pyproject.toml`, `Makefile` and `Dockerfile` into `mcp/<name>/`
   and rename the package. Add a `ci.env` with dummy values that let it start.
   Pick the tool shape by API size. A large or fast-moving API gets generic, spec-driven
   tools like `openai-ads/`. A small, stable API gets one typed tool per operation like
   `google-search-console/`.
2. Write the server and its tests until `make check` passes.
3. Add a row to the table above.

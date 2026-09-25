# MCP servers

Custom [Model Context Protocol](https://modelcontextprotocol.io) servers, one per
directory. Each server is self-contained and can run locally over stdio or be
deployed as a container.

| Server | What it gives an LLM |
|---|---|
| [`openai`](openai/) | Full access to the OpenAI REST API via five generic, spec-driven tools |

## Contract for every server

Each `mcp/<name>/` directory has:

- `pyproject.toml`: a Python package (hatchling build backend) with a console
  script entry point, plus the **strict quality configuration** below
- `Dockerfile` (non-root, `/healthz` health check) and, where useful,
  `docker-compose.yml` and `.env.example`
- `Makefile` with `make install` and `make check`
- `README.md`: tools, configuration, security model, limitations
- `tests/`: collected by CI automatically

These are the repo's first `pyproject.toml` and `Dockerfile` files. The rest of the
repo is scripts and skills without packaging.

### Strict quality gates

Every server copies the `[tool.ruff]`, `[tool.mypy]` and `[tool.pytest]`
configuration from [`openai/pyproject.toml`](openai/pyproject.toml):

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
and 3.13 and builds the Docker image. A server with no collected tests fails the
job. Tests must never be able to go dark.

## Adding a server

1. Copy `openai/pyproject.toml`, `Makefile` and `Dockerfile` into `mcp/<name>/`
   and rename the package.
2. Write the server and its tests until `make check` passes.
3. Add a row to the table above.

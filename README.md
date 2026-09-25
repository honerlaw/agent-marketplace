# Agent Marketplace

A personal plugin marketplace for AI coding agents. Each plugin in `plugins/` is self-contained with its own skills and automation scripts.

📖 **[Documentation site](https://honerlaw.github.io/agent-marketplace/)** — the minerva guide, skill reference, and lifecycle walkthroughs.

## Install a Plugin

```bash
git clone https://github.com/honerlaw/agent-marketplace
cd agent-marketplace
./install.sh utils
```

Restart Claude Code — that's it. The installer handles Claude Code settings registration automatically (and Python dependencies / Playwright if the plugin ships any).

Minerva supports Claude Code and local Codex app, CLI, and IDE conversations from
the same 23 skills. Git, Python 3.11+, and a POSIX shell are required; PR workflows
also require authenticated `gh` and repository permissions.

```bash
./install.sh minerva --host both     # or --host claude / --host codex
./install.sh minerva --host both --dry-run
```

Codex installation uses `codex plugin marketplace add` and `codex plugin add`;
install the Codex CLI first. Start a new conversation after installation. The
default host remains Claude Code, and utils remains a Claude plugin.

To wire Codex manually from the cloned checkout:

```bash
codex plugin marketplace add /absolute/path/to/agent-marketplace
codex plugin add minerva@agent-marketplace
```

Then select `$minerva:using-minerva` in a new Codex conversation and run
`minerva:init --host both` in each consumer project.

See [Minerva compatibility and validation](plugins/minerva/COMPATIBILITY.md) for
host capabilities, resume behavior, and the regression checks.

## Update

```bash
git pull  # symlink keeps the plugin live immediately
./install.sh minerva --host both  # refresh registrations / Codex cache
```

## Plugins

<!-- Source of truth for each plugin's "Skills" cell: that plugin's `skills/` subdirectory. When you add a skill there, add its `plugin:skill-name` to the cell here too. -->

| Plugin | Skills | Description |
|--------|--------|-------------|
| utils | `humanizer` | Miscellaneous utility skills |
| minerva | `minerva:init` `minerva:explore` `minerva:propose` `minerva:replan` `minerva:grill-plan` `minerva:round-table` `minerva:work` `minerva:promote` `minerva:review` `minerva:ship` `minerva:cleanup` `minerva:propose-ship` `minerva:propose-ship-auto` `minerva:debug` `minerva:lint` `minerva:lint-fix` `minerva:synthesize` `minerva:migrate` `minerva:migrate-fix` `minerva:status` `minerva:using-minerva` | Durable record discipline for software work — proposal → work → replan → promote → review → ship, with a `.minerva/` persistence hierarchy of knowledge artifacts, proposals, and scratchpads. `propose-ship` conducts the whole lifecycle with user gates; `propose-ship-auto` runs it without human gates, giving each decision the tier it earns — the main model alone when provably small, one fresh-context reviewer by default, or a 3-agent Proponent/Skeptic/Arbiter consensus panel (extracted as `minerva:round-table`, usable standalone on any decision) when ambiguous or high-stakes — and moving up a tier instead of stopping. |

## MCP servers

[`mcp/`](mcp/) holds custom [MCP](https://modelcontextprotocol.io) servers, one self-contained
directory each, runnable locally over stdio or deployed as a container.

| Server | Description |
|--------|-------------|
| [`openai`](mcp/openai/) | Full access to the OpenAI REST API through five generic, spec-driven tools; stdio, HTTP (bearer-token auth) or Docker |
| [`google-search-console`](mcp/google-search-console/) | Full access to the Google Search Console API (search analytics, sites, sitemaps, URL inspection) through ten typed tools, with an optional read-only mode; stdio, HTTP (bearer-token auth) or Docker |

Every server is held to strict gates (Ruff with all rules, complexity ≤ 5, `mypy --strict`,
100% branch coverage), enforced by `.github/workflows/mcp.yml`. See [`mcp/README.md`](mcp/README.md).

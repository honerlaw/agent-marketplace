# lorestrom

minerva's durable records, kept in [Lorestrom](https://www.lorestrom.com): a shared workspace
of linked docs that several repositories, people and agents read through its MCP server.
There is no local file mode.

## This version (0.1.0): connect and publish

- `lorestrom:init` links a Git repository to a Lorestrom project (found by the repository's
  remote, or created in a workspace you pick) and caches the link in the clone, or commits it
  with `--shared`.
- It then offers a confirmed import of the repository's minerva knowledge entries as a
  **snapshot**. The repository's minerva files stay authoritative, and minerva keeps the
  lifecycle. Re-run `lorestrom:init` to import new entries; changed ones are reported, never
  overwritten.
- `lorestrom:using-lorestrom` explains the plugin and how an agent reads lore from Lorestrom.

The lifecycle skills (propose, work, review, promote, ship, cleanup and the orchestrators)
arrive in 0.2.0, when Lorestrom becomes authoritative for a linked repository. Sweeping other
clones' units and linting Lorestrom docs arrive in 0.3.0.

## Setup

1. Connect your organization's Lorestrom MCP server in your host and authenticate. In Claude
   Code: `claude mcp add --transport http --client-id <client id> --callback-port 53682 lorestrom https://www.lorestrom.com/mcp/o/<org id>`,
   then `/mcp`. The client id is in your organization's Lorestrom setup instructions.
2. Install this plugin: `./install.sh lorestrom --host both`.
3. In a repository, run `lorestrom:init`.

With minerva also installed, both plugins' skills are available. Until 0.2.0 use minerva's
skills for the lifecycle; lorestrom only links and publishes.

## Maintainer notes

- `scripts/knowledge_lint.py` and `scripts/knowledge_spans.py` are **byte-identical copies** of
  minerva's, so import parses entries exactly as minerva's catalog does.
  `tests/test_lorestrom_plugin.py` fails when they differ. A minerva change to either file
  copies it here in the same PR and bumps lorestrom's patch version.
- `scripts/plugin_guard.py` and `scripts/lorestrom_runtime.py` are adapted copies of minerva's.
- Lorestrom's tool names, node-key rule, statuses and limits are vendored in
  `scripts/lorestrom_backend.py` and the tests; re-check them when Lorestrom's MCP schemas
  change.

# lorestrom

minerva's durable records, kept in [Lorestrom](https://www.lorestrom.com): a shared workspace
of linked docs that several repositories, people and agents read through its MCP server.
There is no local file mode.

## This version (0.2.0): lifecycle and handover

- `lorestrom:init` links a Git repository to a Lorestrom project (found by the repository's
  remote, or created in a workspace you pick) and caches the link in the clone, or commits it
  with `--shared`. In a repository that used minerva it then hands over: a confirmed sync of
  the knowledge entries and reference docs, and separate offers, each kept by default, to
  replace the agent file's minerva routing section and to remove the imported files in one
  commit. It says how to disable minerva for the repository; it never edits host settings.
- **Lorestrom is authoritative** for a linked repository. `propose`, `work`, `replan`,
  `review`, `promote`, `ship`, `cleanup`, `status`, `grill-plan`, `explore`, `one-by-one` and
  `debug` keep work units, their records, knowledge entries and reference docs in Lorestrom.
  A unit's knowledge is held on its gate and becomes current when `cleanup` releases the gate
  on live merge evidence.
- Worktrees live under `.lorestrom/worktrees/`, checkpoints under
  `<git-common-dir>/lorestrom/runtime/`.

The orchestrators (`propose-ship`, `propose-ship-auto`) arrive in 0.3.0, and with them the
`--auto` modes the lifecycle skills already carry (inert until then). Sweeping other clones'
units and linting Lorestrom docs arrive in 0.4.0.

## Setup

1. Connect your organization's Lorestrom MCP server in your host and authenticate. In Claude
   Code: `claude mcp add --transport http --client-id <client id> --callback-port 53682 lorestrom https://www.lorestrom.com/mcp/o/<org id>`,
   then `/mcp`. The client id is in your organization's Lorestrom setup instructions.
2. Install this plugin: `./install.sh lorestrom --host both`.
3. In a repository, run `lorestrom:init`.

With minerva also installed, both plugins' skills are available. In a linked repository run
the lifecycle with lorestrom's skills, one by one until 0.3.0, and never minerva's
orchestrators: they would write records as `.minerva/` files that Lorestrom ignores. Disable
minerva for that repository in the host's plugin settings.

## Maintainer notes

- `scripts/knowledge_lint.py` and `scripts/knowledge_spans.py` are **byte-identical copies** of
  minerva's, so import parses entries exactly as minerva's catalog does.
  `tests/test_lorestrom_plugin.py` fails when they differ. A minerva change to either file
  copies it here in the same PR and bumps lorestrom's patch version.
- `scripts/work_status.py` is a byte-identical copy of minerva's phase parser, checked the same way.
- `scripts/plugin_guard.py` and `scripts/lorestrom_runtime.py` are adapted copies of minerva's.
- The 12 lifecycle and read-side skills were copied from minerva verbatim in one commit and
  adapted in later ones, so their diff against minerva's skills is the adaptation itself.
- Lorestrom's tool names, node-key rule, statuses and limits are vendored in
  `scripts/lorestrom_backend.py` and the tests; re-check them when Lorestrom's MCP schemas
  change.

# Claude Code and Codex compatibility

Version 0.1.0 packages one canonical `skills/` tree for Claude Code and local Codex app,
CLI and IDE conversations. It needs Git, Python 3.9+, a POSIX shell, and a Lorestrom MCP
server connected in the host for the organization being linked
(`https://www.lorestrom.com/mcp/o/<org id>`, authenticated by the user through the host).
There is no API key or script login: CI and scripts cannot reach Lorestrom.

## Capabilities

| Operation | Claude Code | Local Codex |
| --- | --- | --- |
| Load another skill | `Skill`, original arguments | Available loader, or read the installed skill and references in the current agent |
| Required user decision | Available question tool | Available question tool in the appropriate mode, or direct question |
| Lorestrom tools | `mcp__<server>__<tool>`, found by its tools | The host's MCP tools, found by their names |

Every skill requires the shared [runtime contract](skills/using-lorestrom/references/runtime.md),
its applicable [Claude](skills/using-lorestrom/references/claude.md) or
[Codex](skills/using-lorestrom/references/codex.md) adapter, and the
[storage contract](skills/using-lorestrom/references/storage.md).

## State

- The clone's link is untracked JSON under the Git common directory, `lorestrom/config.json`;
  `--shared` commits `.lorestrom/config.json` instead. Nothing the plugin keeps locally lives
  where minerva looks: its worktrees will be under `.lorestrom/worktrees/` and its checkpoints
  under `<git-common-dir>/lorestrom/runtime/` (0.2.0).
- Helper paths derive from the loaded package, resolve symlinks, and reject stale or
  incomplete script directories. `LORESTROM_SCRIPTS` is the explicit override.
- The helper always runs in Python's UTF-8 mode (`python3 -X utf8`, or it re-executes itself
  so), so entries are read as UTF-8 whatever the locale.

## Validation

`tests/test_lorestrom_backend.py` and `tests/test_lorestrom_plugin.py` run in CI with the
repository's other tests, and the repository's skill guards (names are data, mutating
commands, the runtime pointer, plugin-guard sites, the SKILL.md budget, installation) scan
this plugin too. There are no behaviour evals yet: they need a reachable Lorestrom test
server. Nothing in this version has been run against a live Lorestrom server by its tests.

# Proposal: lorestrom-connect-via-agents-page

**Date**: 2026-11-26
**Status**: Draft

## Goal

Wherever the lorestrom plugin tells a person to connect the Lorestrom MCP server, it sends them
to the Lorestrom web app's **Agents** page, `https://www.lorestrom.com/agents` (the
organization switcher's "Agents"), which shows the `claude mcp add` command already filled in
with that organization's endpoint and the OAuth client id, plus the endpoint alone for other
MCP clients. Today the plugin says to take the client id and org id from "your organization's
Lorestrom setup instructions", which do not exist for anyone but the operator.

The connect guidance covers the three situations a person can be in, in order:

1. **No Lorestrom account or organization:** sign up or sign in at `https://www.lorestrom.com`,
   then create an organization there or accept an invitation to one.
2. **No server connected:** open Agents with that organization chosen in the switcher, run the
   command it shows (Claude Code) or connect the address it shows (Codex or another client).
3. **Connected but not signed in, or the sign-in lapsed** (the server is listed but its tools
   are not, or a call is refused as unauthorized): in Claude Code run `/mcp`, choose the
   server and sign in with the same account used on the website.

Under a link, the server to connect is the link's organization: Agents with that organization
chosen. Lorestrom plugin 0.5.1.

## Why

The user asked whether using the plugin prompts them to (1) set up the MCP server and (2) have
an account and sign in. The plugin checks for a connected server and stops with "connect the
organization's Lorestrom MCP server", but the client id and org id it needs have no source a
member can reach, sign-in is mentioned only as "`/mcp` to authenticate", and nothing covers a
person with no account or organization. The Lorestrom web app now has an Agents page that shows
the filled command for the organization chosen in its switcher, so the plugin can point there.

## Approach

**A (recommended): one canonical connect block per host adapter; every other mention points
at it.**

- `skills/using-lorestrom/references/claude.md`, section "Lorestrom tools": replace the
  placeholder command and "setup instructions" sentence with the three-situation guidance
  above (account → Agents page command → `/mcp` sign-in). It describes the command in prose
  ("copy the `claude mcp add` command Agents shows") rather than showing it with
  placeholders. The order of checks: search the tool list for deferred `find_docs` first (the
  existing step); only when no Lorestrom tools exist, deferred or not, and the server is listed
  under `/mcp` does it suggest signing in there; a call refused as unauthorized means signing
  in again with `/mcp`. When Agents says Claude Code can't connect to this server yet, the
  person tells whoever runs their Lorestrom; the plugin cannot work around it.
- `skills/using-lorestrom/references/codex.md`, section "Lorestrom tools": the same three
  situations for Codex: the account, then the address shown on Agents, connected and signed
  in as Codex's MCP settings allow (OAuth). No Codex command is named.
- `skills/using-lorestrom/references/storage.md` ground rules: the remedy a stopped write
  names becomes "connect the organization's Lorestrom MCP server from the Agents page
  (`https://www.lorestrom.com/agents`), as the host adapter's Lorestrom tools section says, or
  run `lorestrom:init`".
- `skills/init/references/link.md` step 2: with no server, point at the Agents page for the
  organization instead of the endpoint placeholder and "setup instructions".
- `README.md` setup step 1 and `COMPATIBILITY.md`: the Agents page as the source of the
  command; the account step; COMPATIBILITY drops its `/mcp/o/<org id>` endpoint placeholder.
- Unchanged, because they already defer to the host adapter or to `lorestrom:init`:
  `init/SKILL.md` and `migrate/SKILL.md` ("say how to connect one, as the host adapter
  shows"), and the skills that stop with "no connected Lorestrom server" and name
  `lorestrom:init` (propose's `on-approval.md`, status, lint, the orchestrators).
- Version 0.5.1 in both manifests, the plugin README and COMPATIBILITY headings,
  `using-lorestrom/SKILL.md`, `runtime.md`'s "0.5.0 runs the lifecycle on Lorestrom" line
  (it states the current version), the top-level README table row,
  `tests/test_lorestrom_plugin.py`'s `VERSION` and `tests/test_install_plugin.py`'s installed
  version assertion. `tests/test_untrusted_names.py`'s "0.5.0:" comment dates a past change
  and stays.
- Tests (`tests/test_lorestrom_plugin.py`): no file under `plugins/lorestrom/` says "setup
  instructions" or holds the `<client id>` placeholder (`<org id>` stays where it names a
  link's org); both host adapters, storage.md's remedy, link.md and the
  README name `https://www.lorestrom.com/agents`; the Claude adapter names `/mcp` sign-in and
  the account step.
- minerva and every other plugin are unchanged. No reference to the Lorestrom app's source
  repository (it is private): only the public URL.

### Approaches considered

- **A — point at the Agents page from one canonical block per host** (above).
- **B — the plugin builds the command itself**, asking the person for their org id and
  reading a client id from plugin config. The client id is per deployment and not public in
  the plugin; asking for an org id is the same unanswerable question. Rejected.
- **C — README only.** The skills, where a stopped write tells the agent what to say, would
  keep the unanswerable text. Rejected.

## Success criteria

1. No file under `plugins/lorestrom/` contains "setup instructions" or `<client id>`; a test
   enforces it.
2. claude.md's Lorestrom tools section gives the account step, the Agents page and its
   command, and `/mcp` sign-in (including the listed-but-no-tools and unauthorized cases);
   codex.md gives the account step and the address on the Agents page; tests check each
   names `https://www.lorestrom.com/agents`.
3. storage.md's write-stop remedy and link.md's no-server step name the Agents page; tested.
4. The plugin README's setup and COMPATIBILITY name the Agents page and the account step.
5. Version 0.5.1 everywhere the plugin states its current version, including
   `tests/test_install_plugin.py`; `test_lorestrom_plugin.py` and `test_install_plugin.py`
   pass.
6. The repository's full test suite passes (`pytest`).
7. Before ship, `https://www.lorestrom.com/agents` no longer answers 404 (a 200, or a
   redirect to sign in, both count: the deploy that carries it has finished); checked by hand
   with `curl`, not in `pytest`.

## Open Questions

- The Agents page merged to the Lorestrom app's main branch today and its deploy was still
  running at propose time (the URL answered 404): criterion 7 holds ship until it is live.
- Whether production's `MCP_CLIENT_IDS` lists the Lorestrom MCP client id first is an operator
  step in the app's runbook; until it does, Agents says Claude Code can't connect and still
  shows the address. The plugin's guidance stays correct either way.

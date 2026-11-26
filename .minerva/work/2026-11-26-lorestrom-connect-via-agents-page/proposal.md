# Proposal: lorestrom-connect-via-agents-page

**Date**: 2026-11-26
**Status**: Shipped (2026-11-26)

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

**A, as built: one canonical connect block per host adapter; every other mention points at
it.** Lorestrom plugin 0.5.1.

- `skills/using-lorestrom/references/claude.md`, "Lorestrom tools": after the existing
  deferred-tool search, three ordered steps. (1) An account and an organization at
  `https://www.lorestrom.com` (create an account; create an organization or accept an
  invitation). (2) In the web app, choose the organization in the switcher (under a link, the
  link's organization), open **Agents** from the switcher's menu or go to
  `https://www.lorestrom.com/agents`, and run the `claude mcp add` command it shows, already
  filled in (described in prose, no placeholder). (3) `/mcp`, choose the server, sign in with
  the same account; the agent acts as that person with their role. Then: with no Lorestrom
  tools, deferred or not, a server `/mcp` lists as needing authentication means step 3 and
  none means steps 1–3; a call refused as unauthorized means step 3, then membership if
  refused again; "Claude Code can't connect to this server yet" on Agents means telling
  whoever runs that Lorestrom.
- `codex.md`, "Lorestrom tools": the account, then the address on Agents (organization chosen
  first), added as an MCP server and signed in with OAuth as Codex's MCP settings allow; an
  unauthorized call means signing in again, then checking membership. No Codex command named.
- `storage.md`'s write-stop remedy: connect from the Agents page, or sign in again after an
  unauthorized call, as the host adapter says, or run `lorestrom:init`. `init/references/link.md`
  step 2: say how to connect, as the adapter does, the command or address being on Agents.
- Plugin `README.md` Setup step 1 and a "Connecting (0.5.1)" bullet in "This version";
  `COMPATIBILITY.md` names the Agents page and the account sign-in and drops its
  `/mcp/o/<org id>` placeholder.
- Unchanged, because they already defer to the host adapter or to `lorestrom:init`:
  `init/SKILL.md` and `migrate/SKILL.md`, and the skills that stop with "no connected Lorestrom
  server" (propose's `on-approval.md`, status, lint, the orchestrators).
- Version 0.5.1 in both manifests, the plugin README and COMPATIBILITY, `using-lorestrom/SKILL.md`,
  `runtime.md`'s "runs the lifecycle" line, the top-level README row,
  `tests/test_lorestrom_plugin.py`'s `VERSION` and `tests/test_install_plugin.py`; the dated
  "0.5.0:" comment in `tests/test_untrusted_names.py` stays.
- Tests in `tests/test_lorestrom_plugin.py`: no `.md`/`.py`/`.json` file under
  `plugins/lorestrom/` says "setup instructions" or holds `<client id>`; the two adapters,
  storage.md, link.md, README and COMPATIBILITY name the Agents page; the Claude adapter
  covers the account, the command, `/mcp`, the unauthorized and can't-connect cases, with the
  deferred-tool search first; the Codex adapter covers the account, the page and OAuth.
- minerva and every other plugin are unchanged; only the public URL is named.

### Approaches considered

- **A — point at the Agents page from one canonical block per host** (chosen, above).
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
6. CI's suite passes: `python -m pytest tests/`, the skill and compatibility eval dry-runs and
   knowledge lint (the evals workflow).
7. Before ship, `https://www.lorestrom.com/agents` no longer answers 404 (a 200, or a
   redirect to sign in, both count: the deploy that carries it has finished); checked by hand
   with `curl`, not in `pytest`.

## Open Questions

- The Agents page merged to the Lorestrom app's main branch today and its deploy was still
  running at propose time (the URL answered 404): criterion 7 holds ship until it is live.
- Whether production's `MCP_CLIENT_IDS` lists the Lorestrom MCP client id first is an operator
  step in the app's runbook; until it does, Agents says Claude Code can't connect and still
  shows the address. The plugin's guidance stays correct either way.
- Whether Codex can complete OAuth against Lorestrom, which admits only pre-registered client
  ids, was not verified; codex.md hedges with "as Codex's MCP settings allow".

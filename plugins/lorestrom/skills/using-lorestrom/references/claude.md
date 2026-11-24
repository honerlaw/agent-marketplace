# Claude Code execution adapter

Read only in Claude Code. Apply the shared runtime contract and skill protocol.

## Skill loader and questions

Use the `Skill` tool with `skill: lorestrom:<name>` and the original arguments.
Do not shadow the loaded skill's behavior. Use `AskUserQuestion` for required
user decisions when available, otherwise ask directly and wait.

## Independent review

Use the `Agent` tool with fresh context, `subagent_type: general-purpose`, and
`run_in_background: false`. Always wait for results. Do not reuse an author or
previous reviewer for a fold-audit or an Adjudicator. Reviewer-tier agents
(`propose-ship-auto`'s Skeptic, fold-audit, Adjudicator and Verifier) use `model: sonnet`,
preserving minerva's cost policy; ordinary code review leaves `model` unpinned. For a wave of independent
decisions, issue all of its first-wave `Agent` calls in one message; calls in
one message already run concurrently, so a wave needs no new capability. If any
required capability is missing, stop with an actionable recovery report.

When an OPEN PR exists and `code-review:code-review` is installed, use that skill
for code quality. Without it, use an independent reviewer with the shared review
brief against the PR diff, retaining both the unit audit and code quality lenses and finding format.

## Watchers, schedules, and peers

For a tracked CI watcher, run `gh pr checks <pr> --watch --fail-fast` through
`Bash` with `run_in_background: true` when completion notifications are supported.
Retain the completion handle only in the live session. Otherwise observe the
process with the available shell tools while this session remains active.

If `ScheduleWakeup` supports re-entry, keep the existing long fallback at
`delaySeconds: 1800`, re-arming while CI is pending. Merge waits retain
`delaySeconds: 300`, capped at 12 and by the saved deadline. Pass the exact
resume prompt, including `--auto`, `--watch-iteration`, `--cleanup-only`, and
`--retry` when applicable. If no scheduler is available, save progress and
report pending with the exact manual resume prompt. Never promise automatic
resumption based solely on a detached process.

Use `ListAgents` / `SendMessage` for peer discovery only if they enumerate peer
sessions, the user authorized sending, and the existing filters pass. Never
confuse a subagent id with a separate interactive peer session.

## Lorestrom tools

A connected Lorestrom MCP server's tools appear as `mcp__<server>__<tool>`, where `<server>`
is whatever name the user gave it (for example `mcp__lorestrom__find_docs`). Find the server
by its tools, as the storage contract says, never by its name alone. If no such tools are
listed, they may be deferred: search the tool list for `find_docs` before deciding that no
server is connected. Connecting one is the user's step:
`claude mcp add --transport http --client-id <client id> --callback-port 53682 lorestrom https://www.lorestrom.com/mcp/o/<org id>`,
then `/mcp` to authenticate, with the client id from their organization's Lorestrom setup
instructions.

# Claude Code execution adapter

Read only in Claude Code. Apply the shared runtime contract and skill protocol.

## Skill loader and questions

Use the `Skill` tool with `skill: minerva:<name>` and the original arguments.
Do not shadow the loaded skill's behavior. Use `AskUserQuestion` for required
user decisions when available, otherwise ask directly and wait. A skill's
`allowed-tools` grants turn-local permissions; it does not remove other tools.
Read-only behavior comes from the shared contract, not this frontmatter.

## Independent review and panels

Use the `Agent` tool with fresh context, `subagent_type: general-purpose`, and
`run_in_background: false`. Always wait for results. Do not reuse an author or
previous reviewer for a fold-audit. Round-table panelists and reviewer-tier agents
(Skeptic, fold-audit, Verifier) use `model: sonnet`, preserving Claude's existing cost policy; ordinary code
review leaves `model` unpinned. Proponent and Skeptic calls run in parallel;
Arbiter runs after both outputs are available. If any required capability is
missing, stop with an actionable recovery report.

When an OPEN PR exists and `code-review:code-review` is installed, use that skill
for code quality. Without it, use an independent reviewer with the shared review
brief against the PR diff, retaining both Minerva lenses and finding format.

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

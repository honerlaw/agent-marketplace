# Codex execution adapter

Read only in local Codex app, CLI or IDE sessions. Apply the shared runtime
contract and skill protocol. Coding workflows require Git, Python 3.11+, and a
POSIX shell; GitHub workflows also need authenticated `gh` and permissions.

## Skill loader and questions

Use the available skill-loading capability if provided. Otherwise read the
named `skills/<name>/SKILL.md` from this loaded plugin root, then its required
references, and execute its protocol in the current agent with the original
arguments. Preserve drafts and the return phase; do not spawn an agent just to
load a skill. User-facing examples use `$minerva:<name>`; use the actual qualified
name exposed by the skill selector if a host renders the namespace differently.

Use an available question tool when appropriate to the current collaboration
mode, otherwise ask the required question directly and wait. Respect prior user
authorization and sandbox approvals. A fallback answer is not permission.

## Independent review and panels

Use the actual available subagent API (`collaboration.spawn_agent` with
`fork_turns: none`, or a native `spawn_agent` exposing its fresh-context option).
Explicitly request delegation in the skill brief. Pass only the specified
ARTIFACT, CONTEXT, and role brief. Leave model and reasoning effort unpinned so
the reviewer inherits the session settings; never pass a Claude model alias.
If fresh-context delegation is unavailable, stop this workflow with recovery
instructions. Do not send the full authoring history to an independent reviewer.

Wait for results through the available wait/status tools. Parallel Proponent
and Skeptic agents must both finish before Arbiter starts. Balanced fold-audit
uses a new agent and excludes the author's arbitration reasoning. Close or
release completed agents where supported. No background handle is a verdict.

Use a structured independent code reviewer for local and PR diffs when the
optional external review skill is absent. Fetch OPEN PR diffs through `gh` and
keep the same severity + file:line + description format and both Minerva lenses.

## Watchers, schedules, and peers

Start `gh pr checks <pr> --watch --fail-fast` through the available shell execution
tool. If it returns a process/session id, use its polling tool (for example
`write_stdin`) to observe completion while the agent remains active. Keep each
blocking wait at or below 60 seconds and provide progress updates. Requery check
buckets after completion; a failed command is not proof that checks are green.

Use a scheduled resume capability only if the current host exposes one and it
actually supports re-entry. Otherwise checkpoint and provide the exact resume
prompt before ending the turn. Ending a Codex turn does not arrange a future
turn merely because a watcher process exists. Merge and reconciliation waits
follow the same explicit fallback and retain all counters and deadlines.

Codex child-agent listing covers this task's agents, not a fleet of unrelated
interactive sessions. Skip peer-session detection unless a separate authorized
integration supplies genuine peer discovery/messaging. Preserve local-unit,
branch and PR collision evidence regardless of peer capability.

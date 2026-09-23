# Shared runtime contract

Read this before executing any Minerva skill. Identify the host from the actual
available tools, then read `skills/using-minerva/references/claude.md` or
`skills/using-minerva/references/codex.md`, relative to the **loaded plugin root**.
Do not load both adapters. User instructions, existing authorization, workspace
permissions and project rules take precedence over a skill's defaults.

## Installed paths and helpers

The loaded `skills/<name>/SKILL.md` path identifies the plugin root: ascend from
the skill directory through `skills/` to its parent. Resolve symlinks. Never
search a host cache or use a consumer project's `scripts/` as a fallback.
`skills/<name>/references/<file>.md` pointers are relative to this plugin root;
bare `references/<file>.md` pointers belong to their named owning skill.

For **each** shell invocation using a documented helper snippet, supply
`MINERVA_PLUGIN_ROOT` and `MINERVA_SKILL_FILE` as the absolute installed root and
the absolute current SKILL.md path. Shell-quote these values; do not assume
variables or a `cd` survive between tool calls. For fragments that use variables
from an earlier step, repeat that step's initialization in the same new shell
call or pass its values explicitly as quoted arguments. The `resolve` operation validates
the script directory and stale-code guard. `MINERVA_SCRIPTS` is an explicit
override; it must contain all shipped modules. Import paths and corpus paths
must be passed as Python arguments, never interpolated into Python source.

Retain the distinction between current working-tree corpus paths and primary
checkout paths reaching sibling worktrees. Address active worktrees by full
path and use `git -C`; never switch the session into a host-managed worktree.

## Shared operations

- **Skill loader:** load the named skill's instructions using the host adapter,
  pass its arguments verbatim, follow its protocol and return to the caller.
  Loading a skill does not create a new agent. Preserve drafts in conversation.
- **User question:** use the host's available interaction mechanism. Resolve
  discoverable facts first. Honor prior authorization; for a required decision,
  wait for the answer before performing dependent work. No answer is not approval.
- **Independent reviewer operation:** dispatch a fresh-context agent and **wait for results**, with only
  the specified brief and artifacts before arbitration.
  The panel operation runs Proponent/Skeptic in parallel, waits for results, then
  sends their outputs to Arbiter and waits again. Release completed agents.
  If delegation is unavailable, stop this workflow with recovery instructions;
  never replace independent review or consensus with the author's self-review.
- **Tracked watcher operation:** observe the completion of a shell process while
  the current session is active. A process handle is not durable progress and
  does not imply automatic re-entry after the session ends.
- **Scheduled resume operation:** use a scheduler only if it exists and actually
  supports re-entry. Carry caller and retry flags. Without one, checkpoint and
  report **pending** with an exact resume prompt; never claim a wake is scheduled.

Read-only skills (`status`, `lint`, `migrate`, `explore`) never edit files, write
checkpoints, advance the lifecycle, or run repair skills. `allowed-tools` is
Claude permission metadata, not a portable read-only restriction. A read-only
report may name a mutating command for the user without executing it.

Peer-session discovery is optional. A child-agent list is not a peer fleet.
Outbound peer messages require the user's authorization, correct project and
liveness filtering, and the cross-session information-only contract. Unavailable
or unauthorized peer discovery does not block intake.

## Durable lifecycle checkpoints

Read this section when shipping, waiting for merge, or reconciling knowledge.
Run `python3 "$PLUGIN_SCRIPTS/minerva_runtime.py" read --unit <slug>` from the
unit's working tree (or pass its absolute `--cwd`). Missing state returns null
without writes. Invalid/version-mismatched state stops automatic continuation:
report the error and recover from Git/GitHub with the user, never reset silently.

State lives under the Git common directory at `minerva/runtime/<unit>/run.json`.
It survives worktree removal and stays out of proposals, scratchpads and commits.
It records progress, not new permission. Existing flags still determine mode.
Validate branch/PR identity against live Git/GitHub evidence on every resume;
an unrelated branch or changed caller stops automatic continuation. The
retired `propose-ship-quick` / `propose-ship-balanced` callers are the same
caller as `propose-ship-auto`; the helper canonicalizes them.

Use `write --unit <slug>` with JSON supplied through stdin. For the first write
include `revision: 0`, `branch`, `caller` (null or the orchestrator's name), and
`phase` (`ship`, `cleanup`, `reconciliation`, `done`). Include the current
`fix_iteration`, `cleanup_retry`, `escalations`, `decisions`, `reviewers`, `pr`
number or null, `cleanup_deadline` or null, and `status` (`pending`, `blocked`,
`completed`). Subsequent writes use the last read revision and may update only
changed fields. Identity/version fields are generated by the helper. Counters
cannot decrease and the original branch, work PR, caller, and deadline cannot change.
Reconciliation retains the work PR identity; discover its separate PR from the
existing fixed reconciliation branch rather than replacing the work PR in state.

Checkpoint before yielding and after completed phase transitions. Copy counters
already incurred during intake into the initial checkpoint. Save **each fix
attempt before starting it**, not just after a successful push. Save cleanup
retry/deadline before waiting: first merge wait establishes an absolute deadline
of now + 3600 seconds; each retry retains it, and either 12 retries or the
deadline exhausts the budget. Reconciliation waiting has no merge-retry budget;
checkpoint pending stems through the existing on-disk corpus and reread them on
resume, never assume the competing reconciliation PR did the entire job.

`read --unit <slug> --host claude|codex` renders a host-correct resume prompt.
Copy all applicable flags and the caller. A standalone cleanup prompt omits
`--yes`; preserve it only when explicitly supplied/authorized in the current
invocation. The same helper counters govern scheduled and manual resumes.

For legacy runs, reconstruct Git/PR progress and seed counters from explicit
`--watch-iteration` / `--retry` and existing decision logs. Unknown prior budget
usage requires user recovery rather than pretending zero. For bare shipping,
use `bare-` plus the SHA-256 of the branch name as the checkpoint key and give
the user the current branch and bare ship prompt (do not treat that key as a
work unit). Bare shipping can mark done after its PR is confirmed merged and
repository knowledge signals show no pending reconciliation; no unit teardown
is needed. A pending bare run resumes on its recorded branch.

Do not clear progress while anything is pending. After live evidence confirms
completion, write `phase: done, status: completed`. Explicit `clear --unit
<slug> --revision <N>` can then remove a completed checkpoint. Starting a genuinely
independent shipping run requires a completed prior checkpoint, clearing it
explicitly and verifying the new branch/PR; it never resets an unfinished run.
For the next declared phase of the same orchestrator run, use `write --start-phase`
with the completed checkpoint revision and newly verified phase branch. This
resets only that phase's fix/merge-wait budgets and PR identity; aggregate escalation,
decision, and reviewer counters plus the original caller remain. Never clear
aggregate governance counters between phases. Completed reads render no resume prompt.
Repeated signals must reuse existing PRs, recheck merge/cleanup/reconciliation,
and avoid running a second watcher or handoff. Checkpoint revision locking
protects checkpoint writes, not the goal or remote actions: it is not a fleet lock.

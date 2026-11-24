---
name: status
description: Prints the current overall status of a Lorestrom-linked project's workstream as markdown tables — every unit's lifecycle stage and gate, its age and who opened it (other clones' and people's units included), phase progress, branch/PR state and the next lifecycle step to run, plus knowledge health and the deferred backlog. Read-only; mutates nothing. Use when the user asks where things stand, what's in flight, what to do next, what still needs shipping or cleaning up, or for a status check / summary / dashboard / overview of the work; when an agent resumes a project and needs to orient before picking up work ("pick up where we left off", "what were we doing"); or when they invoke `lorestrom:status`.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

## Runtime

Read `skills/using-lorestrom/references/runtime.md` before executing; follow its host adapter.

Answer **"where does everything stand, and what should I do next?"** in one screen.
`lorestrom:status` aggregates the records that already exist — every work unit's doc and gate
in Lorestrom, its phase topology, the project's knowledge, the deferred backlog — and renders
them as three markdown tables.

> **Read-only contract.** This skill must not modify any file or Lorestrom doc, and writes no
> checkpoint. Its `allowed-tools` is host metadata; the read-only protocol applies regardless
> of available tools. Every call below is a read: it never writes back a refreshed
> `minerva:state`, never releases a gate, and never advances the lifecycle. The **Next step**
> column *names* the skill to run next and stops there — running it is the user's call.

## The failure this skill must not have

Under-reporting. A missing column is visible; a workstream that renders as "nothing in
flight" looks exactly like a tidy project, and the reader's next action is to start work
that already exists. Every resolution rule below is chosen for that failure direction.

## Step 1 — Resolve the link and the primary checkout

Run `storage:project.discover` as a read-only skill. With no link, no connected server or no
project, say so in one line, render only the local facts (worktrees and branches under
`.lorestrom/worktrees/`, from the runtime's `units`) and stop: no unit table is better than a
falsely clean one.

```bash
WORK_ROOT="$(cd "$(dirname "$(git rev-parse --git-common-dir)")" && pwd)"
```

**`WORK_ROOT` is the PRIMARY checkout, and deliberately not `git rev-parse
--show-toplevel`.** Inside a linked worktree `--show-toplevel` returns *the worktree*, which
holds no `.lorestrom/worktrees/` directory, so a status run from a worktree — exactly the
"resuming agent" case this skill exists for — would report every sibling's worktree as
absent. Bare `dirname "$(git rev-parse --git-common-dir)"` is relative in the common case;
the `cd … && pwd` wrapper makes it absolute.

## Step 2 — Collect the units

`storage:unit.list`: only ids `unit-ids` printed are used, and its `refused` count is reported.
It lists every unit of this project in Lorestrom, whoever opened it and whichever clone it was
worked in. Call `whoami` once, and `get_gate` each unit's doc; step 3 pipes them to
`unit-state` once it has the unit's phase count. **The gate is the authority**: a stale `minerva:state` property is shown as
stale, never trusted, and never rewritten here. `stale` (no recorded head after 14 days) is
shown, never acted on. Note each unit's `.lorestrom/worktrees/<date-slug>/` presence: a unit
with none here was worked on elsewhere, and that is not a cleanup signal.

## Step 3 — Phases and merges

Fetch first — a stale ref reports a merged phase as unmerged:

```bash
git -C "$WORK_ROOT" fetch --quiet origin 2>/dev/null
gh pr list --state all --limit 200 --json number,state,headRefName 2>/dev/null
```

For each open unit, run the helper's `phases --unit <date-slug>` on its proposal record, the
head names of MERGED PRs and the unit doc's recorded heads and base (`storage:unit.read`). Join PRs on each phase's `branch`, never by
string equality with the slug: a phased unit ships phases 2+ on `<date-slug>-phase-N`. The
unit doc's `minerva:pr_<n>` is the PR ship recorded; prefer it when it is a number.

Then, for each unit, pipe its properties, the gate's `state`, `openedAt` and `openedByUserId`,
your user id and its phase count (`phases`' `total`, 1 when unphased) to `unit-state`:
`promoted`, `shipped`, `state`, `age_days`, `stale` and `mine` (`storage:unit.list`).

If `gh` is unavailable, unauthenticated, or the repo has no GitHub remote — run the probe in
`lorestrom:promote`'s "Step 1 — Capability probe" exactly as written there, then **skip the PR
column silently** and render `—`. Never stall or apologise for an absent tracker.

## Step 4 — Knowledge

`storage:knowledge.list` for this project's entries: counts by `minerva:type`, distinct
themes, unthemed entries, pending entries (status `draft` with a `minerva:context`, by unit)
and incomplete imports. Reference docs: a count from `storage:reference.read`. Read no body.

## Step 5 — Render the tables

**Read [references/tables.md](references/tables.md)** for the three table shapes, the
column list, and the full **Next step** mapping. Two rules from it are load-bearing enough
to state here:

- **A worktree on an incomplete phased unit is not a cleanup signal.** That unit keeps its
  worktree *by design* — `lorestrom:cleanup`'s "Teardown waits" — and its gate waits for the
  final phase. Its next step is the next phase, not cleanup.
- **List only the unfinished units.** Finished ones (gate released or abandoned, no worktree)
  are counted in the rollup. A 60-row table is not a status check.

## Out of scope

- **Any mutation**, of files, Lorestrom docs, gates or checkpoints, and any lifecycle
  advancement. This skill names the next step and never invokes `lorestrom:work` / `ship` /
  `promote` / `cleanup`. The action it *names* is the one way it can still cause damage — see
  the phase-first ordering in the Next step mapping.
- **Re-deriving lifecycle state.** `unit-state` and `phases` own it. A status surface that
  restates either is a copy that drifts.
- **Linting the knowledge.** That is `lorestrom:lint`; this table counts, it does not judge.
- **Updating a stale checkout.** The rollup prints HEAD beside `origin/<default>` so a stale
  tree is *visible* — but this skill never pulls.

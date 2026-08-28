---
name: status
description: Prints the current overall status of a project's minerva workstream as markdown tables — every unit's lifecycle stage, phase progress, branch/PR state and the next lifecycle step to run, plus knowledge-wiki health and the deferred backlog. Read-only; mutates nothing. Use when the user asks where things stand, what's in flight, what to do next, what still needs shipping or cleaning up, or for a status check / summary / dashboard / overview of the work; when an agent resumes a project and needs to orient before picking up work ("pick up where we left off", "what were we doing"); or when they invoke `minerva:status`.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

Answer **"where does everything stand, and what should I do next?"** in one screen.
`minerva:status` aggregates the records that already exist — every work unit's declared
state, its phase topology, the knowledge wiki's health, the deferred backlog — and renders
them as three markdown tables.

> **Read-only contract.** This skill must not modify any file. Its `allowed-tools` omits
> `Edit` / `Write` / `MultiEdit` by design, and every command below is a read. It reports;
> it never advances the lifecycle. The **Next step** column *names* the skill to run next
> and stops there — running it is the user's call.

## The failure this skill must not have

Under-reporting. A missing column is visible; a workstream that renders as "nothing in
flight" looks exactly like a tidy project, and the reader's next action is to start work
that already exists. Every resolution rule below is chosen for that failure direction.

## Step 1 — Resolve the two roots

They answer different questions and are resolved differently. Do not collapse them.

```bash
WORK_ROOT="$(cd "$(dirname "$(git rev-parse --git-common-dir)")" && pwd)"
PLUGIN_SCRIPTS=$(find -L "${HOME}/.claude/plugins/minerva" "${HOME}/.claude/plugins/cache/agent-marketplace/minerva" -maxdepth 2 -type d -name "scripts" 2>/dev/null | head -1)
```

**`WORK_ROOT` is the PRIMARY checkout, and deliberately not `git rev-parse
--show-toplevel`.** Every other minerva skill anchors on `--show-toplevel`, correctly:
their target is the worktree-local `.minerva/knowledge/`, so per-branch semantics are the
point. They are wrong for this skill. Inside a linked worktree `--show-toplevel` returns
*the worktree*, which contains no `.minerva/worktrees/` directory at all — so a status
walk invoked from a worktree, which is where `minerva:work` sessions live and exactly the
"resuming agent" case this skill exists for, would report every sibling unit as absent.

The `cd … && pwd` wrapper is not decoration. Bare `dirname "$(git rev-parse
--git-common-dir)"` returns `.` from the primary checkout and a relative path from any
subdirectory; it is absolute only from inside a linked worktree — i.e. it is wrong in the
common case, silently, and in the direction that produces a falsely-clean table. The rule
and its three-position test are
`2026-08-28-constraint-worktree-reaching-paths-anchor-to-the-primary-checkout`; this skill
is one of its cases, not a second statement of it.

`PLUGIN_SCRIPTS` follows the plugin-cache-first rule in
`2026-06-03-constraint-skill-wraps-script-via-importable-api` — `find -L` included, because
the local install path is a symlink and `find` without it stops at the symlink.

## Step 2 — Collect the merged branches

`workstream_status` is a pure reader: it takes the merged set as an argument rather than
shelling out, the same contract `work_status.phase_progress` already has. Fetch first — a
stale ref reports a merged phase as unmerged.

```bash
git -C "$WORK_ROOT" fetch --quiet origin 2>/dev/null
MERGED="$(gh pr list --state merged --limit 200 --json headRefName -q '.[].headRefName' 2>/dev/null)"
[ -z "$MERGED" ] && MERGED="$(git -C "$WORK_ROOT" branch --merged "$(git -C "$WORK_ROOT" symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|origin/||' || echo main)" --format='%(refname:short)')"
```

**Merged-PR first, `git branch --merged` only as a fallback** — the same order and the
same reason as `minerva:cleanup`'s "Merge detection": a squash-merged branch is not an
ancestor of the default branch, so `git branch --merged` cannot see it. Do not union the
two sources: `git branch --merged` also lists a *freshly created* branch that has no
commits yet, which would report an unstarted phase as shipped.

## Step 3 — Run the aggregator

```bash
python3 -c "import sys, json; sys.path.insert(0, '${PLUGIN_SCRIPTS:-$WORK_ROOT/scripts}'); \
from workstream_status import workstream_status; \
print(json.dumps(workstream_status('$WORK_ROOT', '''$MERGED'''.split()), indent=2))"
```

Returns `{units, counts, knowledge}`. Per unit: `slug`, the `work_status.unit_state()`
keys (`promoted` / `status` / `in_flight` / …), `worktree_present`, `stage`, `phases` and
`progress`. Every lifecycle predicate is **imported** from `work_status`, never restated —
the in-flight rule once had four prose copies, and the promote marker it reads grew eight
spellings while a one-string check misread 16 of 51 units.

`stage` is one of `draft` → `in-progress` → `promoted` → `shipped`, derived from the
filesystem alone, so it is available even with no `gh` and no network.

## Step 4 — Join the branch and PR state

```bash
gh pr list --state all --limit 200 --json number,state,headRefName 2>/dev/null
git -C "$WORK_ROOT" branch --list
```

Both are optional. If `gh` is unavailable, unauthenticated, or the repo has no GitHub
remote — run the probe in `minerva:promote`'s "Step 1 — Capability probe" exactly as
written there, then **skip the PR column silently** and render `—`. Never stall or
apologise for an absent tracker; the stage-only table is coarser and still correct.

**Resolve a unit's branch names through `phase_branch()`, never by string equality with
the slug.** A phased unit ships one PR per phase: phase 1 on the bare `<date-slug>`,
phases 2+ on `<date-slug>-phase-N`. The script already returns each phase's branch in
`phases[].branch`; join on those. `minerva:cleanup`'s "Why this step has to exist at all"
is explicit that exact-match on `<date-slug>` can never match a `-phase-N` branch.

## Step 5 — Render the tables

**Read [references/tables.md](references/tables.md)** for the three table shapes, the
column list, and the full **Next step** mapping. Two rules from it are load-bearing enough
to state here:

- **`worktree_present` on an incomplete phased unit is not a cleanup signal.** That unit
  keeps its worktree *by design* — `minerva:cleanup`'s "Teardown waits" defers teardown
  until the final phase, because removing the worktree between phases destroys the
  workspace the remaining phases are cut in. Its next step is the next phase, not cleanup.
- **List only the unfinished units.** Finished ones are counted in the rollup. A 60-row
  table is not a status check.

## Out of scope

- **Any file mutation**, and any lifecycle advancement. This skill is read-only: it names
  the next step, does not run it, and never invokes `minerva:work` / `ship` / `promote` /
  `cleanup`. The action it *names* is the one way it can still cause damage — see the
  phase-first ordering in the Next step mapping.
- **Re-deriving lifecycle state.** `unit_state`, `read_phases`, `phase_progress` and
  `phase_branch` are imported from `work_status`; `synthesis_status` and `lint_knowledge`
  own wiki health. A status surface that restates any of them is a copy that drifts.
- **Judging wiki health.** The counts come from `minerva:lint` / `minerva:synthesize`'s
  own signals; interpreting them is those skills' job, and this table only points at them.
- **Reconciling a stale checkout.** The walk reads files, so it reports whatever the
  primary checkout is on. Step 2 fetches and the rollup prints HEAD beside
  `origin/<default>` so a stale tree is *visible* — but this skill never pulls.

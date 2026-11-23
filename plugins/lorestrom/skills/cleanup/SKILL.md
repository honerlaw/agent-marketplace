---
name: cleanup
description: In a repository linked to Lorestrom, releases a merged work unit's gate so its pending knowledge becomes current, then removes `.lorestrom/worktrees/YYYY-MM-DD-slug/` directories whose branches have been merged into the default branch and prunes the corresponding local branches. Acts only on live merge evidence; abandons a unit whose PR closed unmerged. Idempotent; never force-removes unmerged work, never commits, and opens no PR. Use after a PR merges, when the user asks to remove merged worktrees, prune stale lorestrom branches, or generally tidy up after shipped work, or when they invoke `lorestrom:cleanup`.
---

## Runtime

Read `skills/using-lorestrom/references/runtime.md` before executing; follow its host adapter.

Tidy up after shipped work — release each merged unit's Lorestrom gate, then remove `.lorestrom/worktrees/<date-slug>/` directories whose branches have been merged into the default branch, and prune the corresponding local branches. Idempotent: safe to run on a clean tree (reports zero items removed).

## Usage

- `lorestrom:cleanup` — sweep all merged worktrees + branches in the current repo
- `lorestrom:cleanup 005-add-payments` — clean up only the named work unit (a checked id)
- `lorestrom:cleanup 005-add-payments --merged <sha>` — name the merge commit when no PR shows it
- `lorestrom:cleanup 005-add-payments --abandon` — abandon the unit: discard its held writes
- `lorestrom:cleanup --dry-run` — list what would be released and removed, changing nothing

## Target resolution

Same pattern used by `lorestrom:work`, `lorestrom:replan`, `lorestrom:promote`, `lorestrom:review`, `lorestrom:ship`. **Keep all six blocks in sync if you edit one.** For `lorestrom:cleanup` specifically, the default mode (no argument) is "all merged worktrees" rather than a single target — but resolution rules apply when an argument is passed.

1. **Explicit argument** (a checked id: one `storage:unit.list` or the runtime's `units` printed) → operate on just that work unit: its Lorestrom unit and `.lorestrom/worktrees/<date-slug>/`. Required: its branch merged into default (see Merge detection), except with `--abandon` or `--merged`.
2. **No argument** → scan all `.lorestrom/worktrees/*/` directories and this project's units with open gates (`storage:unit.list`), and check each branch's merge state. Use only checked ids (`units`, runtime contract "Names are data"): skip any other directory and report how many were refused. Match **both** id forms — `YYYY-MM-DD-<slug>` and `NNN-<slug>`; a digit-anchored glob would silently skip date-named worktrees.
3. **Non-git repo** → report "not a git repo, nothing to clean up" and stop.

## Checkpoint entry

Unless `--dry-run`, read the resolved unit's runtime checkpoint before removal.
Revalidate live merge evidence and explicit mode arguments — a checkpoint is not
authorization for `--yes`. Save phase `cleanup` before waiting, and mark this shipping
pass `done` after safe teardown (or a phased unit's teardown deferral — it can finish this
pass while keeping its worktree for the next phase). If blocked, retain pending/blocked
state and provide an exact resume prompt. For multi-unit cleanup, maintain a checkpoint
per unit. Dry-run writes none.

## Pre-flight checks

Bail with a clear message on any failure:

1. **Git repo.** `git rev-parse --is-inside-work-tree` returns true.
2. **`gh` CLI available** (optional but preferred). Falls back to local-only merge detection if `gh` is missing or unauthenticated.
3. **Not currently inside a worktree being cleaned.** If invoked from inside `.lorestrom/worktrees/<date-slug>/`, that worktree cannot be removed while it's the current working tree. Report and ask the user to `cd` out (back to the main repo root) and re-run. Cleanup always operates from the parent repo — its job is to remove worktrees, so it must never be running inside one. (No lifecycle skill makes a worktree its working directory: the others address worktrees by `.lorestrom/worktrees/<date-slug>/`-prefixed paths, while cleanup removes them outright.)

## Default-branch detection

Use the runtime contract's default-branch snippet ("Names are data") in each shell call that
runs a merge check, and refer to the result only as `"${BASE:?}"`.

## Merge detection per worktree

A worktree is safe to remove only once its branch has merged into the default branch. The full
detection protocol — including the squash-merge case a plain `git branch --merged` misses —
lives in `references/merge-detection.md`. **Read it before removing anything.**
On a phased unit teardown waits for the final phase — **read `references/phased-units.md`** before
tearing anything down. The rule itself is stated once, in `references/merge-detection.md`.

## Release the unit's gate

Before removing a merged unit's worktree, decide its gate on live evidence with the helper's
`reconcile` and release, confirm, abandon or wait as it answers. **Read `references/release.md`
before releasing or abandoning anything.** A STALE reference replace is reported with its unit
and doc and never re-applied automatically. A unit whose gate waits keeps its worktree.

## Orchestrated mode (`--yes`)

**Mode argument**: `--yes`

With an explicit single-unit argument `--yes` satisfies the confirmation gate below — how the
autonomous orchestrators (0.3.0) invoke cleanup. Act on the argument, not on who you think is calling.
`--yes` never confirms a merge `reconcile` could not prove (`storage:unit.confirm`), and never abandons.

## Confirmation gate

Before removing anything, present the list:

```
Will release:
  005-add-payments   (merged; holds reference replace: Topology)
Will abandon:
  008-dead-end       (PR closed unmerged — needs a yes naming this unit)
Will remove:
  .lorestrom/worktrees/005-add-payments/   (branch 005-add-payments, merged via PR #42 on 2026-05-12)
  .lorestrom/worktrees/006-add-ship-skill/ (branch 006-add-ship-skill, merged via PR #45 on 2026-05-15)
Will skip:
  .lorestrom/worktrees/007-add-cleanup/    (branch 007-add-cleanup, NOT merged — unmerged work, leaving alone)
```

Ask:
> "Release these units' gates, remove these worktrees and prune the matching local branches? [y/N]"

Default is no — destructive operations require explicit yes. The user can also batch ("yes, all" / "just the first two" / "skip 006"). A sweep abandons a unit only on a yes naming it; an explicit `<unit> --abandon` is that yes.

Skip this gate when `--dry-run` is set (nothing destructive happens) or when the user invokes with an explicit single-unit argument **and** says `--yes` (e.g. `lorestrom:cleanup 005-add-payments --yes`).

## Removal

Conservative by design — each step prefers to refuse and surface rather than force, because
cleanup's failure mode is destroying unmerged work. **Read [references/removal.md](references/removal.md) before removing anything**; it carries the worktree removal, the `-d`/`-D` branch-delete rule and its squash-merge rationale, the phased-unit branch prune, and the metadata prune.

## Final report

```
Gates released:        N (<list>)   waiting: N (<list with reason>)   abandoned: N
Held writes failed:    N (<unit — doc — code>, STALE reference replaces named)
Worktrees removed:     N (<list>)
Branches pruned:       N (<list>)
Skipped (unmerged):    N (<list with branch names>)
Skipped (uncommitted): N (<list — needs manual review>)
Remaining worktrees:   N (<list>)
```

If any worktrees were skipped due to uncommitted changes, recommend the user inspect each (`cd .lorestrom/worktrees/<slug>; git status`) and decide whether the changes are valuable.

## Knowledge: released, never rewritten

Cleanup writes no knowledge entry and opens no PR. Its one knowledge effect is the gate
release, which makes the unit's pending entries current and applies its held edges. Earlier
minerva versions opened a `minerva/reconcile` PR here; do not recreate one.

## Idempotency

Cleanup rederives candidates from live Git/PR evidence and retains only untracked
runtime progress. Releasing a released gate again is success (`release-outcome`), and an
interrupted abandon finishes when called again. Re-running on a fresh tree finds zero candidates and reports zero removed. Running mid-CI for a branch with an auto-merge pending will correctly skip that worktree (PR is `OPEN`, not `MERGED`).

If a user manually removed a worktree directory without running `git worktree remove`, the next `lorestrom:cleanup` call will see stale worktree metadata; `git worktree prune` at the end of the run handles this.

## Out of scope

- **Deleting a unit's records.** They stay in Lorestrom; the scratchpad was archived by promote.
- **Re-applying a STALE reference replace.** Reported, never retried automatically.
- **Force-removing unmerged work.** Always requires explicit user override; cleanup is conservative by default.
- **Pruning remote branches.** GitHub usually auto-deletes the source branch after merge if the repo is configured for it. Local prune handles the local side; remote prune is `git fetch --prune` and not part of this skill.

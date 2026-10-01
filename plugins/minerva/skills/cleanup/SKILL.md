---
name: cleanup
description: Removes `.minerva/worktrees/YYYY-MM-DD-slug/` directories whose branches have been merged into the default branch, prunes the corresponding local branches. Idempotent; never force-removes unmerged work, never commits, and opens no PR — the knowledge wiki needs no post-merge pass because its catalog, backlinks and supersession are derived on read. Use after a PR merges, when the user asks to remove merged worktrees, prune stale minerva branches, or generally tidy up after shipped work, or when they invoke `minerva:cleanup`.
---

## Runtime

Read `skills/using-minerva/references/runtime.md` before executing; follow its host adapter.

Tidy up after shipped work — remove `.minerva/worktrees/<date-slug>/` directories whose branches have been merged into the default branch, and prune the corresponding local branches. Idempotent: safe to run on a clean tree (reports zero items removed).

## Usage

- `minerva:cleanup` — sweep all merged worktrees + branches in the current repo
- `minerva:cleanup 005-add-payments` — clean up only the named work unit (slug or path)
- `minerva:cleanup --dry-run` — list what would be removed, changing nothing

## Target resolution

Same pattern used by `minerva:work`, `minerva:replan`, `minerva:promote`, `minerva:review`, `minerva:ship`. **Keep all six blocks in sync if you edit one.** For `minerva:cleanup` specifically, the default mode (no argument) is "all merged worktrees" rather than a single target — but resolution rules apply when an argument is passed.

1. **Explicit argument** (slug or path) → operate on just that work unit. Check both `.minerva/work/<date-slug>/` and `.minerva/worktrees/<date-slug>/`. Required: the corresponding branch must be merged into default (see Merge detection).
2. **No argument** → scan all `.minerva/worktrees/*/` directories and check each branch's merge state. Match **both** id forms — `YYYY-MM-DD-<slug>` and legacy `NNN-<slug>`. A glob anchored on digits-then-dash (`[0-9][0-9][0-9]-*`) does **not** match `2026-08-09-slug`, so a date-named worktree would be silently skipped and never cleaned up.
3. **Non-git repo** → report "not a git repo, nothing to clean up" and stop.

## Checkpoint entry

Unless `--dry-run`, read the resolved unit's runtime checkpoint before removal.
Revalidate live merge evidence and explicit mode arguments — a checkpoint is not
authorization for `--yes`. Save phase `cleanup` before waiting, and mark this shipping
pass `done` after safe teardown (or a phased unit's teardown deferral — it can finish this
pass while keeping its worktree for the next phase). If blocked, retain pending/blocked
state and provide an exact resume prompt. For multi-unit cleanup, maintain a checkpoint
per unit. Dry-run writes none. A 2.x checkpoint saved at the legacy `reconciliation` phase
has nothing left to do: revalidate the merge and mark it `done`.

## Pre-flight checks

Bail with a clear message on any failure:

1. **Git repo.** `git rev-parse --is-inside-work-tree` returns true.
2. **`gh` CLI available** (optional but preferred). Falls back to local-only merge detection if `gh` is missing or unauthenticated.
3. **Not currently inside a worktree being cleaned.** If invoked from inside `.minerva/worktrees/<date-slug>/`, that worktree cannot be removed while it's the current working tree. Report and ask the user to `cd` out (back to the main repo root) and re-run. Cleanup always operates from the parent repo — its job is to remove worktrees, so it must never be running inside one. (No lifecycle skill makes a worktree its working directory: the others address worktrees by `.minerva/worktrees/<date-slug>/`-prefixed paths, while cleanup removes them outright.)

## Default-branch detection

Resolve **once** at the start:

1. `git symbolic-ref refs/remotes/origin/HEAD` → parse `refs/remotes/origin/<name>`.
2. Fall back to `main`, then `master`.

Use the resolved value for all merge checks.

## Merge detection per worktree

A worktree is safe to remove only once its branch has merged into the default branch. The full
detection protocol — including the squash-merge case a plain `git branch --merged` misses —
lives in `references/merge-detection.md`. **Read it before removing anything.**
On a phased unit teardown waits for the final phase — **read `references/phased-units.md`** before
tearing anything down. The rule itself is stated once, in `references/merge-detection.md`.

## Orchestrated mode (`--yes`)

**Mode argument**: `--yes`

With an explicit single-unit argument `--yes` satisfies the confirmation gate below — how the
autonomous orchestrators invoke cleanup. Act on the argument, not on who you think is calling.

## Confirmation gate

Before removing anything, present the list:

```
Will remove:
  .minerva/worktrees/005-add-payments/   (branch 005-add-payments, merged via PR #42 on 2026-05-12)
  .minerva/worktrees/006-add-ship-skill/ (branch 006-add-ship-skill, merged via PR #45 on 2026-05-15)
Will skip:
  .minerva/worktrees/007-add-cleanup/    (branch 007-add-cleanup, NOT merged — unmerged work, leaving alone)
```

Ask:
> "Remove these worktrees and prune the matching local branches? [y/N]"

Default is no — destructive operations require explicit yes. The user can also batch ("yes, all" / "just the first two" / "skip 006").

Skip this gate when `--dry-run` is set (nothing destructive happens) or when the user invokes with an explicit single-unit argument **and** says `--yes` (e.g. `minerva:cleanup 005-add-payments --yes`).

## Removal

Conservative by design — each step prefers to refuse and surface rather than force, because
cleanup's failure mode is destroying unmerged work. **Read [references/removal.md](references/removal.md) before removing anything**; it carries the worktree removal, the `-d`/`-D` branch-delete rule and its squash-merge rationale, the phased-unit branch prune, and the metadata prune.

## Final report

```
Worktrees removed:     N (<list>)
Branches pruned:       N (<list>)
Skipped (unmerged):    N (<list with branch names>)
Skipped (uncommitted): N (<list — needs manual review>)
Remaining worktrees:   N (<list>)
```

If any worktrees were skipped due to uncommitted changes, recommend the user inspect each (`cd .minerva/worktrees/<slug>; git status`) and decide whether the changes are valuable.

## No knowledge reconciliation

Cleanup does **not** touch `.minerva/knowledge/`, and it opens no PR. There is nothing to catalogue after a
merge: `minerva:promote` writes write-once entries carrying their own `**Theme**` and
`**Summary**`, and the catalog, backlinks and supersession are derived on read by
`knowledge_catalog.py` (`2026-10-01-decision-knowledge-aggregates-are-derived-on-read`). The
knowledge update ships complete in the unit's own PR. Earlier versions opened a
`minerva/reconcile` PR here; do not recreate one. A stale local `minerva/reconcile` branch
left by a 2.x run holds only squash-merged machine commits, so `git branch -d` refuses it:
confirm no PR is open on it (`gh pr list --head minerva/reconcile --state open`), then
delete it with `git branch -D`.

## Idempotency

Cleanup rederives candidates from live Git/PR evidence and retains only untracked
runtime progress. Re-running on a fresh tree finds zero candidates and reports zero removed. Running mid-CI for a branch with an auto-merge pending will correctly skip that worktree (PR is `OPEN`, not `MERGED`).

If a user manually removed a worktree directory without running `git worktree remove`, the next `minerva:cleanup` call will see stale worktree metadata; `git worktree prune` at the end of the run handles this.

## Out of scope

- **Removing the work-unit's `.minerva/work/<date-slug>/` directory from `main`.** The docs already moved into the worktree at `minerva:work` time and were merged into `main` via the PR; the canonical record lives at `.minerva/work/<date-slug>/` post-merge. `cleanup` only removes the worktree, not the merged docs.
- **Removing knowledge files.** `.minerva/knowledge/` entries are permanent by design.
- **Force-removing unmerged work.** Always requires explicit user override; cleanup is conservative by default.
- **Pruning remote branches.** GitHub usually auto-deletes the source branch after merge if the repo is configured for it. Local prune handles the local side; remote prune is `git fetch --prune` and not part of this skill.

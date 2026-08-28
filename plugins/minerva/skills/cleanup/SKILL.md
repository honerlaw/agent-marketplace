---
name: cleanup
description: Removes `.minerva/worktrees/<date-slug>/` directories whose branches have been merged into the default branch, prunes the corresponding local branches, and reconciles the knowledge wiki on the default branch — cataloguing entries that add-only promotes left pending, writing their reciprocal links, and refreshing the overview — via a single auto-merging PR. Idempotent; never force-removes unmerged work, and never commits directly to the default branch. Use after a PR merges, when the user asks to remove merged worktrees, prune stale minerva branches, catalogue pending knowledge entries, or generally tidy up after shipped work, or when they invoke `minerva:cleanup`.
---

Tidy up after shipped work — remove `.minerva/worktrees/<date-slug>/` directories whose branches have been merged into the default branch, and prune the corresponding local branches. Idempotent: safe to run on a clean tree (reports zero items removed).

## Usage

- `minerva:cleanup` — sweep all merged worktrees + branches in the current repo
- `minerva:cleanup 005-add-payments` — clean up only the named work unit (slug or path)
- `minerva:cleanup --dry-run` — list what would be removed and what reconciliation would do, changing nothing

## Target resolution

Same pattern used by `minerva:work`, `minerva:replan`, `minerva:promote`, `minerva:review`, `minerva:ship`. **Keep all six blocks in sync if you edit one.** For `minerva:cleanup` specifically, the default mode (no argument) is "all merged worktrees" rather than a single target — but resolution rules apply when an argument is passed.

1. **Explicit argument** (slug or path) → operate on just that work unit. Check both `.minerva/work/<date-slug>/` and `.minerva/worktrees/<date-slug>/`. Required: the corresponding branch must be merged into default (see Merge detection).
2. **No argument** → scan all `.minerva/worktrees/*/` directories and check each branch's merge state. Match **both** id forms — `YYYY-MM-DD-<slug>` and legacy `NNN-<slug>`. A glob anchored on digits-then-dash (`[0-9][0-9][0-9]-*`) does **not** match `2026-08-09-slug`, so a date-named worktree would be silently skipped and never cleaned up.
3. **Non-git repo** → report "not a git repo, nothing to clean up" and stop.

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

For each `.minerva/worktrees/<date-slug>/` candidate, determine if its branch (`<date-slug>` by convention) has been merged into the default branch:

1. **Branch exists?** `git rev-parse --verify <date-slug>` — if the branch is already gone (was deleted upstream and locally), the worktree is orphaned and can be removed.
2. **Merged via PR (preferred)** — `gh pr list --head <date-slug> --state merged --json number,mergedAt --limit 1`. If a merged PR exists, the work is shipped.
3. **Merged locally** — `git branch --merged <default> | grep -q "^[* ] <date-slug>$"`. Catches the case where the branch was merged locally or where `gh` isn't available.
4. **Neither** — branch is **not** merged. Skip. Do not remove an unmerged worktree (the user's in-progress work would be lost).
5. **Phased unit?** If the candidate's `proposal.md` declares `## Phases`, a merged phase-1 branch means that *phase* shipped, not the unit. Teardown waits for the final phase; reconciliation never does. **Read [references/phased-units.md](references/phased-units.md)** before tearing anything down. No-op for unphased units.

Report each candidate's state. For `--dry-run`, stop here.

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

## Knowledge reconciliation

Because `minerva:promote` is add-only — it writes new knowledge entries on a work-unit branch and touches no aggregate — the `index.md` catalog lines, watermark, reciprocal `## Related` links, supersession banners, and `overview.md` are all written **here**, on the default branch, where there is one writer at a time. This is what makes concurrent minerva PRs conflict-free.

**Run it on every invocation**, decoupled from worktree removal: a merge done through the GitHub UI leaves pending entries with no worktree to remove. It is cheap and silent when nothing is pending. Exception: a repo that reconciles in CI (Step 0).

The full protocol — the deterministic pending/un-synthesized signal, the at-most-one-open-PR rule, the throwaway worktree, the `knowledge_fix` + `minerva:synthesize` pass, and the auto-merging PR — lives in `references/reconciliation.md`. **Read it before reconciling.** Three rules bind even before you read it: never commit to the default branch directly (reconciliation always goes through its own PR); if `gh pr merge --auto` is rejected, report the PR URL and stop rather than merging another way; and **never end a run leaving entries uncatalogued without naming them** — if a reconciliation PR is already open, wait for it and reconcile what remains, and if it never merges, list every still-pending entry stem under `Pending, NOT catalogued`. A run that leaves entries invisible must not report itself clean.

## Idempotency

Cleanup is stateless. Re-running on a fresh tree finds zero candidates and reports zero removed. Reconciliation is likewise idempotent — `knowledge_fix` is a byte-level no-op on an already-reconciled corpus, so a second run reports nothing pending. Running mid-CI for a branch with an auto-merge pending will correctly skip that worktree (PR is `OPEN`, not `MERGED`).

If a user manually removed a worktree directory without running `git worktree remove`, the next `minerva:cleanup` call will see stale worktree metadata; `git worktree prune` at the end of the run handles this.

## Out of scope

- **Removing the work-unit's `.minerva/work/<date-slug>/` directory from `main`.** The docs already moved into the worktree at `minerva:work` time and were merged into `main` via the PR; the canonical record lives at `.minerva/work/<date-slug>/` post-merge. `cleanup` only removes the worktree, not the merged docs.
- **Removing knowledge files.** `.minerva/knowledge/` entries are permanent by design.
- **Force-removing unmerged work.** Always requires explicit user override; cleanup is conservative by default.
- **Pruning remote branches.** GitHub usually auto-deletes the source branch after merge if the repo is configured for it. Local prune handles the local side; remote prune is `git fetch --prune` and not part of this skill.

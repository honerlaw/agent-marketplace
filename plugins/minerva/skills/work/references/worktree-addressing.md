# Worktree addressing — run before Setup

Every active work unit lives in an isolated git worktree created by `minerva:propose`. This section runs **before** reading docs. **minerva never calls `EnterWorktree`** — it only reliably enters worktrees under `.claude/worktrees/`, and minerva's live under `.minerva/worktrees/`. The session's working directory stays the parent repo; you address the worktree by writing every file path with the `.minerva/worktrees/<date-slug>/` prefix and running every git command as `git -C .minerva/worktrees/<date-slug> …`.

1. **Determine <date-slug>** from the resolved target (e.g. `005-add-payments`).

2. **Decide the entry path** based on where the work unit's docs live:

   ### Primary path — worktree exists

   `.minerva/worktrees/<date-slug>/` exists. This is the common case after `minerva:propose`.

   - Address it by prefix (no `EnterWorktree`): every file path gets the `.minerva/worktrees/<date-slug>/` prefix; git runs as `git -C .minerva/worktrees/<date-slug> …`. Relative paths resolve to the parent repo and silently misroute edits onto the wrong branch (see `.minerva/knowledge/008-constraint-enter-worktree-absolute-paths.md`).
   - Continue to Setup.

   ### Exceptional path — worktree missing, docs only on default branch

   `.minerva/worktrees/<date-slug>/` does **not** exist, but `.minerva/work/<date-slug>/` exists on the default branch. This is the resurrection case: the unit was previously shipped and `minerva:cleanup` removed its worktree, but the user wants to re-open it. Surface a one-line note before proceeding: "no worktree found for `<date-slug>` — re-creating from the shipped docs on `<default-branch>`."

   1. Resolve the default branch the same way `ship` and `cleanup` do:
      - `git symbolic-ref refs/remotes/origin/HEAD` → parse `refs/remotes/origin/<name>`.
      - Fall back to `main`, then `master`.
   2. Confirm `.minerva/worktrees/` is gitignored on `<default-branch>` (`git show <default-branch>:.gitignore | grep -q '\.minerva/worktrees/'`). If missing, bail with "run `minerva:init` first to install the gitignore entry, then retry."
   3. `git worktree add -b <date-slug> .minerva/worktrees/<date-slug> <default-branch>` — branches from the merged default, picking up the shipped docs automatically.
   4. Address it by prefix (no `EnterWorktree`): prefix file paths with `.minerva/worktrees/<date-slug>/` and run git as `git -C .minerva/worktrees/<date-slug> …`.
   5. Continue to Setup. (No file move or commit needed — the docs are already on the branch.)

   ### Neither location has the unit

   Report "no such work unit `<date-slug>` — run `minerva:propose` first" and stop.

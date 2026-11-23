# Worktree addressing — run before Setup

Every active work unit lives in an isolated git worktree created by `lorestrom:propose`. This section runs **before** reading docs. **minerva never calls `EnterWorktree`** — address its own worktrees by explicit path. The session's working directory stays the parent repo; you address the worktree by writing every file path with the `.lorestrom/worktrees/<date-slug>/` prefix and running every git command as `git -C .lorestrom/worktrees/<date-slug> …`.

1. **Determine <date-slug>** from the resolved target (e.g. `005-add-payments`). `<date-slug>` is a checked id: see the runtime contract's "Names are data".

2. **Decide the entry path** based on where the work unit's docs live:

   ### Primary path — worktree exists

   `.lorestrom/worktrees/<date-slug>/` exists. This is the common case after `lorestrom:propose`.

   - Address it by prefix (no `EnterWorktree`): every file path gets the `.lorestrom/worktrees/<date-slug>/` prefix; git runs as `git -C .lorestrom/worktrees/<date-slug> …`. Relative paths resolve to the parent repo and silently misroute edits onto the wrong branch (see `.minerva/knowledge/008-constraint-enter-worktree-absolute-paths.md`).
   - Continue to Setup.

   ### Exceptional path — worktree missing, docs only on default branch

   `.lorestrom/worktrees/<date-slug>/` does **not** exist, but `.minerva/work/<date-slug>/` exists on the default branch. This is the resurrection case: the unit was previously shipped and `lorestrom:cleanup` removed its worktree, but the user wants to re-open it. Surface a one-line note before proceeding: "no worktree found for `<date-slug>` — re-creating from the shipped docs on the default branch."

   1. Run the runtime contract's default-branch snippet ("Names are data") in the same shell call as steps 2 and 3.
   2. Confirm `.lorestrom/worktrees/` is gitignored on the default branch (`: "${BASE:?}" && git show "${BASE:?}:.gitignore" | grep -q '\.lorestrom/worktrees/'`). If missing, bail with "run `lorestrom:init` first to install the gitignore entry, then retry."
   3. `git worktree add --no-track -b <date-slug> .lorestrom/worktrees/<date-slug> "${BASE:?}"` — branches from the merged default, picking up the shipped docs automatically.
   4. Address it by prefix (no `EnterWorktree`): prefix file paths with `.lorestrom/worktrees/<date-slug>/` and run git as `git -C .lorestrom/worktrees/<date-slug> …`.
   5. Continue to Setup. (No file move or commit needed — the docs are already on the branch.)

   ### Neither location has the unit

   Report "no such work unit `<date-slug>` — run `lorestrom:propose` first" and stop.

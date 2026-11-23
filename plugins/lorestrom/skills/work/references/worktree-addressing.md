# Worktree addressing — run before Setup

Every active work unit's code lives in an isolated git worktree created by `lorestrom:propose`; its records live in Lorestrom. This section runs **before** reading records. **lorestrom never calls `EnterWorktree`** — address its own worktrees by explicit path. The session's working directory stays the parent repo; you address the worktree by writing every repository file path with the `.lorestrom/worktrees/<date-slug>/` prefix and running every git command as `git -C .lorestrom/worktrees/<date-slug> …`.

1. **Determine <date-slug>** from the resolved target (e.g. `005-add-payments`). `<date-slug>` is a checked id: see the runtime contract's "Names are data".

2. **Decide the entry path** based on what exists:

   ### Primary path — worktree exists

   `.lorestrom/worktrees/<date-slug>/` exists. This is the common case after `lorestrom:propose`.

   - Address it by prefix (no `EnterWorktree`): every repository file path gets the `.lorestrom/worktrees/<date-slug>/` prefix; git runs as `git -C .lorestrom/worktrees/<date-slug> …`. Relative paths resolve to the parent repo and silently misroute edits onto the wrong branch.
   - Continue to Setup.

   ### Exceptional path — worktree missing, unit doc present

   `.lorestrom/worktrees/<date-slug>/` does **not** exist, but the unit's doc does (`storage:unit.read`). This is the resurrection case: the unit was previously shipped and `lorestrom:cleanup` removed its worktree, but the user wants to re-open it. Surface a one-line note before proceeding: "no worktree found for `<date-slug>` — re-creating it." A unit whose gate is released or abandoned is finished: re-opening it means a new unit (`lorestrom:propose`), so stop and say so.

   1. Pick the branch: `<date-slug>` for an unphased unit; for a phased unit, the `next_branch` the helper's `phases` printed (`storage:unit.read`), which is `<date-slug>` for phase 1 and `<date-slug>-phase-N` after. Below, `<date-slug>-phase-N` stands for whichever it is. Run `git fetch origin` and check `git rev-parse --verify --quiet "refs/remotes/origin/<date-slug>-phase-N"`. Run the runtime contract's default-branch snippet ("Names are data") in the same shell call as step 3.
   2. Confirm `.lorestrom/worktrees/` is ignored (`git check-ignore -q .lorestrom/worktrees/probe`: `lorestrom:init` ignores it in this clone, or in `.gitignore` with `--shared`). If not, bail with "run `lorestrom:init` first, then retry."
   3. **Origin has the branch:** `git worktree add --no-track -b <date-slug>-phase-N .lorestrom/worktrees/<date-slug> "refs/remotes/origin/<date-slug>-phase-N"`, so pushed work is kept. **It does not:** ask the user before cutting a fresh `<date-slug>-phase-N` from `"${BASE:?}"` (the same command with that start point), since unpushed work may live in another clone. Never start a fresh branch silently.
   4. Address it by prefix (no `EnterWorktree`): prefix repository file paths with `.lorestrom/worktrees/<date-slug>/` and run git as `git -C .lorestrom/worktrees/<date-slug> …`.
   5. Continue to Setup. The records are already in Lorestrom; nothing moves.

   ### The unit has no doc

   Report "no such work unit `<date-slug>` — run `lorestrom:propose` first" and stop.

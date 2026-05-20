# Proposal: worktree-creation-in-propose

**Date**: 2026-05-20
**Status**: Draft

## Goal

Move worktree and branch creation from `minerva:work` into `minerva:propose`. The propose skill creates `.minerva/worktrees/<NNN-slug>/` on a `<NNN-slug>` branch, calls `EnterWorktree` to switch the session in, and then writes `proposal.md` and `scratchpad.md` inside the worktree — never on `main`. All downstream lifecycle skills (`work`, `replan`, `review`, `promote`, `ship`) become worktree-aware: when the resolved target's docs live in a worktree and the session isn't in that worktree, the skill calls `EnterWorktree` before doing anything else. `minerva:init` pre-installs the `.minerva/worktrees/` `.gitignore` entry so propose can run without modifying `.gitignore` from inside a worktree.

## Why

Today's flow has `minerva:propose` write docs to `.minerva/work/<NNN-slug>/` on `main`, then `minerva:work` (on first invocation) creates the worktree, moves the docs into it, and commits. That transitional state — "docs on main, then moved" — pollutes `main`'s working tree between propose and work and forces every other lifecycle skill's target-resolution block to scan two locations (`.minerva/work/` on main vs `.minerva/worktrees/.../`) for the in-flight window.

Collapsing the transition into propose makes the propose phase atomic: it produces a branch + worktree + committed docs in one go. `main` never sees in-flight work. The "two possible locations" rule still applies post-merge (shipped docs land on `main`, active docs live in worktrees), but the meaning is cleaner: main = shipped/historical, worktree = active. There is no longer an awkward "docs created but worktree not yet materialized" window.

For end-to-end orchestration (`minerva:propose-ship`), this means the worktree is already set up before `minerva:work` runs, so the work skill simplifies down to "enter the worktree and start implementing" — no setup logic in the common path.

## Approach

### `propose/SKILL.md` — main change

After the existing pre-write hard gate (all sections approved), insert a worktree-setup phase before any file is written:

1. **Slug derivation + duplicate check** (unchanged): derive slug, scan `.minerva/work/<NNN-slug>/`, `.minerva/worktrees/<NNN-slug>/`, and `git branch --list "*-<slug>"` (both local and remote). Abort on collision.
2. **NNN computation** (unchanged): scan local `.minerva/work/`, local branches `[0-9][0-9][0-9]-*` and `minerva/[0-9][0-9][0-9]-*`, remote branches with the same patterns. Max+1, pad to 3 digits.
3. **Default-branch detection** (new): same logic block used by `ship` and `cleanup`:
   - `git symbolic-ref refs/remotes/origin/HEAD` → parse the trailing name.
   - Fall back to `main`, then `master`.
4. **Pre-flight gitignore check** (new): verify `.minerva/worktrees/` appears in the default branch's `.gitignore`. If missing, abort with "the `.minerva/worktrees/` gitignore entry is missing on `<default-branch>` — run `minerva:init` first to install it, or add `.minerva/worktrees/` to `.gitignore` and commit on `<default-branch>`." Do not auto-edit `.gitignore` from inside propose (propose may be invoked from a worktree where editing `.gitignore` would land on the wrong branch).
5. **Worktree + branch creation** (new): from the main repo working directory, run `git worktree add -b <NNN-slug> .minerva/worktrees/<NNN-slug> <default-branch>`. Branching explicitly from the default branch (rather than HEAD) prevents accidentally stacking on an in-flight branch when propose is invoked from another worktree.
6. **Enter the worktree** (new): call `EnterWorktree` with `path: ".minerva/worktrees/<NNN-slug>"`. All subsequent file operations run inside the worktree.
7. **Create `.minerva/work/<NNN-slug>/`** (unchanged target, new location: inside the worktree).
8. **Write `proposal.md` and `scratchpad.md`** (unchanged content).
9. **Self-review and inline fixes** (unchanged).
10. **Commit on the branch** (new): `git add .minerva/work/<NNN-slug>/` then `git commit -m "chore: initialize <NNN-slug> work unit"`.
11. **Post-write user gate** (unchanged content, new commit behavior): if the user requests edits, edit inline, then create a follow-up commit (no `--amend` — the previous commit is the starting state of the branch and amending it would invalidate any history viewer that already saw it).
12. **Suggest `minerva:work` as the next step** (unchanged).

The `Out of scope` section gets one sentence noting that the worktree is created by propose, not work.

### `work/SKILL.md` — flip worktree setup to "enter, don't create"

The existing "Worktree setup" section becomes "Worktree entry" with the priority inverted:

- **Worktree exists at `.minerva/worktrees/<NNN-slug>/`** (the common case after propose) → `EnterWorktree path: ".minerva/worktrees/<NNN-slug>"`, continue to Setup.
- **Worktree does not exist BUT `.minerva/work/<NNN-slug>/` exists on `<default-branch>`** (the rare case: a shipped work unit being resurrected after `minerva:cleanup`) → keep the existing creation flow as a documented fallback. Surface a one-line note to the user: "no worktree found — re-creating from the shipped docs on `<default-branch>`."
- **Neither location has the work unit** → "no such work unit `<NNN-slug>` — run `minerva:propose` first" and stop.

Target resolution is unchanged: still scans both `.minerva/work/` and `.minerva/worktrees/` because shipped units live on main.

### `replan/SKILL.md`, `review/SKILL.md`, `promote/SKILL.md`, `ship/SKILL.md` — worktree awareness

After each skill's target-resolution block, insert a uniform "worktree entry" step that reads roughly:

> **Worktree entry.** If the resolved target's docs live at `.minerva/worktrees/<NNN-slug>/.minerva/work/<NNN-slug>/` and the current session is not in that worktree, call `EnterWorktree` with `path: ".minerva/worktrees/<NNN-slug>"` before reading or writing anything. If the docs only live on `<default-branch>` (a shipped unit being inspected), operate on the main repo without entering a worktree.

This makes the skills robust against being invoked from a stale cwd — they always end up in the right working tree before touching files or running git commands.

`ship/SKILL.md` already has a partial worktree-handling note ("prefer entering the worktree before shipping"); replace the prose with the concrete `EnterWorktree` call.

### `cleanup/SKILL.md` — no worktree entry

Cleanup removes worktrees, so it must stay outside the worktrees it's removing. The existing "Not currently inside a worktree being cleaned" pre-flight check already enforces this. No structural changes — but add a one-line cross-reference acknowledging the new propose-creates-worktree flow so future readers don't expect cleanup to also handle creation.

### `init/SKILL.md` — install gitignore entry

Step 2 ("gitignore check") gets a new sub-step: if `.minerva/worktrees/` is **not** present in `.gitignore`, append it and report `gitignore: added .minerva/worktrees/`. If it is present, report `gitignore ✓ (worktrees ignored)`. Existing gitignore-violation detection (patterns that would exclude `.minerva/knowledge/` or `.minerva/work/`) is unchanged.

This makes `.minerva/worktrees/` part of init's idempotent scaffold rather than something propose has to install on first run. Knowledge entry `005-decision-gitignore-before-worktree` already documents the constraint; pulling it into init is the natural home.

### `using-minerva/SKILL.md` — update lifecycle ownership

Two prose updates:

- In the "Canonical lifecycle order" diagram, change `minerva:work # implementation in a git worktree` to `minerva:work # implementation inside the worktree from propose`, and change `minerva:propose # design + write proposal.md` to `minerva:propose # design + branch + worktree + proposal.md`.
- In "Common scenarios", the propose blurb gets a sentence: "Propose also creates the work unit's branch and worktree at `.minerva/worktrees/<NNN-slug>/` and enters it — all writes happen in the worktree, not on `<default-branch>`."

### `propose-ship/SKILL.md` — minor prose update

The "Phase sequence" comment becomes: "propose now owns worktree creation; work enters the existing worktree." No structural change to the orchestrator — it's still a thin conductor.

### Implementation order

To keep each commit reviewable in isolation:

1. `init/SKILL.md` — gitignore install (small, foundational).
2. `propose/SKILL.md` — worktree setup phase (the main change).
3. `work/SKILL.md` — flip priority of worktree-entry vs creation.
4. `replan`, `review`, `promote`, `ship` — uniform worktree-entry block (can be a single commit since they're parallel changes).
5. `cleanup/SKILL.md` — cross-reference note.
6. `using-minerva/SKILL.md`, `propose-ship/SKILL.md` — prose updates reflecting new ownership.

## Success criteria

- `plugins/minerva/skills/propose/SKILL.md` runs `git worktree add` and `EnterWorktree` between NNN computation and the first file write, branches explicitly from the resolved default branch, and commits the initial docs on the new branch.
- `plugins/minerva/skills/work/SKILL.md`'s worktree section lists "worktree exists → EnterWorktree" as the primary path; creation logic is marked as a fallback for shipped-unit resurrection only.
- `plugins/minerva/skills/replan/SKILL.md`, `review/SKILL.md`, `promote/SKILL.md`, `ship/SKILL.md` each contain an explicit "Worktree entry" block immediately after their Target resolution section, with the same EnterWorktree guidance.
- `plugins/minerva/skills/init/SKILL.md` adds `.minerva/worktrees/` to `.gitignore` when absent, reports it as part of step 2, and is idempotent (no-op when already present).
- `plugins/minerva/skills/using-minerva/SKILL.md` describes worktree+branch creation as propose's responsibility in both the lifecycle diagram and the common-scenarios section.
- `plugins/minerva/skills/propose-ship/SKILL.md` prose reflects that the worktree exists from the propose phase onward.
- All six target-resolution blocks (`work`, `replan`, `promote`, `review`, `ship`, `cleanup`) remain byte-identical to each other (the "keep all six in sync" rule still holds after the edits).
- Running `minerva:propose` on a fresh slug in a clean repo produces: a `<NNN-slug>` branch checked out at `.minerva/worktrees/<NNN-slug>/`, a single commit on that branch containing `.minerva/work/<NNN-slug>/{proposal.md,scratchpad.md}`, and no changes to `.minerva/work/` on the default branch.

## Open Questions

- Should the work skill keep the worktree-creation fallback for resurrecting shipped units, or remove it entirely and require the user to recreate the worktree manually? Leaning keep — it's the only way to re-enter a cleaned-up unit without manual git plumbing, and the prose can mark it as the exceptional path.
- Should propose offer to remove the worktree if the user rejects at the post-write gate? Leaning no — keep propose's responsibilities narrow; the user can `git worktree remove .minerva/worktrees/<NNN-slug>` or run `minerva:cleanup <slug> --force` (where `--force` is a future addition, not part of this work unit) to abandon. Defer the abandon path.

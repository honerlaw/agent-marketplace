# Proposal: worktree-creation-in-propose

**Date**: 2026-05-20
**Status**: Shipped (2026-05-20)

## Goal

Move worktree and branch creation from `minerva:work` into `minerva:propose`. The propose skill creates `.minerva/worktrees/<NNN-slug>/` on a `<NNN-slug>` branch, calls `EnterWorktree` to switch the session in, and then writes `proposal.md` and `scratchpad.md` inside the worktree — never on `main`. All downstream lifecycle skills (`work`, `replan`, `review`, `promote`, `ship`) become worktree-aware: when the resolved target's docs live in a worktree and the session isn't in that worktree, the skill calls `EnterWorktree` before doing anything else. `minerva:init` pre-installs the `.minerva/worktrees/` `.gitignore` entry so propose can run without modifying `.gitignore` from inside a worktree.

## Why

Today's flow has `minerva:propose` write docs to `.minerva/work/<NNN-slug>/` on `main`, then `minerva:work` (on first invocation) creates the worktree, moves the docs into it, and commits. That transitional state — "docs on main, then moved" — pollutes `main`'s working tree between propose and work and forces every other lifecycle skill's target-resolution block to scan two locations (`.minerva/work/` on main vs `.minerva/worktrees/.../`) for the in-flight window.

Collapsing the transition into propose makes the propose phase atomic: it produces a branch + worktree + committed docs in one go. `main` never sees in-flight work. The "two possible locations" rule still applies post-merge (shipped docs land on `main`, active docs live in worktrees), but the meaning is cleaner: main = shipped/historical, worktree = active. There is no longer an awkward "docs created but worktree not yet materialized" window.

For end-to-end orchestration (`minerva:propose-ship`), this means the worktree is already set up before `minerva:work` runs, so the work skill simplifies down to "enter the worktree and start implementing" — no setup logic in the common path.

## Approach

### `propose/SKILL.md` — main change

The "On approval — worktree setup + file writes" section has 13 steps. A section preamble states which steps run from the parent repo vs. inside the worktree, plus a non-git-repo escape clause:

> Steps 1–6 run from the parent repo. Step 7 enters the worktree. Steps 8–13 run inside the worktree. Non-git escape clause: skip steps 4, 5, 6, 7, and 11 entirely; run 1–3, jump to 8, continue with 9, 10, 12, 13.

The steps:

1. Derive the slug from the confirmed goal title.
2. Duplicate slug check across `.minerva/work/<NNN-slug>/`, `.minerva/worktrees/<NNN-slug>/`, and `git branch --list "*-<slug>"` (local and remote).
3. Compute the next NNN by scanning local `.minerva/work/`, local branches `[0-9][0-9][0-9]-*` / `minerva/[0-9][0-9][0-9]-*`, and matching remote branches.
4. Resolve the default branch via `git symbolic-ref refs/remotes/origin/HEAD` → fall back to `main` → fall back to `master`.
5. Pre-flight gitignore check: `git show <default-branch>:.gitignore` and grep for `.minerva/worktrees/`. If missing, abort with a message pointing at `minerva:init`. Propose does **not** auto-edit `.gitignore` (it may be running from a worktree, where the edit would land on the wrong branch).
6. `git worktree add -b <NNN-slug> .minerva/worktrees/<NNN-slug> <default-branch>` — branching explicitly from `<default-branch>` (not HEAD) so the new unit doesn't stack on an in-flight branch.
7. `EnterWorktree` with `path: ".minerva/worktrees/<NNN-slug>"`. All subsequent file ops run inside the worktree.
8. Create `.minerva/work/<NNN-slug>/` (relative to the worktree root).
9. Write `proposal.md` and `scratchpad.md`.
10. Self-review the proposal and fix issues inline.
11. `git add .minerva/work/<NNN-slug>/` then `git commit -m "chore: initialize <NNN-slug> work unit"`.
12. Post-write user gate. If the user requests edits, create a follow-up commit (no `--amend` — the initial commit was already published as the branch's starting state).
13. Suggest `minerva:work` as the next step.

`Out of scope` was extended with an explicit note about worktree abandonment: if the user rejects at the post-write gate, they remove the worktree and branch manually — propose has no `--abandon` flow.

### `work/SKILL.md` — flip worktree setup to "enter, don't create"

The old "Worktree setup" section is now "Worktree entry" with two named paths:

- **Primary path — worktree exists**: `.minerva/worktrees/<NNN-slug>/` is present (the common case after propose). Call `EnterWorktree` and continue to Setup.
- **Exceptional path — worktree missing, docs only on default branch**: the resurrection case (shipped + cleaned-up unit being re-opened). Surface a one-line note, re-resolve the default branch, confirm `.minerva/worktrees/` is gitignored (else bail to `minerva:init`), `git worktree add -b <NNN-slug> .minerva/worktrees/<NNN-slug> <default-branch>`, then EnterWorktree. No file move or commit needed — the docs are already on the branch.
- **Neither location has the work unit** → "no such work unit — run `minerva:propose` first" and stop.

Target resolution prose was updated to say "active work lives in worktrees; shipped + merged units live in `.minerva/work/` on the default branch" instead of the obsolete "after `minerva:work` runs once, the docs move".

### `replan/SKILL.md`, `review/SKILL.md`, `promote/SKILL.md`, `ship/SKILL.md` — worktree awareness

Each gets a `## Worktree entry` block inserted immediately after `## Target resolution`. The block reads:

> If the resolved target's docs live at `.minerva/worktrees/<NNN-slug>/.minerva/work/<NNN-slug>/` and the current session is not in that worktree, call `EnterWorktree` with `path: ".minerva/worktrees/<NNN-slug>"`. If the docs live only on the default branch (a shipped unit being inspected), operate on the parent repo. If the session is already in the matching worktree, do nothing.

`review` adds a clause for the no-minerva-context path (skip the worktree entry, run code review in the user's cwd). `ship` adds a clause for bare mode (no worktree entry). `ship`'s older "Worktree handling" section near the bottom was rewritten to cross-reference the new "Worktree entry" block instead of restating the rules.

### `cleanup/SKILL.md` — no worktree entry

Cleanup removes worktrees, so it must stay outside. The existing pre-flight check ("Not currently inside a worktree being cleaned") was extended with a one-line cross-reference: "Unlike other lifecycle skills, cleanup does not call `EnterWorktree` — its job is to remove worktrees, so it must operate from the parent repo." No structural change.

### `init/SKILL.md` — install gitignore entry

Step 2 ("gitignore check") was split into two parts:

- **Part A — flag patterns that would exclude committed dirs** (existing behavior, unchanged): warn on patterns that would exclude `.minerva/`, `.minerva/knowledge/`, `.minerva/work/`, etc. Do not auto-edit; suggest the user fix it.
- **Part B — install `.minerva/worktrees/` if missing** (new): if no line in `.gitignore` matches `.minerva/worktrees/` (exact or parent pattern), append it and report `gitignore: added .minerva/worktrees/`. If present, report `gitignore ✓ (worktrees ignored)`.

Part B is explicitly part of init's scaffold (not user territory). The report block gained a `.minerva/worktrees/` row. The `Out of scope` note about not editing `.gitignore` was qualified to clarify that init does install the worktrees entry.

### `using-minerva/SKILL.md` — update lifecycle ownership

- Lifecycle diagram: `init` mentions `.gitignore for worktrees`; `propose` says `design + branch + worktree + proposal.md (all writes inside the worktree)`; `work` says `enter the existing worktree and implement`; `replan` says it appends inside the worktree; `ship` says it pushes the work-unit branch; `cleanup` says it runs from the parent repo.
- An "ownership" paragraph below the diagram names propose as the worktree creator, lists all the downstream skills that enter on invocation, and calls out cleanup as the only outside-the-worktree skill.
- "Common scenarios" entries for `propose` and `work` were updated to describe the new flow.
- "Working in a minerva project without invoking skills" was updated: active work lives in worktrees, shipped work lives on `main`.

### `propose-ship/SKILL.md` — minor prose update

A paragraph below the phase-sequence diagram names propose as the worktree creator and notes that every downstream phase enters the worktree automatically (or is already in it). Cleanup runs from outside. The orchestrator logic itself is unchanged — it's still a thin conductor.

## Success criteria

- `plugins/minerva/skills/propose/SKILL.md` runs `git worktree add` and `EnterWorktree` between NNN computation and the first file write, branches explicitly from the resolved default branch, and commits the initial docs on the new branch. ✓
- `plugins/minerva/skills/work/SKILL.md`'s worktree section lists "worktree exists → EnterWorktree" as the **Primary path**; creation logic is marked as the **Exceptional path** for shipped-unit resurrection. ✓
- `plugins/minerva/skills/replan/SKILL.md`, `review/SKILL.md`, `promote/SKILL.md`, `ship/SKILL.md` each contain an explicit `## Worktree entry` block immediately after their Target resolution section, with the same EnterWorktree guidance. ✓
- `plugins/minerva/skills/init/SKILL.md` adds `.minerva/worktrees/` to `.gitignore` when absent, reports it as part of step 2, and is idempotent (no-op when already present). ✓
- `plugins/minerva/skills/using-minerva/SKILL.md` describes worktree+branch creation as propose's responsibility in both the lifecycle diagram and the common-scenarios section. ✓
- `plugins/minerva/skills/propose-ship/SKILL.md` prose reflects that the worktree exists from the propose phase onward. ✓
- All six target-resolution blocks (`work`, `replan`, `promote`, `review`, `ship`, `cleanup`) preserve the shared 5-step pattern (explicit arg → session context → MRU across both locations → ambiguity → none-found). The blocks are not byte-identical (each has documented skill-specific variation — `review`'s no-minerva-context fallback, `ship`'s bare mode, `cleanup`'s collection-mode default), but the shared rule structure stays consistent across all six. ✓
- Running `minerva:propose` on a fresh slug in a clean repo produces: a `<NNN-slug>` branch checked out at `.minerva/worktrees/<NNN-slug>/`, a single commit on that branch containing `.minerva/work/<NNN-slug>/{proposal.md,scratchpad.md}`, and no changes to `.minerva/work/` on the default branch. ✓ (dogfooded for this very work unit — branch `010-worktree-creation-in-propose` was created from main, EnterWorktree'd, and the first commit `7863801 chore: initialize 010-worktree-creation-in-propose work unit` matches the expected shape).

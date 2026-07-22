# propose — on approval: worktree setup + file writes

## On approval — worktree setup + file writes

Steps 1–6 run from the parent repo (typically on `<default-branch>`). Step 7 establishes how to address the worktree. Steps 8–13 write into the worktree **via its prefixed path** — the session's working directory never changes.

**Non-git repo escape clause:** in a non-git project (no `.git/` directory at the project root), there's nothing to commit and no worktree to create. Skip steps 4, 5, 6, 7, and 11 entirely; run steps 1–3 (NNN computation already has its own non-git fallback), then jump from step 3 to step 8 — create `.minerva/work/<NNN-slug>/` directly at the project root and continue with steps 9, 10, 12, 13.

1. **Derive the slug silently** from the confirmed goal title: lowercase, replace whitespace/underscores with `-`, strip everything outside `[a-z0-9-]`.

2. **Duplicate slug check** — look for `.minerva/work/NNN-<slug>/`, `.minerva/worktrees/NNN-<slug>/`, and any branch named `*-<slug>` (`git branch --list "*-<slug>"`, `git branch -r --list "*-<slug>"`). If found, do **not** proceed. Tell the user the existing path / branch and suggest `minerva:replan` if they want to course-correct an in-flight work unit.

3. **Compute the next NNN** by scanning **all three** sources so parallel work in worktrees and remotes doesn't collide:

   ```
   # local work directory
   ls -1 .minerva/work/ | grep -E '^[0-9]{3}-'

   # local branches (catches in-flight worktrees whose docs left .minerva/work/)
   git branch --list '[0-9][0-9][0-9]-*' --format '%(refname:short)'
   git branch --list 'minerva/[0-9][0-9][0-9]-*' --format '%(refname:short)'

   # remote branches (catches work shipped from elsewhere)
   git ls-remote --heads origin '[0-9][0-9][0-9]-*' 2>/dev/null
   git ls-remote --heads origin 'minerva/[0-9][0-9][0-9]-*' 2>/dev/null
   ```

   Parse the 3-digit prefix from each, take the max across all sources, add 1, pad to 3 digits. If none exist, start at `001`. Skip the git steps cleanly in a non-git repo or when offline (treat the source as empty).

4. **Resolve the default branch.** Same logic used by `ship` and `cleanup`, executed once and reused:
   - `git symbolic-ref refs/remotes/origin/HEAD` → parse `refs/remotes/origin/<name>` and take `<name>`.
   - Fall back to `main`, then `master`.

5. **Pre-flight gitignore check** — verify `.minerva/worktrees/` is ignored on `<default-branch>`. Check the default branch's `.gitignore` (not just the current working tree's) via `git show <default-branch>:.gitignore 2>/dev/null` and grep for a line matching `.minerva/worktrees/` (or a parent pattern like `.minerva/`).

   - If present → continue.
   - If missing → **abort**: "The `.minerva/worktrees/` entry is missing from `.gitignore` on `<default-branch>`. Run `minerva:init` first to install it (init handles this idempotently), or add `.minerva/worktrees/` to `.gitignore` and commit on `<default-branch>` manually before re-running `minerva:propose`."

   Do not auto-edit `.gitignore` from propose: propose may be invoked from inside another worktree, where editing `.gitignore` would land the change on the wrong branch. Init is the one place that installs this entry.

6. **Create the worktree and branch:**

   ```
   git worktree add -b <NNN-slug> .minerva/worktrees/<NNN-slug> <default-branch>
   ```

   Branching explicitly from `<default-branch>` (not HEAD) prevents accidentally stacking the new work unit on top of another in-flight branch when propose is invoked from another worktree. The branch name uses the `NNN-` prefix so reviewers can tie a branch to its work unit number, and so propose's own NNN-collision scan picks up in-flight worktrees by branch.

7. **Address the worktree directly — do *not* call `EnterWorktree`.** minerva worktrees live under `.minerva/worktrees/`, which the `EnterWorktree` tool does not reliably enter (its contract only switches into worktrees under `.claude/worktrees/`), so minerva never uses it. The session's working directory stays the parent repo. For every remaining step, prefix each file path with `.minerva/worktrees/<NNN-slug>/` and run each git command as `git -C .minerva/worktrees/<NNN-slug> …`. Relative paths resolve to the parent repo and will silently land edits on the wrong branch (see `.minerva/knowledge/008-constraint-enter-worktree-absolute-paths.md`).

8. **Create the work-unit directory** `.minerva/work/<NNN-slug>/`, addressed via the step-7 prefix (i.e. `.minerva/worktrees/<NNN-slug>/.minerva/work/<NNN-slug>/`).

9. **Write `proposal.md`** using the approved content, structured as:

   ```markdown
   # Proposal: <slug>

   **Date**: YYYY-MM-DD
   **Status**: Draft

   ## Goal
   <approved goal>

   ## Why
   <approved motivation>

   ## Approach
   <approved approach — will be rewritten by minerva:promote to describe what shipped>

   ## Success criteria
   - <concrete, checkable item 1>
   - <concrete, checkable item 2>
   <each item must be objectively answerable yes/no when implementation is "done">

   ## Open Questions
   - <any remaining items>
   ```

   Also write `scratchpad.md` with this header and nothing else:

   ```markdown
   # Scratchpad: <slug>

   > **Ephemeral working memory.** Most of what lands here is noise — small
   > decisions that don't matter, dead ends, momentary confusion. At feature
   > completion, run `minerva:promote`: significant items get promoted to
   > `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
   > the raw scratchpad is archived.

   ```

10. **Self-review the written proposal.** Re-read `proposal.md` with fresh eyes and fix inline:
    - **Placeholders** — any `TBD`, `TODO`, vague phrasing, or incomplete sections.
    - **Internal consistency** — does `## Approach` actually achieve `## Goal`? Do `## Success criteria` cover what `## Goal` promises?
    - **Ambiguity** — could any requirement be read two different ways? Pick one and make it explicit.
    - **Scope** — is this still a single work unit, or did the prose drift into multi-unit territory? If the latter, stop and re-decompose with the user.

    Fix issues inline. No need to re-review — just fix and move on.

11. **Commit the initial docs on the branch:**

    ```
    git -C .minerva/worktrees/<NNN-slug> add .minerva/work/<NNN-slug>/
    git -C .minerva/worktrees/<NNN-slug> commit -m "chore: initialize <NNN-slug> work unit"
    ```

    (In a non-git repo, skip this step — there's no branch to commit on.)

12. **Post-write user gate.** Report the created path and ask:

    > "Proposal written to `.minerva/work/<NNN-slug>/proposal.md` on branch `<NNN-slug>` in worktree `.minerva/worktrees/<NNN-slug>/`. Please review the file directly and let me know if you want to change anything before we start work."

    Wait for the user's response. If they request changes, edit `proposal.md` directly, re-run the self-review, and create a **follow-up commit** (no `--amend` — the initial commit was already published as the branch's starting state). Only once the user approves the written file is the proposal considered final.

13. Suggest `minerva:work` as the next step. The work skill will detect the existing worktree and address it by the same prefix.


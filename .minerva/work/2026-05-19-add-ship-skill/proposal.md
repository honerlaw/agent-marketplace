# Proposal: add-ship-skill

**Date**: 2026-05-19
**Status**: Shipped

## Goal

Added `minerva:ship` — a skill that closes the minerva lifecycle by committing outstanding work to a branch (creating one if currently on the default branch), opening a PR titled and described from the active work unit's `proposal.md`, watching CI to green with a bounded auto-fix loop (3 iterations), and enabling auto-merge when repo permissions allow.

## Why

- The minerva lifecycle previously ended at `minerva:promote` / `minerva:review` — the user was left to push, open, watch, and merge by hand, or fall back to the generic `ship-it` skill from elsewhere.
- The generic `ship-it` skill knows nothing about minerva: branch names don't reference the work unit, PR bodies don't pull from `proposal.md`, and the closing summary doesn't reflect minerva state.
- A minerva-aware ship phase derives everything (branch name, PR title, PR body) from the active work unit silently, with no extra prompting.
- Bounded CI auto-fix is the real time-saver: most CI failures on freshly opened branches are lint / format / type errors that the agent can patch and re-push without human attention.

## Approach

`plugins/minerva/skills/ship/SKILL.md` defines the full protocol. The skill:

1. **Resolves the target work unit** by current-session inference → most-recently-modified `.minerva/work/NNN-*/` → ambiguity prompt → bare-mode fallback when no work unit is found. Bare mode is a first-class path, not an error.
2. **Resolves the default branch once** (`git symbolic-ref refs/remotes/origin/HEAD` → `main` → `master`) in a dedicated section and reuses the result across pre-flight, branch creation, and the branch-vs-default diff — avoiding the footgun of repeating the detection rule at each call site.
3. **Runs pre-flight checks** and bails on any failure with a one-line message: in a git repo, `gh` CLI available and authenticated, something to ship (uncommitted changes or commits ahead of default), and not a no-op (default branch, zero commits ahead, clean tree).
4. **Creates a branch** named `<NNN>-<slug>` (or `claude/<slug-from-recent-commit-or-timestamp>` in bare mode) **only when currently on the default branch**; otherwise ships from the existing branch unchanged.
5. **Commits outstanding changes** with a HEREDOC commit message drafted from scratchpad highlights + `## Goal` + filenames. When `scratchpad.md` is the post-`minerva:promote` one-line marker (the canonical empty state — see `.minerva/knowledge/003-constraint-post-promote-scratchpad-canonical-empty.md`), the draft falls back to `## Goal` + filenames only. The commit message is the only **hard gate** in the protocol — shown for confirmation. `git add` always uses specific paths, never `-A`.
6. **Opens a PR** via `gh pr create` with a HEREDOC body — but first checks `gh pr view --json url,number,state`: if an OPEN PR already exists on the branch, reuses it and jumps straight to the CI loop instead of erroring on re-create. Title is `## Goal`'s first sentence truncated to ~70 chars; body has `## Summary` (from `## Why` + scratchpad) and `## Test plan` sections, with a footer linking to `.minerva/work/NNN-<slug>/proposal.md`. Bare-mode PR body is built from `git log` of branch-vs-default.
7. **Watches CI with a bounded auto-fix loop** capped at 3 iterations. Each iteration: `gh pr checks --watch` → on failure, fetch logs via `gh run view --log-failed`, classify into `format` / `lint` / `typecheck` / `test` / `build` / `other`, attempt fix only when the cause is clearly local (formatter diff, lint patch, missing import, etc.), commit as a **new** commit, push, loop. After the cap or on any non-trivial failure → report and stop without enabling auto-merge.
8. **Enables auto-merge** once checks are green via `gh pr merge --auto`, preferring `--squash` then `--merge` then `--rebase` based on repo settings detected through `gh repo view --json mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed`. On permission failure → leave PR open and report.
9. **Reports** branch, PR URL, CI state, auto-merge status, and a context-specific suggested next step.
10. **Surfaces lifecycle nudges only** — never auto-runs `minerva:promote` or `minerva:review`. If the scratchpad has unpromoted entries, suggests promote first; if review hasn't obviously run, suggests review first. Both are warnings, never blockers.
11. **Stateless and re-run safe** — does not write a metadata file or append a `## Shipped` marker to the scratchpad. The existing-PR detection in step 6 is what makes the Idempotency section's promise actually load-bearing: re-running ship on a branch with an open PR reuses the existing PR.
12. **Worktree-neutral** — ships from wherever invoked, including `.minerva/worktrees/` worktrees.

Documentation and structural tests landed alongside the skill:

- `plugins/minerva/README.md` — added `minerva:ship` to the skills table and to the typical-flow diagram.
- `plugins/minerva/skills/using-minerva/SKILL.md` — added ship to the detection list, the decision matrix, and a common scenario; updated the "six skills" wording to "seven skills".
- `README.md` (root) — added `minerva:ship` to the minerva row.
- `tests/test_minerva.py` — new `test_ship_skill_exists_with_frontmatter` asserts the SKILL.md exists with frontmatter, references `proposal.md`, uses `gh pr create` + `gh pr merge --auto`, describes branch creation with `git checkout -b`, names "bare mode", caps the CI loop at "3 iteration", nudges to `minerva:promote` and `minerva:review`, falls back via "most-recently-modified", **mentions `gh pr view` (existing-PR check), defines a "Default-branch detection" section, and handles the post-promote scratchpad marker explicitly** — pinning the three review-fix elements against regression. Existing tests for the root README, plugin README, and using-minerva were extended to require `minerva:ship`. All 14 tests pass.

## Open Questions

All resolved during proposal:

- **CI fix iteration limit** → 3 iterations. Tunable later if it proves wrong in practice.
- **Scratchpad → ship summary** → stateless. No `## Shipped` marker, no review-style log file. PR URL on GitHub is the source of truth.
- **Strict mode** (turn nudges into hard blockers) → skipped for v1. Users who want strict ordering can just run the skills in order.
- **Worktree awareness** → ship from wherever invoked. No special-casing for `.minerva/worktrees/`.

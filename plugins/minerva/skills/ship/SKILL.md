---
name: ship
description: Use when the user invokes `minerva:ship`, asks to ship / push / open a PR for / merge the current work, or wants the agent to commit outstanding changes to a branch, open a pull request, watch CI, fix CI failures, and enable auto-merge. Closes the minerva lifecycle after `minerva:work` / `minerva:promote` / `minerva:review`.
---

Close the minerva lifecycle by committing outstanding work to a branch, opening a PR titled and described from the active work unit's `proposal.md`, watching CI to green with a bounded auto-fix loop, and enabling auto-merge when repo permissions allow.

## Usage

- `minerva:ship` — ships the work unit inferred from current-session context, or the most-recently-modified if context is ambiguous, or runs in **bare mode** if no work unit is found

## Target resolution

Same pattern as `minerva:replan`, `minerva:work`, `minerva:promote`, and `minerva:review`:

1. Check current-session chat history for a mentioned work unit. If one is clearly referenced, use it.
2. Fall back to the most-recently-modified `.minerva/work/NNN-*/` by directory mtime.
3. If multiple candidates exist and context is ambiguous, list them and ask the user which to target.
4. `.minerva/work/` missing, empty, or no work-unit context can be confidently inferred → run in **bare mode**: ship from git state alone, no proposal-derived PR title/body.

Bare mode is a first-class fallback, not an error path. Users may want `minerva:ship` for routine work outside a tracked unit.

## Default-branch detection

Several steps below reference "the default branch". Resolve it **once** at the start of the run using this sequence and reuse the result:

1. `git symbolic-ref refs/remotes/origin/HEAD` — parse out `refs/remotes/origin/<name>` and take `<name>`.
2. If that fails, fall back to `main`.
3. If `main` doesn't exist locally or on the remote, fall back to `master`.

Use the same resolved value in pre-flight, branch creation, and the branch-vs-default diff for PR-body construction.

## Pre-flight checks

Bail with a clear, one-line message on any failure:

1. **Git repo.** `git rev-parse --is-inside-work-tree` returns true.
2. **`gh` CLI available and authenticated.** `gh auth status` exits 0.
3. **Something to ship.** At least one of:
   - `git status --porcelain` is non-empty (staged, unstaged, or untracked changes), or
   - the current branch has commits ahead of the default branch.
4. **Not a no-op.** If currently on the default branch with zero commits ahead and no local changes, there is nothing to ship — stop.

## Branch creation

Only if currently on the default branch (see **Default-branch detection** above):

1. Derive the branch name:
   - Work-unit mode: `<NNN>-<slug>` (e.g. `006-add-ship-skill`).
   - Bare mode: `claude/<slug-from-recent-commit-or-timestamp>`.
2. `git checkout -b <branch>`.

If already on a non-default branch, **do not switch branches** — ship from where you are. The user picked this branch on purpose.

## Commit outstanding changes

Only if `git status --porcelain` is non-empty:

1. Build a one-paragraph commit-message draft from:
   - Scratchpad highlights (skim `scratchpad.md` for bullets, especially anything that looks decision-flavored).
   - `## Goal` from `proposal.md`, truncated to one sentence.
   - List of filenames changed.
   In bare mode, use the diff and recent commit messages as the source.

   If `scratchpad.md` is the post-promote one-line marker (`Summarized at minerva:promote on YYYY-MM-DD — see archive/.`), that's the canonical post-`minerva:promote` state and means there's nothing to skim. Fall back to `## Goal` + filenames only.
2. **Hard gate for the commit message only.** Show the draft and prompt the user to redirect or accept.
3. `git add` with **specific file paths** (never `-A` or `.`) for tracked changes and untracked files the user wants included.
4. `git commit -m "$(cat <<'EOF' ... EOF)"` using a HEREDOC for clean formatting. Honor the project's git footer conventions if any are visible in recent commits.

If nothing is uncommitted, skip this step entirely.

## Push & open PR

1. `git push -u origin <branch>` (or just `git push` if upstream is already set).
2. **Check for an existing PR** on this branch: `gh pr view --json url,number,state 2>/dev/null`. If a PR already exists and is `OPEN`, **skip steps 3–5** and jump straight to the **CI watch & auto-fix loop** using the existing PR URL. Report that the existing PR was reused. (`MERGED` or `CLOSED` → proceed to create a new PR as normal.) This is what makes the Idempotency promise below load-bearing — re-running ship on the same branch must not error out on `gh pr create`.
3. **PR title.** First sentence of `## Goal` from `proposal.md`, truncated to ~70 chars. Bare mode: branch name humanized, or the most recent commit subject.
4. **PR body**, built with a HEREDOC:

   ```
   ## Summary
   <bullets derived from proposal's ## Why and scratchpad highlights>

   ## Test plan
   <bullets — surface anything the proposal mentioned about testing;
    otherwise a generic checklist of "run tests / manually verify X / etc.">

   ---
   Tracked in `.minerva/work/NNN-<slug>/proposal.md`
   ```

   Bare-mode body is built from `git log` of branch-vs-default (no footer).
5. `gh pr create --title "<title>" --body "$(cat <<'EOF' ... EOF)"`. Capture the returned PR URL.

## CI watch & auto-fix loop

Bounded at **3 iterations**. After the cap, report state and stop without enabling auto-merge.

For each iteration:

1. **Watch.** `gh pr checks --watch` blocks until all required checks complete. Some repos use `gh run watch` per workflow run — either is fine.
2. **Green?** Exit the loop and proceed to auto-merge.
3. **Failed?** Fetch failing job logs:
   - `gh run view --log-failed` for the failing run, or
   - `gh pr checks` + `gh run view <run-id> --log-failed` per failing check.
4. **Classify the failure family.** One of:
   - `format` — formatter diff (prettier, ruff format, gofmt, etc.)
   - `lint` — linter rules (eslint, ruff check, golangci-lint, etc.)
   - `typecheck` — type errors (tsc, pyright, mypy, etc.)
   - `test` — test failures
   - `build` — compile / bundle errors
   - `other` — anything that doesn't cleanly fit, including infra/auth/network failures
5. **Attempt fix** per family:
   - `format` → re-run the formatter locally, commit the diff.
   - `lint` → patch the specific lint errors cited in the log.
   - `typecheck` → patch the specific type errors cited in the log.
   - `test` → only attempt if the failure is clearly local (snapshot mismatch with an obvious fix, missing import, off-by-one). Bail to user otherwise.
   - `build` → only attempt if the cause is obvious (missing dep, syntax). Bail to user otherwise.
   - `other` → always bail to user.
6. **Commit & push.** Create a **new commit** (never `--amend` — the previous push already published it). Push to the PR branch. Loop back to step 1.
7. **Bail on cap or non-trivial failure.** Print the failing check, the log excerpt, and the suggested manual next step. Do **not** enable auto-merge.

## Auto-merge

Once checks are green:

1. Detect the repo's merge strategy:

   ```
   gh repo view --json mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed
   ```

   Prefer `--squash`, fall back to `--merge`, then `--rebase`.
2. `gh pr merge --auto <strategy> <pr-number>`. If the PR is already mergeable and protections permit, GitHub merges immediately; otherwise it merges as soon as required checks pass.
3. On permission failure (no write access, repo doesn't allow auto-merge, branch protection blocks it) → report it cleanly, leave the PR open with checks green. The user can merge manually.

## Final report

After all steps, print:

```
Branch:        <branch name>
PR:            <url>
CI:            green | failing | pending
Auto-merge:    enabled | declined by repo | not attempted (CI not green)
Next:          <recommendation>
```

The recommendation:

- Auto-merge enabled and CI green → "GitHub will merge when checks pass. Nothing else to do."
- Auto-merge declined by repo → "Merge manually when ready: `gh pr merge <pr-number>`."
- CI failed after 3 fix iterations → "Investigate the failure manually; the fix loop bailed."
- CI still pending → "Watch with `gh pr checks --watch`."

## Lifecycle nudges

`minerva:ship` does **not** run `minerva:promote` or `minerva:review` for the user. It surfaces nudges, not blockers:

- If `scratchpad.md` contains entries that look unpromoted (i.e. it's not just the empty header) → "Consider running `minerva:promote` before shipping so the PR body picks up durable knowledge."
- If `minerva:review` has not obviously been run for this branch (no review-derived scratchpad entries, no recent review commits) → "Consider running `minerva:review` before shipping."

Surface both nudges as part of the initial summary, then proceed. The user can ship and skip — strict ordering is not enforced.

## Worktree handling

Ship from wherever the user invokes the skill. If invoked inside a `.minerva/worktrees/` worktree, ship from that worktree — `git`, `gh`, and branch state are already correct there. No special-casing.

## Idempotency

Ship does not write its own metadata file or append a `## Shipped` marker to `scratchpad.md`. The PR URL lives on GitHub; nothing minerva-side needs to remember it. Re-running on a branch that already has an open PR will detect that (`gh pr view`) and pick up at the CI-watch step instead of re-creating.

## Out of scope

- **Writing to `.minerva/knowledge/` directly.** All durable knowledge goes through `minerva:promote`.
- **Running `minerva:promote` or `minerva:review` automatically.** Only nudges, never auto-invokes — keeps the user in control of what gets promoted and reviewed.
- **A strict mode** that turns nudges into hard blockers. Deferred; users who want strict ordering can run the skills in order themselves.
- **Replacing `ship-it` for non-minerva projects.** This skill assumes a `.minerva/` project or runs in explicit bare mode; the generic `ship-it` skill is still the right tool when the user is not in a minerva project.

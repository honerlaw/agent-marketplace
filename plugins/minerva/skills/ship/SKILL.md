---
name: ship
description: Use when the user invokes `minerva:ship`, asks to ship / push / open a PR for / merge the current work, or wants the agent to commit outstanding changes to a branch, open a pull request, watch CI, fix CI failures, and enable auto-merge. CI is watched via ScheduleWakeup polling instead of blocking. Closes the minerva lifecycle after `minerva:work` / `minerva:promote` / `minerva:review`.
---

Close the minerva lifecycle by committing outstanding work to a branch, opening a PR titled and described from the active work unit's `proposal.md`, watching CI to green with a bounded auto-fix loop (3 iterations) via ScheduleWakeup polling, and enabling auto-merge when repo permissions allow.

## Usage

- `minerva:ship` — ships the work unit inferred from current-session context, or the most-recently-modified if context is ambiguous, or runs in **bare mode** if no work unit is found
- `minerva:ship 005-add-payments` — ship the named unit explicitly

## Target resolution

Same pattern used by `minerva:work`, `minerva:replan`, `minerva:promote`, `minerva:review`, `minerva:cleanup`. **Keep all six blocks in sync if you edit one.**

1. **Explicit argument** — slug or path. Look in both `.minerva/work/<NNN-slug>/` and `.minerva/worktrees/<NNN-slug>/.minerva/work/<NNN-slug>/`.
2. **Current-session context** — explicit mention in this session.
3. **Most-recently-modified across both locations** — scan `.minerva/work/NNN-*/` AND `.minerva/worktrees/NNN-*/.minerva/work/NNN-*/` by directory mtime.
4. **Ambiguity** → list candidates, ask.
5. **None found** → run in **bare mode**: ship from git state alone, no proposal-derived PR title/body. Bare mode is a first-class fallback, not an error path.

If the resolved work unit's docs live in a worktree (`.minerva/worktrees/NNN-slug/.minerva/work/NNN-slug/`) and the current shell is not in that worktree, prefer entering the worktree before shipping (its branch is already set up correctly). If the user is intentionally on a different branch, ship from there and warn that the PR body will not reflect the work-unit proposal.

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

Only if currently on the default branch:

1. Derive the branch name:
   - Work-unit mode: `<NNN>-<slug>` (e.g. `006-add-ship-skill`).
   - Bare mode: `<git-user>/<slug-from-recent-commit-or-timestamp>`, where `<git-user>` is taken from `git config user.email` (local part before `@`) or `git config user.name` lowercased; fall back to `work` if neither is set. Avoids hardcoding any single agent identity into branch names.
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
2. **Hard gate #1 (commit message).** Show the draft and prompt the user to redirect or accept.
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
5. **Hard gate #2 (PR title + body).** Show the proposed title and body block and prompt the user to redirect or accept. The user can edit either in place. Routine work can accept with one word ("ok"); bigger changes get a real preview.
6. `gh pr create --title "<title>" --body "$(cat <<'EOF' ... EOF)"`. Capture the returned PR URL.

## CI watch & auto-fix loop (ScheduleWakeup polling)

Bounded at **3 fix iterations**. The loop does **not** block the agent — between checks, the session can do other work or end and be re-entered.

### Polling cadence

1. Immediately after `gh pr create` (or detecting an existing OPEN PR), run `gh pr checks --json name,state,conclusion` once to get the initial state.
2. If any check is still `IN_PROGRESS` / `QUEUED` / `PENDING`, schedule the next check via `ScheduleWakeup` with `delaySeconds: 270` (stays under the 5-minute prompt-cache TTL — see ScheduleWakeup docs). The wake-up `prompt` re-invokes `minerva:ship` for the same work unit.
3. Each subsequent wake re-runs `gh pr checks --json …` once. **Do not** stack multiple sleeps inside a single session — one schedule per wake-up.
4. If all checks have `state: COMPLETED` → proceed to result handling.

### Result handling per fix iteration

Once checks are no longer pending:

1. **All green** → exit the watch loop, proceed to auto-merge.
2. **At least one failed** → fetch failing job logs:
   - `gh run view --log-failed` for the failing run, or
   - `gh pr checks` + `gh run view <run-id> --log-failed` per failing check.
3. **Classify the failure family.** One of:
   - `format` — formatter diff (prettier, ruff format, gofmt, etc.)
   - `lint` — linter rules (eslint, ruff check, golangci-lint, etc.)
   - `typecheck` — type errors (tsc, pyright, mypy, etc.)
   - `test` — test failures
   - `build` — compile / bundle errors
   - `other` — anything that doesn't cleanly fit, including infra/auth/network failures
4. **Attempt fix** per family:
   - `format` → re-run the formatter locally, commit the diff.
   - `lint` → patch the specific lint errors cited in the log.
   - `typecheck` → patch the specific type errors cited in the log.
   - `test` → only attempt if the failure is clearly local (snapshot mismatch with an obvious fix, missing import, off-by-one). Bail to user otherwise.
   - `build` → only attempt if the cause is obvious (missing dep, syntax). Bail to user otherwise.
   - `other` → always bail to user.
5. **Bail conditions** — stop and report (do NOT enable auto-merge) when:
   - Fix iterations hit the cap (3).
   - The fix itself introduces git conflicts that can't be resolved cleanly.
   - The failure family is `other` or a non-trivial `test`/`build`.
6. **Commit & push.** Create a **new commit** (never `--amend` — the previous push already published it). Push to the PR branch. Schedule the next watch wake-up (delaySeconds: 270) and exit this turn. The next wake handles re-checking.

### Track iteration count across wakes

Persist the iteration count in the wake-up `prompt` payload (e.g. `minerva:ship 005-add-payments --watch-iteration=2`) so the loop bound holds across wake-ups. Reset on a fresh `minerva:ship` invocation.

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
CI:            green | failing | pending (will re-check at <timestamp>)
Auto-merge:    enabled | declined by repo | not attempted (CI not green)
Next:          <recommendation>
```

The recommendation:

- Auto-merge enabled and CI green → "GitHub will merge when checks pass. Run `minerva:cleanup` afterward to remove the worktree."
- Auto-merge declined by repo → "Merge manually when ready: `gh pr merge <pr-number>`. Run `minerva:cleanup` after merge."
- CI failed after 3 fix iterations → "Investigate the failure manually; the fix loop bailed."
- CI still pending → "Next watch wake scheduled."

## Lifecycle nudges

`minerva:ship` does **not** run `minerva:promote` or `minerva:review` for the user. It surfaces nudges, not blockers:

- If `scratchpad.md` contains entries that look unpromoted (i.e. it's not just the post-promote marker) → "Consider running `minerva:promote` before shipping so the PR body picks up durable knowledge."
- If `minerva:review` has not obviously been run for this branch (no `## Review triage` blocks in scratchpad, no review-fix commits) → "Consider running `minerva:review` before shipping."

Surface both nudges as part of the initial summary, then proceed. The user can ship and skip — strict ordering is not enforced.

## Worktree handling

Ship from wherever the user invokes the skill. If invoked inside a `.minerva/worktrees/` worktree, ship from that worktree — `git`, `gh`, and branch state are already correct there. If the work unit lives in a worktree but the user is elsewhere, prefer suggesting they enter the worktree first (see [Target resolution](#target-resolution)).

After merge, the worktree and its branch should be cleaned up via `minerva:cleanup` — `ship` does not delete them automatically since CI may still be running asynchronously.

## Idempotency

Ship does not write its own metadata file or append a `## Shipped` marker to `scratchpad.md`. The PR URL lives on GitHub; nothing minerva-side needs to remember it. Re-running on a branch that already has an open PR will detect that (`gh pr view`) and pick up at the CI-watch step instead of re-creating.

Wake-ups re-invoke `minerva:ship`; the skill detects the existing PR and resumes the watch loop using the iteration count carried in the wake-up prompt.

## Out of scope

- **Writing to `.minerva/knowledge/` directly.** All durable knowledge goes through `minerva:promote`.
- **Running `minerva:promote` or `minerva:review` automatically.** Only nudges, never auto-invokes — keeps the user in control of what gets promoted and reviewed.
- **Worktree cleanup.** Owned by `minerva:cleanup`.
- **A strict mode** that turns nudges into hard blockers. Deferred; users who want strict ordering can run the skills in order themselves.
- **Replacing `ship-it` for non-minerva projects.** This skill assumes a `.minerva/` project or runs in explicit bare mode; the generic `ship-it` skill is still the right tool when the user is not in a minerva project.

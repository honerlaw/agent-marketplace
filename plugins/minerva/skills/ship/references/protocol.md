# ship — full step protocols

## Target resolution

Same pattern used by `minerva:work`, `minerva:replan`, `minerva:promote`, `minerva:review`, `minerva:cleanup`. **Keep all six blocks in sync if you edit one.**

1. **Explicit argument** — slug or path. Look in both `.minerva/work/<NNN-slug>/` and `.minerva/worktrees/<NNN-slug>/.minerva/work/<NNN-slug>/`.
2. **Current-session context** — explicit mention in this session.
3. **Most-recently-modified across both locations** — scan `.minerva/work/NNN-*/` AND `.minerva/worktrees/NNN-*/.minerva/work/NNN-*/` by directory mtime.
4. **Ambiguity** → list candidates, ask.
5. **None found** → run in **bare mode**: ship from git state alone, no proposal-derived PR title/body. Bare mode is a first-class fallback, not an error path.

## Worktree addressing

After resolving the target and before running any git commands:

- **Do not call `EnterWorktree`** — minerva worktrees live under `.minerva/worktrees/`, which that tool does not reliably enter; the session's working directory stays the parent repo.
- If the resolved target's docs live at `.minerva/worktrees/<NNN-slug>/.minerva/work/<NNN-slug>/`, run every git command for this skill as `git -C .minerva/worktrees/<NNN-slug> …` and prefix any file path with `.minerva/worktrees/<NNN-slug>/`. The work-unit branch is already checked out there, so branch detection, commit, push, and PR open all run against the correct branch automatically.
- If the docs live only on the default branch (a shipped unit being re-shipped — rare; usually a no-op anyway) or no minerva context was found (bare mode), do **not** address a worktree. Ship from whatever working tree the user invoked the skill from. If the user is intentionally on a different branch, warn that the PR body will not reflect the work-unit proposal.

## Default-branch detection

Several steps below reference "the default branch". Resolve it **once** at the start of the run using this sequence and reuse the result:

1. `git symbolic-ref refs/remotes/origin/HEAD` — parse out `refs/remotes/origin/<name>` and take `<name>`.
2. If that fails, fall back to `main`.
3. If `main` doesn't exist locally or on the remote, fall back to `master`.

Use the same resolved value in pre-flight, branch creation, and the branch-vs-default diff for PR-body construction.

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
2. **Hard gate #1 (commit message).** Show the draft and prompt the user to redirect or accept. (When an invoking skill or the user has pre-authorized non-interactive shipping, accept the draft without prompting — this applies to gate #2 as well.)
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

## CI watch & auto-fix loop (tracked watcher + durable fallback)

Bounded at **3 fix iterations**. The loop does **not** block the agent — between checks, the session can do other work or end and be re-entered.

### Sizing the wait

A wait is sized from what is actually being waited on, never from a constant. Measured CI durations differ by two orders of magnitude across repos this skill runs in (~10-26s in a docs/tests-only repo; ~1000s for a full CI suite), so any fixed cadence idles for minutes on one and burns wake-ups on the other.

1. Immediately after `gh pr create` (or detecting an existing OPEN PR), run `gh pr checks --json name,state,conclusion` once to get the initial state.
2. If any check is still `IN_PROGRESS` / `QUEUED` / `PENDING`, estimate how long this repo's CI actually takes:

   ```
   gh run list --workflow <name> --limit 10 --json createdAt,updatedAt,conclusion
   ```

   Take the **maximum** elapsed time among recent completed runs. A max over a small window, not a percentile — observed per-repo variance is tight, so percentile machinery is not earned. No history (new workflow) → treat the estimate as 600s.

### Waiting

Run both of the following. They are complements, not alternatives.

3. **Tracked watcher (resume-when-settled).** Start a backgrounded `until` loop via `Bash` with `run_in_background: true` that re-checks every 30s and exits once nothing is pending:

   ```bash
   # MAX_POLLS = min(120, ceil(2 * estimate_seconds / 30)) — substitute the number.
   for _ in $(seq MAX_POLLS); do
     gh pr checks <pr> --json bucket --jq 'all(.[]; .bucket != "pending")' | grep -qx true && break
     sleep 30
   done
   ```

   The harness re-invokes you when it exits, so the run resumes when CI genuinely settles rather than at an arbitrary poll boundary. The loop is **bounded on purpose** — `2 ×` the estimate, hard-capped at 120 polls (~60 min) — so a check wedged in `pending` cannot leave a process looping forever; write the bound into the command rather than relying on the watcher being killed. Poll no faster than 30s: `gh` is a remote API with rate limits.

   This does *not* make CI itself harness-tracked; only the wrapper process is. The benefit is resume latency, nothing more.
4. **Durable fallback (always armed).** Independently schedule one `ScheduleWakeup` at `max(1200, estimate)`, clamped to `[60, 3600]`, whose `prompt` re-invokes `minerva:ship` for the same work unit. Arm it *even when* step 3 is running: it is what survives a watcher that dies, a wedged check, or a session that ends — the property this section's opening sentence promises. Long interval by design, so it stays a safety net rather than a poll.
5. Whichever path resumes you, re-run `gh pr checks --json …` **once**. **Do not** stack sleeps or arm a second watcher for the same wait.
6. If all checks have `state: COMPLETED` → proceed to result handling.

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
6. **Commit & push.** Create a **new commit** (never `--amend` — the previous push already published it). Push to the PR branch. Re-enter the watch per **Waiting** above (re-size the estimate — a fix push starts a fresh run) and exit this turn. Whichever path resumes you handles the re-check.

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

The [Worktree addressing](#worktree-addressing) section above handles entering the work unit's worktree before any git operations run. Once entered, the branch and remote tracking are already set up by `minerva:propose`, so the rest of ship works against the correct state automatically.

After merge, the worktree and its branch should be cleaned up via `minerva:cleanup` — `ship` does not delete them automatically since CI may still be running asynchronously.


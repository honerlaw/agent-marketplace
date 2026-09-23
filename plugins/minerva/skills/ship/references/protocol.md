# ship — full step protocols

## Target resolution

Same pattern used by `minerva:work`, `minerva:replan`, `minerva:promote`, `minerva:review`, `minerva:cleanup`. **Keep all six blocks in sync if you edit one.**

1. **Explicit argument** — slug or path. Look in both `.minerva/work/<date-slug>/` and `.minerva/worktrees/<date-slug>/.minerva/work/<date-slug>/`.
2. **Current-session context** — explicit mention in this session.
3. **Most-recently-modified across both locations** — scan `.minerva/work/*/` AND `.minerva/worktrees/*/.minerva/work/*/` by directory mtime. Match **both** id forms — `YYYY-MM-DD-<slug>` and legacy `NNN-<slug>`; a digit-anchored glob misses date-named units entirely.
4. **Ambiguity** → list candidates, ask.
5. **None found** → run in **bare mode**: ship from git state alone, no proposal-derived PR title/body. Bare mode is a first-class fallback, not an error path.

## Worktree addressing

After resolving the target and before running any git commands:

- **Do not call `EnterWorktree`** — minerva worktrees live under `.minerva/worktrees/`, which that tool does not reliably enter; the session's working directory stays the parent repo.
- If the resolved target's docs live at `.minerva/worktrees/<date-slug>/.minerva/work/<date-slug>/`, run every git command for this skill as `git -C .minerva/worktrees/<date-slug> …` and prefix any file path with `.minerva/worktrees/<date-slug>/`. The work-unit branch is already checked out there, so branch detection, commit, push, and PR open all run against the correct branch automatically.
- If the docs live only on the default branch (a shipped unit being re-shipped — rare; usually a no-op anyway) or no minerva context was found (bare mode), do **not** address a worktree. Ship from whatever working tree the user invoked the skill from. If the user is intentionally on a different branch, warn that the PR body will not reflect the work-unit proposal.

## Checkpoint entry

Before advancing this shipping run, read its checkpoint using the runtime
contract. Resolve the unit working tree and live branch/PR first. Validate any
saved caller against explicit `--auto`; restore counters from this run without
resetting them. An explicit `--watch-iteration` cannot lower the saved count.
Missing legacy state uses the existing PR and explicit retry/log evidence;
unknown budget usage requires recovery. Bare mode uses the runtime contract's
branch-derived key and never interprets it as a work unit.

After creating/reusing a PR, write phase `ship`, status `pending`, its PR number,
branch, caller, and current counters. Checkpoint each attempted fix before
performing it and before every wait/yield. Before returning to cleanup, write
phase `cleanup`; only confirmed completion/reconciliation marks this run done.
Never include checkpoint files in `git add` or commit messages.

## Phase resolution

Run this immediately after worktree addressing, and **skip it entirely in bare mode**.

Read the resolved unit's `proposal.md`. If it has **no `## Phases` section the unit is unphased**
— which is the normal case — and nothing in this section applies: ship exactly as before. Do not
invent phases for a unit that did not declare them.

If it *is* phased, resolve which phase this run is shipping. Never rebuild the branch names by
hand; ask the module that owns them:

```bash
# The PRIMARY checkout, resolvable from any CWD. `--show-toplevel` returns the LINKED
# worktree when invoked inside one, and these paths reach *into* .minerva/worktrees/.
ROOT="$(cd "$(dirname "$(git rev-parse --git-common-dir)")" && pwd)"
PLUGIN_SCRIPTS="$(python3 "$MINERVA_PLUGIN_ROOT/scripts/minerva_runtime.py" resolve --skill-file "$MINERVA_SKILL_FILE")" || exit 1
[ -n "$PLUGIN_SCRIPTS" ] && { python3 "$PLUGIN_SCRIPTS/plugin_guard.py" || exit 1; }
WT="$ROOT/.minerva/worktrees/<date-slug>"        # the unit's worktree, addressed by prefix
python3 -c "
import subprocess, sys; sys.path.insert(0, sys.argv[1])
from work_status import read_phases, phase_progress, phase_name
slug = '<date-slug>'
merged = subprocess.run(['git','-C',sys.argv[2],'branch','--merged','<default-branch>',
                         '--format=%(refname:short)'],
                        capture_output=True, text=True).stdout.split()
phases = read_phases(open(sys.argv[3]).read())
state = phase_progress(phases, merged, slug)
print(state, [phase_name(t) for n, t in phases if n >= (state['next_position'] or 1)])
" "$PLUGIN_SCRIPTS" "$WT" "$WT/.minerva/work/<date-slug>/proposal.md"
```

**Both paths are anchored, not CWD-relative**, and that is load-bearing twice over:

- The scripts path uses the installed plugin runtime resolver (`minerva:lint`,
  `minerva:migrate-fix`, and `minerva:cleanup` use the same resolver). A bare
  `sys.path.insert(0, 'scripts')` raises `ModuleNotFoundError` from any subdirectory
  (`2026-06-03-constraint-skill-wraps-script-via-importable-api`).
- The proposal path carries the `$WT` prefix because **ship never enters the worktree** — the
  session's CWD stays the parent repo. Unprefixed, `.minerva/work/<date-slug>/proposal.md`
  either does not exist there yet (phase 1 of a new unit: the file lives only on the branch) or
  is a *stale merged copy* from an earlier phase. The stale-copy branch is the dangerous one:
  `read_phases` succeeds, `phase_progress` returns a wrong `next_branch`, and ship targets the
  wrong phase without erroring.

**If this raises `ImportError: cannot import name 'read_phases'`,** update the installed Minerva package or explicitly choose a complete `MINERVA_SCRIPTS` directory. Never silently fall back to consumer code.

Use `--merged <default-branch>` against a **freshly fetched** default branch; a stale local ref
reports a phase as unmerged after its PR landed, which would try to re-ship it.

- `next_branch` is the branch this run ships. If the worktree is on a different branch, say so
  and stop rather than guessing — the user may be mid-phase deliberately.
- `complete` is true → every phase has merged. There is nothing to ship; report that and stop.
- Carry `merged`, `total` and the outstanding phase names into the [Final report](#final-report).

To **start** phase N (N≥2), cut its branch from the freshly fetched default branch inside the
unit's existing worktree — `proposal.md` and `scratchpad.md` arrive with it, because they merged
there with the previous phase:

```bash
git -C .minerva/worktrees/<date-slug> fetch origin <default-branch>
git -C .minerva/worktrees/<date-slug> checkout -b <date-slug>-phase-N origin/<default-branch>
```

Full rules — the soft ceiling, why phase 1 keeps the bare slug, and why progress is derived
rather than written — are in
`skills/propose/references/phasing.md`. **Read it before shipping any phase
other than the first.**

## Default-branch detection

Several steps below reference "the default branch". Resolve it **once** at the start of the run using this sequence and reuse the result:

1. `git symbolic-ref refs/remotes/origin/HEAD` — parse out `refs/remotes/origin/<name>` and take `<name>`.
2. If that fails, fall back to `main`.
3. If `main` doesn't exist locally or on the remote, fall back to `master`.

Use the same resolved value in pre-flight, branch creation, and the branch-vs-default diff for PR-body construction.

## Branch creation

Only if currently on the default branch:

1. Derive the branch name:
   - Work-unit mode: `<YYYY-MM-DD>-<slug>` (e.g. `006-add-ship-skill`). For a **phased** unit take `next_branch` from [Phase resolution](#phase-resolution) instead — phase 1 resolves to exactly this same bare name, so the two agree by construction rather than by coincidence.
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

   If `work_status.is_post_promote(scratchpad_text)` is true, the unit is in its post-`minerva:promote` state and there is nothing to skim — fall back to `## Goal` + filenames only. Use that predicate rather than comparing against the canonical marker string: the marker has had at least nine spellings, and a string match reads a validly-promoted unit as un-promoted.
2. **Hard gate #1 (commit message).** Show the draft and prompt the user to redirect or accept. (Under `--auto=<orchestrator>`, or when the user has pre-authorized non-interactive shipping, accept the draft without prompting — this applies to gate #2 as well.)
3. `git add` with **specific file paths** (never `-A` or `.`) for tracked changes and untracked files the user wants included.
4. `git commit -m "$(cat <<'EOF' ... EOF)"` using a HEREDOC for clean formatting. Honor the project's git footer conventions if any are visible in recent commits.

If nothing is uncommitted, skip this step entirely.

## Push & open PR

1. `git push -u origin <branch>` (or just `git push` if upstream is already set).
2. **Check for an existing PR** on this branch: `gh pr view --json url,number,state 2>/dev/null`. If a PR already exists and is `OPEN`, **skip steps 3–5** and jump straight to the **CI watch & auto-fix loop** using the existing PR URL. Report that the existing PR was reused. This is what makes the Idempotency promise below load-bearing — re-running ship on the same branch must not error out on `gh pr create`.

   - **`MERGED`, and the branch has no commits the PR did not carry** → this run is a stale re-entry (a watch fallback firing after the work already shipped). Report "already shipped as #N" and **exit without opening a PR**.
   - **`MERGED` with new local commits, or `CLOSED`** → proceed to create a new PR as normal; there is genuinely new work to ship.
3. **PR title.** First sentence of `## Goal` from `proposal.md`, truncated to ~70 chars. Bare mode: branch name humanized, or the most recent commit subject.
4. **PR body**, built with a HEREDOC:

   ```
   ## Summary
   <bullets derived from proposal's ## Why and scratchpad highlights>

   ## Test plan
   <bullets — surface anything the proposal mentioned about testing;
    otherwise a generic checklist of "run tests / manually verify X / etc.">

   Closes #12
   Closes #34

   ---
   Tracked in `.minerva/work/<date-slug>/proposal.md`
   ```

   **The `Closes` lines.** Read the proposal's optional `**Closes**: #N, #M` field and emit
   **one `Closes #N` line per entry** — GitHub only honours the keyword when each issue has
   its own reference, so a single `Closes #12, #34` closes just the first. Omit the block
   entirely when the field is absent, which is the common case.

   **Re-verify each entry against the diff before emitting it.** The field may have been written
   at intake, when the user adopted an open issue and no diff existed yet
   (`skills/propose/references/issue-match.md`), and ship is reached without
   `minerva:promote` often enough for that to matter — this skill nudges, it does not enforce
   ordering, and an autonomous orchestrator auto-accepts the PR-body gate below, so this is the
   last point anything checks. Drop an entry the diff does not resolve and say which, in the
   report. This is not inference in the sense the next paragraph forbids: dropping an unsupported
   claim leaves an issue open, the cheap failure, while the expensive one is closing an issue
   nothing resolved.

   The field is **authored**, never inferred: do not scan the diff, the branch name, or the
   commit log for issue numbers to close. A wrong auto-close destroys a real record, and a
   stale-open issue is the cheaper failure. If the work plainly closes an issue the field
   does not list, say so in the summary and leave the issue open for a human.

   Bare-mode body is built from `git log` of branch-vs-default (no footer, no `Closes`
   lines — bare mode has no proposal to read the field from).
5. **Hard gate #2 (PR title + body).** Show the proposed title and body block and prompt the user to redirect or accept. The user can edit either in place. Routine work can accept with one word ("ok"); bigger changes get a real preview.
6. Write the exact approved PR body to a temporary file, then run `gh pr create --title "<title>" --body-file <absolute-body-file>`. Capture the returned PR URL.

## CI watch & auto-fix loop (tracked watcher + durable fallback)

Bounded at **3 fix iterations**. The host adapter observes a tracked watcher while the session remains active. Before ending the session, checkpoint and arrange a supported scheduled resume or report an exact manual resume prompt.

The old fixed cadence (a wake-up every 270s) was wrong in both directions — measured CI runs ~10-26s in a docs/tests-only repo and ~1000s for a full suite — so it idled minutes on one and burned wake-ups on the other. Neither number is knowable in advance, so **do not guess an interval**: let `gh` tell you when checks settle, and keep one supported scheduled fallback underneath, or checkpoint for manual resumption.

**Check state with `bucket`, not `state`.** `gh pr checks --json` exposes `bucket`, which normalizes every check into `pass` / `fail` / `pending` / `skipping` / `cancel`. There is no `conclusion` field (requesting it is a hard error), and `state` carries values like `SUCCESS`, never `COMPLETED`. "Still running" means **some check has `bucket == "pending"`** — that phrasing, and only it, is used throughout this section.

1. Immediately after `gh pr create` (or on detecting an existing OPEN PR), run `gh pr checks <pr> --json name,state,bucket` once.
2. If nothing is `pending`, skip straight to result handling.

### Waiting

3. **Tracked watcher.** Use the tracked watcher operation in the host adapter:

   ```bash
   gh pr checks <pr> --watch --fail-fast
   ```

   In a live Codex session, observe the returned process through the available
   polling tool, keeping waits at or below 60 seconds. In Claude retain its
   background completion path where supported. Requery buckets on completion;
   the watch exit code is not a verdict. Never start a second concurrent watcher
   for the same wait. If an older `gh` rejects `--watch`, use an available scheduled
   fallback or checkpoint and report pending with a manual resume prompt.

4. **Resume fallback.** Save the checkpoint before waiting. If the host supports
   automatic re-entry, arm the scheduled resume operation at **1800s** with:

   ```
   minerva:ship <date-slug> --watch-iteration=<N> [--auto=<orchestrator>]
   ```

   **Carry `--auto=<orchestrator>` verbatim when it was passed.** Preserve
   `--watch-iteration` and all run counters. The long fallback complements a
   completion watcher; it is a re-arming keep-alive, not a CI-duration budget.
   If scheduling is unavailable and this session must end, report **pending**,
   render the exact host-correct resume prompt from the checkpoint, and stop.
   A detached process alone cannot resume an ended session.

5. **On resume, whichever path resumed you:** reread the checkpoint and live
   `gh pr checks <pr> --json name,state,bucket` once. Reuse existing PRs and check
   whether they merged or closed before taking any action.
   - **Nothing pending** → result handling below. Ignore already-completed stale
     signals; do not duplicate watchers, fixes or orchestrator handoffs.
   - **Still pending** → observe the existing live watcher, or start a new one
     only if none is live. Re-arm a supported scheduler; otherwise preserve the
     explicit pending/manual-resume fallback. Checkpoint before yielding.

### Result handling per fix iteration

Once checks are no longer pending:

1. **All green** (every bucket is `pass` or `skipping`, or no checks are configured) → exit the watch loop, proceed to auto-merge. `cancel`, unknown buckets, and check-query errors are not green; classify/escalate them rather than enabling auto-merge.
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
4. **Attempt fix** per family. Before starting an attempt, increment and save
   `fix_iteration` in the checkpoint; a failed/interrupted fix consumes the attempt.
   Never begin a fourth attempt. Then:
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
6. **Commit & push.** Create a **new commit** (never `--amend` — the previous push already published it). Push to the PR branch. Re-enter the watch per **Waiting** above (re-size the estimate — a fix push starts a fresh run) and continue observing the tracked watcher while this session is active. Before ending a turn, save progress and use either a supported scheduled resume or the explicit manual-resume fallback.

### Track iteration count across wakes

Persist the iteration count **and any `--auto=<orchestrator>`** in the wake-up `prompt` payload (e.g. `minerva:ship 005-add-payments --watch-iteration=2 --auto=propose-ship-auto`) so both the loop bound and the caller hold across wake-ups. A resume never resets the saved count. A genuinely new run/phase requires the completed-checkpoint transition in the runtime contract; a next declared phase uses `write --start-phase` to retain aggregate governance counters.

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
CI:            green | failing | pending (scheduled at <timestamp> | manual resume required)
Auto-merge:    enabled | declined by repo | not attempted (CI not green)
Phase:         2 of 3 — outstanding: 3. <name>        <- phased units only; omit the line entirely when unphased
Next:          <recommendation>
```

**The `Phase:` line is not optional on a phased unit, and it must name the outstanding phases,
not just count them.** A unit that stalls after phase 1 has to be visible as a unit that
stalled. A report that omits work it deferred lies by omission, and deferred work whose trigger
is never named is undetectable — both halves of
`2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption`, which was logged six times
in two days on this project, every one found by accident.

The recommendation:

- **Phased unit with phases outstanding** → "Phase N merged. Run `minerva:ship` again to start phase N+1 (`<next branch>`); `minerva:promote` waits for the final phase — use its Mode B for durable knowledge found meanwhile."
- Auto-merge enabled and CI green → "GitHub will merge when checks pass. Run `minerva:cleanup` afterward to remove the worktree."
- Auto-merge declined by repo → "Merge manually when ready: `gh pr merge <pr-number>`. Run `minerva:cleanup` after merge."
- CI failed after 3 fix iterations → "Investigate the failure manually; the fix loop bailed."
- CI still pending → state whether automatic re-entry is actually scheduled; otherwise print **pending — manual resume required** and the exact resume prompt.

**Under `--auto=<orchestrator>`, the report may not be the end of the run** — and which of the two
paths applies is decided by an observable fact, not a guess:

- **Resumed from a CI-watch wake-up** (this invocation carried `--watch-iteration`): the orchestrator's
  turn ended when the watch was armed, so its Phase 6 will never resume. Hand back by invoking
  `minerva:<orchestrator> --cleanup-only <date-slug>` via the skill loader — the re-entry all four
  orchestrators document, which skips phases 1-6 and runs their cleanup gate.
- **Returning synchronously** (no wake-up happened; the orchestrator's turn is still live): do **not**
  invoke it. Phase 6 continues to Phase 7 on its own, and invoking here as well runs the cleanup gate
  twice — a second `minerva:cleanup`, and potentially a second knowledge-reconciliation PR.

Either way, do not print the "Run `minerva:cleanup` afterward" recommendation: it addresses a human
who is not driving this run.

## Lifecycle nudges

`minerva:ship` does **not** run `minerva:promote` or `minerva:review` for the user. It surfaces nudges, not blockers:

- If `scratchpad.md` contains entries that look unpromoted (i.e. it's not just the post-promote state per `work_status.is_post_promote`) → "Consider running `minerva:promote` before shipping so the PR body picks up durable knowledge."
- If `minerva:review` has not obviously been run for this branch (no `## Review triage` blocks in scratchpad, no review-fix commits) → "Consider running `minerva:review` before shipping."

Surface both nudges as part of the initial summary, then proceed. The user can ship and skip — strict ordering is not enforced.

## Worktree handling

The [Worktree addressing](#worktree-addressing) section above handles entering the work unit's worktree before any git operations run. Once entered, the branch and remote tracking are already set up by `minerva:propose`, so the rest of ship works against the correct state automatically.

After merge, the worktree and its branch should be cleaned up via `minerva:cleanup` — `ship` does not delete them automatically since CI may still be running asynchronously.

On a **phased** unit the worktree survives between phases: `minerva:cleanup` defers teardown while any declared phase is unmerged, and phase N+1 is cut inside that same worktree. Running cleanup between phases is still correct and still worth doing — it reconciles the knowledge wiki for anything `minerva:promote`'s Mode B landed in the phase that just merged.


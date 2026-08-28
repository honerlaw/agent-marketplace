# cleanup — knowledge reconciliation on the default branch

`minerva:promote` is **add-only**: on a work-unit branch it writes new
`.minerva/knowledge/<YYYY-MM-DD>-*.md` entry files and touches nothing else. That is what
keeps concurrent PRs from conflicting — a branch's `.minerva/` footprint is purely
additions, and new files always merge cleanly.

The work promote no longer does happens here, on the default branch, where there is
exactly one writer at a time:

- each new entry's `index.md` catalog line, generated from the entry's `**Summary**`;
- the `index-watermark` bump;
- the reverse direction of every forward `## Related` link, plus the supersession
  banner implied by any `supersedes` edge;
- `overview.md`, when there is enough un-synthesized scope to warrant it.

**Why cleanup owns this.** It is already the post-merge, default-branch, last-in-the-
lifecycle phase that every orchestrator calls. No new phase, no CI workflow to install
in each consumer repo, no git merge driver (those are per-clone local config that CI
checkouts silently lack).

## Decoupled from worktree removal

Reconciliation runs on **every** invocation — including one that removed no
worktrees, and including `minerva:cleanup` invoked with no argument on a clean tree.
A merge that happened through the GitHub UI leaves pending entries with no worktree
to remove, and those still need cataloguing.

The one exception is Step 0: a repo that reconciles in CI already has a writer, and a
second one is a race rather than a redundancy.

## Step 0 — Stand down if the repo reconciles in CI

Some repos have installed a workflow that reconciles on merge. Where one exists it owns
this work, and cleanup must not also do it:

```bash
grep -rl "knowledge_fix.py" .github/workflows/ 2>/dev/null
```

A hit means stand down: report `reconciliation: owned by CI (<workflow file>)`, **name any
entries the signal below would have reported as pending** so the run is not quietly
trusting something it has not verified, and skip to the final report. Do not open a PR.

The anchor is the pinned fixer rather than a filename or a marker: `knowledge_fix.py` *is*
the deterministic half of reconciliation, so a workflow that calls it is a CI reconciler and
one that does not is not. A declared marker file would need per-repo setup, and a repo that
installs the workflow and forgets the marker gets exactly the race described below.

**This is not a de-duplication nicety — the two writers are unserialised.** Step 3.3's
mutual exclusion is a non-forced push to the fixed `minerva/reconcile` ref, and that
argument holds only because both racers push the *same* ref. A CI job pushes a unique
branch per run (`minerva/reconcile-ci/<run_id>` in the known implementation), so there is no
contended ref, nothing rejects the loser, and both writers can open a PR editing `index.md`
— the concurrent-writer collision this whole add-only design exists to prevent.

Repos with no such workflow are unaffected; the grep finds nothing and every instruction
below applies unchanged.

## Step 1 — Signal (deterministic, read-only)

Both signals already exist; neither is a judgment call.

```bash
ROOT="$(git rev-parse --show-toplevel)"
PLUGIN_SCRIPTS=$(find -L "${HOME}/.claude/plugins/minerva" "${HOME}/.claude/plugins/cache/agent-marketplace/minerva" -maxdepth 2 -type d -name "scripts" 2>/dev/null | head -1)
[ -n "$PLUGIN_SCRIPTS" ] && { python3 "$PLUGIN_SCRIPTS/plugin_guard.py" knowledge_lint || exit 1; }
SCRIPTS="${PLUGIN_SCRIPTS:-$ROOT/scripts}"
python3 "$SCRIPTS/knowledge_lint.py" "$ROOT/.minerva/knowledge"     # pending-reconciliation warnings
python3 "$SCRIPTS/synthesis_status.py" "$ROOT/.minerva/knowledge"   # un-synthesized entries
```

Pending work exists if `knowledge_lint` reports any `pending reconciliation` warning
**or** `synthesis_status` reports un-synthesized entries.

A `reciprocal-manual` warning is **not** pending work and must not be treated as such.
It marks an edge on a line with no single relationship label — a multi-target bullet —
which `knowledge_fix.plan_reciprocals` refuses to derive a reciprocal for, by design and
on every run. Its wording deliberately omits `pending reconciliation` for exactly this
reason: counting it would describe a reconcile that can never settle. Clearing one means
a human writing the back-link, or splitting the line into one target and one label. If neither does, report
`reconciliation: nothing pending` and skip to the final report — this is the common
case and must stay silent and cheap.

## Step 2 — One at a time, but never abandon the pending set

```bash
gh pr list --state open --json number,url,headRefName \
  --jq '[.[] | select(.headRefName | startswith("minerva/reconcile"))][0]'
```

A **prefix** match, not `--head`. `--head` takes an exact branch name, so an open
`minerva/reconcile-ci/31727177896` is invisible to it and the check reports clear while a
reconciliation is in flight. Step 0 should already have stood the run down before this
line is reached; this is what keeps the failure safe when it has not — a differently-named
CI job, or a caller that skipped Step 0.

**At most one outstanding at a time** — two would edit `index.md` concurrently and
conflict with each other, recreating the exact problem this design removes.

If one is open, **wait for it to merge and then continue from Step 3** — do not stop.
Poll `gh pr view <N> --json state` until `MERGED`, then **re-run Step 1's signal**
against the updated default branch and reconcile whatever is still pending. Re-running
the signal is not optional: the PR you waited on may have catalogued some of it, and the
second pass has to ask rather than assume.

**Why waiting, and not "the next run will pick it up".** That was this step's original
instruction and it is false in the common case. Cleanup runs once per work unit, so "the
next run" is whenever someone next finishes a unit — days away, or never. A reconciliation
PR opened minutes before another unit merges cannot contain that unit's entries: it read
the default branch at open time and never revisits. Those entries then sit on the default
branch **present but uncatalogued** — absent from `index.md`, invisible to anyone reading
the wiki, which is most of what an entry is for. The run that skipped reports itself
successful, so nothing surfaces it. Observed six times in two days on one project before
it was diagnosed, every occurrence found by accident.

If the open PR does **not** merge — CI red, auto-merge declined, human review pending —
do not wait indefinitely and do not open a second concurrent PR. Fall through to the
final report and name every still-pending entry under `Pending, NOT catalogued`. "The
next run picks them up" becomes a true statement only once the report has told someone.

This check is an early-out, **not** the lock. It is a read followed by an act, so two
cleanups running at once — a manual invocation racing a `propose-ship-auto` wake-up,
say — can both pass it. The actual mutual exclusion is the remote ref update in
Step 3.3: a non-forced push to `minerva/reconcile` is atomic, so exactly one of the
two wins and the loser is rejected. Handle that rejection as the serialization signal
it is, never by forcing.

## Step 3 — Reconcile in a throwaway worktree

Never reconcile in the user's working tree: cleanup's pre-flight only guarantees it
is not *inside* a worktree, not that it is on the default branch or up to date.

```bash
git fetch --quiet origin
git worktree add -B minerva/reconcile .minerva/worktrees/minerva-reconcile "origin/<default-branch>"
```

`-B` resets the branch if it already exists (a previous PR merged and GitHub deleted
the remote branch, leaving a stale local one). `.minerva/worktrees/` is gitignored, so
the throwaway leaves no trace. Address it by prefix — every path gets
`.minerva/worktrees/minerva-reconcile/`, every git command runs as
`git -C .minerva/worktrees/minerva-reconcile …`. **minerva never calls
`EnterWorktree`** (knowledge 008/044).

1. **Apply the mechanical fixes.**

   ```bash
   python3 "$SCRIPTS/knowledge_fix.py" .minerva/worktrees/minerva-reconcile/.minerva/knowledge
   ```

   This adds catalog lines from each entry's `**Summary**`, bumps the watermark,
   writes missing reciprocals and banners, and relocates wrong-Type lines. Surface any
   `REFUSED` items in the final report rather than working around them — the two that
   matter are an entry with no `**Summary**` (author its catalog line by hand) and a
   an unresolvable target (nothing is written for it).

2. **Refresh the overview, if warranted.** When `synthesis_status` reported
   un-synthesized entries, invoke the `minerva:synthesize` skill via the `Skill` tool,
   pointing it at the throwaway worktree's corpus. Its own Step-2 self-gate decides
   whether the scope justifies a rewrite — do not second-guess it, and do not run it
   at all when the signal was empty.

3. **Commit and open the PR.**

   ```bash
   git -C .minerva/worktrees/minerva-reconcile add .minerva/knowledge/
   git -C .minerva/worktrees/minerva-reconcile commit -m "chore: reconcile knowledge index"
   git -C .minerva/worktrees/minerva-reconcile push -u origin minerva/reconcile   # NEVER --force
   gh pr create --head minerva/reconcile --base "<default-branch>" \
     --title "chore: reconcile knowledge index" --body "<body>"
   gh pr merge --auto --squash <pr-number>
   ```

   **The push is the lock.** It must be non-forced: `--force` / `--force-with-lease`
   would let a second concurrent cleanup overwrite the first's branch out from under
   its open PR.

   **A rejected push has two causes, and they need opposite responses. Diagnose before
   concluding — do not assume the race.**

   ```bash
   gh pr list --head minerva/reconcile --state all --json number,state --limit 5
   ```

   - **A reconcile PR is OPEN → a real race.** Another run won. Report
     `reconciliation: another run is in flight`, name every still-pending entry stem
     under `Pending, NOT catalogued` (see below), clean up per step 4, and exit 0. The
     winning run's pass covers the same pending set, because both computed their edits
     from the same default-branch corpus — but say which entries you did not write, in
     case it does not.
   - **No PR is OPEN → a stale branch, NOT a race.** This is the common case in a
     squash-merging repo: the merged PR's commit never lands on the default branch, and
     GitHub keeps the branch unless configured to delete it, so the next run's
     `-B`-reset branch diverges from a ref nothing is using. Observed on this repo
     2026-08-11, and again after the very next reconciliation merged. Concluding "race"
     here strands the run's entries for a concurrency event that never happened.
     The remedy is to delete the stale remote branch and push again — **not** to force,
     since the rule above exists to protect an open PR's head and there is no open PR.
     Deleting a shared remote ref is outward-facing, so **ask the user first**; if they
     decline, fall through to the report and list the entries under
     `Pending, NOT catalogued`.

   **Neither path may exit quietly.** A skip that names no entries is the same
   silent-deferral failure step 2 above was already corrected for
   (knowledge 2026-08-07): the run reports success, the entries sit on the default
   branch uncatalogued, and nothing surfaces it. Whatever the cause, a run that does
   not catalogue a pending entry must name that entry in its report.

   The body names the entries catalogued, whether `overview.md` was refreshed, and any
   refusals. Auto-merge is appropriate here **because the content is derived** —
   regenerated from the corpus by a tested script, not authored — so there is no
   judgment for a reviewer to apply.

   If `gh pr merge --auto` is rejected (auto-merge disabled on the repo, or a
   protection rule forbids it), **report the PR URL and stop**. Do not merge directly,
   do not retry with a different flag, do not push to the default branch. A human
   merging it at their convenience is a correct outcome; the next run sees the PR open
   and skips.

4. **Remove the throwaway.**

   ```bash
   git worktree remove .minerva/worktrees/minerva-reconcile
   ```

   Run this even when an earlier step failed, so a broken run doesn't strand a
   worktree. Leave the branch alone — it is the PR's head.

## `--dry-run`

Report the signal — how many entries are pending, how many un-synthesized, whether a
reconciliation PR is already open — and stop. Create no branch, no worktree, no PR.

## Final report

Add to cleanup's existing report:

```
Reconciliation:          <nothing pending | owned by CI (<workflow>) | PR #N opened, auto-merge enabled | waited on PR #N>
  Entries catalogued:    N (<list>)
  Overview refreshed:    <yes (N entries newly linked) | no (self-gate declined) | not run>
  Refusals:              N (<list — needs manual attention>)
  Pending, NOT catalogued: N (<list of stems — why>)
```

`Pending, NOT catalogued` is the line that makes a strand impossible to miss. It is
non-empty whenever entries exist in the corpus with no catalog line and this run did not
add one — an open reconciliation PR that never merged, a `REFUSED` item, anything. A run
that leaves entries invisible must not describe itself as clean.

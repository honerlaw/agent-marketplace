# cleanup — knowledge reconciliation on the default branch

`minerva:promote` is **add-only**: on a work-unit branch it writes new
`.minerva/knowledge/NNN-*.md` entry files and touches nothing else. That is what
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

## Step 1 — Signal (deterministic, read-only)

Both signals already exist; neither is a judgment call.

```bash
ROOT="$(git rev-parse --show-toplevel)"
PLUGIN_SCRIPTS=$(find -L "${HOME}/.claude/plugins/minerva" "${HOME}/.claude/plugins/cache/agent-marketplace/minerva" -maxdepth 2 -type d -name "scripts" 2>/dev/null | head -1)
SCRIPTS="${PLUGIN_SCRIPTS:-$ROOT/scripts}"
python3 "$SCRIPTS/knowledge_lint.py" "$ROOT/.minerva/knowledge"     # pending-reconciliation warnings
python3 "$SCRIPTS/synthesis_status.py" "$ROOT/.minerva/knowledge"   # un-synthesized entries
```

Pending work exists if `knowledge_lint` reports any `pending reconciliation` warning
**or** `synthesis_status` reports un-synthesized entries. If neither does, report
`reconciliation: nothing pending` and skip to the final report — this is the common
case and must stay silent and cheap.

## Step 2 — Skip if one is already open

```bash
gh pr list --head minerva/reconcile --state open --json number,url --limit 1
```

If a reconciliation PR is open, report `reconciliation: PR #N already open, skipping`
and stop. **At most one outstanding at a time** — two would edit `index.md`
concurrently and conflict with each other, recreating the exact problem this design
removes. Anything pending is simply picked up by the next run after that PR lands.

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
   duplicate NNN (quarantined; nothing is written for it).

2. **Refresh the overview, if warranted.** When `synthesis_status` reported
   un-synthesized entries, invoke the `minerva:synthesize` skill via the `Skill` tool,
   pointing it at the throwaway worktree's corpus. Its own Step-2 self-gate decides
   whether the scope justifies a rewrite — do not second-guess it, and do not run it
   at all when the signal was empty.

3. **Commit and open the PR.**

   ```bash
   git -C .minerva/worktrees/minerva-reconcile add .minerva/knowledge/
   git -C .minerva/worktrees/minerva-reconcile commit -m "chore: reconcile knowledge index"
   git -C .minerva/worktrees/minerva-reconcile push -u origin minerva/reconcile
   gh pr create --head minerva/reconcile --base "<default-branch>" \
     --title "chore: reconcile knowledge index" --body "<body>"
   gh pr merge --auto --squash <pr-number>
   ```

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
Reconciliation:        <nothing pending | PR #N already open | PR #N opened, auto-merge enabled>
  Entries catalogued:  N (<list>)
  Overview refreshed:  <yes (watermark NNN→MMM) | no (self-gate declined) | not run>
  Refusals:            N (<list — needs manual attention>)
```

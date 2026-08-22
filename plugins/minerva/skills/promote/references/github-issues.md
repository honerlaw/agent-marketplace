# TODO disposition — GitHub issues

The **Keep** disposition in [Mode A step 5](modes.md) has two paths. On a GitHub repo whose
issues this session can create, a kept item becomes an **issue** carrying an explicit
priority. Everywhere else it becomes a `followups.md` bullet, exactly as before.

`followups.md` is write-only: nothing in it ever marks an item done, so a backlog of them
has to be re-read in full every time someone scopes work. An issue has the state the file
lacks — it closes, and a closed issue drops out of every query below on its own.

**Read this file before executing the Keep disposition.** Run the commands; do not
paraphrase them.

## Step 1 — Capability probe (once per promote run)

```bash
gh repo view --json nameWithOwner,hasIssuesEnabled
```

- **Non-zero exit** — no `gh` on PATH, not authenticated, or no GitHub remote → **file
  path**. Take `followups.md` for every kept item and skip the rest of this file.
- **`hasIssuesEnabled` is `false`** — issues are turned off for this repo → **file path**.
- **Otherwise** → **issue path**. Record `nameWithOwner`; it names the repo in the report.

Do **not** gate on `viewerPermission`. On GitHub anyone with read access can open an issue
while issues are enabled, so requiring `WRITE` or above would wrongly push a capable
outside contributor onto the file path. The creation attempt in step 4 is the real
permission check, and step 5 catches it when it fails.

Run the probe from wherever the skill is already operating. A minerva worktree shares its
remotes with the parent repo, so `gh` resolves the same `nameWithOwner` from inside
`.minerva/worktrees/<date-slug>/` as from the repo root — no `-C` juggling needed.

## Step 2 — Priority

Propose exactly one level per kept item. These definitions are the whole vocabulary; use
them verbatim so two runs on the same item agree:

| Level | Meaning |
|---|---|
| `critical` | We absolutely should do this before anything else. |
| `high` | We should do this as soon as possible. |
| `medium` | We should eventually do this. |
| `low` | It does not matter whether we do it. |

The level is a **proposal**, not a fact. Show it alongside the item at Mode A's step-6 hard
gate — that gate is where a wrong level gets corrected, before anything is created.
Default to `medium` when an item gives no signal either way; `critical` is for work that
genuinely blocks everything else, not for emphasis.

## Step 3 — Labels, and the duplicate check

Bootstrap each needed label once. Check before creating so an existing label is left
untouched — never `--force`, which would overwrite a repo's own colour and description:

**Do not run this block under `set -e` or `set -u`.** Every call here is allowed to fail —
`ensure_label` returns 1 rather than aborting, and `USABLE` is legitimately empty on a repo
where no label could be created.

```bash
# Returns 0 if the label is usable (already present, or created just now), 1 if not.
ensure_label() {  # $1 name, $2 hex colour, $3 description
  gh label list --limit 200 --json name --jq '.[].name' | grep -qxF "$1" \
    || gh label create "$1" --color "$2" --description "$3" \
    || return 1
}

# Collect the flags for the labels that are actually usable. USABLE is what step 4 passes;
# a label that could not be ensured simply contributes no flag.
USABLE=()
ensure_label "minerva:followup"   5319E7 "Deferred work recorded by minerva:promote" \
  && USABLE+=(--label "minerva:followup")
ensure_label "priority: $LEVEL"   "$COLOUR" "$DEFINITION" \
  && USABLE+=(--label "priority: $LEVEL")
```

Colour and definition per level — `critical` `B60205`, `high` `D93F0B`, `medium` `FBCA04`,
`low` `0E8A16`, each described by its row in the step-2 table. Ensure only the level a given
item actually uses; there is no reason to create all four on a repo that needs one.

If a label cannot be created — the caller can open issues but not manage labels, or the
repo already runs its own `P0`-style taxonomy — **do not fail and do not force it**. Carry
on without that label; the `**Priority**:` body line in step 4 still denotes the level.
Note the degradation in the report.

Then, before creating anything, ask whether this unit's followups are already filed.
Creating an issue is the only externally-visible side effect promote has, and a duplicate
is a notification on someone's repo — the same reason `minerva:ship` checks `gh pr view`
before `gh pr create`. Check three sources, cheapest and most reliable first:

1. **This run's own record** — issue numbers created earlier in this same promote run.
2. **The unit's `proposal.md` `## Deferred work` section** (step 6). Local, exact, and
   instant — this is the authority for a re-run after a partial failure.
3. **A repository search**, for a re-run from a different clone or session:

   ```bash
   gh issue list --state all --limit 200 --search '"<date-slug>" in:body' \
     --json number,title --jq '.[] | "\(.number)\t\(.title)"'
   ```

Skip any kept item whose headline already appears, and report it as `already filed as #N`.

Source 3 alone is **not** sufficient: GitHub's search index is not synchronous with issue
creation, so an issue filed seconds ago may not be searchable yet. That is exactly the
window a retry-after-partial-failure lands in, which is why sources 1 and 2 come first.

## Step 4 — Create the issue

One issue per kept item. The **headline** is the item's one-line summary; the body carries
the item's full prose so nothing is lost in compression:

```bash
gh issue create \
  --title "$headline" \
  "${USABLE[@]}" \
  --body "$(cat <<'MINERVA_ISSUE_BODY'
<the item's full prose, verbatim from the scratchpad>

**Priority**: <level> — <that level's definition from step 2>

Deferred from `.minerva/work/<date-slug>/` by `minerva:promote`.
MINERVA_ISSUE_BODY
)"
```

Two substitution rules, because the item's text is copied verbatim and you do not control it:

- **Title.** Set `headline` as a shell variable and pass `"$headline"` — do **not** paste the
  text straight into the command line. A headline like `Fix the "foo" parser` breaks a
  double-quoted `--title`.
- **Body.** The quoted `<<'MINERVA_ISSUE_BODY'` delimiter disables all expansion, so `$`,
  backticks and quotes in the prose are safe. The one thing that still breaks it is a line
  in the prose that is *exactly* the delimiter — hence the deliberately unlikely name. If
  the item somehow contains it, pick another.

Keep the back-link line exactly as written — it is what the step-3 search matches on.

Only **Keep** items become issues. A **Seed new proposal** item still goes to
`minerva:propose`, which produces a full `proposal.md` — a richer record than a one-line
issue. A **Discard** item is still dropped.

## Step 5 — Fail-soft, per item

If `gh issue create` fails for an item, that item falls back to `followups.md` verbatim,
exactly as on the file path. **Never lose a kept item.** Do not abort the remaining items —
a repo-wide failure will simply drop them all to the file, which is the correct outcome.

## Step 6 — Record and report

Write the created issues into the unit's `proposal.md` under a `## Deferred work` section:

```markdown
## Deferred work

- #12 — cross-link the eval fixtures (priority: high)
- #13 — retire the legacy id resolver (priority: low)
```

This is a historical fact — *this unit deferred that item to that issue* — so it cannot go
stale the way a `followups.md` entry does once the work is finished. Do **not** also write
the item's prose to `followups.md`; the issue is the record, and a second copy is what
made the file rot in the first place.

The Mode A step-8 report then names, for each kept item: the issue URL, or `already filed
as #N`, or `fell back to followups.md` with the reason. A report that omits an item it
skipped lies by omission
(`.minerva/knowledge/2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption.md`).

## Reading deferred work back

The skills that read `followups.md` read open followup issues alongside it —
`minerva:review`, and the `propose-ship-*` orchestrators at both their context-assembly and
their TODO-disposition steps:

```bash
gh issue list --label "minerva:followup" --state open \
  --json number,title,labels,url \
  --jq '.[] | "\(.number)\t\(.title)\t\(.labels | map(.name) | join(","))"'
```

Closed issues fall out of that query by themselves, which is the entire point. Skip the
query without comment when the step-1 probe says the repo has no issues.

This applies to **new** items only. The `followups.md` files already in a repo are not
migrated — they stay exactly as they are, and stay worth grepping.

# migrate-fix — Part B: backfill entry metadata

## Part B — Backfill entry metadata from the legacy aggregates

Before 3.0 the wiki stored a catalog (`index.md`, one summary line per entry) and a
theme-grouped narrative (`overview.md`) beside the entries. 3.0 derives both on read from
two lines every entry carries — `**Theme**` and `**Summary**` — so nothing shared is ever
written and there is nothing to keep current after a merge
(`2026-10-01-decision-knowledge-aggregates-are-derived-on-read`). A pre-3.0 corpus holds
that data in the legacy files instead; the backfill moves it onto the entries once.

## Step 5 — Plan (dry run, read-only)

```bash
ROOT="$(git rev-parse --show-toplevel)"
PLUGIN_SCRIPTS="$(python3 "$MINERVA_PLUGIN_ROOT/scripts/minerva_runtime.py" resolve --skill-file "$MINERVA_SKILL_FILE")" || exit 1
[ -n "$PLUGIN_SCRIPTS" ] && { python3 "$PLUGIN_SCRIPTS/plugin_guard.py" || exit 1; }
python3 "$PLUGIN_SCRIPTS/knowledge_backfill.py" "$ROOT/.minerva/knowledge" --dry-run
```

It reports how many entries would gain metadata, which legacy files would be deleted, and
two hand-work lists:

- **`no Summary (write by hand)`** — entries with no `**Summary**` and no `index.md`
  catalog line to fill it from.
- **`no Theme (assign by hand)`** — entries with no `**Theme**` that no `overview.md`
  section links. Theme is single-valued, so an entry several sections link takes the
  first; the heading text before its first `:` is kebab-cased with a leading article
  dropped (`## The knowledge wiki: a navigable corpus` → `knowledge-wiki`).

A corpus with neither legacy file prints `already migrated` and is a no-op — skip to
Step 8. (Entries that still lack metadata there have nothing to fill from; write their
lines by hand.)

## Step 6 — Confirmation gate (REQUIRED)

Show the counts, the files to be deleted, the derived theme names (the dry run's
`[themes derived from overview.md sections]` block — each theme beside the heading it came
from, exactly as the script derives it), and both hand-work lists. Ask before proceeding. The theme names deserve a look:
they become the catalog's grouping, and a heading that kebab-cases badly is cheaper to
fix now than after the overview it came from is deleted.

## Step 7 — Apply and report

```bash
python3 "$PLUGIN_SCRIPTS/knowledge_backfill.py" "$ROOT/.minerva/knowledge"
```

It inserts only the missing metadata lines — directly after each entry's `**Type**` line
(else `**Date**`, else the H1), Theme before Summary — and changes no other byte. Entry
bodies, `## Related` blocks and any stored back-links or supersession banners are left in
place: they are still valid, and the catalog still reads legacy banners when deriving
supersession. It then deletes `index.md` and `overview.md`.

Report the hand-work lists to the user and write those lines by hand (a `**Summary**` is
one line; a `**Theme**` is a single lowercase kebab-case name — reuse an existing one from
`knowledge_catalog.py --themes` unless none fits). Then re-run `minerva:init` if
`minerva:migrate` reported stale routing: the old `## minerva` section still names the
deleted files.

## Step 8 — Verify

Run `minerva:lint`. A migrated corpus should report **zero errors**. Expect advisory
warnings: a theme used by only one entry, and missing metadata on older entries you have
not yet hand-filled. **Read `references/upgrading.md`** before comparing a finding count
across the upgrade — the 3.0 detector checks different things, so the old number is not a
baseline.

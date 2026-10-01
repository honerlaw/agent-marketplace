# Upgrading: the finding count is not a baseline

The first `minerva:lint` run after upgrading minerva can report a **different** number of
findings than the same corpus reported before, and the difference is not damage. A finding
count is only comparable under one detector; when the detector changes, re-baseline.

Two consequences worth stating, because one of them cost a real team a post-merge surprise:

- **Do not read a change as a regression** introduced by the migration or the upgrade.
- **Re-baseline any pending finding-count comparison.** A "verified finding-neutral, N
  before and N after" claim made under the old detector does not survive the upgrade. In
  the case this note comes from (a 2.x upgrade that unified the `## Related` edge model), a
  migration measured as exactly neutral under the old detector produced 0 findings before
  merge and 9 after, on byte-identical content.

## What changes at 3.0

minerva 3.0 stopped storing `index.md`, its watermark, reciprocal `## Related` back-links,
supersession banners and `overview.md`; all are derived on read
(`2026-10-01-decision-knowledge-aggregates-are-derived-on-read`). The detector changed with
them:

- **Gone:** index drift, watermark and missing-reciprocal findings. A corpus that carried
  many of these drops them all at once — not because they were repaired, but because the
  thing they checked is no longer stored.
- **New:** missing `**Theme**` / `**Summary**` (an error for an entry dated 2026-10-01 or
  later, a warning for an older or `NNN` one), a warning while legacy `index.md` /
  `overview.md` are still present, and an advisory warning for a theme only one entry uses.
- **Unchanged:** invalid ids and broken `## Related` links stay errors.

An un-backfilled 2.x corpus therefore typically shows **one warning per entry** (missing
metadata) plus the legacy-aggregate warning, and no errors: the date-keyed rule enforces
metadata only on entries written under 3.0, so an old corpus stays green until it is
migrated.

## What to do on first run after upgrade

1. Run `minerva:migrate`; follow its checklist (renames, then `minerva:migrate-fix`'s
   backfill, then `minerva:init` for routing).
2. Run `minerva:lint` and record the count as the new baseline. Do not compare it against
   any number recorded before the upgrade.
3. Hand-fill the metadata the backfill reported it could not derive, then re-run
   `minerva:lint`. What remains is genuine.

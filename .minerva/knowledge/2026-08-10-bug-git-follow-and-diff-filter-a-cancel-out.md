# `git log --follow --diff-filter=A` returns nothing, and callers read that as "no history"

**Date**: 2026-08-10
**Type**: bug
**Summary**: --follow reports a creation as a rename, so pairing it with --diff-filter=A filters every commit away
**Context**: .minerva/work/2026-08-09-date-prefixed-identity

## Context
The `NNN` → date migration derives each entry's id from the git history of its own path.
"The date the file was added, following renames" reads as a direct translation:

```bash
git log --follow --diff-filter=A --reverse --format=%cs -- <path>
```

Both flags are individually correct. `--diff-filter=A` selects the add. `--follow` keeps
history intact across a `git mv`. The migration's own design document specified exactly
this command, and it survived a three-agent review panel.

It returns **empty** for any path that has ever been renamed.

## Finding
**`--follow` and `--diff-filter=A` are mutually exclusive in effect.** Under `--follow`,
git rewrites the walk so a path's original creation is reported as a **rename (R)**, not an
add (A). Filtering for `A` then discards it — and every other commit too — so the command
succeeds, exits 0, and prints nothing.

The damage came from how the caller read that silence. Empty output meant "git could not
date this path", which the planner handled by **skipping** the entry. Measured on this
repo: 5 of 102 paths silently dropped, every one touched by the historical `git mv` that
moved `.minerva/decisions/` to `.minerva/knowledge/`. A migration that reported success
would have left a permanently half-renamed corpus.

The fix is to drop the filter and keep `--follow`:

```bash
git log --follow --reverse --format=%cs -- <path>   # first line
```

The oldest commit that touches a path **is** its creation, so the filter was never adding
information. Verified by measuring both forms across all 58 entries that each can date:
identical dates, zero disagreements.

## Implications
- `--reverse` with the first line, never `-1`: git orders reverse-chronologically, so `-1`
  returns the *newest* match. The two mistakes compose — `-1` on a directory pathspec
  silently yields whenever it was last touched.
- **An empty result from a query is not the same as an empty subject.** Distinguish "git
  said no commits" from "git could not answer" before deciding to skip; a skip path that
  triggers on a flag interaction is invisible in review.
- Verify a history-derived value against a second derivation over the real corpus, not a
  fixture. Both this bug and its fix look right in prose.
- The general shape: two filters that each narrow correctly can, composed, narrow to
  nothing while still exiting 0.

## Related
- [[2026-08-10-decision-date-ids-make-identity-the-path]] — builds on

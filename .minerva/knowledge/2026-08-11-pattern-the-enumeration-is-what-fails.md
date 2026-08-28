# The hand-enumerated list of formats is the thing that fails; ask the corpus

**Date**: 2026-08-11
**Type**: pattern
**Summary**: a marker with eight spellings broke a check for months, and enumerating them by eye failed three times in one sitting — the assertion that held asks the corpus
**Context**: .minerva/work/2026-08-11-close-remaining-loose-ends

## Context
`minerva:promote` archives a unit's scratchpad and replaces it with a one-line marker. Its
idempotency check read that marker to decide "already promoted, stop". The check matched
**one exact string**. One 51-unit corpus contains **eight** spellings:

```
Summarized at minerva:promote on <date> — see archive/.     35   ← the one it matched
promoted <date> — durable knowledge in .minerva/knowledge/…  6
Summarized at /promote on <date> — see archive/.             2   ← before the skill rename
promoted <date>                                              2
<!-- post-promote -->                                        2
## Promote <date>                                            2   ← appended, live scratchpad
Promoted <date>. Scratchpad archived.                        1
> **PROMOTED <date>** — durable item is knowledge 057…       1   ← blockquote and bold
```

So on **16 of 51 units** the check failed *open*: promote did not recognise an
already-promoted unit, re-ran its mutating pass, and could duplicate knowledge entries.

This was known. `2026-05-19-bug-promote-idempotency-check-misses-old-marker` reported it in
May, recommended "accept either marker string (**preferred — forward-compatible**)", and
that was never applied. The affected set grew from 3 units to 16 while the marker kept
being reworded — each new promote author writing the phrasing that read well to them.

## Finding
The interesting failure is not the check. It is that **enumerating the spellings by hand
failed three times in one sitting**, on a corpus of 51 files, by someone who had just read
the entry warning about it:

1. A grep recognising two spellings reported "14 units unpromoted". Most were promoted; the
   detector could not see them. This reproduced the documented bug while investigating it.
2. A `head -1` sweep produced nine spellings — including
   `promoted <date><!-- post-promote -->`, **which exists nowhere.** One scratchpad has no
   trailing newline, so `head -1` concatenated its marker onto the next file's output and
   manufactured a format. That phantom was then written into a test fixture whose docstring
   asserted every entry "was taken from a real unit".
3. A per-file count in Python finally gave eight spellings across 16 units.

Two independent reviewers caught (1) and (2). Neither was caught by rereading.

**A hand-built list of the shapes your data takes is a hypothesis, not an inventory**, and
the tooling you build it with has its own failure modes — a missing trailing newline is not
a thing anyone reasons about while counting. Every artifact derived from such a list
inherits its errors, including the fixtures meant to prove it right.

The fix is a **tolerant reader plus an assertion that queries the corpus**:

```python
def test_no_live_unit_is_misread_as_unpromoted():
    missed = [d.name for d in WORK.iterdir()
              if unit_state(d)["status"].startswith("Shipped") and not unit_state(d)["promoted"]]
    assert missed == []
```

That test caught the eighth spelling — the blockquote form — immediately, after eight
others had been enumerated by hand. It cannot be fooled by a phrasing nobody predicted,
because it does not hold a list of phrasings.

## Implications
- When a value has drifted in spelling, read it with a predicate over its *meaning*, and
  pick the tolerant direction by failure cost. Here a false negative re-runs a mutating
  pass and a false positive only skips one, so read generously — then anchor at line start
  and require a date, so ordinary prose ("Promoted entries are listed below") cannot trip
  it.
- **Write canonically, read tolerantly.** Normalising the 16 stale markers was rejected: it
  edits historical records and leaves the tolerant reader untested against the drift it
  exists to absorb.
- Pair every hand-enumerated fixture list with one assertion over the real corpus. The
  fixtures document the shapes you know; only the corpus test finds the ones you do not.
- Beware `head -1`, `uniq -c` and friends when the data may lack trailing newlines. Count
  in a language that reads files as files.
- A recommended fix recorded in a knowledge entry and never applied is worse than no entry:
  it converts a live bug into one everybody has already agreed about. Check whether a
  "known" issue's prescribed fix actually shipped.

## Related
- [[2026-05-19-bug-promote-idempotency-check-misses-old-marker]] — builds on
- [[2026-08-09-pattern-read-authored-metadata-from-where-it-is]] — builds on
- [[2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant]] — see also
- [[2026-08-11-decision-ci-runs-the-whole-suite]] — see also
- [[2026-08-11-pattern-a-tolerant-reader-needs-a-boundary]] — see also
- [[2026-08-11-pattern-an-unenforced-constraint-is-aspirational]] — see also
- [[2026-08-28-pattern-a-corpus-assertion-must-survive-its-own-first-instance]] — see also
- [[2026-08-28-pattern-a-decider-and-an-executor-are-different-surfaces]] — see also
- [[2026-08-28-pattern-a-registry-with-the-wrong-arity-manufactures-agreement]] — see also

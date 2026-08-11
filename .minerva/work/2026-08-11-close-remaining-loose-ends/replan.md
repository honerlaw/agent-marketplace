# Replan: close-remaining-loose-ends

## 2026-08-11 — the record inconsistency was a live correctness bug, not untidiness

### Original plan

Item 5 fixed **two** work-unit records (`2026-05-19-add-review-skill`,
`2026-06-12-run-context-footprint-estimator`) whose `Status` and scratchpad state made
them register as in-flight in every orchestrator's pre-flight collision check. The user
approved that two-unit treatment.

### What changed

Verifying that fix against the whole corpus turned up something the proposal did not
anticipate, in two stages — and I got it **wrong the first time**, in exactly the way this
unit is about.

**First pass (wrong).** Grepping for the post-promote marker found 14 units that looked
`Shipped` but unpromoted, and I was about to record that in `followups.md`. The reviewer
caught it: my grep recognised **two** marker spellings and the corpus has more, so most of
those 14 were promoted and my detector could not see it. That is the same naive
single-string match the repo already has a knowledge entry about
([[2026-05-19-bug-promote-idempotency-check-misses-old-marker]]) — I reproduced the
documented bug while investigating it.

**Second pass (measured) — and it was still wrong.** I enumerated the distinct first
lines and reported nine spellings and "15 of 50". The acceptance reviewer recounted and
found the table both undercounted two shapes and contained a spelling **that exists
nowhere**: `promoted <date><!-- post-promote -->`. It was an artifact of `head -1` over a
file with no trailing newline, which concatenated one unit's marker onto the next unit's
output. I had then pinned that phantom in a test fixture whose docstring asserted every
entry "was taken from a real unit".

**Third pass (counted in Python, per file).** 51 units, **9** real spellings, **16**
non-canonical:

| shape | units |
|---|---|
| `Summarized at minerva:promote on <date> — see archive/.` | 35 (canonical) |
| `promoted <date> — durable knowledge in .minerva/knowledge/…` | 6 |
| `Summarized at /promote on <date> — see archive/.` (pre-rename) | 2 |
| `promoted <date>` | 2 |
| `<!-- post-promote -->` | 2 |
| `## Promote <date>` appended to a live scratchpad | 2 |
| `Promoted <date>. Scratchpad archived.` | 1 |
| `> **PROMOTED <date>** — durable item is knowledge 057…` | 1 |

That is three counting attempts, two of them wrong, on a corpus of 51 files — which is
the argument for the predicate stated more sharply than any prose could: **the enumeration
is the thing that keeps failing.** The tests that hold are the ones that ask the corpus.

**The live bug.** `promote/references/modes.md`'s idempotency check matched **one** of
those nine. So on **16 of 51 units** it fails *open*: promote does not recognise the unit
as already promoted, re-runs its mutating pass, and can duplicate `.minerva/knowledge/`
entries. `ship/references/protocol.md` hardcodes the same string for a lower-stakes nudge.

This is not new information to the project. The May 2026 entry reported it, recommended
"accept either marker string (**preferred — forward-compatible**)", and that was never
applied; the affected set grew from 3 units to 16 while the marker kept being reworded.

**Escalated to the user**, because it is a correctness bug outside the approved scope and
this unit was already large. They chose to fix it here.

### New plan

Add `plugins/minerva/scripts/work_status.py` with `is_post_promote(text)` and
`unit_state(dir)` — a **tolerant reader**, and have `promote` and `ship` call it instead of
comparing strings. This mirrors how `knowledge_lint.parse_entry` resolves an entry's type
across three spellings plus two fallbacks
([[2026-08-09-pattern-read-authored-metadata-from-where-it-is]]): the question being asked
is "has promote run", and a unit answers in whatever words the promote of its day used.

The failure direction matters and picks the design: a **false negative re-runs a mutating
pass**, a false positive only skips one. So read generously and anchor at line start so
prose that merely mentions promotion cannot trip it.

Three things this must not become:
- **Not** "normalize the 15 markers to the canonical form." That edits historical records
  and leaves the tolerant reader untested against the drift it exists to absorb. Writers
  still emit the canonical marker; only *reading* is tolerant.
- **Not** an enumeration in prose. Enumerating spellings in a SKILL.md is what already
  failed once. It is a tested predicate with the nine real spellings as fixtures.
- **Not** a repair of the two inverse cases (`Status: Draft` with a marker present). They
  are inconsistent but harmless — recorded as a follow-up.

**Success criteria gain an eleventh item:** every spelling present in the corpus reads as
promoted, a working scratchpad does not, and no unit whose proposal says `Shipped` reads
as unpromoted — asserted against the **live corpus**, not only fixtures.

### What that live-corpus assertion immediately caught

It failed on first run, on `2026-08-07-reconcile-never-strands-entries` — whose scratchpad
declares promotion as `> **PROMOTED 2026-08-07** …`, a blockquote-and-bold shape absent
from the eight I had enumerated by hand. Its knowledge *was* promoted
([[2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption]] names it as
`**Context**`), so the predicate was wrong, not the unit.

That is the argument for the tolerant reader in miniature: the ninth spelling was found by
a test that asks the corpus rather than by another round of me listing formats. Enumerating
by hand is what failed in May, and it is what failed again in this unit's own first pass an
hour ago.

### Folded from the acceptance review

The reviewer returned **revise** with three findings that were all correct on verification:

- **The corrected table was still wrong** (above). Recounted per-file in Python; the
  fabricated fixture is deleted and the test docstring now records why it was there.
- **The fix had left the identical check naive in eight other places** — the four
  orchestrator pre-flights, `round-table`'s scratchpad-target check, `ship`'s nudge, and,
  worst, `propose-ship-quick`/`propose-ship-balanced`'s `references/phases.md` Phase 4,
  which inline a literal duplicate of the very `minerva:promote` idempotency check being
  fixed. Fixing promote while leaving its inlined copies untouched would have left the
  duplicate-entry path fully open through the orchestrators. All eight now name the
  predicate. This is [[2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant]]
  recurring one layer up: a shared invariant needs a shared implementation, and prose
  duplicated across eight files is not one.
- **`is_post_promote` false-positived on prose opening a line with "Promoted ".** The
  `promoted` and `## Promote` arms now require a date immediately after the word, which
  every real marker has. The failure direction matters: a false positive makes promote
  skip real work silently.

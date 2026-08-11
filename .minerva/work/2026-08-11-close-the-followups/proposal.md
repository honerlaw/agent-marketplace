# Proposal: close-the-followups

**Date**: 2026-08-11
**Status**: Draft
**Base**: `origin/main`

## Goal

Close the five follow-ups left by `2026-08-11-close-remaining-loose-ends`: two stale
records, a half-finished single-sourcing, a gate that does not pair two related warnings,
and one item that turns out to need no change at all.

## Why

The last unit pointed the pre-flight predicate's **scratchpad** limb at
`work_status.is_post_promote` and left its **Status** limb as prose. That prose names a
field spelling the corpus does not use, and `unit_state` cannot read the one proposal that
does use it. Two units still carry factually wrong `Status` values. None of this is
dangerous — the predicate fails safe in every direction — but it is the same
prose-disagrees-with-reality shape this repo keeps paying for.

Live counts, re-measured rather than carried over: **53** work units, **52** using the
inline `**Status**:` field, **1** (`2026-05-21-sync-skill-catalogs`) using a `## Status`
heading.

## Approach

### 1. Correct the two inverse records

`2026-05-19-add-propose-ship-skill` and `2026-06-03-synthesize-skill` each carry a
canonical post-promote marker (dated 2026-05-19 and 2026-06-03) but `**Status**: Draft`.
They are the **only** two units the pre-flight predicate currently reads as in-flight. Set
each to `Shipped (<its marker date>)`.

### 2. `unit_state` reads Status from either spelling — anchored to the section

The parser matches only the inline field, so the one `## Status` proposal reads
`status=None`.

The obvious fix is dangerous and the review caught it. "Take the next non-blank line after
the heading" walks past the section boundary. Given

```
## Status

## Goal
Shipped code already exists for the export path; this proposal only adds Y.
```

it returns `"Shipped code already exists…"`, which `startswith("Shipped")` reads as done —
**a live draft classified as not-in-flight**, a false negative on the one check whose job
is stopping two agents colliding on the same unit.

So the fallback is anchored: **the heading's section ends at the next line beginning with
`#`; the value is the single non-blank line inside that boundary, and if there is none,
Status is absent.** The inline field is tried first, so the form 52 of 53 units use always
wins and the fallback can only fill a gap
([[2026-08-09-pattern-read-authored-metadata-from-where-it-is]]).

This is deliberately **narrower** than `is_post_promote`'s tolerance, and the reason is
worth stating because the precedent does not transfer cleanly. That marker has eight
actively-recurring spellings and nothing stopping a ninth. `## Status` has exactly one
instance, and step 3 removes the prose that produced it — so a permissive walker would
exist forever to serve a single frozen file, buying misread risk for no drift absorption.

### 3. Fix the write-side prose, and give the readers a runnable invocation

- `promote/references/modes.md` tells authors to update "`## Status`" — the minority
  spelling its own output does not produce. Corrected to `**Status**:`.
- The four orchestrators' pre-flight names `work_status` but gives no way to run it, so an
  agent must invent the import path before `promote`'s phase (where the concrete one-liner
  lives) has been read. Each gets the same runnable snippet `modes.md` already carries,
  now covering **both** limbs via `unit_state(...)["in_flight"]`.

`in_flight` lives on `unit_state` because all four consumers use an identical predicate.
That does make `unit_state` half state-reader, half policy — flagged in its docstring so a
future skill wanting a different notion of "in progress" forks deliberately rather than by
accident.

**The predicate's meaning does not change.** It stays `Draft OR not-post-promote`.

### 4. Pair the undated and shorthand warnings at `migrate-fix`'s gate

An entry git cannot date has no target stem, so bare-`[[NNN]]` resolution refuses it — but
the operator meets that only as a refusal reason, while the `UNDATED (skipped)` list prints
separately. Same underlying cause, two disconnected messages; the gate now names the
relationship.

### 5. The `financials` `__pycache__` leftover — no change

Verified: `__pycache__/` is `.gitignore` line 1 and `git status --ignored` shows
`plugins/financials/` as ignored. Purely local cruft in one clone, nothing tracked. The
lesson (check tracked state with `git ls-files`, not `ls`) is already recorded in
[[2026-08-11-decision-ci-runs-the-whole-suite]]. Closed as already-handled.

### What this deliberately does NOT do

**It does not change the predicate**, which the follow-up floated as "possibly the real
defect". After item 1, no unit trips it spuriously. But the honest statement is *no known
instances, not cannot recur*: `promote` writes Status and archives the scratchpad as two
separate steps, so an interrupted run reproduces the shape.

That is survivable **because of the `OR`**, and the review's own worry resolves once the
orderings are checked. Interrupted after the Status rewrite: `Shipped` + unarchived
scratchpad → the scratchpad limb still flags it. Interrupted after archiving: `Draft` +
marker → the Status limb flags it. **Both partial states read as in-flight**, which is the
safe direction — an extra confirmation, never silent adoption of half-promoted work. A
predicate that fails safe on every partial state of its own writer is not the defect.

Recorded with the irony named: this closes "the predicate may be wrong" by enumerating
today's instances rather than proving a property, which is structurally the move
[[2026-08-11-pattern-the-enumeration-is-what-fails]] warns about. The difference is blast
radius — that bug silently duplicated knowledge entries; this one asks a redundant
question — and the `OR` argument above is a property, not a snapshot.

## Success criteria

1. Both inverse units read `Shipped (<marker date>)`, and **no** unit in the corpus reads
   as in-flight afterwards.
2. `unit_state` resolves Status from the inline field **or** an anchored `## Status`
   section; the inline field always wins when both are present.
3. The anchored parse returns `None` — never a neighbouring section's prose — for an empty
   `## Status` section, and does not match a near-miss heading like `## Status quo`.
4. `unit_state` exposes `in_flight` implementing `Draft OR not-post-promote` unchanged, and
   its docstring records that it is a policy predicate, not raw state.
5. `promote/references/modes.md` instructs writing `**Status**:`; all four orchestrators'
   pre-flights carry a runnable invocation covering both limbs.
6. `migrate-fix`'s gate names the undated/shorthand relationship.
7. Regression fixtures for every behavioural change, each verified to fail before its fix,
   including the constructed false-negative from criterion 3.
8. Bare `python3 -m pytest` passes (baseline 486) and `knowledge_lint` stays clean.

## Open questions

None. One observation recorded rather than acted on: `2026-07-29-right-size-lifecycle-waits`
independently logged "the eight units with stale in-flight metadata make the pre-flight
collision check noisy" — the same complaint as this unit's item 2, filed weeks earlier. It
is resolved here by data, not by weakening the check.

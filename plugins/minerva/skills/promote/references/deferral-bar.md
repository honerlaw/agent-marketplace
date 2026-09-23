# The deferral bar — what may be deferred, and where it goes

**This file is the single statement of the rule.** `minerva:review`'s triage, `minerva:promote`'s
TODO disposition, and the `propose-ship-*` orchestrators point here rather than restating
it. If you are about to write the bar into another skill's prose, don't — add a pointer instead.
Six copies of a block held together by a plea to keep them in sync is a shape this project
already carries once, and it took a work unit to discover the copies had silently diverged
(`2026-08-22-pattern-repeated-blocks-may-be-deliberate-divergence-not-duplication`).

**Read this before disposing of any forward-looking item**, in triage or at promote.

## Why there is a bar at all

Every path that produced deferred work treated **recording as free and dropping as lossy**. The
issue-creation protocol said so outright — *"Never lose a kept item"* — and no skill anywhere
stated a budget, a bar, or a cost for filing. A judgment with a stated cost on one side and none
on the other only ever falls one way.

The result, measured on this repo: ~150 bullets across 24 `followups.md` files, 18 tracker
issues of which 15 were filed in a single backfill batch, and an entire skill written for no
purpose but to excavate the backlog after it rotted. The old `low` priority tier was defined as
*"It does not matter whether we do it"* — and filed an issue anyway.

A backlog nobody reads is not a record. It is a place where real defects go to become invisible
among things that were never going to be done.

## The bar

> **An item may become a tracker issue only if all three hold:**
>
> 1. **It is a defect** — you can write a concrete failure scenario for it: specific inputs or
>    state producing a wrong output, a crash, data loss, or a security exposure.
> 2. **It is valuable** — it merits `critical` or `high` priority
>    ([github-issues.md](github-issues.md)). A defect nobody would schedule soon is not worth a
>    tracker slot.
> 3. **It is too large to absorb** — fixing it needs its own design or proposal, changes a public
>    interface or cross-cutting contract, or would materially widen what this PR touches.

**Condition 1** is mechanical on purpose. If you cannot write that sentence, it is not a defect,
and no argument about severity changes that. It is the same discipline the `ReportFindings` tool
already enforces with its required `failure_scenario` field ("concrete inputs/state → wrong
output/crash"), and it refuses the entire *this could be cleaner* class by construction. Latency
does not matter: a latent bug nobody has hit qualifies; a maintainability hazard that bites every
week does not. The question is whether a failure can be *described*, not whether it has
*happened*.

**Conditions 2 and 3 exist because condition 1 alone still filed too much.** After the bar
first shipped with only condition 1, asking for one unit of work routinely produced two or three
follow-ups. Each was a real defect, but most were small enough to fix in the same PR, or never
urgent enough to be scheduled at all. The old `medium` tier ("we should eventually do this")
filed exactly those, and both open followups on this repo at the time carried it. A real defect
is not by itself worth a tracker slot. It is either worth doing now, or worth doing soon *and*
too big to do now.

**The bar states what qualifies, never what is excluded.** That direction is deliberate. A rule
written as a list of things not worth filing has gaps that are invisible by definition — you
cannot notice the exclusion you failed to think of — and the surface it governs grows on its
own. An allowlist's refusals are complete
(`2026-08-22-pattern-a-denylist-safety-guard-fails-open`).

## The outlets

Every forward-looking item lands in exactly one of these, **tried in this order**. The only
other disposition is to seed a new proposal (the TODO gate in `minerva:promote`'s "Mode A — no argument (end-of-work full pass)"), which a user may
choose for any item they want designed rather than recorded. "Leave it in the scratchpad" is not
a disposition.

### 0. A defect you can absorb → fix it now

**Fixing now is the default for a defect.** A defect that clears condition 1 but fails
condition 3 is part of this unit's work, **even when it sits outside the diff**, whatever its
priority. "It isn't in my diff" is not a reason to defer a five-minute fix. It is how one
request turns into three issues.

*Absorbable* is bounded, so fix-now does not become scope creep. The fix must be local, need no
new design decision, change no public interface or cross-cutting contract, and be small beside
the unit's own change. A fix that fails any of those fails condition 3 and goes to outlet 1 or 2.

Absorb where the item is found. During work, fix it then. At review triage it is **FIX**. An
absorbable defect that only surfaces at promote was missed earlier, and **it does not get fixed
inside promote**. Code written after review would ship without a reviewer seeing it. Stop the
promote pass before it writes anything, fix the defect, log it in the scratchpad as a review
fix, and send the new commits back through review. An orchestrator returns to its review phase
and then re-runs promote. Run standalone, promote stops and recommends `minerva:review`, then a
fresh `minerva:promote`.

An absorbed fix is **in scope, not scope creep**. Log it in the scratchpad as
`- Absorbed fix: <file> — <failure scenario it closes>` so review's spec-fidelity lens and
promote's `## Approach` rewrite both see it as part of the unit.

### 1. Clears all three conditions → a tracker issue

File it per [github-issues.md](github-issues.md). The issue body carries a required
`**Failure scenario**:` line — the very sentence condition 1 asked you to write. An item whose
failure scenario cannot be written cannot be filed by the documented command, which is what
makes the bar structural rather than advisory.

Priority denotes **how urgent this defect is**, not whether it is worth having. See the
two-level table in `github-issues.md`.

**Soft cap: one filed issue per unit.** A second issue from the same unit needs a one-line
justification: why it is independent of the first, and why neither could be absorbed. Put it
in the second issue's body, and repeat it in the promote report. An orchestrator also logs it
under its own decisions header. The cap
is soft because a unit that uncovers two genuine `critical` defects must not drop one. It exists
to make a flood visible, not to forbid it.

### 2. Below the bar → a knowledge entry, or nothing

An item that fails condition 1 or condition 2 and was not absorbed lands here.

A maintainability hazard, a duplicated block, an inconsistency, a "we should probably", a
real-but-unurgent defect too large to absorb — these
are **standing facts about the system**, and that is exactly what a `reference` entry in
`.minerva/knowledge/` is for
(`2026-08-09-decision-reference-is-a-fifth-entry-type`; one of the four entries that justified
adding the type was a curated followups backlog).

Write it as what *is*, not as what someone should do:

- ✗ "We should extract the shared fence-stripping helper."
- ✓ "Two test modules derive fence-stripping independently; they can drift."

This is not a euphemism — it is the reframing that makes the item durable. A TODO expires the
moment someone does it or decides not to. A description of the system stays true until the
system changes, and `minerva:review` reads `.minerva/knowledge/` on **every** future unit, so it
resurfaces by locality when relevant code is next touched.

**It carries no burn-down obligation, and that is the point.** `followups.md` rotted because it
was a list you were implicitly supposed to finish and nobody ever did. A corpus of standing
facts has nothing to finish.

If the observation is not even worth a standing fact, **discard it**. Discarding is a legitimate
disposition, not a failure of nerve.

### 3. Documentation → neither; it is not deferred work

**Documentation for behavior this diff touched is never deferred.** It is not a triage outlet at
all — it is a definition-of-done condition on the work, alongside tests passing.

Scope is bounded by the diff, so the question is always answerable:

- **In scope** — every doc describing behavior the change **added, altered, or removed**:
  `.minerva/reference/` pages, skill prose, READMEs, the docs site, docstrings. This includes
  writing a doc that should now exist for behavior that did not exist before.
- **Out of scope** — docs the diff did not invalidate. "While I'm here, the docs could be
  better" is below-bar work like any other; it does not ride along.

A stale doc is not future work. It is a part of the current change that was left unfinished.

## What this rule does not do

- It does not apply retroactively. Existing `followups.md` files and already-filed issues stay
  as they are, still greppable, never re-triaged — re-triaging a legacy backlog is precisely the
  attention cost this bar exists to remove.
- It does not gate shipping. Nothing here blocks a PR; it governs what gets *recorded*.
- It is not audited. The documentation rule in particular is stated, not enforced by a check —
  a deliberate choice, and the honest caveat is that this project's own corpus notes an
  unenforced constraint tends to get violated
  (`2026-08-11-pattern-an-unenforced-constraint-is-aspirational`). If documentation drift shows
  up repeatedly, that entry is the argument for adding the lens to `minerva:review`.

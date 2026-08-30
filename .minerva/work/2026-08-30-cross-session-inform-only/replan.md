# Replan log: cross-session-inform-only

## 2026-08-30 — Reach widened to six pointers; issue #107 adopted

**Original plan**: Reach the receive contract two ways — an information-not-instruction marker
inline in every outbound message, plus **one** terse read-directive pointer squeezed into
`using-minerva/SKILL.md`'s 178 bytes of headroom. Issue #107 (that headroom) was **linked**, not
adopted.

**What changed**: Code review found the reach model did not cover the audience the contract
declares. Finding #2 [high]: the contract says it applies "whenever a message arrives —
mid-`minerva:work`, mid-review, or in a session running no lifecycle skill at all", and the
proposal's `## Why` names the plain `minerva:work` session as "the gap that produced the observed
behaviour" — yet no pointer existed in `work/SKILL.md` or any orchestrator, and `using-minerva`'s
own description tells sessions to skip it "for routine bugfixes, trivial edits, and one-shot
Q&A". The declared audience had no route to the file. Finding #8 [medium]: the pointer left
`using-minerva/SKILL.md` at 52 bytes, making line 24's standing "add a catalog row" instruction
unsatisfiable. Both were escalated; the user chose the wider option in each case. The Skeptic
gate on this replan returned `revise` and its two load-bearing points are folded in below.

**New plan**: (1) **Adopt #107** — move unanchored detail prose out of `using-minerva/SKILL.md`
into its existing `references/guide.md`, restoring at least ~200 bytes of headroom (enough for a
future catalog row), then place the pointer with room to spare; `**Closes**: #107`. (2) Add the
**same pointer sentence, verbatim**, to `work/SKILL.md` and all four `propose-ship*/SKILL.md`
files — one wording reused, never re-derived per file, with **239 bytes** (`propose-ship-balanced`'s
headroom) as the binding ceiling every copy must fit under; the nearby in-flight-check precedent in
those files is a ~500-byte restated block and must **not** be imitated. (3) **Anchor all six
pointers** in `evals/work/contract.json` and the four `evals/propose-ship*/contract.json`, mirroring
the existing anchors those files already carry for the `in-flight-check.md` path — without this,
any one of six near-identical lines could be deleted with nothing going red
(`2026-08-24-pattern-extracted-copies-split-into-shared-and-divergent-halves`).

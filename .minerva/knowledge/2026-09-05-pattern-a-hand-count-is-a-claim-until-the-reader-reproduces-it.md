---
name: a-hand-count-is-a-claim-until-the-reader-reproduces-it
description: Use when a proposal's motivation rests on a number derived by hand (grep, awk, eyeballing logs) and the unit ships a tool that measures the same thing — run the tool against the motivating claim before promote; here it demoted the headline finding from #1 to #2.
metadata:
  type: pattern
---

# A hand-derived count in a proposal is a claim until the shipped reader reproduces it

**Date**: 2026-09-05
**Type**: pattern
**Summary**: run the reader a unit ships against the unit's own motivating numbers; a free-text grep over-counted the headline finding
**Context**: .minerva/work/2026-09-05-balanced-rechecks-folds (see git history if the worktree has been cleaned up)

## Context

The unit that added `decision_telemetry.py` was motivated by a telemetry pass done by hand: grep
and awk over 39 archived scratchpads. One headline claim — "whole-proposal acceptance was auto's
**most**-revised panel gate (~19 revision-involved lines vs ~15 approach, ~8 scope)" — was written
into the proposal, the skill prose, and the draft knowledge entry before the tool existed.

The first thing the tool did, run against the same corpus, was disagree: by tag classification the
revision rounds rank approach **17**/25, whole-proposal **13**/27, scope 7/22, completion 0/18.
The hand pass had grepped `revis` through free text, so a panel line that *mentioned* a revision
anywhere in its rationale counted as a revision at that gate. Whole-proposal was the second-most
revised gate, not the first; the first was the one balanced already reviewed.

## Finding

**A number derived by hand is a claim with the same standing as any other authored-before-evidence
field** ([[2026-08-22-pattern-a-value-written-before-its-evidence-needs-re-verifying]]): it must
be re-verified at the consumer, and when the unit itself ships the consumer, the consumer's first
job is the unit's own motivation. The argument here survived — whole-proposal was still the only
heavy-revision gate run solo, and completion at 0/18 vindicated an earlier choice — but three
surfaces carried a wrong ranking until the reader ran.

The same session produced a second instance: two decision-log lines appended under the wrong
scratchpad header were invisible to the tally, and the tally's count being two short is how they
were found. Both are the shape [[2026-08-11-pattern-the-enumeration-is-what-fails]] describes —
eyeballing a corpus fails in ways that only asking the corpus reveals.

## Implications

- When a unit ships a reader for some corpus, **run it against the unit's own proposal before
  promote**, and treat any disagreement as a correction to the proposal, not to the reader —
  unless the reader can be shown wrong on a specific line.
- Prefer classifying a structured field (a tag, a leading vote fraction) over grepping a marker
  word through free text; the free-text hit rate is inflated by every rationale that *discusses*
  the thing being counted.
- Measure before trusting the last resort ([[2026-08-09-pattern-read-authored-metadata-from-where-it-is]])
  applies to one's own arithmetic too: a corrected number is cheap the day the tool lands and
  expensive once three surfaces cite it.

## Related
- [[2026-08-22-pattern-a-value-written-before-its-evidence-needs-re-verifying]] — builds on
- [[2026-08-11-pattern-the-enumeration-is-what-fails]] — see also
- [[2026-08-09-pattern-read-authored-metadata-from-where-it-is]] — see also
- [[2026-09-05-decision-balanced-rechecks-its-folds]] — see also
